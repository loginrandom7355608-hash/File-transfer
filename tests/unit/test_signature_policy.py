from __future__ import annotations

from pathlib import Path

from app.validation.extension_policy import ExtensionPolicy
from app.validation.signature_policy import SignaturePolicy


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
    b"\x90wS\xde"
    b"\x00\x00\x00\x0cIDAT\x08\x99c\xf8\x0f\x00\x01\x01\x01\x00"
    b"\x18\xdd\x8d\xb1"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_signature_policy_allows_matching_png(tmp_path: Path) -> None:
    file_path = tmp_path / "image.png"
    file_path.write_bytes(PNG_BYTES)

    policy = SignaturePolicy(ExtensionPolicy(), enabled=True)
    result = policy.inspect_file(file_path, claimed_extension=".png")

    assert result.decision == "allow"
    assert result.detected_extension == ".png"


def test_signature_policy_rejects_blocked_detected_type(tmp_path: Path) -> None:
    file_path = tmp_path / "fake.jpg"
    file_path.write_bytes(b"MZ" + b"\x00" * 128)

    policy = SignaturePolicy(ExtensionPolicy(), enabled=True)
    result = policy.inspect_file(file_path, claimed_extension=".jpg")

    assert result.decision == "reject"