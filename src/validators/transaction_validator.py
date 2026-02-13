from __future__ import annotations

from typing import Dict


def assert_fields(actual: Dict[str, str], expected: Dict[str, str]) -> None:
    missing = [k for k in expected.keys() if k not in actual]
    if missing:
        raise AssertionError(f"Missing fields in response: {missing}. Actual keys: {list(actual.keys())}")

    diffs = []
    for k, v in expected.items():
        if str(actual.get(k)) != str(v):
            diffs.append((k, v, actual.get(k)))

    if diffs:
        lines = ["Response validation failed:"]
        for k, exp, act in diffs:
            lines.append(f" - {k}: expected={exp!r} actual={act!r}")
        lines.append(f"Full actual response: {actual}")
        raise AssertionError("\n".join(lines))
