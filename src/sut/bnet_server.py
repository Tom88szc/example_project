import json
import logging
import socket
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from src.transport.framing import Length2JsonFraming


@dataclass
class BnetServerConfig:
    host: str = "127.0.0.1"
    port: int = 5000
    read_timeout: float = 10.0
    log_name: str = "sut.bnet_server"


@dataclass
class BnetServer:
    """
    Simple SUT TCP server (we are the server now).
    Protocol for now: 2-byte length prefix + JSON payload (dict with MTI/DE fields).
    """
    config: BnetServerConfig = field(default_factory=BnetServerConfig)

    _log: logging.Logger = field(init=False)
    _srv_sock: Optional[socket.socket] = field(default=None, init=False)
    _thread: Optional[threading.Thread] = field(default=None, init=False)
    _stop_evt: threading.Event = field(default_factory=threading.Event, init=False)

    # in-memory state for dependent flows (auth -> reversal)
    _auth_store: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._log = logging.getLogger(self.config.log_name)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_evt.clear()
        self._srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv_sock.bind((self.config.host, self.config.port))
        self._srv_sock.listen(5)
        self._srv_sock.settimeout(0.5)

        self._thread = threading.Thread(target=self._accept_loop, name="BnetServer", daemon=True)
        self._thread.start()
        self._log.info("SUT server listening on %s:%s", self.config.host, self.config.port)

    def stop(self) -> None:
        self._stop_evt.set()
        try:
            if self._srv_sock:
                try:
                    self._srv_sock.close()
                except Exception:
                    pass
        finally:
            self._srv_sock = None

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        self._log.info("SUT server stopped")

    def _accept_loop(self) -> None:
        assert self._srv_sock is not None
        while not self._stop_evt.is_set():
            try:
                conn, addr = self._srv_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            self._log.info("Client connected: %s:%s", addr[0], addr[1])
            t = threading.Thread(target=self._client_loop, args=(conn, addr), daemon=True)
            t.start()

    def _client_loop(self, conn: socket.socket, addr) -> None:
        framing = Length2JsonFraming()
        try:
            while not self._stop_evt.is_set():
                try:
                    msg = framing.receive(conn, timeout=0.5)
                except socket.timeout:
                    continue
                except ConnectionError:
                    break
                except OSError:
                    break

                if msg is None:
                    continue

                self._log.info("RX: %s", msg)
                resp = self._handle_message(msg)
                self._log.info("TX: %s", resp)
                framing.send(conn, resp)
        finally:
            try:
                conn.close()
            except Exception:
                pass
            self._log.info("Client disconnected: %s:%s", addr[0], addr[1])

    def _handle_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        mti = str(msg.get("MTI", ""))

        # Heartbeat / network management
        if mti == "0800":
            return {"MTI": "0810", "DE039": "00", "ECHO": msg}

        # Authorization
        if mti == "0100":
            rrn = msg.get("DE037")
            if rrn:
                self._auth_store[str(rrn)] = {"request": dict(msg)}
            # provide DE038 to enable reversal copy
            return {"MTI": "0110", "DE039": "00", "DE038": "AUTH123", "ECHO": msg}

        # Reversal
        if mti == "0400":
            rrn = msg.get("DE037")
            if rrn and str(rrn) in self._auth_store:
                self._auth_store[str(rrn)]["reversal"] = dict(msg)
                return {"MTI": "0410", "DE039": "00", "ECHO": msg}
            return {"MTI": "0410", "DE039": "25", "ECHO": msg}

        # Default
        return {"MTI": (mti[:-1] + "10") if len(mti) == 4 else "9999", "DE039": "00", "ECHO": msg}
