from __future__ import annotations

from typing import Any, Dict, Protocol


class ExternalBinBuilder(Protocol):
    """External builder that returns HEX including 2-byte length prefix (4 hex chars)."""
    def create_message_with_prefix(self) -> str: ...


class ExternalBnetBinMessageAdapter:
    """
    Adapter: uses external builder that returns HEX = [2B length prefix][payload].
    Returns PAYLOAD bytes only (no prefix), because prefix must be added by framing.
    """
    def __init__(self, fields: Dict[str, Any], external_builder: ExternalBinBuilder):
        self.fields = fields
        self.external_builder = external_builder

    def to_payload_bytes(self) -> bytes:
        hex_with_prefix = self.external_builder.create_message_with_prefix().strip()
        if len(hex_with_prefix) < 4:
            raise ValueError(f"External builder returned too short hex: {hex_with_prefix!r}")
        payload_hex = hex_with_prefix[4:]  # strip 2B length prefix (4 hex chars)
        return bytes.fromhex(payload_hex)
