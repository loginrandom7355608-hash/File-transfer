from __future__ import annotations

import logging
import os
import socket
import threading
from pathlib import Path

from app.integrity.hashing import sha256_file
from app.models.resume import ResumeState
from app.networking.transport import SocketTransport
from app.security.path_validator import PathSecurityValidator
from app.state.resume_store import ResumeStore
from app.transfer.duplicate_policy import resolve_duplicate_path

logger = logging.getLogger(__name__)

# How long the receiver waits for the next message from the sender.
# Must be generous enough to cover: SHA256 hashing of large files on the
# sender side, plus disk write time, plus network latency.
# 120 seconds is safe even for large files on slow hardware.
_READ_TIMEOUT_SECONDS = 120.0


class ReceiverService:
    def __init__(
        self,
        *,
        bind_host: str,
        port: int,
        destination_root: Path,
        chunk_size: int = 1024 * 1024,
        duplicate_policy: str = "skip",
    ) -> None:
        self.bind_host = bind_host
        self.port = port
        self.destination_root = destination_root.resolve()
        self.chunk_size = chunk_size
        self.duplicate_policy = duplicate_policy
        self.resume_store = ResumeStore()
        self._path_validator = PathSecurityValidator(self.destination_root)
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._server_socket: socket.socket | None = None
        logger.info(f"ReceiverService initialized with destination: {self.destination_root}")

    def start(self) -> None:
        self.destination_root.mkdir(parents=True, exist_ok=True)
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        self._ready_event.wait(timeout=5)

    def stop(self) -> None:
        self._stop_event.set()
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _serve(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.bind_host, self.port))
            server.listen(1)
            self._server_socket = server
            self._ready_event.set()

            while not self._stop_event.is_set():
                try:
                    server.settimeout(0.5)
                    conn, addr = server.accept()
                    logger.info(f"Connection accepted from {addr}")
                except TimeoutError:
                    continue
                except OSError:
                    break

                # Set generous read timeout on the accepted connection so the
                # receiver doesn't drop the socket while the sender is hashing
                # the next file before sending FILE_START.
                conn.settimeout(_READ_TIMEOUT_SECONDS)
                conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)

                with conn:
                    transport = SocketTransport(conn)
                    try:
                        self._handle_connection(transport)
                    except Exception as exc:
                        logger.error(f"Connection error: {exc}")

    def _handle_connection(self, transport: SocketTransport) -> None:
        hello = transport.receive_json_message()
        if hello.get("type") != "HELLO":
            transport.send_json_message({"type": "ERROR", "reason": "expected_hello"})
            return

        transport.send_json_message({"type": "HELLO_ACK"})

        manifest_message = transport.receive_json_message()
        if manifest_message.get("type") != "MANIFEST":
            transport.send_json_message({"type": "ERROR", "reason": "expected_manifest"})
            return

        files = manifest_message["files"]
        transport.send_json_message({"type": "MANIFEST_RESULT", "accepted": True, "file_count": len(files)})
        logger.info(f"Transfer session started: {len(files)} file(s)")

        for item in files:
            file_start = transport.receive_json_message()
            if file_start.get("type") != "FILE_START":
                transport.send_json_message({"type": "ERROR", "reason": "expected_file_start"})
                return

            relative_path = item["relative_path"]
            logger.info(f"Receiving file: {relative_path}")

            # On path validation failure send FILE_SKIP (not ERROR) so the sender
            # stays in sync and continues with the next file in the batch.
            try:
                final_path = self._path_validator.validate_for_destination(relative_path)
            except ValueError as e:
                logger.error(f"Invalid path rejected: {relative_path} - {e}")
                transport.send_json_message({"type": "FILE_SKIP", "reason": "invalid_file_path"})
                continue

            final_path.parent.mkdir(parents=True, exist_ok=True)

            decision = resolve_duplicate_path(final_path, self.duplicate_policy)
            if decision.action == "fail":
                transport.send_json_message({"type": "FILE_SKIP", "reason": "duplicate_exists"})
                continue
            if decision.action == "skip":
                transport.send_json_message({"type": "FILE_SKIP", "reason": "duplicate_skipped"})
                continue

            target_path = decision.target_path
            part_path = self.resume_store.part_file_path_for(target_path)
            state_path = self.resume_store.state_file_path_for(target_path)

            offset = 0
            if part_path.exists() and state_path.exists():
                consistency = self.resume_store.check_consistency(part_path, state_path)
                if consistency.is_consistent:
                    offset = consistency.actual_part_size

            transport.send_json_message({"type": "FILE_RESUME_INFO", "offset": offset})

            expected_size = int(item["size_bytes"])
            expected_sha256 = str(item["sha256"])
            chunk_size = int(file_start["chunk_size"])
            bytes_written = offset

            mode = "r+b" if part_path.exists() else "wb"
            with part_path.open(mode) as handle:
                if offset:
                    handle.seek(offset)

                while bytes_written < expected_size:
                    remaining = expected_size - bytes_written
                    next_chunk_size = min(chunk_size, remaining)
                    chunk = transport.receive_exactly(next_chunk_size)
                    handle.write(chunk)
                    bytes_written += len(chunk)

                    state = ResumeState(
                        state_version=1,
                        session_id=str(manifest_message["session_id"]),
                        transfer_id=str(item["relative_path"]),
                        relative_path=str(item["relative_path"]),
                        original_filename=Path(relative_path).name,
                        expected_size=expected_size,
                        bytes_written=bytes_written,
                        chunk_size=chunk_size,
                        source_size=expected_size,
                        source_mtime_ns=int(item["modified_time_ns"]),
                        expected_sha256=expected_sha256,
                        status="in_progress",
                        retry_count=0,
                        started_at="2026-07-24T00:00:00Z",
                        updated_at="2026-07-24T00:00:00Z",
                    )
                    self.resume_store.save(state_path, state)

                # Single fsync after all chunks — not after every chunk.
                # Per-chunk fsync caused 2-3 min transfers for small files.
                handle.flush()
                os.fsync(handle.fileno())

            file_complete = transport.receive_json_message()
            if file_complete.get("type") != "FILE_COMPLETE":
                transport.send_json_message({"type": "ERROR", "reason": "expected_file_complete"})
                return

            actual_sha256 = sha256_file(part_path, chunk_size=self.chunk_size)
            if actual_sha256.lower() != expected_sha256.lower():
                transport.send_json_message(
                    {"type": "FILE_HASH_RESULT", "ok": False, "actual_sha256": actual_sha256},
                )
                continue

            if decision.action == "replace" and target_path.exists():
                target_path.unlink()

            part_path.replace(target_path)
            self.resume_store.delete(state_path)
            transport.send_json_message(
                {"type": "FILE_HASH_RESULT", "ok": True, "actual_sha256": actual_sha256},
            )
            logger.info(f"File received OK: {relative_path} ({bytes_written} bytes)")

        done = transport.receive_json_message()
        if done.get("type") == "TRANSFER_COMPLETE":
            transport.send_json_message({"type": "TRANSFER_COMPLETE_ACK"})
            logger.info("Transfer session complete — all files done")