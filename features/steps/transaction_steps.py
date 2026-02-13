from behave import when


@when("the transaction is sent")
def step_send_transaction(context):
    context.last_request = dict(context.iso_fields)
    context.last_response = context.bnet.send_transaction(context.iso_fields)
