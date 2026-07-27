from __future__ import annotations

import pytest

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
from app.protocol.state_machine import (
    ProtocolStateMachine,
    STATE_AUTHENTICATED,
    STATE_COMPLETED,
    STATE_FILE_TRANSFER,
    STATE_HELLO_ACKED,
    STATE_HELLO_SENT,
    STATE_MANIFEST_ACCEPTED,
)


def test_state_machine_happy_path() -> None:
    machine = ProtocolStateMachine()

    machine.on_outbound(MESSAGE_TYPE_HELLO)
    assert machine.state == STATE_HELLO_SENT

    machine.on_inbound(MESSAGE_TYPE_HELLO_ACK)
    assert machine.state == STATE_HELLO_ACKED

    machine.on_outbound(MESSAGE_TYPE_AUTH_REQUEST)
    machine.on_inbound(MESSAGE_TYPE_AUTH_RESULT)
    assert machine.state == STATE_AUTHENTICATED

    machine.on_outbound(MESSAGE_TYPE_MANIFEST)
    machine.on_inbound(MESSAGE_TYPE_MANIFEST_RESULT)
    assert machine.state == STATE_MANIFEST_ACCEPTED

    machine.on_outbound(MESSAGE_TYPE_FILE_START)
    assert machine.state == STATE_FILE_TRANSFER

    machine.on_inbound(MESSAGE_TYPE_FILE_RESUME_INFO)
    machine.on_outbound(MESSAGE_TYPE_FILE_CHUNK)
    machine.on_outbound(MESSAGE_TYPE_FILE_COMPLETE)
    machine.on_inbound(MESSAGE_TYPE_FILE_HASH_RESULT)
    machine.on_outbound(MESSAGE_TYPE_TRANSFER_COMPLETE)
    assert machine.state == STATE_COMPLETED


def test_state_machine_rejects_invalid_transition() -> None:
    machine = ProtocolStateMachine()
    with pytest.raises(ProtocolError):
        machine.on_outbound(MESSAGE_TYPE_MANIFEST)