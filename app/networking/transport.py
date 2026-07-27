from __future__ import annotations

import json
import struct
import socket
from typing import Any

from app.exceptions import ProtocolError


_HEADER_STRUCT = struct.Struct("!I")


class SocketTransport:
    def __init__(self, sock: socket.socket) -> None:
        self._sock = sock

    def set_timeouts(self, *, read_timeout: float | None, write_timeout: float | None) -> None:
        timeout = read_timeout if read_timeout is not None else write_timeout
        self._sock.settimeout(timeout)

    def send_all(self, data: bytes) -> None:
        try:
            self._sock.sendall(data)
        except OSError as exc:
            raise ProtocolError("Socket send failed") from exc

    def receive_exactly(self, size: int) -> bytes:
        if size < 0:
            raise ProtocolError("Invalid receive size")

        buffer = bytearray()
        while len(buffer) < size:
            try:
                chunk = self._sock.recv(size - len(buffer))
            except OSError as exc:
                raise ProtocolError("Socket receive failed") from exc

            if not chunk:
                raise ProtocolError("Socket closed before expected bytes were received")

            buffer.extend(chunk)

        return bytes(buffer)

    def send_json_message(self, payload: dict[str, Any]) -> None:
        try:
            encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ProtocolError("Failed to encode JSON message") from exc

        self.send_all(_HEADER_STRUCT.pack(len(encoded)))
        self.send_all(encoded)

    def receive_json_message(self) -> dict[str, Any]:
        header = self.receive_exactly(_HEADER_STRUCT.size)
        try:
            (size,) = _HEADER_STRUCT.unpack(header)
        except struct.error as exc:
            raise ProtocolError("Invalid message header") from exc

        body = self.receive_exactly(size)

        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProtocolError("Invalid JSON message body") from exc

        if not isinstance(payload, dict):
            raise ProtocolError("JSON message body must be an object")

        return payload

    def close(self) -> None:
        self._sock.close()