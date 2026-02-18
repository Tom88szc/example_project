
import logging
import socket
import threading
from typing import Any, Dict, Optional

from src.transport.framing import send_frame, recv_frame
from src.utils.protocol.iso8583_adapter import build_payload, parse_payload

HOST = "127.0.0.1"
PORT = 5000

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("server.tcp_server")

AUTH_STORE: Dict[str, Dict[str, Any]] = {}


def handle(msg: Dict[str, Any]) -> Dict[str, Any]:
    mti = str(msg.get("MTI", ""))

    if mti == "0800":
        return {"MTI": "0810", "DE039": "00", "ECHO": msg}

    if mti == "0100":
        rrn = msg.get("DE037")
        if rrn:
            AUTH_STORE[str(rrn)] = msg
        return {"MTI": "0110", "DE039": "00", "DE038": "AUTH123", "ECHO": msg}

    if mti == "0400":
        rrn = msg.get("DE037")
        if rrn and str(rrn) in AUTH_STORE:
            return {"MTI": "0410", "DE039": "00", "ECHO": msg}
        return {"MTI": "0410", "DE039": "25", "ECHO": msg}

    # default
    resp_mti = (mti[:-1] + "10") if len(mti) == 4 else "9999"
    return {"MTI": resp_mti, "DE039": "00", "ECHO": msg}


def _client_loop(conn: socket.socket, addr) -> None:
    log.info("Client connected: %s:%s", addr[0], addr[1])
    try:
        while True:
            raw = recv_frame(conn, timeout=0.5)
            if raw is None:
                continue
            msg = parse_payload(raw)
            log.info("RX: %s", msg)
            resp = handle(msg)
            log.info("TX: %s", resp)
            payload = build_payload(resp)
            send_frame(conn, payload)
    except Exception as e:
        log.error("Client loop error: %s", e)
    finally:
        try:
            conn.close()
        finally:
            log.info("Client disconnected: %s:%s", addr[0], addr[1])


def start() -> None:
    log.info("Starting TCP mock server on %s:%s", HOST, PORT)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=_client_loop, args=(conn, addr), daemon=True)
            t.start()


if __name__ == "__main__":
    start()
