from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class ResumeState:
    state_version: int
    session_id: str
    transfer_id: str
    relative_path: str
    original_filename: str
    expected_size: int
    bytes_written: int
    chunk_size: int
    source_size: int
    source_mtime_ns: int
    expected_sha256: str | None
    status: str
    retry_count: int
    started_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResumeState":
        return cls(
            state_version=int(data["state_version"]),
            session_id=str(data["session_id"]),
            transfer_id=str(data["transfer_id"]),
            relative_path=str(data["relative_path"]),
            original_filename=str(data["original_filename"]),
            expected_size=int(data["expected_size"]),
            bytes_written=int(data["bytes_written"]),
            chunk_size=int(data["chunk_size"]),
            source_size=int(data["source_size"]),
            source_mtime_ns=int(data["source_mtime_ns"]),
            expected_sha256=data.get("expected_sha256"),
            status=str(data["status"]),
            retry_count=int(data["retry_count"]),
            started_at=str(data["started_at"]),
            updated_at=str(data["updated_at"]),
        )