from __future__ import annotations

from pathlib import Path

from app.config.loader import load_app_config


def test_load_example_config(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[app]
name = "Safe Media Transfer"
mode = "sender"
protocol_version = 1
debug_logging = false
theme = "system"

[network]
bind_ip = "0.0.0.0"
receiver_ip = "192.168.50.2"
port = 48555
connect_timeout_seconds = 10
read_timeout_seconds = 30
write_timeout_seconds = 30
heartbeat_interval_seconds = 10
idle_disconnect_seconds = 90

[transfer]
chunk_size_bytes = 8388608
resume_enabled = true
max_retries = 3
max_file_count = 100000
max_file_size_bytes = 1099511627776
max_manifest_bytes = 33554432
duplicate_policy = "skip_identical"

[storage]
default_destination = "D:\\\\SafeMediaInbox"
log_folder = "logs"
report_folder = "reports"
state_folder = "state"
staging_suffix = ".part"
state_suffix = ".part.json"

[verification]
sha256_enabled = true
signature_validation_enabled = true

[metadata]
enabled = false
mode = "off"

[allowed_extensions.images]
values = [".jpg", ".jpeg", ".png"]

[allowed_extensions.videos]
values = [".mp4", ".mkv"]

[blocked_extensions]
values = [".exe", ".bat"]

[logging]
level = "INFO"
max_bytes = 1024
backup_count = 3
""",
        encoding="utf-8",
    )

    config = load_app_config(config_file)
    assert config.app_name == "Safe Media Transfer"
    assert config.network.port == 48555
    assert ".jpg" in config.allowed_extensions["images"]