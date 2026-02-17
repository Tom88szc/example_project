
from behave import then


@then("the response should be validated")
def step_validate(context):
    expected = {r["FIELD"]: r["EXPECTED_VALUE"] for r in context.table}
    actual = context.last_response or {}

    missing = [k for k in expected.keys() if k not in actual]
    if missing:
        raise AssertionError(f"Missing fields: {missing}. Actual={actual}")

    mismatches = []
    for k, exp in expected.items():
        act = actual.get(k)
        if str(act) != str(exp):
            mismatches.append(f"{k}: expected={exp!r} actual={act!r}")

    if mismatches:
        raise AssertionError("Mismatches:\n" + "\n".join(mismatches) + f"\nActual={actual}")


@then("the response should contain fields")
def step_response_should_contain_fields(context):
    actual = context.last_response or {}
    required_fields = [row["FIELD"] for row in context.table]

    missing = [field for field in required_fields if field not in actual]
    if missing:
        raise AssertionError(f"Missing required fields: {missing}. Actual={actual}")
