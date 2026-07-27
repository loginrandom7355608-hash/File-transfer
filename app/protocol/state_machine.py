from __future__ import annotations

from dataclasses import dataclass, field

from app.constants import (
    MESSAGE_TYPE_AUTH_REQUEST,
    MESSAGE_TYPE_AUTH_RESULT,
    MESSAGE_TYPE_FILE_CHUNK,
    MESSAGE_TYPE_FILE_COMPLETE,
    MESSAGE_TYPE_FILE_HASH_RESULT,
    MESSAGE_TYPE_FILE_RESUME_INFO,
    MESSAGE_TYPE_FILE_START,
    MESSAGE_TYPE_HELLO,
    MESSAGE_TYPE_HELLO_ACK,
    MESSAGE_TYPE_MANIFEST,
    MESSAGE_TYPE_MANIFEST_RESULT,
    MESSAGE_TYPE_TRANSFER_COMPLETE,
)
from app.exceptions import ProtocolError


STATE_INIT = "INIT"
STATE_HELLO_SENT = "HELLO_SENT"
STATE_HELLO_ACKED = "HELLO_ACKED"
STATE_AUTHENTICATED = "AUTHENTICATED"
STATE_MANIFEST_ACCEPTED = "MANIFEST_ACCEPTED"
STATE_FILE_TRANSFER = "FILE_TRANSFER"
STATE_COMPLETED = "COMPLETED"


@dataclass(slots=True)
class ProtocolStateMachine:
    state: str = field(default=STATE_INIT)

    def on_outbound(self, message_type: int) -> None:
        if self.state == STATE_INIT and message_type == MESSAGE_TYPE_HELLO:
            self.state = STATE_HELLO_SENT
            return
        if self.state == STATE_HELLO_ACKED and message_type == MESSAGE_TYPE_AUTH_REQUEST:
            return
        if self.state == STATE_AUTHENTICATED and message_type == MESSAGE_TYPE_MANIFEST:
            return
        if self.state == STATE_MANIFEST_ACCEPTED and message_type == MESSAGE_TYPE_FILE_START:
            self.state = STATE_FILE_TRANSFER
            return
        if self.state == STATE_FILE_TRANSFER and message_type in {MESSAGE_TYPE_FILE_CHUNK, MESSAGE_TYPE_FILE_COMPLETE}:
            return
        if self.state == STATE_FILE_TRANSFER and message_type == MESSAGE_TYPE_TRANSFER_COMPLETE:
            self.state = STATE_COMPLETED
            return
        raise ProtocolError(f"Invalid outbound message {message_type} in state {self.state}")

    def on_inbound(self, message_type: int) -> None:
        if self.state == STATE_HELLO_SENT and message_type == MESSAGE_TYPE_HELLO_ACK:
            self.state = STATE_HELLO_ACKED
            return
        if self.state == STATE_HELLO_ACKED and message_type == MESSAGE_TYPE_AUTH_RESULT:
            self.state = STATE_AUTHENTICATED
            return
        if self.state == STATE_AUTHENTICATED and message_type == MESSAGE_TYPE_MANIFEST_RESULT:
            self.state = STATE_MANIFEST_ACCEPTED
            return
        if self.state == STATE_FILE_TRANSFER and message_type in {
            MESSAGE_TYPE_FILE_RESUME_INFO,
            MESSAGE_TYPE_FILE_HASH_RESULT,
        }:
            return
        raise ProtocolError(f"Invalid inbound message {message_type} in state {self.state}")