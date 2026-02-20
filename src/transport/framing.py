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


def send_frame(sock: socket.socket, payload: Union[bytes, bytearray, memoryview, str]) -> None:
    """Send raw payload bytes (without adding a 2-byte length prefix)."""
    payload_bytes = _coerce_payload_bytes(payload)
    sock.sendall(payload_bytes)


def recv_frame(
    sock: socket.socket,
    timeout: Optional[float] = None,
    buffer_size: int = 8192,
) -> Optional[bytes]:
    """Receive raw payload bytes (without consuming a 2-byte length prefix)."""
    if timeout is not None:
        sock.settimeout(timeout)

    try:
        data = sock.recv(buffer_size)
        if not data:
            return None
        return data
    except (OSError, socket.timeout):
        return None
