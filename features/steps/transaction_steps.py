
from behave import given, when


@given("the transaction with the following data")
def step_tx_data(context):
    msg = {}
    for r in context.table:
        msg[r["FIELD"]] = r["VALUE"]
    context.last_request = msg


@when("the transaction is sent")
def step_send(context):
    context.last_response = context.bnet.send(context.last_request)
