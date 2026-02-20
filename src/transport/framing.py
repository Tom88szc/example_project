import socket
from typing import Optional, Union


def _coerce_payload_bytes(payload: Union[bytes, bytearray, memoryview, str]) -> bytes:
    """Normalize payload into bytes accepted by socket.sendall()."""
    if isinstance(payload, bytes):
        return payload

    if isinstance(payload, (bytearray, memoryview)):
        return bytes(payload)

    if isinstance(payload, str):
        # Debug paths often provide uppercase HEX text. Prefer HEX decoding first.
        compact = "".join(payload.split())
        if compact:
            try:
                return bytes.fromhex(compact)
            except ValueError:
                return payload.encode("utf-8")
        return b""

    raise TypeError(f"Unsupported payload type: {type(payload)!r}")


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

def send_frame(sock: socket.socket, payload: Union[bytes, bytearray, memoryview, str]) -> None:
    """Send payload with 2-byte big-endian length prefix."""