from __future__ import annotations

from app.validation.extension_policy import ExtensionPolicy


def test_blocked_extension_detected() -> None:
    policy = ExtensionPolicy()
    assert policy.is_blocked(".exe") is True
    assert policy.is_blocked("EXE") is True


def test_allowed_image_category() -> None:
    policy = ExtensionPolicy()
    assert policy.allowed_category_for_extension(".jpg") == "images"


def test_allowed_video_category() -> None:
    policy = ExtensionPolicy()
    assert policy.allowed_category_for_extension("mp4") == "videos"


def test_unknown_extension_rejected() -> None:
    policy = ExtensionPolicy()
    assert policy.allowed_category_for_extension(".xyz") is None