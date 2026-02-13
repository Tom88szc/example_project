from __future__ import annotations

from typing import Dict

from src.utils.generators import gen_date_mmdd, gen_rrn, gen_stan, gen_time_hhmmss, gen_trace_id


def resolve_placeholders(fields: Dict[str, str], extra_context: Dict[str, str]) -> Dict[str, str]:
    """
    Zamienia placeholdery typu:
      {CARD}, {EXPIRE_DATE}, {TIME}, {DATE}, {STAN}, {RRN}, {TRACE_ID}
    """
    resolved = {}
    runtime = {
        "TIME": gen_time_hhmmss(),
        "LOCAL_TIME": gen_time_hhmmss(),
        "DATE": gen_date_mmdd(),
        "STAN": gen_stan(),
        "RRN": gen_rrn(),
        "TRACE_ID": gen_trace_id(),
    }
    runtime.update(extra_context)

    for k, v in fields.items():
        out = v
        for name, value in runtime.items():
            out = out.replace("{" + name + "}", str(value))
        resolved[k] = out

    return resolved
