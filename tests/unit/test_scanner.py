from __future__ import annotations

from pathlib import Path

from app.scanning.scanner import FileScanner
from app.validation.extension_policy import ExtensionPolicy
from app.validation.signature_policy import SignaturePolicy


def test_scanner_collects_allowed_files_without_signature_check(tmp_path: Path) -> None:
    (tmp_path / "photos").mkdir()
    (tmp_path / "videos").mkdir()
    (tmp_path / "photos" / "one.jpg").write_bytes(b"fakejpg")
    (tmp_path / "videos" / "clip.mp4").write_bytes(b"fakemp4")
    (tmp_path / "script.ps1").write_text("Write-Host hacked", encoding="utf-8")
    (tmp_path / "note.txt").write_text("hello", encoding="utf-8")

    scanner = FileScanner(
        extension_policy=ExtensionPolicy(),
        signature_policy=SignaturePolicy(ExtensionPolicy(), enabled=False),
    )
    result = scanner.scan(tmp_path)

    assert result.category_count("images") == 1
    assert result.category_count("videos") == 1
    assert len(result.skipped) == 2
    assert result.images[0].relative_path == "photos/one.jpg"
    assert result.videos[0].relative_path == "videos/clip.mp4"