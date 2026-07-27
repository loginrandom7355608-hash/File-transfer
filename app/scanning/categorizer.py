from __future__ import annotations

from app.constants import DEFAULT_ALLOWED_IMAGE_EXTENSIONS, DEFAULT_ALLOWED_VIDEO_EXTENSIONS


def category_for_extension(extension: str) -> str | None:
    normalized = extension.lower().strip()
    if normalized in DEFAULT_ALLOWED_IMAGE_EXTENSIONS:
        return "images"
    if normalized in DEFAULT_ALLOWED_VIDEO_EXTENSIONS:
        return "videos"
    return None