
import logging
import os

from src.client.bnet_client import BnetClient, BnetClientConfig


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
