from __future__ import annotations

import socket
from pathlib import Path

from app.integrity.hashing import sha256_file
from app.models.manifest import FileManifestEntry, TransferManifest
from app.networking.transport import SocketTransport
from app.transfer.chunk_io import iter_file_chunks

# 4MB chunks — optimal for Ethernet transfers (LAN saturates quickly at this size)
# Original was 4KB which caused ~1000x more send() calls per file
_CHUNK_SIZE = 4 * 1024 * 1024

# How long to wait for the receiver to respond to any message.
# Set generously (120s) to allow for large file SHA256 hashing on slow hardware
# without the connection dropping between files.
_READ_TIMEOUT_SECONDS = 120.0


class SenderService:
    def __init__(self, *, receiver_host: str, receiver_port: int, chunk_size: int = _CHUNK_SIZE) -> None:
        self.receiver_host = receiver_host
        self.receiver_port = receiver_port
        self.chunk_size = chunk_size

    def send_manifest(self, manifest: TransferManifest, source_root: Path) -> None:
        with socket.create_connection((self.receiver_host, self.receiver_port), timeout=10) as sock:
            # Large send/recv buffers for fast LAN throughput
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4 * 1024 * 1024)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
            # TCP keepalive — detects dead connections on a direct cable
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # Read timeout — prevents indefinite blocking
            sock.settimeout(_READ_TIMEOUT_SECONDS)

            transport = SocketTransport(sock)

            transport.send_json_message({"type": "HELLO"})
            hello_ack = transport.receive_json_message()
            if hello_ack.get("type") != "HELLO_ACK":
                raise RuntimeError("receiver_did_not_ack_hello")

            # Hash each file exactly once before sending the manifest.
            # Original code hashed each file twice (once in _entry_to_payload,
            # again in _send_one_file), doubling disk read time for large files.
            file_hashes: dict[str, str] = {}
            files_payload = []
            for entry in manifest.files:
                source_path = source_root / Path(entry.relative_path)
                sha256 = sha256_file(source_path, chunk_size=self.chunk_size)
                file_hashes[entry.relative_path] = sha256
                files_payload.append(self._entry_to_payload(entry, sha256))

            transport.send_json_message(
                {
                    "type": "MANIFEST",
                    "session_id": manifest.session_id,
                    "protocol_version": manifest.protocol_version,
                    "files": files_payload,
                },
            )

            manifest_result = transport.receive_json_message()
            if manifest_result.get("type") != "MANIFEST_RESULT" or not manifest_result.get("accepted"):
                raise RuntimeError("manifest_rejected")

            for entry in manifest.files:
                self._send_one_file(
                    transport,
                    source_root,
                    entry,
                    precomputed_sha256=file_hashes[entry.relative_path],
                )

            transport.send_json_message({"type": "TRANSFER_COMPLETE"})
            final_ack = transport.receive_json_message()
            if final_ack.get("type") != "TRANSFER_COMPLETE_ACK":
                raise RuntimeError("missing_transfer_complete_ack")

    def _send_one_file(
        self,
        transport: SocketTransport,
        source_root: Path,
        entry: FileManifestEntry,
        precomputed_sha256: str,
    ) -> None:
        transport.send_json_message(
            {
                "type": "FILE_START",
                "relative_path": entry.relative_path,
                "chunk_size": self.chunk_size,
            },
        )

        response = transport.receive_json_message()

        if response.get("type") == "FILE_SKIP":
            return
        if response.get("type") == "ERROR":
            reason = response.get("reason", "unknown")
            raise RuntimeError(f"receiver_rejected_file: {reason}")
        if response.get("type") != "FILE_RESUME_INFO":
            raise RuntimeError(f"expected_file_resume_info, got: {response.get('type')}")

        offset = int(response["offset"])
        source_path = source_root / Path(entry.relative_path)

        for chunk in iter_file_chunks(source_path, start_offset=offset, chunk_size=self.chunk_size):
            transport.send_all(chunk)

        transport.send_json_message(
            {
                "type": "FILE_COMPLETE",
                "relative_path": entry.relative_path,
                "sha256": precomputed_sha256,
            },
        )

        hash_result = transport.receive_json_message()
        if hash_result.get("type") != "FILE_HASH_RESULT":
            raise RuntimeError("expected_file_hash_result")
        if not hash_result.get("ok"):
            raise RuntimeError("receiver_reported_hash_mismatch")

    def _entry_to_payload(self, entry: FileManifestEntry, sha256: str) -> dict[str, object]:
        return {
            "relative_path": entry.relative_path,
            "category": entry.category,
            "extension": entry.extension,
            "size_bytes": entry.size_bytes,
            "modified_time_ns": entry.modified_time_ns,
            "sha256": sha256,
        }