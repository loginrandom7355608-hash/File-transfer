from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from app.models.manifest import TransferManifest
from app.transfer.sender_service import SenderService


class SendWorker(QObject):
    finished = Signal()
    failed = Signal(str)
    progress = Signal(str)

    def __init__(
        self,
        *,
        receiver_host: str,
        receiver_port: int,
        manifest: TransferManifest,
        source_root: str,
        chunk_size: int = 4 * 1024 * 1024,
        heavy_mode: bool = False,
    ) -> None:
        super().__init__()
        self.receiver_host = receiver_host
        self.receiver_port = receiver_port
        self.manifest = manifest
        self.source_root = source_root
        self.chunk_size = chunk_size
        self.heavy_mode = heavy_mode

    @Slot()
    def run(self) -> None:
        try:
            mode_label = "heavy video" if self.heavy_mode else "standard"
            self.progress.emit(f"Connecting to receiver ({mode_label} mode)...")
            sender = SenderService(
                receiver_host=self.receiver_host,
                receiver_port=self.receiver_port,
                chunk_size=self.chunk_size,
                heavy_mode=self.heavy_mode,
            )
            sender.send_manifest(self.manifest, Path(self.source_root))
            self.progress.emit("Transfer completed successfully.")
            self.finished.emit()
        except Exception as exc:
            self.failed.emit(str(exc))