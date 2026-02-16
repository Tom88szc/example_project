from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from src.transport.tcp_transport import TcpTransport


@dataclass(frozen=True)
class BnetClientConfig:
    env: str
    host: str
    port: int
    connect_timeout: float = 5.0
    read_timeout: float = 10.0

    default_card_number: str = "5575061111100075"
    default_expiry_date: str = "2907"


EventSink = Callable[[str, Dict[str, Any]], None]


class BnetClientError(RuntimeError):
    pass


class BnetClient:
    """Full-duplex TCP client with 0800->0810 auto-handling and safe shutdown."""

    def __init__(self, config: BnetClientConfig):
        self.config = config
        self.log = logging.getLogger(self.__class__.__name__)
        self._transport: Optional[TcpTransport] = None
        self._receiver: Optional[threading.Thread] = None
        self._running = threading.Event()
        self._inbox: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._event_sink: Optional[EventSink] = None

    def set_event_sink(self, sink: Optional[EventSink]) -> None:
        self._event_sink = sink

    def _emit(self, direction: str, msg: Dict[str, Any]) -> None:
        if self._event_sink is not None:
            try:
                self._event_sink(direction, msg)
            except Exception:
                pass

    def connect_and_login(self) -> None:
        if self.is_connected():
            return
        self._transport = TcpTransport(
            host=self.config.host,
            port=self.config.port,
            connect_timeout=self.config.connect_timeout,
            read_timeout=self.config.read_timeout,
            framing=None,
        )
        self._transport.connect()
        self._running.set()
        self._receiver = threading.Thread(target=self._receiver_loop, daemon=True)
        self._receiver.start()

    def logout_and_close(self) -> None:
        self._running.clear()
        if self._transport is not None:
            try:
                self._transport.shutdown()
            except Exception:
                pass
        if self._receiver is not None and self._receiver.is_alive():
            self._receiver.join(timeout=2.0)
        self._receiver = None
        if self._transport is not None:
            try:
                self._transport.close()
            finally:
                self._transport = None
        while not self._inbox.empty():
            try:
                self._inbox.get_nowait()
            except Exception:
                break

    def is_connected(self) -> bool:
        return self._transport is not None and self._transport.is_connected()

    def _receiver_loop(self) -> None:
        assert self._transport is not None
        while self._running.is_set():
            try:
                msg = self._transport.receive(timeout=0.5)
                if msg is None:
                    continue
                self._emit("RX", msg)
                if str(msg.get("MTI", "")) == "0800":
                    self._handle_0800(msg)
                    continue
                self._inbox.put(msg)
            except Exception as exc:
                if not self._running.is_set():
                    break
                self.log.exception("Receiver loop error: %s", exc)
                self._running.clear()
                break

    def _handle_0800(self, request: Dict[str, Any]) -> None:
        resp: Dict[str, Any] = {"MTI": "0810", "DE039": "00"}
        if "DE070" in request:
            resp["DE070"] = request["DE070"]
        self.send(resp)

    def send(self, fields: Dict[str, Any]) -> None:
        if self._transport is None:
            raise BnetClientError("Not connected.")
        self._emit("TX", fields)
        self._transport.send(fields)

    def send_and_wait(self, fields: Dict[str, Any], expect_mti: str, timeout: float = 10.0) -> Dict[str, Any]:
        self.send(fields)
        deadline = time.time() + timeout
        buffered = []
        while time.time() < deadline:
            remaining = max(0.05, deadline - time.time())
            try:
                msg = self._inbox.get(timeout=min(0.5, remaining))
            except queue.Empty:
                continue
            if str(msg.get("MTI", "")) == expect_mti:
                for b in buffered:
                    self._inbox.put(b)
                return msg
            buffered.append(msg)
        for b in buffered:
            self._inbox.put(b)
        raise BnetClientError(f"Timeout waiting for MTI={expect_mti}")
