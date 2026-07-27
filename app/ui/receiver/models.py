from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ReceiverStatus:
    is_listening: bool
    bind_host: str
    port: int
    destination_root: str