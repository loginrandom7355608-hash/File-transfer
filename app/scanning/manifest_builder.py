from __future__ import annotations

from app.models.manifest import FileManifestEntry, TransferManifest


def build_transfer_manifest(
    *,
    session_id: str,
    source_root: str,
    selected_categories: list[str],
    entries: list[FileManifestEntry],
) -> TransferManifest:
    selected = {item.strip().lower() for item in selected_categories if item.strip()}
    filtered_entries = [entry for entry in entries if entry.category in selected]

    return TransferManifest(
        session_id=session_id,
        protocol_version=1,
        source_root=source_root,
        selected_categories=sorted(selected),
        files=filtered_entries,
    )