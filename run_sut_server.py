from __future__ import annotations

import logging
import os
import time

from src.sut.bnet_server import BnetServer, BnetServerConfig


def _setup_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


def main() -> int:
    _setup_logging()
    host = os.getenv("BN_HOST", "127.0.0.1")
    port = int(os.getenv("BN_PORT", "5000"))

    server = BnetServer(BnetServerConfig(host=host, port=port))
    server.start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
