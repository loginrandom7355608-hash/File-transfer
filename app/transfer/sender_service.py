from __future__ import annotations

import hashlib
import socket
from pathlib import Path

from app.models.manifest import FileManifestEntry, TransferManifest
from app.networking.transport import SocketTransport
from app.transfer.chunk_io import iter_file_chunks

_CHUNK_SIZE = 4 * 1024 * 1024
_HEAVY_CHUNK_SIZE = 16 * 1024 * 1024
_READ_TIMEOUT_SECONDS = 120.0


class SenderService:
    def __init__(
        self,
        *,
        receiver_host: str,
        receiver_port: int,
        chunk_size: int = _CHUNK_SIZE,
        heavy_mode: bool = False,
    ) -> None:
        self.receiver_host = receiver_host
        self.receiver_port = receiver_port
        self.heavy_mode = heavy_mode
        self.chunk_size = _HEAVY_CHUNK_SIZE if heavy_mode else chunk_size

    def send_manifest(self, manifest: TransferManifest, source_root: Path) -> None:
        with socket.create_connection((self.receiver_host, self.receiver_port), timeout=10) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4 * 1024 * 1024)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.settimeout(_READ_TIMEOUT_SECONDS)

            transport = SocketTransport(sock)

            transport.send_json_message({"type": "HELLO"})
            hello_ack = transport.receive_json_message()
            if hello_ack.get("type") != "HELLO_ACK":
                raise RuntimeError("receiver_did_not_ack_hello")

            if self.heavy_mode:
                # Heavy mode: skip pre-hashing entirely.
                # Hash is computed WHILE chunks are sent — one disk read total.
                files_payload = [self._entry_to_payload_no_hash(entry) for entry in manifest.files]
                transport.send_json_message({
                    "type": "MANIFEST",
                    "session_id": manifest.session_id,
                    "protocol_version": manifest.protocol_version,
                    "heavy_mode": True,
                    "files": files_payload,
                })
                manifest_result = transport.receive_json_message()
                if manifest_result.get("type") != "MANIFEST_RESULT" or not manifest_result.get("accepted"):
                    raise RuntimeError("manifest_rejected")
                for entry in manifest.files:
                    self._send_one_file_streaming(transport, source_root, entry)
            else:
                # Standard mode: pre-hash every file then send.
                file_hashes: dict[str, str] = {}
                files_payload = []
                for entry in manifest.files:
                    source_path = source_root / Path(entry.relative_path)
                    sha256 = _sha256_file(source_path, chunk_size=self.chunk_size)
                    file_hashes[entry.relative_path] = sha256
                    files_payload.append(self._entry_to_payload(entry, sha256))
                transport.send_json_message({
                    "type": "MANIFEST",
                    "session_id": manifest.session_id,
                    "protocol_version": manifest.protocol_version,
                    "heavy_mode": False,
                    "files": files_payload,
                })
                manifest_result = transport.receive_json_message()
                if manifest_result.get("type") != "MANIFEST_RESULT" or not manifest_result.get("accepted"):
                    raise RuntimeError("manifest_rejected")
                for entry in manifest.files:
                    self._send_one_file(
                        transport, source_root, entry,
                        precomputed_sha256=file_hashes[entry.relative_path],
                    )

            transport.send_json_message({"type": "TRANSFER_COMPLETE"})
            final_ack = transport.receive_json_message()
            if final_ack.get("type") != "TRANSFER_COMPLETE_ACK":
                raise RuntimeError("missing_transfer_complete_ack")

    def _send_one_file(self, transport, source_root, entry, precomputed_sha256):
        transport.send_json_message({
            "type": "FILE_START",
            "relative_path": entry.relative_path,
            "chunk_size": self.chunk_size,
        })
        response = transport.receive_json_message()
        if response.get("type") == "FILE_SKIP":
            return
        if response.get("type") == "ERROR":
            raise RuntimeError(f"receiver_rejected_file: {response.get('reason', 'unknown')}")
        if response.get("type") != "FILE_RESUME_INFO":
            raise RuntimeError(f"expected_file_resume_info, got: {response.get('type')}")
        offset = int(response["offset"])
        source_path = source_root / Path(entry.relative_path)
        for chunk in iter_file_chunks(source_path, start_offset=offset, chunk_size=self.chunk_size):
            transport.send_all(chunk)
        transport.send_json_message({
            "type": "FILE_COMPLETE",
            "relative_path": entry.relative_path,
            "sha256": precomputed_sha256,
        })
        hash_result = transport.receive_json_message()
        if hash_result.get("type") != "FILE_HASH_RESULT":
            raise RuntimeError("expected_file_hash_result")
        if not hash_result.get("ok"):
            raise RuntimeError("receiver_reported_hash_mismatch")

    def _send_one_file_streaming(self, transport, source_root, entry):
        """
        Send file while computing SHA256 simultaneously — single disk read.
        Normal mode: read file once to hash + read again to send = 2 reads.
        Heavy mode:  read file once, hash each chunk as it leaves = 1 read.
        For a 10GB video this cuts sender disk I/O roughly in half.
        """
        transport.send_json_message({
            "type": "FILE_START",
            "relative_path": entry.relative_path,
            "chunk_size": self.chunk_size,
            "streaming_hash": True,
        })
        response = transport.receive_json_message()
        if response.get("type") == "FILE_SKIP":
            return
        if response.get("type") == "ERROR":
            raise RuntimeError(f"receiver_rejected_file: {response.get('reason', 'unknown')}")
        if response.get("type") != "FILE_RESUME_INFO":
            raise RuntimeError(f"expected_file_resume_info, got: {response.get('type')}")
        offset = int(response["offset"])
        source_path = source_root / Path(entry.relative_path)
        digest = hashlib.sha256()
        # If resuming, hash the already-received bytes first so the final
        # hash covers the complete file from byte 0
        if offset > 0:
            bytes_counted = 0
            for chunk in iter_file_chunks(source_path, start_offset=0, chunk_size=self.chunk_size):
                remaining = offset - bytes_counted
                if remaining <= 0:
                    break
                slice_chunk = chunk[:remaining]
                digest.update(slice_chunk)
                bytes_counted += len(slice_chunk)
        # Stream hash: update digest with each chunk as it goes out the wire
        for chunk in iter_file_chunks(source_path, start_offset=offset, chunk_size=self.chunk_size):
            digest.update(chunk)
            transport.send_all(chunk)
        transport.send_json_message({
            "type": "FILE_COMPLETE",
            "relative_path": entry.relative_path,
            "sha256": digest.hexdigest(),
        })
        hash_result = transport.receive_json_message()
        if hash_result.get("type") != "FILE_HASH_RESULT":
            raise RuntimeError("expected_file_hash_result")
        if not hash_result.get("ok"):
            raise RuntimeError("receiver_reported_hash_mismatch")

    def _entry_to_payload(self, entry, sha256):
        return {
            "relative_path": entry.relative_path,
            "category": entry.category,
            "extension": entry.extension,
            "size_bytes": entry.size_bytes,
            "modified_time_ns": entry.modified_time_ns,
            "sha256": sha256,
        }

    def _entry_to_payload_no_hash(self, entry):
        return {
            "relative_path": entry.relative_path,
            "category": entry.category,
            "extension": entry.extension,
            "size_bytes": entry.size_bytes,
            "modified_time_ns": entry.modified_time_ns,
            "sha256": "",
        }


def _sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()