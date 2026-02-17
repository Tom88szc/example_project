import json
from typing import Dict, Any


class BnetParserMessage:
    """
    Parser layer.

    IMPORTANT (architecture rule):
    - Receives PAYLOAD only (WITHOUT the 2-byte length prefix).
    - The 2-byte length prefix MUST be handled only by transport/framing.

    Default implementation in this repo parses JSON payload into dict so the project runs out-of-the-box.
    Replace the internals with real ISO8583 parsing (bitmap + DE parsing + cp500) when integrating
    with the production protocol stack.
    """

    def __init__(self, payload: bytes, encoding: str = "utf-8"):
        self.payload = payload
        self.encoding = encoding

    def extract_fields(self) -> Dict[str, Any]:
        txt = self.payload.decode(self.encoding)
        return json.loads(txt)
