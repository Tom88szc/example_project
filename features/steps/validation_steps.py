from behave import then
from src.validators.transaction_validator import assert_fields


@then("the response should be validated")
def step_validate_response(context):
    expected = {r["FIELD"]: r["EXPECTED_VALUE"] for r in context.table}
    assert_fields(context.last_response, expected)
