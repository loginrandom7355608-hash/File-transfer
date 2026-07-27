from __future__ import annotations

from typing import Any

from app.constants import (
    MAX_FILE_COUNT,
    MAX_MANIFEST_BYTES,
    MAX_PATH_UTF8_BYTES,
    MESSAGE_NAME_TYPE_MAP,
)
from app.exceptions import ProtocolError


def require_message_type_name(name: str) -> str:
    if name not in MESSAGE_NAME_TYPE_MAP:
        raise ProtocolError(f"Unknown message type name: {name}")
    return name


def require_str_field(payload: dict[str, Any], key: str, *, max_len: int | None = None) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ProtocolError(f"Missing or invalid string field: {key}")
    value = value.strip()
    if max_len is not None and len(value.encode("utf-8")) > max_len:
        raise ProtocolError(f"Field too long: {key}")
    return value


def require_int_field(payload: dict[str, Any], key: str, *, minimum: int | None = None) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ProtocolError(f"Missing or invalid integer field: {key}")
    if minimum is not None and value < minimum:
        raise ProtocolError(f"Field below minimum: {key}")
    return value


def require_bool_field(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ProtocolError(f"Missing or invalid boolean field: {key}")
    return value


def validate_hello_payload(payload: dict[str, Any]) -> dict[str, Any]:
    require_str_field(payload, "role", max_len=32)
    require_str_field(payload, "app_name", max_len=128)
    require_int_field(payload, "protocol_version", minimum=1)
    return payload


def validate_auth_request_payload(payload: dict[str, Any]) -> dict[str, Any]:
    require_str_field(payload, "pairing_code", max_len=64)
    return payload


def validate_manifest_payload(payload: dict[str, Any]) -> dict[str, Any]:
    require_str_field(payload, "session_id", max_len=128)
    require_str_field(payload, "source_root", max_len=1024)

    selected_categories = payload.get("selected_categories")
    if not isinstance(selected_categories, list) or not selected_categories:
        raise ProtocolError("selected_categories must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in selected_categories):
        raise ProtocolError("selected_categories contains invalid values")

    files = payload.get("files")
    if not isinstance(files, list):
        raise ProtocolError("files must be a list")
    if len(files) > MAX_FILE_COUNT:
        raise ProtocolError("files exceeds maximum file count")

    for item in files:
        if not isinstance(item, dict):
            raise ProtocolError("each manifest file entry must be an object")
        require_str_field(item, "relative_path", max_len=MAX_PATH_UTF8_BYTES)
        require_str_field(item, "category", max_len=32)
        require_str_field(item, "extension", max_len=16)
        require_int_field(item, "size_bytes", minimum=0)
        require_int_field(item, "modified_time_ns", minimum=0)

    encoded_length = len(str(payload).encode("utf-8"))
    if encoded_length > MAX_MANIFEST_BYTES:
        raise ProtocolError("manifest exceeds maximum size")

    return payload


def validate_file_start_payload(payload: dict[str, Any]) -> dict[str, Any]:
    require_str_field(payload, "relative_path", max_len=MAX_PATH_UTF8_BYTES)
    require_int_field(payload, "size_bytes", minimum=0)
    require_int_field(payload, "modified_time_ns", minimum=0)
    return payload