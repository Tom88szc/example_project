import subprocess
import sys


if __name__ == "__main__":
    rc = subprocess.call([
        sys.executable,
        "-m",
        "behave",
        "features",
        "-f",
        "request_response_formatter:RequestResponseFormatter",
        "--no-capture",
        "--no-logcapture",
    ])

    raise SystemExit(rc)
