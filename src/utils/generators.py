from __future__ import annotations
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
