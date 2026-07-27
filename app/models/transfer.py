from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class LoggingConfig:
    level: str
    max_bytes: int
    backup_count: int


@dataclass(slots=True)
class NetworkConfig:
    bind_ip: str
    receiver_ip: str
    port: int
    connect_timeout_seconds: int
    read_timeout_seconds: int
    write_timeout_seconds: int
    heartbeat_interval_seconds: int
    idle_disconnect_seconds: int


@dataclass(slots=True)
class TransferConfig:
    chunk_size_bytes: int
    resume_enabled: bool
    max_retries: int
    max_file_count: int
    max_file_size_bytes: int
    max_manifest_bytes: int
    duplicate_policy: str


@dataclass(slots=True)
class StorageConfig:
    default_destination: Path
    log_folder: Path
    report_folder: Path
    state_folder: Path
    staging_suffix: str
    state_suffix: str


@dataclass(slots=True)
class VerificationConfig:
    sha256_enabled: bool
    signature_validation_enabled: bool


@dataclass(slots=True)
class MetadataConfig:
    enabled: bool
    mode: str


@dataclass(slots=True)
class AppConfig:
    app_name: str
    mode: str
    protocol_version: int
    debug_logging: bool
    theme: str
    network: NetworkConfig
    transfer: TransferConfig
    storage: StorageConfig
    verification: VerificationConfig
    metadata: MetadataConfig
    allowed_extensions: dict[str, set[str]] = field(default_factory=dict)
    blocked_extensions: set[str] = field(default_factory=set)
    logging: LoggingConfig = field(default_factory=lambda: LoggingConfig("INFO", 5 * 1024 * 1024, 10))