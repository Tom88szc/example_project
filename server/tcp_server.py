from __future__ import annotations

import json
import logging
import socket
import threading
from typing import Dict, Any


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

log = logging.getLogger("server.tcp_server")


# ==========================
# 2-byte length framing
# ==========================

def _recv_exact(sock: socket.socket, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Socket closed while receiving data")
        data += chunk
    return data


def receive_message(sock: socket.socket) -> Dict[str, Any]:
    header = _recv_exact(sock, 2)
    length = int.from_bytes(header, byteorder="big")
    payload = _recv_exact(sock, length)
    return json.loads(payload.decode("utf-8"))


def send_message(sock: socket.socket, msg: Dict[str, Any]) -> None:
    payload = json.dumps(msg).encode("utf-8")
    header = len(payload).to_bytes(2, byteorder="big")
    sock.sendall(header + payload)


# ==========================
# Server logic
# ==========================

class TcpServer:

    def __init__(self, host: str = "127.0.0.1", port: int = 5000):
        self.host = host
        self.port = port
        self._auth_store: Dict[str, Dict[str, Any]] = {}
        self._stop_event = threading.Event()

    def start(self) -> None:
        log.info("Starting TCP server on %s:%s", self.host, self.port)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((self.host, self.port))
            srv.listen(5)
            srv.settimeout(0.5)

            while not self._stop_event.is_set():
                try:
                    conn, addr = srv.accept()
                except socket.timeout:
                    continue

                log.info("Client connected: %s:%s", addr[0], addr[1])
                thread = threading.Thread(
                    target=self._client_loop,
                    args=(conn, addr),
                    daemon=True,
                )
                thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    # ==========================

    def _client_loop(self, conn: socket.socket, addr) -> None:
        try:
            while True:
                try:
                    msg = receive_message(conn)
                except ConnectionError:
                    break
                except OSError:
                    break

                log.info("RX: %s", msg)

                response = self._handle_message(msg)

                log.info("TX: %s", response)
                send_message(conn, response)

        finally:
            conn.close()
            log.info("Client disconnected: %s:%s", addr[0], addr[1])

    # ==========================

    def _handle_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        mti = str(msg.get("MTI", ""))

        # 0800 -> 0810
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
                self._auth_store[str(rrn)] = msg

            return {
                "MTI": "0110",
                "DE039": "00",
                "DE038": "AUTH123",
                "ECHO": msg,
            }

        # 0400 -> 0410 (Reversal)
        if mti == "0400":
            rrn = msg.get("DE037")

            if rrn and str(rrn) in self._auth_store:
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

        # default echo
        return {
            "MTI": mti[:-1] + "10" if len(mti) == 4 else "9999",
            "DE039": "00",
            "ECHO": msg,
        }


# ==========================
# Run standalone
# ==========================

if __name__ == "__main__":
    server = TcpServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
        log.info("Server stopped")
