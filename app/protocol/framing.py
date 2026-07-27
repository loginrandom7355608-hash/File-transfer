from __future__ import annotations

import json
import struct
from uuid import UUID

from app.constants import (
    FRAME_HEADER_FORMAT,
    FRAME_HEADER_SIZE,
    FRAME_MAGIC,
    MAX_CONTROL_MESSAGE_BYTES,
    MESSAGE_TYPE_FILE_CHUNK,
    PROTOCOL_VERSION,
)
from app.exceptions import ProtocolError
from app.protocol.messages import ProtocolFrame


def encode_frame(frame: ProtocolFrame) -> bytes:
    if frame.protocol_version != PROTOCOL_VERSION:
        raise ProtocolError(f"Unsupported protocol version: {frame.protocol_version}")

    payload_length = len(frame.payload)
    if frame.message_type != MESSAGE_TYPE_FILE_CHUNK and payload_length > MAX_CONTROL_MESSAGE_BYTES:
        raise ProtocolError("Control payload exceeds maximum allowed size")

    header = struct.pack(
        FRAME_HEADER_FORMAT,
        FRAME_MAGIC,
        frame.protocol_version,
        frame.message_type,
        frame.flags,
        payload_length,
        frame.session_id.bytes,
    )
    return header + frame.payload


def decode_frame(data: bytes) -> ProtocolFrame:
    if len(data) < FRAME_HEADER_SIZE:
        raise ProtocolError("Incomplete frame header")

    magic, protocol_version, message_type, flags, payload_length, session_bytes = struct.unpack(
        FRAME_HEADER_FORMAT,
        data[:FRAME_HEADER_SIZE],
    )

    if magic != FRAME_MAGIC:
        raise ProtocolError("Invalid frame magic")
    if protocol_version != PROTOCOL_VERSION:
        raise ProtocolError(f"Unsupported protocol version: {protocol_version}")

    payload = data[FRAME_HEADER_SIZE:]
    if len(payload) != payload_length:
        raise ProtocolError("Payload length mismatch")

    if message_type != MESSAGE_TYPE_FILE_CHUNK and payload_length > MAX_CONTROL_MESSAGE_BYTES:
        raise ProtocolError("Control payload exceeds maximum allowed size")

    return ProtocolFrame(
        protocol_version=protocol_version,
        message_type=message_type,
        flags=flags,
        payload=payload,
        session_id=UUID(bytes=session_bytes),
    )


def encode_json_payload(payload: dict) -> bytes:
    try:
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProtocolError("Invalid JSON payload") from exc

    if len(encoded) > MAX_CONTROL_MESSAGE_BYTES:
        raise ProtocolError("JSON payload exceeds maximum allowed size")
    return encoded


def decode_json_payload(payload: bytes) -> dict:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("Invalid JSON payload encoding") from exc

    if not isinstance(data, dict):
        raise ProtocolError("Protocol JSON payload must be an object")
    return data