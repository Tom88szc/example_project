
from behave import given, when

from src.utils.protocol.bnet_bin_message import BnetBinMessage


@given("the transaction with the following data")
def step_tx_data(context):
    msg = {}
    for r in context.table:
        msg[r["FIELD"]] = r["VALUE"]
    context.last_request = msg


@when("the transaction is sent")
def step_send(context):
    request_for_log = dict(context.last_request or {})

    if "MTI" in request_for_log and "DE001" not in request_for_log:
        request_for_log["DE001"] = request_for_log.pop("MTI")

    try:
        tx_builder = BnetBinMessage(request_for_log)
        print(f"BNET TX HEX (no prefix): {tx_builder.create_message()}")
        print(f"BNET TX HEX (with 2B prefix): {tx_builder.create_message_with_prefix()}")
    except Exception as exc:
        print(f"BNET TX HEX unavailable: {exc}")

    context.last_response = context.bnet.send(context.last_request)
