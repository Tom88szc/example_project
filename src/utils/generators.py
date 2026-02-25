import random, string
from datetime import datetime

def gen_stan() -> str:
    return f"{random.randint(0, 999999):06d}"

def gen_rrn() -> str:
    return "".join(random.choice(string.digits) for _ in range(12))

def gen_trace_id(prefix: str = "TRACE") -> str:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    rnd = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"{prefix}-{ts}-{rnd}"


def gen_transmission_time() -> str:
    """ISO DE007 format: MMDDhhmmss (UTC)."""
    return datetime.utcnow().strftime("%m%d%H%M%S")


def gen_local_time() -> str:
    """ISO DE012 format: hhmmss (local time)."""
    return datetime.now().strftime("%H%M%S")


def gen_local_date() -> str:
    """ISO DE013/DE015/DE016 format: MMDD (local date)."""
    return datetime.now().strftime("%m%d")
