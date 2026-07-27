from __future__ import annotations

from pathlib import Path

from app.state.atomic_json import read_json_file, write_json_atomic


def test_write_json_atomic_creates_file(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    payload = {"session_id": "abc", "bytes_written": 123}

    write_json_atomic(target, payload)

    assert target.exists() is True
    assert read_json_file(target) == payload


def test_write_json_atomic_replaces_existing_file(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    write_json_atomic(target, {"value": 1})

    write_json_atomic(target, {"value": 2, "status": "updated"})

    assert read_json_file(target) == {"value": 2, "status": "updated"}