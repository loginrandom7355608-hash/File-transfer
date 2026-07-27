from __future__ import annotations

import uuid
from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.manifest import FileManifestEntry
from app.scanning.manifest_builder import build_transfer_manifest
from app.ui.dialogs.settings_dialog import SettingsDialog
from app.ui.workers.scan_worker import ScanWorker
from app.ui.workers.send_worker import SendWorker


class SenderMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Safe Media Transfer - Sender")
        self.resize(820, 560)

        self._scan_result = None
        self._scan_thread: QThread | None = None
        self._scan_worker: ScanWorker | None = None
        self._send_thread: QThread | None = None
        self._send_worker: SendWorker | None = None

        central = QWidget()
        self.setCentralWidget(central)

        self.receiver_ip_input = QLineEdit("127.0.0.1")
        self.port_input = QLineEdit("5001")
        self.source_folder_input = QLineEdit()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        self.browse_button = QPushButton("Browse")
        self.scan_button = QPushButton("Scan")
        self.transfer_images_button = QPushButton("Transfer Images")
        self.transfer_videos_button = QPushButton("Transfer Videos")
        self.transfer_both_button = QPushButton("Transfer Both")
        self.settings_button = QPushButton("Settings")

        self.overall_progress = QProgressBar()
        self.current_progress = QProgressBar()

        self.summary_label = QLabel("No scan results yet.")
        self.status_label = QLabel("Idle")

        top_form = QFormLayout()
        top_form.addRow("Receiver IP", self.receiver_ip_input)
        top_form.addRow("Port", self.port_input)
        top_form.addRow("Source Folder", self.source_folder_input)

        folder_row = QHBoxLayout()
        folder_row.addWidget(self.browse_button)
        folder_row.addWidget(self.scan_button)

        transfer_row = QHBoxLayout()
        transfer_row.addWidget(self.transfer_images_button)
        transfer_row.addWidget(self.transfer_videos_button)
        transfer_row.addWidget(self.transfer_both_button)
        transfer_row.addWidget(self.settings_button)

        summary_box = QGroupBox("Scan Summary")
        summary_layout = QVBoxLayout()
        summary_layout.addWidget(self.summary_label)
        summary_box.setLayout(summary_layout)

        layout = QVBoxLayout()
        layout.addLayout(top_form)
        layout.addLayout(folder_row)
        layout.addWidget(summary_box)
        layout.addLayout(transfer_row)
        layout.addWidget(QLabel("Current File Progress"))
        layout.addWidget(self.current_progress)
        layout.addWidget(QLabel("Overall Progress"))
        layout.addWidget(self.overall_progress)
        layout.addWidget(QLabel("Status"))
        layout.addWidget(self.status_label)
        layout.addWidget(QLabel("Logs"))
        layout.addWidget(self.log_output)

        central.setLayout(layout)

        self.browse_button.clicked.connect(self._choose_source_folder)
        self.scan_button.clicked.connect(self._start_scan)
        self.transfer_images_button.clicked.connect(lambda: self._start_transfer(["images"]))
        self.transfer_videos_button.clicked.connect(lambda: self._start_transfer(["videos"]))
        self.transfer_both_button.clicked.connect(lambda: self._start_transfer(["images", "videos"]))
        self.settings_button.clicked.connect(self._open_settings)

    def _choose_source_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_folder_input.setText(folder)

    def _start_scan(self) -> None:
        source_folder = self.source_folder_input.text().strip()
        if not source_folder:
            QMessageBox.warning(self, "Missing folder", "Select a source folder first.")
            return

        if self._scan_thread is not None and self._scan_thread.isRunning():
            self._append_log("Scan already in progress, ignoring duplicate click.")
            return

        self._append_log("Starting scan...")
        self.status_label.setText("Scanning...")
        self.scan_button.setEnabled(False)

        self._scan_thread = QThread(self)
        self._scan_worker = ScanWorker(source_folder)
        self._scan_worker.moveToThread(self._scan_thread)

        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_worker.progress.connect(self._append_log)
        self._scan_worker.finished.connect(self._handle_scan_finished)
        self._scan_worker.failed.connect(self._handle_worker_error)
        self._scan_worker.finished.connect(self._scan_thread.quit)
        self._scan_worker.failed.connect(self._scan_thread.quit)
        self._scan_thread.finished.connect(self._on_scan_thread_finished)

        self._scan_thread.start()

    def _on_scan_thread_finished(self) -> None:
        self.scan_button.setEnabled(True)
        if self._scan_worker is not None:
            self._scan_worker.deleteLater()
            self._scan_worker = None
        if self._scan_thread is not None:
            self._scan_thread.deleteLater()
            self._scan_thread = None

    def _handle_scan_finished(self, result) -> None:
        self._scan_result = result
        image_count = len(result.images)
        image_size = sum(item.size_bytes for item in result.images)
        video_count = len(result.videos)
        video_size = sum(item.size_bytes for item in result.videos)
        skipped_count = len(result.skipped)
        warning_count = len(result.warnings)

        self.summary_label.setText(
            f"Images: {image_count} files / {image_size} bytes | "
            f"Videos: {video_count} files / {video_size} bytes | "
            f"Skipped: {skipped_count} | Warnings: {warning_count}"
        )
        self.status_label.setText("Scan complete")
        self._append_log("Scan completed.")

    def _start_transfer(self, categories: list[str]) -> None:
        if self._scan_result is None:
            QMessageBox.warning(self, "No scan", "Run a scan before transfer.")
            return

        source_root = self.source_folder_input.text().strip()
        receiver_ip = self.receiver_ip_input.text().strip()
        port_text = self.port_input.text().strip()

        if not source_root or not receiver_ip or not port_text:
            QMessageBox.warning(self, "Missing values", "Receiver IP, port, and source folder are required.")
            return

        entries: list[FileManifestEntry] = []
        if "images" in categories:
            entries.extend(self._scan_result.images)
        if "videos" in categories:
            entries.extend(self._scan_result.videos)

        manifest = build_transfer_manifest(
            session_id=str(uuid.uuid4()),
            source_root=source_root,
            selected_categories=categories,
            entries=entries,
        )

        self._append_log("Starting transfer...")
        self.status_label.setText("Transferring...")

        self._send_thread = QThread(self)
        self._send_worker = SendWorker(
            receiver_host=receiver_ip,
            receiver_port=int(port_text),
            manifest=manifest,
            source_root=source_root,
            chunk_size=4 * 1024 * 1024,
        )
        self._send_worker.moveToThread(self._send_thread)

        self._send_thread.started.connect(self._send_worker.run)
        self._send_worker.progress.connect(self._append_log)
        self._send_worker.finished.connect(self._handle_send_finished)
        self._send_worker.failed.connect(self._handle_worker_error)
        self._send_worker.finished.connect(self._send_thread.quit)
        self._send_worker.failed.connect(self._send_thread.quit)
        self._send_thread.finished.connect(self._on_send_thread_finished)

        self._send_thread.start()

    def _on_send_thread_finished(self) -> None:
        if self._send_worker is not None:
            self._send_worker.deleteLater()
            self._send_worker = None
        if self._send_thread is not None:
            self._send_thread.deleteLater()
            self._send_thread = None

    def _handle_send_finished(self) -> None:
        self.status_label.setText("Transfer complete")
        self.current_progress.setValue(100)
        self.overall_progress.setValue(100)
        self._append_log("Transfer completed.")

    def _handle_worker_error(self, message: str) -> None:
        self.status_label.setText("Error")
        self._append_log(f"Error: {message}")
        QMessageBox.critical(self, "Worker error", message)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()

    def _append_log(self, message: str) -> None:
        self.log_output.append(message)