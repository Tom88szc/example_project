import re
from typing import Any, Dict, Iterable, List, Mapping


PARTIAL_MATCH_TYPES = {"equals", "contains", "regex"}


def _format_keys(payload: Mapping[str, Any]) -> str:
    return str(sorted(payload.keys()))


def _ensure_response(actual: Dict[str, Any]) -> None:
    if actual is None:
        raise AssertionError("Response is None")


def _missing_fields(payload: Mapping[str, Any], required_fields: Iterable[str]) -> List[str]:
    return [key for key in required_fields if key not in payload]


def assert_fields_exact(actual: Dict[str, Any], expected: Dict[str, Any]) -> None:
    _ensure_response(actual)
    missing = _missing_fields(actual, expected)
    if missing:
        raise AssertionError(f"Missing fields: {missing}. Actual keys: {_format_keys(actual)}")

    mismatches = []
    for key, exp in expected.items():
        act = actual.get(key)
        if str(act) != str(exp):
            mismatches.append((key, exp, act))

    if mismatches:
        lines = ["Value mismatches:"]
        for key, expected_value, actual_value in mismatches:
            lines.append(f"- {key}: expected={expected_value!r}, actual={actual_value!r}")
        raise AssertionError("\n".join(lines))


def assert_fields_exist(actual: Dict[str, Any], required_fields: List[str]) -> None:
    _ensure_response(actual)
    missing = _missing_fields(actual, required_fields)
    if missing:
        raise AssertionError(f"Missing required fields: {missing}. Actual keys: {_format_keys(actual)}")


def _validate_partial_rule_shape(rule: Mapping[str, str], index: int) -> List[str]:
    errors = []
    if "field" not in rule:
        errors.append(f"Rule #{index}: missing required key 'field'")
    if "match" not in rule:
        errors.append(f"Rule #{index}: missing required key 'match'")
        return errors

    match = str(rule.get("match"))
    if match not in PARTIAL_MATCH_TYPES:
        errors.append(f"Rule #{index}: unknown MATCH={match!r} (use equals|contains|regex)")
    if match in PARTIAL_MATCH_TYPES and "expected" not in rule:
        errors.append(f"Rule #{index}: missing required key 'expected' for MATCH={match!r}")
    return errors


def assert_fields_partial(actual: Dict[str, Any], rules: List[Dict[str, str]]) -> None:
    _ensure_response(actual)
    errors = []

    for index, rule in enumerate(rules, start=1):
        errors.extend(_validate_partial_rule_shape(rule, index))
        field = rule.get("field")
        match = rule.get("match")
        expected = rule.get("expected", "")

        if not field or match not in PARTIAL_MATCH_TYPES:
            continue

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

    if errors:
        raise AssertionError("\n".join(errors))
