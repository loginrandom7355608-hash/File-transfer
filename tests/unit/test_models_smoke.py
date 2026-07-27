from __future__ import annotations

from app.models.manifest import FileManifestEntry, TransferManifest
from app.models.reports import FileTransferReport, TransferSessionReport


def test_manifest_total_size() -> None:
    manifest = TransferManifest(
        session_id="abc",
        protocol_version=1,
        source_root="C:\\Source",
        selected_categories=["images"],
        files=[
            FileManifestEntry(
                relative_path="a.jpg",
                category="images",
                size_bytes=100,
                extension=".jpg",
                modified_time_ns=1,
            ),
            FileManifestEntry(
                relative_path="b.jpg",
                category="images",
                size_bytes=200,
                extension=".jpg",
                modified_time_ns=2,
            ),
        ],
    )
    assert manifest.total_size_bytes() == 300
    assert manifest.total_file_count() == 2


def test_report_to_dict() -> None:
    item = FileTransferReport(relative_path="a.jpg", status="completed", size_bytes=10)
    session = TransferSessionReport(
        session_id="s1",
        sender_endpoint="1.1.1.1:1",
        receiver_endpoint="2.2.2.2:2",
        completed=[item],
    )
    data = session.to_dict()
    assert data["session_id"] == "s1"
    assert data["completed"][0]["status"] == "completed"