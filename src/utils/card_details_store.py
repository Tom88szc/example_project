import json
from pathlib import Path
from typing import Dict, Tuple

from src.utils.calculators import CryptoCalculator


_REPO_ROOT = Path(__file__).resolve().parents[2]
_CARDS_FILE = _REPO_ROOT / "cards" / "cards_detail.yaml"


def _normalize_card_number(card_number: str) -> str:
    digits = "".join(ch for ch in str(card_number or "") if ch.isdigit())
    return digits


def _read_store() -> Dict[str, Dict[str, str]]:
    if not _CARDS_FILE.exists():
        return {}

    raw = _CARDS_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        return {}

    payload = json.loads(raw)
    if not isinstance(payload, dict):
        return {}

    cards = payload.get("cards", {})
    return cards if isinstance(cards, dict) else {}


def _write_store(cards: Dict[str, Dict[str, str]]) -> None:
    _CARDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"cards": cards}
    _CARDS_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_or_create_card_details(card_number: str, expiry_date: str, pvv: str) -> Tuple[Dict[str, str], bool]:
    normalized_card = _normalize_card_number(card_number)
    cards = _read_store()

    existing = cards.get(normalized_card)
    if isinstance(existing, dict):
        card_data = {k: str(v) for k, v in existing.items()}
        card_data.setdefault("CARD_NUMBER", normalized_card)
        return card_data, False

    crypto = CryptoCalculator().calculate_crypto_data(
        card_number=normalized_card,
        expiry_date=expiry_date,
    )

    card_data = {
        "CARD_NUMBER": normalized_card,
        "EXPIRY_DATE": str(expiry_date or ""),
        "PVV": str(pvv or ""),
        **crypto,
    }

    cards[normalized_card] = card_data
    _write_store(cards)
    return card_data, True
