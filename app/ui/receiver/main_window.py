from __future__ import annotations

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.dialogs.settings_dialog import SettingsDialog
from app.ui.workers.receive_worker import ReceiveWorker


class ReceiverMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Safe Media Transfer - Receiver")
        self.resize(760, 480)

        self._receive_thread: QThread | None = None
        self._receive_worker: ReceiveWorker | None = None

        central = QWidget()
        self.setCentralWidget(central)

        self.destination_input = QLineEdit()
        self.bind_ip_input = QLineEdit("127.0.0.1")
        self.port_input = QLineEdit("5001")
        self.status_label = QLabel("Stopped")
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        self.browse_button = QPushButton("Browse")
        self.start_button = QPushButton("Start Listener")
        self.stop_button = QPushButton("Stop Listener")
        self.settings_button = QPushButton("Settings")

        form = QFormLayout()
        form.addRow("Destination Root", self.destination_input)
        form.addRow("Bind IP", self.bind_ip_input)
        form.addRow("Port", self.port_input)

        button_row = QHBoxLayout()
        button_row.addWidget(self.browse_button)
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.stop_button)
        button_row.addWidget(self.settings_button)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(button_row)
        layout.addWidget(QLabel("Status"))
        layout.addWidget(self.status_label)
        layout.addWidget(QLabel("Logs"))
        layout.addWidget(self.log_output)

        central.setLayout(layout)

        self.browse_button.clicked.connect(self._choose_destination)
        self.start_button.clicked.connect(self._start_listener)
        self.stop_button.clicked.connect(self._stop_listener)
        self.settings_button.clicked.connect(self._open_settings)

    def _choose_destination(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.destination_input.setText(folder)

    def _start_listener(self) -> None:
        destination_root = self.destination_input.text().strip()
        bind_ip = self.bind_ip_input.text().strip()
        port_text = self.port_input.text().strip()

        if not destination_root or not bind_ip or not port_text:
            QMessageBox.warning(self, "Missing values", "Destination root, bind IP, and port are required.")
            return

        self._receive_thread = QThread(self)
        self._receive_worker = ReceiveWorker(
            bind_host=bind_ip,
            port=int(port_text),
            destination_root=destination_root,
            chunk_size=4096,
            duplicate_policy="replace",
        )
        self._receive_worker.moveToThread(self._receive_thread)

        self._receive_thread.started.connect(self._receive_worker.start_listening)
        self._receive_worker.started_signal.connect(self._listener_started)
        self._receive_worker.stopped_signal.connect(self._listener_stopped)
        self._receive_worker.failed.connect(self._worker_failed)

        self._receive_thread.start()
        self._append_log("Starting listener...")

    def _stop_listener(self) -> None:
        if self._receive_worker is not None:
            self._receive_worker.stop_listening()

        if self._receive_thread is not None:
            self._receive_thread.quit()
            self._receive_thread.wait()
            self._receive_thread.deleteLater()
            self._receive_thread = None

    def _listener_started(self) -> None:
        self.status_label.setText("Listening")
        self._append_log("Receiver is listening.")

    def _listener_stopped(self) -> None:
        self.status_label.setText("Stopped")
        self._append_log("Receiver stopped.")

    def _worker_failed(self, message: str) -> None:
        self.status_label.setText("Error")
        self._append_log(f"Error: {message}")
        QMessageBox.critical(self, "Receiver error", message)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()

    def _append_log(self, message: str) -> None:
        self.log_output.append(message)