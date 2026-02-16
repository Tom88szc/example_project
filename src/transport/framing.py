from __future__ import annotations

import json
import socket
from typing import Any, Dict, Optional


def _recv_exact(sock: socket.socket, n: int, timeout: Optional[float] = None) -> bytes:
    """Receive exactly n bytes or raise ConnectionError."""
    if timeout is not None:
        sock.settimeout(timeout)
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket closed while receiving data")
        buf += chunk
    return buf


class LineJsonFraming:
    """Legacy framing: newline-delimited JSON."""

    def send(self, sock: socket.socket, msg: Dict[str, Any]) -> None:
        sock.sendall((json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8"))

    def receive(self, sock: socket.socket, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        # NOTE: naive receive (kept for backwards compatibility)
        if timeout is not None:
            sock.settimeout(timeout)
        data = sock.recv(4096)
        if not data:
            return None
        text = data.decode("utf-8", errors="replace").strip()
        if not text:
            return None
        return json.loads(text)


class Length2JsonFraming:
    """2-byte big-endian length prefix + JSON payload (UTF-8)."""

    def send(self, sock: socket.socket, msg: Dict[str, Any]) -> None:
        payload = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        length = len(payload)
        if length > 0xFFFF:
            raise ValueError(f"Payload too large for 2-byte length: {length}")
        prefix = length.to_bytes(2, byteorder="big", signed=False)
        sock.sendall(prefix + payload)

    def receive(self, sock: socket.socket, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        try:
            prefix = _recv_exact(sock, 2, timeout=timeout)
        except (socket.timeout, ConnectionError):
            return None
        length = int.from_bytes(prefix, "big", signed=False)
        if length == 0:
            return None
        payload = _recv_exact(sock, length, timeout=timeout)
        return json.loads(payload.decode("utf-8", errors="replace"))



class Length2RawFraming:
        """2-byte big-endian length prefix framing for raw bytes payload."""

        def send(self, sock, payload: bytes) -> None:
            if payload is None:
                payload = b""
            length = len(payload)
            if length > 0xFFFF:
                raise ValueError(f"Payload too large for 2B length: {length}")
            sock.sendall(length.to_bytes(2, "big") + payload)

        def receive(self, sock, timeout: float | None = None) -> bytes:
            if timeout is not None:
                sock.settimeout(timeout)
            prefix = _recv_exact(sock, 2)
            length = int.from_bytes(prefix, "big")
            if length == 0:
                return b""
            return _recv_exact(sock, length)

        def _recv_exact(sock, n: int) -> bytes:
            data = b""
            while len(data) < n:
                chunk = sock.recv(n - len(data))
                if not chunk:
                    raise ConnectionError("Socket closed while receiving data")
                data += chunk
            return data

