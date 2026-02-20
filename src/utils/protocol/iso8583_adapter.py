from typing import Dict, Any

from src.utils.protocol.bnet_parser_message import BnetParserMessage
from src.utils.protocol.bnet_bin_message import BnetBinMessage


def parse_payload(payload: bytes) -> Dict[str, Any]:
    """Parse payload bytes (WITH 2B length prefix) into fields dict."""
    hex_data = payload.hex()
    hex_data_trimmed = hex_data[4:]
    bnet = BnetParserMessage(hex_data_trimmed)
    recv_message = bnet.extract_fields()
    return recv_message


def build_payload(fields: Dict[str, Any]) -> bytes:
    """Build payload bytes (WITH 2B length prefix) from fields dict."""
    bin_message = BnetBinMessage(fields)
    encoded_message = bytes.fromhex(bin_message.create_message_with_prefix())
    return encoded_message
