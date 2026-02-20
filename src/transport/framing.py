import socket
from typing import Optional, Union


def _coerce_payload_bytes(payload: Union[bytes, bytearray, memoryview, str]) -> bytes:
    """Normalize payload into bytes accepted by socket.sendall()."""
    if isinstance(payload, bytes):
        return payload

    if isinstance(payload, (bytearray, memoryview)):
        return bytes(payload)

    if isinstance(payload, str):
        compact = "".join(payload.split())
        if compact:
            try:
                return bytes.fromhex(compact)
            except ValueError:
                return payload.encode("utf-8")
        return b""

    raise TypeError(f"Unsupported payload type: {type(payload)!r}")


def _recv_exact(sock: socket.socket, size: int) -> Optional[bytes]:
    """Receive exactly `size` bytes or return None if connection closes/timeouts."""
    chunks = bytearray()
    while len(chunks) < size:
        part = sock.recv(size - len(chunks))
        if not part:
            return None
        chunks.extend(part)
    return bytes(chunks)


def send_frame(sock: socket.socket, payload: Union[bytes, bytearray, memoryview, str]) -> None:
    """Send payload as-is (payload already contains 2-byte length prefix)."""
    payload_bytes = _coerce_payload_bytes(payload)
    sock.sendall(payload_bytes)


def recv_frame(
    sock: socket.socket,
    timeout: Optional[float] = None,
    buffer_size: int = 8192,
) -> Optional[bytes]:
    """Receive one full frame using 2-byte length prefix and return [prefix+payload]."""
    del buffer_size
    if timeout is not None:
        sock.settimeout(timeout)

    try:
        prefix = _recv_exact(sock, 2)
        if prefix is None:
            return None

        body_len = int.from_bytes(prefix, "big")
        body = _recv_exact(sock, body_len)
        if body is None:
            return None

        return prefix + body
    except (OSError, socket.timeout):
        return None
