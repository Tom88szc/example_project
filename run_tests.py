import os
import subprocess
import sys


def main() -> int:
    """
    Runs behave tests.
    Assumes SUT server is already running on BN_MOCK_HOST / BN_MOCK_PORT.
    """

    behave_cmd = [
        sys.executable,
        "-m",
        "behave",
        "features",
        "-f",
        "pretty",
        "--no-capture",
        "--no-logcapture",
    ]

    try:
        return subprocess.call(behave_cmd)
    except Exception as e:
        print(f"Error while running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
