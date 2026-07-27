from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(slots=True)
class SessionPeerInfo:
    host: str
    port: int
    role: str


@dataclass(slots=True)
class PairingSession:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    pairing_code: str = ""
    sender: SessionPeerInfo | None = None
    receiver: SessionPeerInfo | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    authenticated: bool = False

    def session_uuid(self) -> UUID:
        return UUID(self.session_id)