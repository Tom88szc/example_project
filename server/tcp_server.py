import logging
import socket
import threading
from typing import Any, Dict

from src.transport.framing import send_frame, recv_frame
from src.utils.protocol.iso8583_adapter import build_payload, parse_payload

HOST = "127.0.0.1"
PORT = 5000

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("server.tcp_server")

AUTH_STORE: Dict[str, Dict[str, Any]] = {}

# Stałe odpowiedzi hosta dla testów lokalnych (ramka z prefiksem długości).
FIXED_HEX_RESPONSES = {
    "0800": (
        "0043F0F8F1F0C22000008000000204000000000000000000"
        "F0F6F5F0F1F2F3F4F1F1F0F7F1F0F0F2F2F1F0F0F1F9F4F0"
        "F6F0F0F2F2F0F2F0F0F9D4C3C3F0F0F6C7E5F1F6F1"
    ),
    "0100": (
        "0043F0F1F1F0C22000008000000204000000000000000000"
        "F0F6F5F0F1F2F3F4F1F1F0F7F1F0F0F2F2F1F0F0F1F9F4F0"
        "F6F0F0F2F2F0F2F0F0F9D4C3C3F0F0F6C7E5F1F6F1"
    ),
    "0400": (
        "0043F0F4F1F0C22000008000000204000000000000000000"
        "F0F6F5F0F1F2F3F4F1F1F0F7F1F0F0F2F2F1F0F0F1F9F4F0"
        "F6F0F0F2F2F0F2F0F0F9D4C3C3F0F0F6C7E5F1F6F1"
    ),
}


def handle(msg: Dict[str, Any]) -> Dict[str, Any]:
    mti = str(msg.get("MTI", ""))

    if mti == "0800":
        return {"MTI": "0810", "DE039": "00"}

    if mti == "0100":
        rrn = msg.get("DE037")
        if rrn:
            AUTH_STORE[str(rrn)] = msg
        return {"MTI": "0110", "DE039": "00", "DE038": "AUTH123"}

    if mti == "0400":
        return {"MTI": "0410", "DE039": "00"}

    # default
    resp_mti = (mti[:-1] + "10") if len(mti) == 4 else "9999"
    return {"MTI": resp_mti, "DE039": "00"}


def _client_loop(conn: socket.socket, addr) -> None:
    log.info("Client connected: %s:%s", addr[0], addr[1])
    try:
        while True:
            raw = recv_frame(conn, timeout=0.5)
            if raw is None:
                try:
                    probe = conn.recv(1, socket.MSG_PEEK)
                except socket.timeout:
                    continue
                except OSError:
                    break

                if not probe:
                    break
                continue

            if len(raw) <= 2:
                log.info("Ignoring empty frame from %s:%s", addr[0], addr[1])
                continue

            msg = parse_payload(raw)
            log.info("RX: %s", msg)
            mti = str(msg.get("MTI", ""))
            fixed_hex = FIXED_HEX_RESPONSES.get(mti)
            if fixed_hex is not None:
                log.info("TX (fixed): %s", fixed_hex)
                payload = bytes.fromhex(fixed_hex)
            else:
                resp = handle(msg)
                if "MTI" in resp and "DE001" not in resp:
                    resp = dict(resp)
                    resp["DE001"] = resp.pop("MTI")
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
