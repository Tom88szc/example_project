from __future__ import annotations
import re
from typing import Any, Dict, List

def _ensure_response(actual: Dict[str, Any]) -> None:
    if actual is None:
        raise AssertionError("Response is None")

def assert_fields_exact(actual: Dict[str, Any], expected: Dict[str, Any]) -> None:
    _ensure_response(actual)
    missing = [k for k in expected if k not in actual]
    if missing:
        raise AssertionError(f"Missing fields: {missing}. Actual keys: {list(actual.keys())}")
    mismatches = []
    for key, exp in expected.items():
        act = actual.get(key)
        if str(act) != str(exp):
            mismatches.append((key, exp, act))
    if mismatches:
        lines = ["Value mismatches:"]
        for k, e, a in mismatches:
            lines.append(f"- {k}: expected={e!r}, actual={a!r}")
        raise AssertionError("\n".join(lines))

def assert_fields_exist(actual: Dict[str, Any], required_fields: List[str]) -> None:
    _ensure_response(actual)
    missing = [k for k in required_fields if k not in actual]
    if missing:
        raise AssertionError(f"Missing required fields: {missing}. Actual keys: {list(actual.keys())}")

def assert_fields_partial(actual: Dict[str, Any], rules: List[Dict[str, str]]) -> None:
    _ensure_response(actual)
    errors = []
    for rule in rules:
        field = rule["field"]
        match = rule["match"]
        expected = rule.get("expected", "")
        if field not in actual:
            errors.append(f"Missing field: {field}")
            continue
        value_str = str(actual.get(field))
        if match == "equals":
            if value_str != str(expected):
                errors.append(f"{field}: equals expected={expected!r} actual={value_str!r}")
        elif match == "contains":
            if str(expected) not in value_str:
                errors.append(f"{field}: contains expected={expected!r} actual={value_str!r}")
        elif match == "regex":
            if re.search(str(expected), value_str) is None:
                errors.append(f"{field}: regex pattern={expected!r} actual={value_str!r}")
        else:
            errors.append(f"{field}: unknown MATCH={match!r} (use equals|contains|regex)")
    if errors:
        raise AssertionError("\n".join(errors))
