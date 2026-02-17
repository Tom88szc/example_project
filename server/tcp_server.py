# In-memory store of authorizations by RRN (DE037)
AUTH_STORE = {}

import logging
import os
import socket
import threading
from typing import Dict, Optional

from src.utils.protocol.iso8583_adapter import parse_payload, build_payload

HOST = os.getenv("BN_MOCK_HOST", "127.0.0.1")
PORT = int(os.getenv("BN_MOCK_PORT", "5000"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("server.tcp_server")


# ============================================================
# 2-byte length framing (ONLY here)
# ============================================================

def _recv_exact(conn: socket.socket, n: int, timeout: Optional[float] = None) -> bytes:
    if timeout is not None:
        conn.settimeout(timeout)

    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Client disconnected")
        buf += chunk
    return buf


def _recv_frame_2b(conn: socket.socket, timeout: Optional[float] = None) -> Optional[Dict]:
    try:
        prefix = _recv_exact(conn, 2, timeout=timeout)
        length = int.from_bytes(prefix, "big", signed=False)
        payload = _recv_exact(conn, length, timeout=timeout)
        return parse_payload(payload)
    except socket.timeout:
        return None
    except ConnectionError:
        return None
    except OSError:
        return None


def _send_frame_2b(conn: socket.socket, msg: Dict) -> None:
    payload = build_payload(msg)
    prefix = len(payload).to_bytes(2, "big")
    conn.sendall(prefix + payload)


# ============================================================
# Business logic
# ============================================================

def _handle_message(msg: Dict) -> Dict:
    mti = str(msg.get("MTI", ""))

    # 0800 -> 0810 (network management)
    if mti == "0800":
        return {
            "MTI": "0810",
            "DE039": "00",
            "ECHO": msg,
        }

    # 0100 -> 0110 (Authorization)
    if mti == "0100":
        rrn = msg.get("DE037")
        if rrn:
            AUTH_STORE[str(rrn)] = msg

        return {
            "MTI": "0110",
            "DE039": "00",
            "DE038": "AUTH123",
            "ECHO": msg,
        }

    # 0400 -> 0410 (Reversal)
    if mti == "0400":
        rrn = msg.get("DE037")

        if rrn and str(rrn) in AUTH_STORE:
            return {
                "MTI": "0410",
                "DE039": "00",
                "ECHO": msg,
            }
        else:
            return {
                "MTI": "0410",
                "DE039": "25",  # no original found
                "ECHO": msg,
            }

    # Default echo response
    if len(mti) == 4:
        resp_mti = mti[:-1] + "10"
    else:
        resp_mti = "9999"

    return {
        "MTI": resp_mti,
        "DE039": "00",
        "ECHO": msg,
    }


# ============================================================
# TCP server loop
# ============================================================

def _client_loop(conn: socket.socket, addr) -> None:
    log.info("Client connected: %s:%s", addr[0], addr[1])

    try:
        while True:
            msg = _recv_frame_2b(conn, timeout=0.5)
            if msg is None:
                continue

            log.info("RX: %s", msg)
            response = _handle_message(msg)
            log.info("TX: %s", response)
            _send_frame_2b(conn, response)

    except Exception as e:
        log.error("Client error: %s", e)

    finally:
        conn.close()
        log.info("Client disconnected: %s:%s", addr[0], addr[1])


def start_server() -> None:
    log.info("Starting TCP server on %s:%s", HOST, PORT)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(5)

        while True:
            conn, addr = srv.accept()
            thread = threading.Thread(
                target=_client_loop,
                args=(conn, addr),
                daemon=True,
            )
            thread.start()


# ============================================================
# Run standalone
# ============================================================

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        log.info("Server stopped by user")
