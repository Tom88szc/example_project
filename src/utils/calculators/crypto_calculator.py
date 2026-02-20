import hashlib
from typing import Dict


class CryptoCalculator:
    """Builds deterministic crypto-related values used in transaction placeholders."""

    def calculate_crypto_data(self, card_number: str, expiry_date: str) -> Dict[str, str]:
        pan = self._digits_only(card_number)
        expiry = self._normalize_expiry(expiry_date)

        cvc2 = self._generate_code("CVC2", pan, expiry, 3)
        emv = self._generate_code("EMV", pan, expiry, 3)
        msr = self._generate_code("MSR", pan, expiry, 3)
        pin = self._generate_code("PIN", pan, expiry, 4)

        service_code = self._generate_code("SERVICE", pan, expiry, 3)
        discretionary = f"{emv}{msr}{cvc2}{pin}"
        track_value = f"{pan}={expiry}{service_code}{discretionary}"

        return {
            "CVC2": cvc2,
            "EMV": emv,
            "MSR": msr,
            "PIN": pin,
            "TRACK_EMV": track_value,
            "TRACK_MSR": track_value,
        }

    @staticmethod
    def _digits_only(value: str) -> str:
        digits = "".join(ch for ch in str(value or "") if ch.isdigit())
        return digits or "0000000000000000"

    @staticmethod
    def _normalize_expiry(value: str) -> str:
        digits = "".join(ch for ch in str(value or "") if ch.isdigit())
        if len(digits) == 4:
            return digits
        return (digits + "0000")[:4]

    @staticmethod
    def _generate_code(name: str, pan: str, expiry: str, length: int) -> str:
        payload = f"{name}|{pan}|{expiry}".encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        number = int(digest[:12], 16) % (10 ** length)
        return str(number).zfill(length)
