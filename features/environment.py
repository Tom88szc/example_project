from __future__ import annotations

import logging
import os

from src.client.bnet_client import BnetClient, BnetClientConfig


def _setup_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )



def _load_config() -> BnetClientConfig:
    return BnetClientConfig(
        env=os.getenv("ENV", "SIT"),
        host=os.getenv("BN_HOST", "127.0.0.1"),
        port=int(os.getenv("BN_PORT", "5000")),
        connect_timeout=float(os.getenv("BN_CONNECT_TIMEOUT", "5")),
        read_timeout=float(os.getenv("BN_READ_TIMEOUT", "10")),
        retries=int(os.getenv("BN_RETRIES", "1")),
        retry_backoff=float(os.getenv("BN_RETRY_BACKOFF", "0.3")),
    )


def before_all(context):
    _setup_logging()
    log = logging.getLogger("behave.environment")
    log.info("Starting Behave run...")

    context.bnet_config = _load_config()
    context.bnet = BnetClient(config=context.bnet_config)

    context.bnet_logged_in = False
    context.last_request = None
    context.last_response = None
    context.iso_fields = {}


def before_scenario(context, scenario):
    log = logging.getLogger("behave.environment")
    log.info("Scenario: %s", scenario.name)

    if "no-login" in scenario.tags:
        log.info("Skipping login due to @no-login")
        return

    if getattr(context, "bnet_logged_in", False):
        log.info("Already logged in - skipping login.")
        return

    context.bnet.login()
    context.bnet_logged_in = True


def after_scenario(context, scenario):
    log = logging.getLogger("behave.environment")

    if "keep-session" in scenario.tags:
        log.info("Keeping session due to @keep-session")
        return

    if getattr(context, "bnet_logged_in", False):
        try:
            context.bnet.logout()
        finally:
            context.bnet_logged_in = False


def after_all(context):
    log = logging.getLogger("behave.environment")
    log.info("Finishing Behave run...")

    try:
        if getattr(context, "bnet_logged_in", False):
            context.bnet.logout()
    finally:
        context.bnet_logged_in = False
        context.bnet.close()
