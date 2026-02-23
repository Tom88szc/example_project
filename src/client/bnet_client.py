
from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.transport.tcp_transport import TcpTransport
from src.transport.framing import send_frame, recv_frame
from src.utils.protocol.iso8583_adapter import build_payload, parse_payload


@dataclass
class BnetClientConfig:
    host: str = "127.0.0.1"
    port: int = 5000
    connect_timeout: float = 5.0
    read_timeout: float = 10.0


class BnetClient:
    def __init__(self, config: Optional[BnetClientConfig] = None):
        self.config = config or BnetClientConfig()
        self.transport = TcpTransport(
            host=self.config.host,
            port=self.config.port,
            connect_timeout=self.config.connect_timeout,
            read_timeout=self.config.read_timeout,
        )
        self.last_exchange: Dict[str, Any] = {}

    def send(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        payload = build_payload(fields)
        self.last_exchange = {
            "sent": {
                "parsed": dict(fields),
                "unparsed_hex": payload.hex(),
            },
            "received": {},
        }

        try:
            self.transport.connect()
            assert self.transport.sock is not None
            send_frame(self.transport.sock, payload)
            raw = recv_frame(self.transport.sock)
        except Exception as exc:
            self.last_exchange["received"] = {
                "parsed": {},
                "unparsed_hex": "",
                "error": f"{type(exc).__name__}: {exc}",
                "target": f"{self.transport.host}:{self.transport.port}",
            }
            raise
        finally:
            self.transport.close()

        if raw is None:
            raise ConnectionError("No response received (server disconnected?)")
        parsed_response = parse_payload(raw)
        self.last_exchange = {
            "sent": {
                "parsed": dict(fields),
                "unparsed_hex": payload.hex(),
            },
            "received": {
                "parsed": parsed_response,
                "unparsed_hex": raw.hex(),
            },
        }

        return parsed_response
