from __future__ import annotations

import json
import logging
import socket
import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class BnetClientConfig:
    env: str
    host: str
    port: int
    connect_timeout: float = 5.0
    read_timeout: float = 10.0
    retries: int = 1
    retry_backoff: float = 0.3


class BnetClientError(RuntimeError):
    pass


class BnetClient:
    """
    Prosty klient TCP do testów.
    Protokół: 1 linia JSON zakończona \n -> 1 linia JSON zakończona \n
    """

    def __init__(self, config: BnetClientConfig):
        self.config = config
        self.log = logging.getLogger(self.__class__.__name__)
        self._sock: Optional[socket.socket] = None
        self._logged_in = False

    def login(self) -> None:
        if self._logged_in:
            return

        self.log.info("Connecting to %s:%s (%s)", self.config.host, self.config.port, self.config.env)

        try:
            sock = socket.create_connection(
                (self.config.host, self.config.port),
                timeout=self.config.connect_timeout,
            )
            sock.settimeout(self.config.read_timeout)
            self._sock = sock
            self._logged_in = True
        except OSError as exc:
            raise BnetClientError(f"Cannot connect/login to server: {exc}") from exc

    def logout(self) -> None:
        if not self._logged_in:
            return
        self.log.info("Disconnecting...")
        self.close()
        self._logged_in = False

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None

    def send_transaction(self, iso_fields: Dict[str, str]) -> Dict[str, str]:
        if not self._logged_in or self._sock is None:
            raise BnetClientError("Not logged in (no socket). Call login() first.")

        payload = json.dumps(iso_fields, ensure_ascii=False) + "\n"
        data = payload.encode("utf-8")

        last_exc: Optional[Exception] = None
        for attempt in range(1, self.config.retries + 2):
            try:
                self.log.info("Sending transaction attempt %d/%d", attempt, self.config.retries + 1)
                self._sock.sendall(data)

                # read one line (\n terminated)
                response_bytes = self._recvline(self._sock)
                response_text = response_bytes.decode("utf-8").strip()
                return json.loads(response_text)

            except (OSError, json.JSONDecodeError) as exc:
                last_exc = exc
                self.log.exception("Send/receive failed: %s", exc)

                if attempt <= self.config.retries:
                    time.sleep(self.config.retry_backoff)
                    # reconnect on retry
                    try:
                        self.close()
                        self._logged_in = False
                        self.login()
                    except Exception:
                        pass
                    continue
                break

        raise BnetClientError(f"Failed to send transaction. Last error: {last_exc}")

    @staticmethod
    def _recvline(sock: socket.socket) -> bytes:
        chunks = []
        while True:
            b = sock.recv(1)
            if not b:
                raise OSError("Connection closed by server")
            if b == b"\n":
                break
            chunks.append(b)
        return b"".join(chunks)
