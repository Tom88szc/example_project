import atexit
import os
import socket
import subprocess
import sys
import time
from typing import Optional


def _can_connect(host: str, port: int, timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _start_sut_if_needed(host: str, port: int) -> Optional[subprocess.Popen]:
    if _can_connect(host, port):
        return None

    sut_cmd = [sys.executable, "run_sut_server.py"]
    proc = subprocess.Popen(
        sut_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if _can_connect(host, port):
            return proc
        if proc.poll() is not None:
            break
        time.sleep(0.1)

    try:
        proc.terminate()
    except Exception:
        pass
    return None


if __name__ == "__main__":
    host = os.getenv("BN_HOST", "127.0.0.1")
    port = int(os.getenv("BN_PORT", "5000"))

    sut_proc = _start_sut_if_needed(host, port)
    if sut_proc is not None:
        atexit.register(lambda: sut_proc.poll() is None and sut_proc.terminate())

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

    if sut_proc is not None and sut_proc.poll() is None:
        sut_proc.terminate()
        try:
            sut_proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            sut_proc.kill()

    raise SystemExit(rc)
