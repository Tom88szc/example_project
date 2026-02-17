
import socket
from typing import Optional


def _recv_exact(sock: socket.socket, n: int, timeout: Optional[float] = None) -> bytes:
    if timeout is not None:
        sock.settimeout(timeout)
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Socket closed while receiving data")
        data += chunk
    return data


def send_frame(sock: socket.socket, payload: bytes) -> None:
    """Send payload with 2-byte big-endian length prefix."""
    prefix = len(payload).to_bytes(2, "big")
    sock.sendall(prefix + payload)


def recv_frame(sock: socket.socket, timeout: Optional[float] = None) -> Optional[bytes]:
    """Receive one framed payload (2-byte length + payload). Returns None on disconnect/timeout."""
    try:
        prefix = _recv_exact(sock, 2, timeout=timeout)
        length = int.from_bytes(prefix, "big")
        return _recv_exact(sock, length, timeout=timeout)
    except (ConnectionError, OSError, socket.timeout):
        return None
