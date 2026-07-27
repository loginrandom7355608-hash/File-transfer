from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(420, 180)

        self.theme_input = QLineEdit("system")
        self.debug_checkbox = QCheckBox("Enable debug logging")

        form = QFormLayout()
        form.addRow("Theme", self.theme_input)
        form.addRow("", self.debug_checkbox)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.close_button)
        self.setLayout(layout)