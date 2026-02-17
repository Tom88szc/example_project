import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from src.client.bnet_client import BnetClient, BnetClientConfig


def _setup_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


def _load_config() -> BnetClientConfig:
    return BnetClientConfig(
        env=os.getenv("ENV", "SIT"),
        host=os.getenv("BN_HOST", "127.0.0.1"),
        port=int(os.getenv("BN_PORT", "5000")),
        connect_timeout=float(os.getenv("BN_CONNECT_TIMEOUT", "5")),
        read_timeout=float(os.getenv("BN_READ_TIMEOUT", "10")),
        default_card_number=os.getenv("BN_DEFAULT_CARD", "5575061111100075"),
        default_expiry_date=os.getenv("BN_DEFAULT_EXPIRY", "2907"),
    )


def _slug(s: str) -> str:
    import re
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "scenario"


def before_all(context):
    _setup_logging()
    logging.getLogger("behave.environment").info("Starting Behave run...")
    Path("reports/tcp").mkdir(parents=True, exist_ok=True)

    context.bnet_config = _load_config()
    context.bnet = BnetClient(config=context.bnet_config)
    context.bnet.connect_and_login()

    # Default card (used if scenario doesn't provide card details)
    context.card = {
        "CARD_NUMBER": context.bnet_config.default_card_number,
        "EXPIRY_DATE": context.bnet_config.default_expiry_date,
    }

    context.iso_fields = {}
    context.last_request = None
    context.last_response = None


def before_scenario(context, scenario):
    logging.getLogger("behave.environment").info("Scenario: %s", scenario.name)
    context._tcp_lines = []
    slug = _slug(f"{scenario.feature.name}-{scenario.name}")
    context._tcp_log_name = f"{slug}.log"

    def sink(direction: str, msg: Dict[str, Any]) -> None:
        ts = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3] + "Z"
        context._tcp_lines.append(f"{ts} {direction} {json.dumps(msg, ensure_ascii=False)}")

    context.bnet.set_event_sink(sink)


def after_scenario(context, scenario):
    context.bnet.set_event_sink(None)
    (Path("reports/tcp") / context._tcp_log_name).write_text("\n".join(context._tcp_lines) + "\n", encoding="utf-8")


def after_all(context):
    logging.getLogger("behave.environment").info("Finishing Behave run...")
    try:
        context.bnet.logout_and_close()
    except Exception:
        pass
