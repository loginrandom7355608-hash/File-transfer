from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(slots=True)
class ProtocolFrame:
    protocol_version: int
    message_type: int
    flags: int
    payload: bytes
    session_id: UUID

    @property
    def payload_length(self) -> int:
        return len(self.payload)


def new_session_id() -> UUID:
    return uuid4()