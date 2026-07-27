from __future__ import annotations

from pathlib import Path
from typing import Any

from app.constants import (
    DEFAULT_PORT,
    MAX_CHUNK_SIZE,
    MAX_FILE_COUNT,
    MAX_MANIFEST_BYTES,
    MIN_CHUNK_SIZE,
    PROTOCOL_VERSION,
)
from app.exceptions import ConfigError


def _require_section(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"Missing or invalid config section: {key}")
    return value


def _require_bool(section: dict[str, Any], key: str) -> bool:
    value = section.get(key)
    if not isinstance(value, bool):
        raise ConfigError(f"Config key '{key}' must be a boolean")
    return value


def _require_int(section: dict[str, Any], key: str) -> int:
    value = section.get(key)
    if not isinstance(value, int):
        raise ConfigError(f"Config key '{key}' must be an integer")
    return value


def _require_str(section: dict[str, Any], key: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Config key '{key}' must be a non-empty string")
    return value.strip()


def _require_list_of_str(section: dict[str, Any], key: str) -> list[str]:
    value = section.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"Config key '{key}' must be a list of strings")
    return value


def validate_raw_config(raw: dict[str, Any], config_path: Path) -> None:
    app = _require_section(raw, "app")
    network = _require_section(raw, "network")
    transfer = _require_section(raw, "transfer")
    storage = _require_section(raw, "storage")
    verification = _require_section(raw, "verification")
    metadata = _require_section(raw, "metadata")
    logging_cfg = _require_section(raw, "logging")
    allowed = _require_section(raw, "allowed_extensions")
    blocked = _require_section(raw, "blocked_extensions")

    mode = _require_str(app, "mode").lower()
    if mode not in {"sender", "receiver"}:
        raise ConfigError("app.mode must be 'sender' or 'receiver'")

    protocol_version = _require_int(app, "protocol_version")
    if protocol_version != PROTOCOL_VERSION:
        raise ConfigError(
            f"Unsupported protocol version in config: {protocol_version}. "
            f"Expected {PROTOCOL_VERSION}."
        )

    _require_bool(app, "debug_logging")
    _require_str(app, "name")
    _require_str(app, "theme")

    port = _require_int(network, "port")
    if port < 1 or port > 65535:
        raise ConfigError(f"network.port must be in range 1..65535, got {port}")

    for key in (
        "connect_timeout_seconds",
        "read_timeout_seconds",
        "write_timeout_seconds",
        "heartbeat_interval_seconds",
        "idle_disconnect_seconds",
    ):
        if _require_int(network, key) <= 0:
            raise ConfigError(f"network.{key} must be greater than 0")

    _require_str(network, "bind_ip")
    _require_str(network, "receiver_ip")

    chunk_size = _require_int(transfer, "chunk_size_bytes")
    if chunk_size < MIN_CHUNK_SIZE or chunk_size > MAX_CHUNK_SIZE:
        raise ConfigError(
            f"transfer.chunk_size_bytes must be between {MIN_CHUNK_SIZE} and {MAX_CHUNK_SIZE}"
        )

    max_retries = _require_int(transfer, "max_retries")
    if max_retries < 0:
        raise ConfigError("transfer.max_retries must be >= 0")

    max_file_count = _require_int(transfer, "max_file_count")
    if max_file_count < 1 or max_file_count > MAX_FILE_COUNT:
        raise ConfigError(f"transfer.max_file_count must be in range 1..{MAX_FILE_COUNT}")

    max_manifest_bytes = _require_int(transfer, "max_manifest_bytes")
    if max_manifest_bytes < 1024 or max_manifest_bytes > MAX_MANIFEST_BYTES:
        raise ConfigError(
            f"transfer.max_manifest_bytes must be between 1024 and {MAX_MANIFEST_BYTES}"
        )

    if _require_int(transfer, "max_file_size_bytes") <= 0:
        raise ConfigError("transfer.max_file_size_bytes must be > 0")

    if _require_str(transfer, "duplicate_policy") not in {
        "skip_identical",
        "rename_incoming",
        "fail",
    }:
        raise ConfigError("transfer.duplicate_policy must be one of: skip_identical, rename_incoming, fail")

    _require_bool(transfer, "resume_enabled")

    _require_str(storage, "default_destination")
    _require_str(storage, "log_folder")
    _require_str(storage, "report_folder")
    _require_str(storage, "state_folder")
    _require_str(storage, "staging_suffix")
    _require_str(storage, "state_suffix")

    _require_bool(verification, "sha256_enabled")
    _require_bool(verification, "signature_validation_enabled")

    _require_bool(metadata, "enabled")
    if _require_str(metadata, "mode") not in {"off"}:
        raise ConfigError("metadata.mode currently supports only 'off' in Phase 1")

    level = _require_str(logging_cfg, "level").upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigError("logging.level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL")

    if _require_int(logging_cfg, "max_bytes") <= 0:
        raise ConfigError("logging.max_bytes must be > 0")
    if _require_int(logging_cfg, "backup_count") < 1:
        raise ConfigError("logging.backup_count must be >= 1")

    if "images" not in allowed or "videos" not in allowed:
        raise ConfigError("allowed_extensions must contain 'images' and 'videos' categories")

    allowed_flat: set[str] = set()
    for category_name, category_value in allowed.items():
        if not isinstance(category_value, dict):
            raise ConfigError(f"allowed_extensions.{category_name} must be a table")
        values = _require_list_of_str(category_value, "values")
        for ext in values:
            normalized = ext.strip().lower()
            if not normalized.startswith("."):
                normalized = f".{normalized}"
            allowed_flat.add(normalized)

    blocked_values = _require_list_of_str(blocked, "values")
    blocked_flat: set[str] = set()
    for ext in blocked_values:
        normalized = ext.strip().lower()
        if not normalized.startswith("."):
            normalized = f".{normalized}"
        blocked_flat.add(normalized)

    overlap = allowed_flat.intersection(blocked_flat)
    if overlap:
        raise ConfigError(f"Allowed and blocked extensions overlap: {sorted(overlap)}")

    if not config_path.suffix.lower() == ".toml":
        raise ConfigError("Configuration file must use .toml extension")

    if DEFAULT_PORT < 1:
        raise ConfigError("Internal default port constant is invalid")