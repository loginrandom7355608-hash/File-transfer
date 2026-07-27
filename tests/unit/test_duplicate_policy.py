from __future__ import annotations

from pathlib import Path

from app.transfer.duplicate_policy import resolve_duplicate_path


def test_duplicate_policy_skip_existing(tmp_path: Path) -> None:
    target = tmp_path / "photo.jpg"
    target.write_bytes(b"x")

    result = resolve_duplicate_path(target, "skip")

    assert result.action == "skip"
    assert result.target_path == target


def test_duplicate_policy_rename_incoming(tmp_path: Path) -> None:
    target = tmp_path / "photo.jpg"
    target.write_bytes(b"x")

    result = resolve_duplicate_path(target, "rename_incoming")

    assert result.action == "write"
    assert result.target_path != target
    assert result.target_path.name == "photo (1).jpg"