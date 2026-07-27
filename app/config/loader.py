from __future__ import annotations

import tomllib
from pathlib import Path

from app.exceptions import ConfigError
from app.models.transfer import (
    AppConfig,
    LoggingConfig,
    MetadataConfig,
    NetworkConfig,
    StorageConfig,
    TransferConfig,
    VerificationConfig,
)
from app.config.validator import validate_raw_config


def _normalize_extension_set(values: list[str]) -> set[str]:
    normalized: set[str] = set()
    for item in values:
        ext = item.strip().lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        normalized.add(ext)
    return normalized


def load_app_config(config_path: Path) -> AppConfig:
    if not config_path.exists():
        raise ConfigError(
            f"Configuration file not found: {config_path}. "
            f"Copy config.example.toml to config.toml first."
        )

    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    validate_raw_config(raw, config_path)

    storage = raw["storage"]
    network = raw["network"]
    transfer = raw["transfer"]
    verification = raw["verification"]
    metadata = raw["metadata"]
    logging_cfg = raw["logging"]
    app = raw["app"]

    allowed_extensions = {
        category: _normalize_extension_set(data["values"])
        for category, data in raw["allowed_extensions"].items()
    }
    blocked_extensions = _normalize_extension_set(raw["blocked_extensions"]["values"])

    return AppConfig(
        app_name=app["name"],
        mode=app["mode"],
        protocol_version=app["protocol_version"],
        debug_logging=app["debug_logging"],
        theme=app["theme"],
        network=NetworkConfig(
            bind_ip=network["bind_ip"],
            receiver_ip=network["receiver_ip"],
            port=network["port"],
            connect_timeout_seconds=network["connect_timeout_seconds"],
            read_timeout_seconds=network["read_timeout_seconds"],
            write_timeout_seconds=network["write_timeout_seconds"],
            heartbeat_interval_seconds=network["heartbeat_interval_seconds"],
            idle_disconnect_seconds=network["idle_disconnect_seconds"],
        ),
        transfer=TransferConfig(
            chunk_size_bytes=transfer["chunk_size_bytes"],
            resume_enabled=transfer["resume_enabled"],
            max_retries=transfer["max_retries"],
            max_file_count=transfer["max_file_count"],
            max_file_size_bytes=transfer["max_file_size_bytes"],
            max_manifest_bytes=transfer["max_manifest_bytes"],
            duplicate_policy=transfer["duplicate_policy"],
        ),
        storage=StorageConfig(
            default_destination=Path(storage["default_destination"]),
            log_folder=Path(storage["log_folder"]),
            report_folder=Path(storage["report_folder"]),
            state_folder=Path(storage["state_folder"]),
            staging_suffix=storage["staging_suffix"],
            state_suffix=storage["state_suffix"],
        ),
        verification=VerificationConfig(
            sha256_enabled=verification["sha256_enabled"],
            signature_validation_enabled=verification["signature_validation_enabled"],
        ),
        metadata=MetadataConfig(
            enabled=metadata["enabled"],
            mode=metadata["mode"],
        ),
        allowed_extensions=allowed_extensions,
        blocked_extensions=blocked_extensions,
        logging=LoggingConfig(
            level=logging_cfg["level"],
            max_bytes=logging_cfg["max_bytes"],
            backup_count=logging_cfg["backup_count"],
        ),
    )