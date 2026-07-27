from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SenderScanSummary:
    image_count: int
    image_size_bytes: int
    video_count: int
    video_size_bytes: int
    skipped_count: int
    warning_count: int