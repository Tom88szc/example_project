import logging
import os

from src.client.bnet_client import BnetClient, BnetClientConfig


def _print_message_block(title, message):
    print(f"{title}:")
    if not message:
        print("  - <empty>")
        return

    for field in sorted(message.keys()):
        print(f"  - {field}: {message[field]}")


def before_all(context):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    context.bnet_config = BnetClientConfig(
        host=os.getenv("BN_HOST", "127.0.0.1"),
        port=int(os.getenv("BN_PORT", "5000")),
        connect_timeout=float(os.getenv("BN_CONNECT_TIMEOUT", "5")),
        read_timeout=float(os.getenv("BN_READ_TIMEOUT", "10")),
    )
    context.bnet = BnetClient(config=context.bnet_config)
    context.last_request = None
    context.last_response = None


def after_all(context):
    # Client opens/closes per request in this simple sample.
    pass


def before_scenario(context, scenario):
    context.current_scenario = getattr(scenario, "name", "")
    print(f"Scenario: {context.current_scenario}")


def after_step(context, step):
    if step.status != "failed":
        return

    print("Failure context dump:")
    _print_message_block("Last request", getattr(context, "last_request", {}) or {})
    _print_message_block("Last response", getattr(context, "last_response", {}) or {})

    exchange = getattr(getattr(context, "bnet", None), "last_exchange", {}) or {}
    sent = exchange.get("sent", {})
    received = exchange.get("received", {})

    print("Wire data (sent):")
    print(f"  - unparsed_hex: {sent.get('unparsed_hex', '<missing>')}")
    _print_message_block("  - parsed", sent.get("parsed", {}))

    print("Wire data (received):")
    print(f"  - unparsed_hex: {received.get('unparsed_hex', '<missing>')}")
    if received.get("error"):
        print(f"  - error: {received.get('error')}")
    if received.get("target"):
        print(f"  - target: {received.get('target')}")
    _print_message_block("  - parsed", received.get("parsed", {}))
