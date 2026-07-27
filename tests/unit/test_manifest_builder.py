from __future__ import annotations

from app.models.manifest import FileManifestEntry
from app.scanning.manifest_builder import build_transfer_manifest


def test_build_transfer_manifest_filters_selected_categories() -> None:
    entries = [
        FileManifestEntry(
            relative_path="a.jpg",
            category="images",
            extension=".jpg",
            size_bytes=10,
            modified_time_ns=1,
        ),
        FileManifestEntry(
            relative_path="b.mp4",
            category="videos",
            extension=".mp4",
            size_bytes=20,
            modified_time_ns=2,
        ),
    ]

    manifest = build_transfer_manifest(
        session_id="session-1",
        source_root="C:\\Source",
        selected_categories=["images"],
        entries=entries,
    )

    assert manifest.total_file_count() == 1
    assert manifest.total_size_bytes() == 10
    assert manifest.files[0].relative_path == "a.jpg"