from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from app.transfer.receiver_service import ReceiverService


class ReceiveWorker(QObject):
    started_signal = Signal()
    stopped_signal = Signal()
    failed = Signal(str)

    def __init__(
        self,
        *,
        bind_host: str,
        port: int,
        destination_root: str,
        chunk_size: int = 4096,
        duplicate_policy: str = "replace",
    ) -> None:
        super().__init__()
        self.bind_host = bind_host
        self.port = port
        self.destination_root = destination_root
        self.chunk_size = chunk_size
        self.duplicate_policy = duplicate_policy
        self._service: ReceiverService | None = None

    @Slot()
    def start_listening(self) -> None:
        try:
            self._service = ReceiverService(
                bind_host=self.bind_host,
                port=self.port,
                destination_root=Path(self.destination_root),
                chunk_size=self.chunk_size,
                duplicate_policy=self.duplicate_policy,
            )
            self._service.start()
            self.started_signal.emit()
        except Exception as exc:
            self.failed.emit(str(exc))

    @Slot()
    def stop_listening(self) -> None:
        try:
            if self._service is not None:
                self._service.stop()
            self.stopped_signal.emit()
        except Exception as exc:
            self.failed.emit(str(exc))