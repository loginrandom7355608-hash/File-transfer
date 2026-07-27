from __future__ import annotations

from pathlib import Path


def resolve_config_path(preferred: Path) -> Path:
    if preferred.exists():
        return preferred

    example = Path("config.example.toml")
    if example.exists():
        return example

    return preferred