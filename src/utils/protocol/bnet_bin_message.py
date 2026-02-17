import json
from typing import Dict, Any


class BnetBinMessage:
    """
    Builder layer.

    IMPORTANT (architecture rule):
    - Builds PAYLOAD only (WITHOUT the 2-byte length prefix).
    - The 2-byte length prefix MUST be handled only by transport/framing.

    Default implementation in this repo builds JSON payload bytes so the project runs out-of-the-box.
    Replace the internals with real ISO8583 building (bitmap + DE building + cp500) when integrating
    with the production protocol stack.
    """

    def __init__(self, fields: Dict[str, Any], encoding: str = "utf-8"):
        self.fields = fields
        self.encoding = encoding

    def to_bytes(self) -> bytes:
        return json.dumps(self.fields, ensure_ascii=False).encode(self.encoding)
