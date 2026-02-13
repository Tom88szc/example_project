from __future__ import annotations

import random
import string
from datetime import datetime


def gen_stan() -> str:
    return f"{random.randint(0, 999999):06d}"


def gen_rrn() -> str:
    # 12 cyfr/znaków - prosty generator do testów
    return "".join(random.choice(string.digits) for _ in range(12))


def gen_trace_id(prefix: str = "TRACE") -> str:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    rnd = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"{prefix}-{ts}-{rnd}"


def gen_time_hhmmss() -> str:
    return datetime.utcnow().strftime("%H%M%S")


def gen_date_mmdd() -> str:
    return datetime.utcnow().strftime("%m%d")
