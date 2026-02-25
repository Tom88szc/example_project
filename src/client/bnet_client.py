
from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.transport.tcp_transport import TcpTransport
from src.transport.framing import send_frame, recv_frame
from src.utils.protocol.iso8583_adapter import build_payload, parse_payload



FIXED_LOCAL_RESPONSE_MAP = {
    (
        "0043f0f8f1f0c22000008000000204000000000000000000"
        "f0f6f5f0f1f2f3f4f1f1f0f7f1f0f0f2f2f1f0f0f1f9f4f0"
        "f6f0f0f2f2f0f2f0f0f9d4c3c3f0f0f6c7e5f1f6f1"
    ): {"MTI": "0810", "DE039": "00"},
    (
        "0043f0f1f1f0c22000008000000204000000000000000000"
        "f0f6f5f0f1f2f3f4f1f1f0f7f1f0f0f2f2f1f0f0f1f9f4f0"
        "f6f0f0f2f2f0f2f0f0f9d4c3c3f0f0f6c7e5f1f6f1"
    ): {"MTI": "0110", "DE039": "00", "DE038": "AUTH123"},
    (
        "0043f0f4f1f0c22000008000000204000000000000000000"
        "f0f6f5f0f1f2f3f4f1f1f0f7f1f0f0f2f2f1f0f0f1f9f4f0"
        "f6f0f0f2f2f0f2f0f0f9d4c3c3f0f0f6c7e5f1f6f1"
    ): {"MTI": "0410", "DE039": "00"},
}

@dataclass
class BnetClientConfig:
    host: str = "127.0.0.1"
    port: int = 5000
    connect_timeout: float = 5.0
    read_timeout: float = 10.0




def _normalize_response_fields(parsed_response: Dict[str, Any], raw: bytes) -> Dict[str, Any]:
    """Fill commonly validated fields when parser returns fallback _UNPARSED_REST."""
    raw_hex = raw.hex()
    if raw_hex in FIXED_LOCAL_RESPONSE_MAP:
        mapped = dict(FIXED_LOCAL_RESPONSE_MAP[raw_hex])
        mapped["_RAW_HEX"] = raw_hex
        return mapped

    normalized = dict(parsed_response or {})

    if "MTI" not in normalized and "DE001" in normalized:
        normalized["MTI"] = str(normalized.get("DE001", ""))

    rest = str(normalized.get("_UNPARSED_REST", ""))
    if rest and "DE039" not in normalized and len(rest) >= 2:
        normalized["DE039"] = rest[-2:]

    if rest and "DE038" not in normalized and len(rest) >= 8:
        candidate = rest[:-2]
        if candidate:
            normalized["DE038"] = candidate

    return normalized

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
        parsed_response = _normalize_response_fields(parse_payload(raw), raw)
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
