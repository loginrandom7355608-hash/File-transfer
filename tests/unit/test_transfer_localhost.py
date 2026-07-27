from __future__ import annotations

import socket
import time
from pathlib import Path

from app.models.manifest import FileManifestEntry, TransferManifest
from app.transfer.receiver_service import ReceiverService
from app.transfer.sender_service import SenderService


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_transfer_localhost_single_file(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    destination_root = tmp_path / "dest"
    source_root.mkdir()
    destination_root.mkdir()

    source_file = source_root / "photo.jpg"
    source_bytes = b"abc123" * 10000
    source_file.write_bytes(source_bytes)

    entry = FileManifestEntry(
        relative_path="photo.jpg",
        category="images",
        extension=".jpg",
        size_bytes=len(source_bytes),
        modified_time_ns=source_file.stat().st_mtime_ns,
    )
    manifest = TransferManifest(
        session_id="session-1",
        protocol_version=1,
        source_root=str(source_root),
        selected_categories=["images"],
        files=[entry],
    )

    port = get_free_port()
    receiver = ReceiverService(
        bind_host="127.0.0.1",
        port=port,
        destination_root=destination_root,
        chunk_size=4096,
        duplicate_policy="replace",
    )
    receiver.start()
    time.sleep(0.1)

    sender = SenderService(receiver_host="127.0.0.1", receiver_port=port, chunk_size=4096)
    sender.send_manifest(manifest, source_root)

    receiver.stop()

    received_file = destination_root / "photo.jpg"
    assert received_file.exists() is True
    assert received_file.read_bytes() == source_bytes