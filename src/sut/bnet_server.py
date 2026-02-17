import socket
import threading
import logging

from src.transport.framing import add_length_prefix, strip_length_prefix
from src.protocol.iso8583_adapter import parse_payload, build_payload


log = logging.getLogger("sut.server")


class BnetServerConfig:
    def __init__(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port


class BnetServer:

    def __init__(self, config: BnetServerConfig):
        self.config = config

    def start(self):
        log.info(f"Starting BnetServer on {self.config.host}:{self.config.port}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.config.host, self.config.port))
            s.listen(5)

            while True:
                conn, addr = s.accept()
                threading.Thread(
                    target=self._client_loop,
                    args=(conn, addr),
                    daemon=True
                ).start()

    def _client_loop(self, conn, addr):
        log.info(f"Client connected: {addr}")
        try:
            while True:
                raw = strip_length_prefix(conn)
                if not raw:
                    break

                msg = parse_payload(raw)
                log.info(f"RX: {msg}")

                response = self._handle(msg)
                log.info(f"TX: {response}")

                payload = build_payload(response)
                conn.sendall(add_length_prefix(payload))

        except Exception as e:
            log.error(f"Client error: {e}")
        finally:
            conn.close()

    def _handle(self, msg: dict) -> dict:
        mti = msg.get("MTI")

        if mti == "0100":
            return {"MTI": "0110", "DE039": "00", "ECHO": msg}

        if mti == "0400":
            return {"MTI": "0410", "DE039": "00", "ECHO": msg}

        if mti == "0800":
            return {"MTI": "0810", "DE039": "00", "ECHO": msg}

        return {"MTI": "9999", "DE039": "96"}
