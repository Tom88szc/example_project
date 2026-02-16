from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class BnetBinMessage:
    """
    Protocol layer (ISO8583) builder.
    MUST return PAYLOAD bytes only (no 2-byte length prefix).
    Length prefix is handled exclusively by transport/framing.
    """
    fields: Dict[str, Any]
    codec: str = "cp500"

    def to_payload_bytes(self) -> bytes:
        # TODO: Replace with real ISO8583 packing (MTI + bitmap + DE fields)
        # Placeholder: MTI as EBCDIC 4 bytes.
        mti = str(self.fields.get("MTI", ""))
        return mti.encode(self.codec)

    def to_payload_hex(self) -> str:
        return self.to_payload_bytes().hex().upper()
