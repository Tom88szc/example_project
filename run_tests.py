import subprocess
import sys

if __name__ == "__main__":
    raise SystemExit(subprocess.call([
        sys.executable,
        "-m",
        "behave",
        "features",
        "-f",
        "request_response_formatter:RequestResponseFormatter",
        "--no-capture",
        "--no-logcapture",
    ]))
