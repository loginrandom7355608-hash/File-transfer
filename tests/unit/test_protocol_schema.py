from __future__ import annotations

import pytest

from app.exceptions import ProtocolError
from app.protocol.schema import (
    validate_auth_request_payload,
    validate_file_start_payload,
    validate_hello_payload,
    validate_manifest_payload,
)


def test_validate_hello_payload() -> None:
    payload = {"role": "sender", "app_name": "Safe Media Transfer", "protocol_version": 1}
    assert validate_hello_payload(payload) == payload


def test_validate_auth_request_payload_rejects_missing_code() -> None:
    with pytest.raises(ProtocolError):
        validate_auth_request_payload({})


def test_validate_manifest_payload_accepts_minimal_valid_manifest() -> None:
    payload = {
        "session_id": "abc",
        "source_root": "C:\\Source",
        "selected_categories": ["images"],
        "files": [
            {
                "relative_path": "photo.jpg",
                "category": "images",
                "extension": ".jpg",
                "size_bytes": 100,
                "modified_time_ns": 1,
            }
        ],
    }
    assert validate_manifest_payload(payload) == payload


def test_validate_file_start_payload_rejects_missing_path() -> None:
    with pytest.raises(ProtocolError):
        validate_file_start_payload({"size_bytes": 1, "modified_time_ns": 1})