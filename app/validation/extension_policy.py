from __future__ import annotations

from dataclasses import dataclass, field

from app.constants import (
    DEFAULT_ALLOWED_IMAGE_EXTENSIONS,
    DEFAULT_ALLOWED_VIDEO_EXTENSIONS,
    DEFAULT_BLOCKED_EXTENSIONS,
)


@dataclass(slots=True)
class ExtensionPolicy:
    allowed_images: set[str] = field(default_factory=lambda: set(DEFAULT_ALLOWED_IMAGE_EXTENSIONS))
    allowed_videos: set[str] = field(default_factory=lambda: set(DEFAULT_ALLOWED_VIDEO_EXTENSIONS))
    blocked_extensions: set[str] = field(default_factory=lambda: set(DEFAULT_BLOCKED_EXTENSIONS))

    def normalize_extension(self, extension: str) -> str:
        ext = extension.strip().lower()
        if not ext.startswith(".") and ext:
            ext = f".{ext}"
        return ext

    def is_blocked(self, extension: str) -> bool:
        return self.normalize_extension(extension) in self.blocked_extensions

    def allowed_category_for_extension(self, extension: str) -> str | None:
        normalized = self.normalize_extension(extension)
        if normalized in self.allowed_images:
            return "images"
        if normalized in self.allowed_videos:
            return "videos"
        return None

    def is_allowed(self, extension: str) -> bool:
        return self.allowed_category_for_extension(extension) is not None