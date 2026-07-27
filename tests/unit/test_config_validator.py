from __future__ import annotations

from pathlib import Path

import pytest

from app.config.validator import validate_raw_config
from app.exceptions import ConfigError


def valid_config() -> dict:
    return {
        "app": {
            "name": "Safe Media Transfer",
            "mode": "sender",
            "protocol_version": 1,
            "debug_logging": False,
            "theme": "system",
        },
        "network": {
            "bind_ip": "0.0.0.0",
            "receiver_ip": "192.168.50.2",
            "port": 48555,
            "connect_timeout_seconds": 10,
            "read_timeout_seconds": 30,
            "write_timeout_seconds": 30,
            "heartbeat_interval_seconds": 10,
            "idle_disconnect_seconds": 90,
        },
        "transfer": {
            "chunk_size_bytes": 8 * 1024 * 1024,
            "resume_enabled": True,
            "max_retries": 3,
            "max_file_count": 1000,
            "max_file_size_bytes": 1024 * 1024 * 1024,
            "max_manifest_bytes": 1024 * 1024,
            "duplicate_policy": "skip_identical",
        },
        "storage": {
            "default_destination": "D:\\SafeMediaInbox",
            "log_folder": "logs",
            "report_folder": "reports",
            "state_folder": "state",
            "staging_suffix": ".part",
            "state_suffix": ".part.json",
        },
        "verification": {
            "sha256_enabled": True,
            "signature_validation_enabled": True,
        },
        "metadata": {
            "enabled": False,
            "mode": "off",
        },
        "allowed_extensions": {
            "images": {"values": [".jpg", ".png"]},
            "videos": {"values": [".mp4", ".mkv"]},
        },
        "blocked_extensions": {
            "values": [".exe", ".bat"],
        },
        "logging": {
            "level": "INFO",
            "max_bytes": 1024,
            "backup_count": 3,
        },
    }


def test_valid_config_passes() -> None:
    validate_raw_config(valid_config(), Path("config.toml"))


def test_invalid_port_fails() -> None:
    data = valid_config()
    data["network"]["port"] = 70000
    with pytest.raises(ConfigError):
        validate_raw_config(data, Path("config.toml"))


def test_overlap_extensions_fail() -> None:
    data = valid_config()
    data["blocked_extensions"]["values"] = [".exe", ".jpg"]
    with pytest.raises(ConfigError):
        validate_raw_config(data, Path("config.toml"))