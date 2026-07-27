from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class FileManifestEntry:
    relative_path: str
    category: str
    extension: str
    size_bytes: int
    modified_time_ns: int
    signature_extension: str | None = None
    mime_type: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "category": self.category,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "modified_time_ns": self.modified_time_ns,
            "signature_extension": self.signature_extension,
            "mime_type": self.mime_type,
            "warnings": list(self.warnings),
        }


@dataclass(slots=True)
class FileTransferReport:
    relative_path: str
    status: str
    size_bytes: int
    expected_sha256: str | None = None
    actual_sha256: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "status": self.status,
            "size_bytes": self.size_bytes,
            "expected_sha256": self.expected_sha256,
            "actual_sha256": self.actual_sha256,
            "reason": self.reason,
        }


@dataclass(slots=True)
class TransferSessionReport:
    session_id: str
    sender_endpoint: str
    receiver_endpoint: str
    completed: list[FileTransferReport] = field(default_factory=list)
    skipped: list[FileTransferReport] = field(default_factory=list)
    failed: list[FileTransferReport] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "sender_endpoint": self.sender_endpoint,
            "receiver_endpoint": self.receiver_endpoint,
            "completed": [item.to_dict() for item in self.completed],
            "skipped": [item.to_dict() for item in self.skipped],
            "failed": [item.to_dict() for item in self.failed],
        }


@dataclass(slots=True)
class TransferManifest:
    session_id: str
    source_root: str
    selected_categories: list[str]
    protocol_version: int = 1
    files: list[FileManifestEntry] = field(default_factory=list)

    def total_size_bytes(self) -> int:
        return sum(item.size_bytes for item in self.files)

    def total_file_count(self) -> int:
        return len(self.files)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "protocol_version": self.protocol_version,
            "source_root": self.source_root,
            "selected_categories": self.selected_categories,
            "files": [item.to_dict() for item in self.files],
        }


@dataclass(slots=True)
class ScanIssue:
    path: str
    reason: str


@dataclass(slots=True)
class ScanResult:
    source_root: str
    images: list[FileManifestEntry] = field(default_factory=list)
    videos: list[FileManifestEntry] = field(default_factory=list)
    skipped: list[ScanIssue] = field(default_factory=list)
    warnings: list[ScanIssue] = field(default_factory=list)

    def category_entries(self, category: str) -> list[FileManifestEntry]:
        if category == "images":
            return self.images
        if category == "videos":
            return self.videos
        return []

    def category_count(self, category: str) -> int:
        return len(self.category_entries(category))

    def category_size_bytes(self, category: str) -> int:
        return sum(item.size_bytes for item in self.category_entries(category))