from __future__ import annotations

import json
import logging
import os
import socket
import threading
from typing import Dict, Tuple


HOST = os.getenv("BN_MOCK_HOST", "127.0.0.1")
PORT = int(os.getenv("BN_MOCK_PORT", "5000"))

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("server.tcp_server")


def _recvline(conn: socket.socket) -> bytes:
    chunks = []
    while True:
        b = conn.recv(1)
        if not b:
            return b""
        if b == b"\n":
            break
        chunks.append(b)
    return b"".join(chunks)


def _build_response(req: Dict[str, str]) -> Dict[str, str]:
    # Minimalna logika: dla MTI=0100 odpowiadamy MTI=0110 i DE039=00
    mti = str(req.get("MTI", ""))
    resp: Dict[str, str] = {}

    if mti == "0100":
        resp["MTI"] = "0110"
        resp["DE039"] = "00"
    else:
        # unknown -> error
        resp["MTI"] = "9999"
        resp["DE039"] = "96"  # system malfunction (przykładowo)

    # Echo request (przydatne w debug)
    resp["ECHO"] = req
    return resp


def handle_client(conn: socket.socket, addr: Tuple[str, int]) -> None:
    log.info("Client connected: %s:%s", addr[0], addr[1])
    with conn:
        while True:
            line = _recvline(conn)
            if not line:
                break

            try:
                req = json.loads(line.decode("utf-8"))
                log.info("REQ: %s", req)
                resp = _build_response(req)
                log.info("RESP: %s", resp)
                conn.sendall((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
            except Exception as exc:  # noqa: BLE001
                err = {"MTI": "9999", "DE039": "96", "ERROR": str(exc)}
                conn.sendall((json.dumps(err, ensure_ascii=False) + "\n").encode("utf-8"))

    log.info("Client disconnected: %s:%s", addr[0], addr[1])


def main() -> None:
    log.info("Starting TCP mock server on %s:%s", HOST, PORT)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(50)

        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()


if __name__ == "__main__":
    main()
