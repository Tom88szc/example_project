from __future__ import annotations

import socket
from typing import Any, Dict, Optional

from src.transport.framing import Length2JsonFraming


class TcpTransport:
    def __init__(self, host: str, port: int, connect_timeout: float, read_timeout: float, framing: Optional[Length2JsonFraming] = None):
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.framing = framing or Length2JsonFraming()
        self._sock: Optional[socket.socket] = None

    def connect(self) -> None:
        if self._sock is not None:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.connect_timeout)
        sock.connect((self.host, self.port))
        sock.settimeout(self.read_timeout)
        self._sock = sock

    def close(self) -> None:
        if self._sock is None:
            return
        try:
            self._sock.close()
        finally:
            self._sock = None

    def send(self, msg: Dict[str, Any]) -> None:
        if self._sock is None:
            raise ConnectionError("Socket is not connected")
        self.framing.send(self._sock, msg)

    def receive(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        if self._sock is None:
            raise ConnectionError("Socket is not connected")
        return self.framing.receive(self._sock, timeout=timeout)

def send_bytes(self, payload: bytes) -> None:
    """Send raw bytes payload using 2B length framing."""
    self._ensure_connected()
    from src.transport.framing import Length2RawFraming
    fr = Length2RawFraming()
    fr.send(self._sock, payload)

def receive_bytes(self, timeout: float | None = None) -> bytes:
    """Receive raw bytes payload using 2B length framing."""
    self._ensure_connected()
    from src.transport.framing import Length2RawFraming
    fr = Length2RawFraming()
    return fr.receive(self._sock, timeout=timeout)

