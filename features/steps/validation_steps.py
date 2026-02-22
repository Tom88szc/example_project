from behave import then


def _print_message_block(title, message):
    print(f"{title}:")
    if not message:
        print("  - <empty>")
        return

    for field in sorted(message.keys()):
        print(f"  - {field}: {message[field]}")


@then("the response should be validated")
def step_validate(context):
    expected = {r["FIELD"]: r["EXPECTED_VALUE"] for r in context.table}
    actual = context.last_response or {}

    _print_message_block("Validation expected", expected)
    _print_message_block("Validation actual", actual)

    missing = [k for k in expected.keys() if k not in actual]
    if missing:
        print("Validation result: FAIL")
        raise AssertionError(f"Missing fields: {missing}. Actual={actual}")

    mismatches = []
    for k, exp in expected.items():
        act = actual.get(k)
        if str(act) != str(exp):
            mismatches.append(f"{k}: expected={exp!r} actual={act!r}")

    if mismatches:
        print("Validation result: FAIL")
        raise AssertionError("Mismatches:\n" + "\n".join(mismatches) + f"\nActual={actual}")

    print("Validation result: PASS")


@then("the response should contain fields")
def step_response_should_contain_fields(context):
    actual = context.last_response or {}
    required_fields = [row["FIELD"] for row in context.table]

    _print_message_block("Validation actual", actual)
    print("Validation expected required fields:")
    for field in required_fields:
        print(f"  - {field}")

    missing = [field for field in required_fields if field not in actual]
    if missing:
        print("Validation result: FAIL")
        raise AssertionError(f"Missing required fields: {missing}. Actual={actual}")

    print("Validation result: PASS")
