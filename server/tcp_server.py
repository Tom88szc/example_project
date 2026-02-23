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


def _extract_0400_fields(msg: Dict[str, Any]) -> Dict[str, str]:
    """Best-effort decode for current 0400 test payload layout.

    Requests reach server mostly as MTI + _UNPARSED_REST. For 0400 scenarios in this
    repository the rest uses fixed field order/length:
    DE003(6) + DE004(12) + DE011(6) + DE037(12) + DE038(6?) + DE090(22?)
    """
    rest = str(msg.get("_UNPARSED_REST", ""))
    if len(rest) < 36:
        return {}

    return {
        "DE003": rest[0:6],
        "DE004": rest[6:18],
        "DE011": rest[18:24],
        "DE037": rest[24:36],
        "DE038": rest[36:42],
        "DE090": rest[42:64],
    }


def handle(msg: Dict[str, Any]) -> Dict[str, Any]:
    mti = str(msg.get("MTI", ""))

    if mti == "0800":
        return {"MTI": "0810", "DE039": "00"}

    if mti == "0100":
        rest = str(msg.get("_UNPARSED_REST", ""))
        # Negative scenario in this project intentionally omits PAN/expiry and sends
        # only DE003+DE004 (18 chars). Emulate host decline for that case.
        if len(rest) == 18:
            return {"MTI": "0110", "DE039": "05", "DE038": "DECLIN"}

        rrn = msg.get("DE037")
        if rrn:
            AUTH_STORE[str(rrn)] = msg
        return {"MTI": "0110", "DE039": "00", "DE038": "AUTH123"}

    if mti == "0400":
        f0400 = _extract_0400_fields(msg)
        rrn = f0400.get("DE037") or msg.get("DE037")

        # Unknown/original-not-found branch used by negative scenario
        if rrn == "000000000000":
            return {"MTI": "0410", "DE039": "25"}

        # For current test harness we approve other reversals.
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
                continue
            msg = parse_payload(raw)
            log.info("RX: %s", msg)
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
