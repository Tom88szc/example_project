from typing import Dict, Any

from src.utils.protocol.bnet_parser_message import BnetParserMessage
from src.utils.protocol.bnet_bin_message import BnetBinMessage


def parse_payload(payload: bytes) -> Dict[str, Any]:
    """Parse payload bytes (WITHOUT 2B length) into fields dict."""
    return BnetParserMessage(payload).extract_fields()


def build_payload(fields: Dict[str, Any]) -> bytes:
    """Build payload bytes (WITHOUT 2B length) from fields dict."""
    return BnetBinMessage(fields).to_bytes()
