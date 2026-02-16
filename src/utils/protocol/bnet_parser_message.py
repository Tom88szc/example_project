from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class BnetParserMessage:
    """
    Protocol layer (ISO8583) parser.
    MUST accept PAYLOAD bytes only (no 2-byte length prefix).
    Length prefix is handled exclusively by transport/framing.
    """
    payload: bytes
    codec: str = "cp500"

    @classmethod
    def from_hex(cls, payload_hex: str, codec: str = "cp500") -> "BnetParserMessage":
        return cls(bytes.fromhex(payload_hex), codec=codec)

    def extract_fields(self) -> Dict[str, Any]:
        # TODO: Replace with real ISO8583 parsing (MTI + bitmap + DE fields)
        # Placeholder: decode first 4 bytes as MTI in EBCDIC.
        if not self.payload:
            return {"MTI": ""}
        mti_bytes = self.payload[:4]
        mti = mti_bytes.decode(self.codec, errors="replace")
        return {"MTI": mti}
