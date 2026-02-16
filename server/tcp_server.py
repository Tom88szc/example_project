from __future__ import annotations
# In-memory store of authorizations by RRN (DE037)
AUTH_STORE = {}


import json
import logging
import os
import socket
import threading
import time
from typing import Dict, Tuple, Optional

HOST = os.getenv("BN_MOCK_HOST", "127.0.0.1")
PORT = int(os.getenv("BN_MOCK_PORT", "5000"))
HEARTBEAT_SECONDS = float(os.getenv("BN_HEARTBEAT_SECONDS", "2.0"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("server.tcp_server")


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
    except (socket.timeout, ConnectionError):
        return None
    length = int.from_bytes(prefix, "big", signed=False)
    if length == 0:
        return None
    payload = _recv_exact(conn, length, timeout=timeout)
    return json.loads(payload.decode("utf-8", errors="replace"))


def _send_frame_2b(conn: socket.socket, msg: Dict) -> None:
    payload = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    length = len(payload)
    conn.sendall(length.to_bytes(2, "big") + payload)


def _heartbeat_loop(conn: socket.socket, stop: threading.Event) -> None:
    # Optional heartbeat (application-level). For demo we keep sending small JSON ping.
    while not stop.is_set():
        time.sleep(HEARTBEAT_SECONDS)
        try:
            _send_frame_2b(conn, {"MTI": "0800", "DE070": "001"})  # mock heartbeat request
        except Exception:
            return


def handle_client(conn: socket.socket, addr: Tuple[str, int]) -> None:
    stop = threading.Event()
    hb = threading.Thread(target=_heartbeat_loop, args=(conn, stop), daemon=True)
    hb.start()
    try:
        while True:
            msg = _recv_frame_2b(conn, timeout=0.5)
            if msg is None:
                continue

            log.info("RX: %s", msg)

            mti = msg.get("MTI")
rrn = msg.get("DE037")
if mti == "0100" and rrn:
    AUTH_STORE[rrn] = {"request": dict(msg)}
            if mti == "0800":
                resp = {"MTI": "0810", "DE039": "00", "ECHO": msg}
            elif mti == "0100":
                resp = {"MTI": "0110", "DE039": "00", "DE038": "AUTH123", "ECHO": msg}
elif mti == "0400":
    rrn = msg.get("DE037")
    if rrn and rrn in AUTH_STORE:
        # optional: update stored reversal info
        AUTH_STORE[rrn]["reversal"] = dict(msg)
        response = {"MTI": "0410", "DE039": "00", "ECHO": msg}
    else:
        response = {"MTI": "0410", "DE039": "25", "ECHO": msg}

            else:
                resp = {"MTI": "9999", "DE039": "96", "ECHO": msg}

            log.info("TX: %s", resp)
            _send_frame_2b(conn, resp)
    except ConnectionError:
        pass
    except Exception as e:
        log.exception("Client handler error: %s", e)
    finally:
        stop.set()
        try:
            conn.close()
        except Exception:
            pass
        log.info("Client disconnected: %s:%s", addr[0], addr[1])


def serve() -> None:
    log.info("Starting TCP mock server on %s:%s (HB every %.1fs) [2B length framing]", HOST, PORT, HEARTBEAT_SECONDS)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        while True:
            conn, addr = s.accept()
            log.info("Client connected: %s:%s", addr[0], addr[1])
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()


if __name__ == "__main__":
    serve()



# --- Optional RAW 2B framing helpers (for future ISO8583 bytes payload) ---
        def _recv_exact(sock, n: int) -> bytes:
            buf = b""
            while len(buf) < n:
                chunk = sock.recv(n - len(buf))
                if not chunk:
                    return b""
                buf += chunk
            return buf

        def recv_len2_payload(sock) -> bytes:
            prefix = _recv_exact(sock, 2)
            if not prefix or len(prefix) < 2:
                return b""
            length = int.from_bytes(prefix, "big")
            if length == 0:
                return b""
            return _recv_exact(sock, length)
