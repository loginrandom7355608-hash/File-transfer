from __future__ import annotations

from pathlib import Path
from typing import Any

from app.state.atomic_json import read_json_file, write_json_atomic


class SessionStore:
    def load(self, path: Path) -> dict[str, Any]:
        return read_json_file(path)

    def save(self, path: Path, payload: dict[str, Any]) -> None:
        write_json_atomic(path, payload)