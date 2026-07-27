from __future__ import annotations

from uuid import uuid4

import pytest

from app.constants import MESSAGE_TYPE_HELLO, PROTOCOL_VERSION
from app.exceptions import ProtocolError
from app.protocol.framing import decode_frame, decode_json_payload, encode_frame, encode_json_payload
from app.protocol.messages import ProtocolFrame


def test_encode_decode_roundtrip() -> None:
    session_id = uuid4()
    payload = encode_json_payload({"role": "sender", "app_name": "Safe Media Transfer"})
    frame = ProtocolFrame(
        protocol_version=PROTOCOL_VERSION,
        message_type=MESSAGE_TYPE_HELLO,
        flags=0,
        payload=payload,
        session_id=session_id,
    )

    encoded = encode_frame(frame)
    decoded = decode_frame(encoded)

    assert decoded.protocol_version == PROTOCOL_VERSION
    assert decoded.message_type == MESSAGE_TYPE_HELLO
    assert decoded.session_id == session_id
    assert decode_json_payload(decoded.payload)["role"] == "sender"


def test_decode_rejects_bad_magic() -> None:
    session_id = uuid4()
    frame = ProtocolFrame(
        protocol_version=PROTOCOL_VERSION,
        message_type=MESSAGE_TYPE_HELLO,
        flags=0,
        payload=b"{}",
        session_id=session_id,
    )
    encoded = bytearray(encode_frame(frame))
    encoded[0:4] = b"BAD!"
    with pytest.raises(ProtocolError):
        decode_frame(bytes(encoded))