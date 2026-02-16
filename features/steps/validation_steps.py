from behave import then
import json
from src.validators.transaction_validator import assert_fields_exact, assert_fields_exist, assert_fields_partial

def _fail_with_debug(err: Exception, context, kind: str) -> None:
    req = getattr(context, "last_request", None)
    resp = getattr(context, "last_response", None)
    req_txt = json.dumps(req, ensure_ascii=False, indent=2) if req is not None else "None"
    resp_txt = json.dumps(resp, ensure_ascii=False, indent=2) if resp is not None else "None"
    message = (
        f"[{kind}] {err}\n\n"
        f"--- DEBUG ---\n"
        f"LAST_REQUEST:\n{req_txt}\n\n"
        f"LAST_RESPONSE:\n{resp_txt}\n"
    )
    raise AssertionError(message) from err

@then("the response should be validated")
def step_validate_exact(context):
    expected = {r["FIELD"]: r["EXPECTED_VALUE"] for r in context.table}
    try:
        assert_fields_exact(context.last_response, expected)
    except AssertionError as e:
        _fail_with_debug(e, context, "EXACT")

@then("the response should contain fields")
def step_validate_exists(context):
    required = [r["FIELD"] for r in context.table]
    try:
        assert_fields_exist(context.last_response, required)
    except AssertionError as e:
        _fail_with_debug(e, context, "EXISTS")

@then("the response should match")
def step_validate_partial(context):
    rules = [{"field": r["FIELD"], "match": r["MATCH"].strip().lower(), "expected": r.get("EXPECTED","")} for r in context.table]
    try:
        assert_fields_partial(context.last_response, rules)
    except AssertionError as e:
        _fail_with_debug(e, context, "PARTIAL")
