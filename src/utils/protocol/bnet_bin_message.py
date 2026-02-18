import codecs
from typing import Dict, Any


class BnetBinMessage:
    """
    Builds ISO-like BNET message (without 2-byte length prefix).
    Transport layer is responsible for framing.
    """

    def __init__(self, de_fields: Dict[str, Any], encoding: str = "cp500"):
        self.encoding = encoding
        self.fields = {k: str(v) if not isinstance(v, dict) else v
                       for k, v in de_fields.items()}

        if "DE001" not in self.fields:
            raise ValueError("DE001 (MTI) is required")

        self.mti = self.fields["DE001"]

    # ============================================================
    # PUBLIC
    # ============================================================

    def build(self) -> bytes:
        """
        Returns full binary message (no length prefix).
        """
        bitmap_hex = self._build_bitmap()
        body_hex = self._build_fields()

        mti_hex = self._ascii_to_ebcdic(self.mti)

        full_hex = mti_hex + bitmap_hex + body_hex
        return bytes.fromhex(full_hex)

    # ============================================================
    # BITMAP
    # ============================================================

    def _build_bitmap(self) -> str:
        primary = ['0'] * 64
        secondary = ['0'] * 64
        has_secondary = False

        for field in self.fields.keys():
            if field in ("DE001",):
                continue

            number = int(field[2:])

            if number <= 64:
                primary[number - 1] = '1'
            elif number <= 128:
                has_secondary = True
                secondary[number - 65] = '1'
            else:
                raise ValueError(f"Field {field} out of range")

        if has_secondary:
            primary[0] = '1'

        primary_hex = f"{int(''.join(primary), 2):016X}"

        if has_secondary:
            secondary_hex = f"{int(''.join(secondary), 2):016X}"
            return primary_hex + secondary_hex

        return primary_hex

    # ============================================================
    # FIELD BUILDING
    # ============================================================

    def _build_fields(self) -> str:
        result = ""

        for field in sorted(self.fields.keys()):
            if field == "DE001":
                continue

            value = self.fields[field]

            if isinstance(value, dict):
                value = self._serialize_tlv(value)

            # variable length example
            if field in ("DE002", "DE035"):
                result += self._encode_llvar(value)
            elif field in ("DE048", "DE055", "DE104", "DE108", "DE112", "DE122"):
                result += self._encode_lllvar(value)
            else:
                result += self._ascii_to_ebcdic(value)

        return result

    # ============================================================
    # ENCODERS
    # ============================================================

    def _ascii_to_ebcdic(self, value: str) -> str:
        encoded = codecs.encode(value, self.encoding)
        return encoded.hex().upper()

    def _encode_llvar(self, value: str) -> str:
        length = str(len(value)).zfill(2)
        return self._ascii_to_ebcdic(length) + self._ascii_to_ebcdic(value)

    def _encode_lllvar(self, value: str) -> str:
        length = str(len(value)).zfill(3)
        return self._ascii_to_ebcdic(length) + self._ascii_to_ebcdic(value)

    # ============================================================
    # TLV SERIALIZATION
    # ============================================================

    def _serialize_tlv(self, data: Dict[str, Any]) -> str:
        """
        Serializes nested dict into TLV string.
        """
        result = ""

        for tag, value in data.items():
            if isinstance(value, dict):
                value = self._serialize_tlv(value)

            length = str(len(value)).zfill(2)
            result += f"{tag}{length}{value}"

        return result
