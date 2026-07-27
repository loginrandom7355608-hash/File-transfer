from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.config.loader import load_app_config
from app.logging_setup.logging_factory import configure_logging
from app.ui.sender.main_window import SenderMainWindow
from app.utils.platform_paths import resolve_config_path


def main() -> int:
    config_path = resolve_config_path(Path("config.toml"))
    config = load_app_config(config_path)
    configure_logging(config)
    logging.getLogger(__name__).info("sender.application_started")

    app = QApplication(sys.argv)
    window = SenderMainWindow()
    window.resize(820, 560)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())