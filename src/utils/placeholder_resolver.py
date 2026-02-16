from __future__ import annotations
from typing import Dict
from src.utils.generators import gen_rrn, gen_stan, gen_trace_id

def resolve_placeholders(fields: Dict[str, str], extra: Dict[str, str]) -> Dict[str, str]:
    runtime = {"STAN": gen_stan(), "RRN": gen_rrn(), "TRACE_ID": gen_trace_id()}
    runtime.update(extra)
    out = {}
    for k, v in fields.items():
        s = v
        for name, val in runtime.items():
            s = s.replace("{" + name + "}", str(val))
        out[k] = s
    return out
