from typing import Any, Dict

from src.utils.generators import (
    gen_local_date,
    gen_local_time,
    gen_rrn,
    gen_stan,
    gen_trace_id,
    gen_transmission_time,
)


def _resolve_value(value: Any, runtime: Dict[str, str]) -> Any:
    if isinstance(value, str):
        resolved = value
        for name, val in runtime.items():
            resolved = resolved.replace("{" + name + "}", str(val))
        return resolved

    if isinstance(value, dict):
        return {k: _resolve_value(v, runtime) for k, v in value.items()}

    if isinstance(value, list):
        return [_resolve_value(item, runtime) for item in value]

    return value


def resolve_placeholders(fields: Dict[str, Any], extra: Dict[str, str]) -> Dict[str, Any]:
    runtime = {
        "STAN": gen_stan(),
        "RRN": gen_rrn(),
        "TRACE_ID": gen_trace_id(),
        "TIME": gen_transmission_time(),
        "LOCAL_TIME": gen_local_time(),
        "DATE": gen_local_date(),
    }
    runtime.update(extra)
    return {k: _resolve_value(v, runtime) for k, v in fields.items()}
