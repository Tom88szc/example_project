import os
import argparse
import time

from src.sut.bnet_server import BnetServer, BnetServerConfig
import sys
from pathlib import Path
from behave.__main__ import main as behave_main

def main() -> int:
    os.environ.setdefault("ENV", "SIT")
    os.environ.setdefault("BN_HOST", "127.0.0.1")
    os.environ.setdefault("BN_PORT", "5000")
    os.environ.setdefault("LOG_LEVEL", "INFO")

    Path("reports/junit").mkdir(parents=True, exist_ok=True)
    Path("reports/json").mkdir(parents=True, exist_ok=True)
    Path("reports/html").mkdir(parents=True, exist_ok=True)

    # IMPORTANT (Behave 1.2.6):
    # - `-o` applies to the most recently added formatter
    # - so we bind output explicitly for each formatter to avoid empty JSON files.
    sys.argv = [
        sys.argv[0],
        "-f", "pretty",
        "-o", "reports/pretty.txt",
        "-f", "json.pretty",
        "-o", "reports/json/results.json",
        "--no-capture",
        "--no-capture-stderr",
        "--no-logcapture",
    ]
    exit_code = behave_main()

    # Generate HTML report even if tests failed
    # try:
    #     pass
    # except Exception as e:
    #     # Never break the test run due to reporting issues
    #     print(f"[REPORT] Failed to generate HTML report: {e}")
    #
    #     if server is not None:
    #     server.stop()
    # return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
# NOTE: CI can pass --feature to limit execution to a single feature folder.
