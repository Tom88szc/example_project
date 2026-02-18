import codecs
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List


# FIELD_DEFS = {
#     "DE002": FieldDef("LLVAR"),
#     "DE003": FieldDef(6),
#     "DE004": FieldDef(12),
#     "DE011": FieldDef(6),
#     "DE037": FieldDef(12),
#     "DE039": FieldDef(2),
#     "DE048": FieldDef("LLLVAR"),
#     "DE055": FieldDef("LLLVAR"),
# }
# TLV_FIELDS = {"DE048", "DE055"}


@dataclass(frozen=True)
class FieldDef:
    """
    Field definition:
    - length: fixed length in characters (int) OR
    - length: "LLVAR" / "LLLVAR" (variable length with 2/3 digits)
    """
    length: Any  # int | "LLVAR" | "LLLVAR"


class BnetParserMessage:
    """
    Parses ISO-like BNET message:
      [MTI (4 chars)] [BITMAP (8 or 16 bytes)] [FIELDS...]
    Payload is EBCDIC cp500.
    Transport framing (2-byte length prefix) MUST be handled elsewhere.
    """

    def __init__(
        self,
        payload: bytes | str,
        *,
        encoding: str = "cp500",
        field_defs: Optional[Dict[str, FieldDef]] = None,
        tlv_fields: Optional[set[str]] = None,
    ):
        """
        payload:
          - bytes: raw message bytes (no length prefix)
          - str: hex string of raw bytes (no length prefix)

        field_defs:
          mapping like {"DE002": FieldDef("LLVAR"), "DE003": FieldDef(6), ...}
          If None, parser will only return MTI + bitmap info (fields not parsed).

        tlv_fields:
          which DE fields should be parsed as TLV (e.g. {"DE048","DE055","DE104"...})
        """
        self.encoding = encoding
        self.field_defs = field_defs or {}
        self.tlv_fields = tlv_fields or set()

        self._raw_bytes = self._coerce_to_bytes(payload)
        self._ascii = self._decode_ebcdic(self._raw_bytes)

        # Parsed
        self.mti: str = ""
        self.bitmap_hex: str = ""
        self.active_fields: List[str] = []
        self.fields: Dict[str, Any] = {}

        self._parse()

    # ============================================================
    # PUBLIC
    # ============================================================

    def extract_fields(self) -> Dict[str, Any]:
        """
        Returns dict with keys:
          - "MTI" plus parsed DE fields: "DE002", "DE003", ...
        """
        return dict(self.fields)

    # ============================================================
    # CORE PARSE
    # ============================================================

    def _parse(self) -> None:
        # MTI is first 4 chars in decoded ASCII/EBCDIC text
        if len(self._ascii) < 4:
            raise ValueError("Payload too short to contain MTI")

        self.mti = self._ascii[:4]
        self.fields = {"MTI": self.mti}

        # Next: bitmap bytes are right after MTI in the raw bytes
        # MTI = 4 chars -> 4 bytes in EBCDIC
        # Primary bitmap = 8 bytes
        if len(self._raw_bytes) < 4 + 8:
            raise ValueError("Payload too short to contain primary bitmap")

        primary_bitmap = self._raw_bytes[4:12]
        primary_bits = self._bytes_to_bits(primary_bitmap)

        has_secondary = primary_bits[0] == "1"

        if has_secondary:
            if len(self._raw_bytes) < 4 + 16:
                raise ValueError("Payload indicates secondary bitmap but payload is too short")
            secondary_bitmap = self._raw_bytes[12:20]
            secondary_bits = self._bytes_to_bits(secondary_bitmap)
            bitmap_bits = primary_bits + secondary_bits
            bitmap_bytes_total = 16
            self.bitmap_hex = (primary_bitmap + secondary_bitmap).hex().upper()
        else:
            bitmap_bits = primary_bits
            bitmap_bytes_total = 8
            self.bitmap_hex = primary_bitmap.hex().upper()

        self.active_fields = self._bits_to_active_fields(bitmap_bits)

        # After bitmap, rest is fields data in decoded string form.
        # We parse fields based on field_defs (lengths are in characters of decoded string).
        body_ascii = self._ascii[4 + bitmap_bytes_total :]  # MTI(4 chars) + bitmap bytes count
        idx = 0

        for de in self.active_fields:
            # DE001 is MTI in your old naming — we already took MTI, so skip DE001
            if de == "DE001":
                continue

            field_def = self.field_defs.get(de)
            if field_def is None:
                # If no definition -> we can't safely move index.
                # In enterprise we either: stop parsing or store remaining raw.
                # Here: stop parsing gracefully.
                self.fields["_UNPARSED_REST"] = body_ascii[idx:]
                return

            value, idx = self._read_field(body_ascii, idx, field_def)

            if de in self.tlv_fields:
                # TLV is expected as ASCII text at this layer (already decoded)
                self.fields[de] = self._parse_tlv(value)
            else:
                self.fields[de] = value

        # In case some bytes remain
        if idx < len(body_ascii):
            self.fields["_TAIL"] = body_ascii[idx:]

    # ============================================================
    # FIELD READERS
    # ============================================================

    def _read_field(self, body: str, idx: int, field_def: FieldDef) -> Tuple[str, int]:
        length = field_def.length

        if isinstance(length, int):
            end = idx + length
            if end > len(body):
                raise ValueError(f"Not enough data for fixed field len={length} at idx={idx}")
            return body[idx:end], end

        if length == "LLVAR":
            if idx + 2 > len(body):
                raise ValueError("Not enough data to read LLVAR length")
            ln = self._safe_int(body[idx : idx + 2], "LLVAR length")
            start = idx + 2
            end = start + ln
            if end > len(body):
                raise ValueError(f"Not enough data for LLVAR value len={ln}")
            return body[start:end], end

        if length == "LLLVAR":
            if idx + 3 > len(body):
                raise ValueError("Not enough data to read LLLVAR length")
            ln = self._safe_int(body[idx : idx + 3], "LLLVAR length")
            start = idx + 3
            end = start + ln
            if end > len(body):
                raise ValueError(f"Not enough data for LLLVAR value len={ln}")
            return body[start:end], end

        raise ValueError(f"Unsupported field length spec: {length!r}")

    # ============================================================
    # TLV
    # ============================================================

    def _parse_tlv(self, s: str) -> Dict[str, Any]:
        """
        Simple TLV parser:
          TAG (2 chars) + LEN (2 digits) + VALUE (LEN chars) repeated
        If nested TLV needed, you can extend later.
        """
        out: Dict[str, Any] = {}
        i = 0
        while i + 4 <= len(s):
            tag = s[i : i + 2]
            ln = self._safe_int(s[i + 2 : i + 4], "TLV length")
            start = i + 4
            end = start + ln
            if end > len(s):
                # keep raw remainder for debugging
                out["_TLV_REMAINDER"] = s[i:]
                return out
            out[tag] = s[start:end]
            i = end

        if i != len(s):
            out["_TLV_TAIL"] = s[i:]
        return out

    # ============================================================
    # HELPERS
    # ============================================================

    def _coerce_to_bytes(self, payload: bytes | str) -> bytes:
        if isinstance(payload, bytes):
            return payload
        if isinstance(payload, str):
            hex_str = payload.strip().replace(" ", "")
            return bytes.fromhex(hex_str)
        raise TypeError("payload must be bytes or hex-string")

    def _decode_ebcdic(self, b: bytes) -> str:
        try:
            return codecs.decode(b, self.encoding)
        except Exception as e:
            raise ValueError(f"Failed to decode EBCDIC using {self.encoding}: {e}") from e

    def _bytes_to_bits(self, b: bytes) -> str:
        return "".join(f"{byte:08b}" for byte in b)

    def _bits_to_active_fields(self, bits: str) -> List[str]:
        # bits[0] is "secondary bitmap present" flag (field 1)
        active: List[str] = []

        # ISO rule: bit position 1..n corresponds to field number.
        # We start from 2, because 1 is bitmap presence bit.
        for pos in range(2, len(bits) + 1):
            if bits[pos - 1] == "1":
                active.append(f"DE{pos:03d}")

        return active

    def _safe_int(self, txt: str, label: str) -> int:
        if not txt.isdigit():
            raise ValueError(f"{label} is not numeric: {txt!r}")
        return int(txt)


# parser = BnetParserMessage(payload_bytes, field_defs=FIELD_DEFS, tlv_fields=TLV_FIELDS)
# fields = parser.extract_fields()
# print(fields["MTI"], fields.get("DE039"))

#
# 1) Gdzie wysyłamy wiadomość (send)
# ✅ Client → Server
#
# Najczęściej:
#
# src/client/bnet_client.py
# metoda w stylu: send(...), send_and_receive(...), request(...)
#
# Tam zobaczysz coś takiego (logicznie):
#
# budowa payload (np. JSON / hex)
#
# self._transport.send(payload)
#
# ✅ Server → Client
#
# src/sut/bnet_server.py albo server/tcp_server.py (zależy którą wersję uruchamiasz)
# w handlerze klienta:
#
# conn.sendall(...) albo transport.send(...)
#
# 2) Gdzie odbieramy wiadomość (receive)
# ✅ Client odbiera odpowiedź z serwera
#
# src/client/bnet_client.py
# albo w tle w wątku:
#
# _receiver_loop() (to miałeś wcześniej w logach)
#
# I wewnątrz jest:
#
# msg = self._transport.receive(...)
#
# ✅ Server odbiera request od klienta
#
# server/tcp_server.py albo src/sut/bnet_server.py
# w pętli połączenia:
#
# data = conn.recv(...) albo transport.receive(...)
#
# 3) Najniższy poziom (konkretne sockety)
# Wysyłanie “fizycznie” po TCP
#
# src/transport/tcp_transport.py
# tam jest zwykle:
#
# self._sock.sendall(...)
#
# Odbieranie “fizycznie” po TCP
#
# src/transport/tcp_transport.py
# tam jest:
#
# self._sock.recv(...)
#
# A jeśli masz framing (2B length), to:
#
# src/transport/framing.py
# tam jest logika:
#
# write length + payload (send)
#
# read 2B length, potem read_exact(payload_len) (receive)
#
# Jak to szybko znaleźć u siebie (bez zgadywania)
#
# W PyCharm:
#
# Ctrl+Shift+F i szukasz:
#
# sendall(
#
# recv(
#
# .send(
#
# .receive(
#
# _receiver_loop
#
# To wskaże Ci dokładne pliki i linie.
#
# Jeśli wkleisz mi listę plików w src/transport/ (albo zawartość tcp_transport.py + framing.py), powiem Ci 1:1: tu wysyłasz, tu odbierasz, tu dokładamy prefix 2B w Twojej aktualnej paczce.