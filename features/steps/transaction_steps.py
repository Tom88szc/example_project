
from behave import given, when

from src.utils.protocol.bnet_bin_message import BnetBinMessage
from src.utils.placeholder_resolver import resolve_placeholders
from src.utils.calculators import CryptoCalculator


def _build_placeholder_context(context):
    card = getattr(context, "card", {}) or {}
    auth_request = getattr(context, "auth_request", {}) or {}
    auth_response = getattr(context, "auth_response", {}) or {}

    extra = {
        "CARD": card.get("CARD_NUMBER", ""),
        "EXPIRY_DATE": card.get("EXPIRY_DATE", ""),
        "PVV": card.get("PVV", ""),
        "PvV": card.get("PVV", ""),
    }

    crypto_data = CryptoCalculator().calculate_crypto_data(
        card_number=extra.get("CARD", ""),
        expiry_date=extra.get("EXPIRY_DATE", ""),
    )
    extra.update(crypto_data)
    extra.update({f"CRYPTO_{name}": value for name, value in crypto_data.items()})

    # Prefer values from response, fallback to saved authorization request.
    for field in ("DE004", "DE037", "DE038"):
        if field in auth_response:
            extra[field] = auth_response[field]
        elif field in auth_request:
            extra[field] = auth_request[field]

    # Framework format: MTI(4) + STAN(6) + RRN(12)
    if "DE090" not in extra and all(name in extra for name in ("DE037",)):
        mti = auth_request.get("DE001") or auth_request.get("MTI") or "0100"
        stan = auth_request.get("DE011", "000000")
        rrn = extra.get("DE037", "000000000000")
        extra["DE090"] = f"{mti}{stan}{rrn}"

    return extra


def _print_placeholder_changes(original_request, resolved_request):
    print("Placeholder resolution:")
    changed = False

    for field in original_request:
        before = str(original_request.get(field, ""))
        after = str(resolved_request.get(field, ""))
        if before != after:
            changed = True
            print(f"  - {field}: {before} -> {after}")

    if not changed:
        print("  - no placeholder changes")


@given("the transaction with the following data")
def step_tx_data(context):
    msg = {}
    for r in context.table:
        msg[r["FIELD"]] = r["VALUE"]
    context.last_request = msg


@when("the transaction is sent")
def step_send(context):
    request_raw = dict(context.last_request or {})
    request_for_send = resolve_placeholders(request_raw, _build_placeholder_context(context))
    _print_placeholder_changes(request_raw, request_for_send)

    if "MTI" in request_for_send and "DE001" not in request_for_send:
        mti_value = request_for_send["MTI"]
        request_for_send["DE001"] = request_for_send.pop("MTI")
        print(f"  - MTI normalized to DE001: {mti_value}")

    request_for_log = dict(request_for_send)

    try:
        tx_builder = BnetBinMessage(request_for_log)
        print(f"BNET TX HEX (no prefix): {tx_builder.create_message()}")
        print(f"BNET TX HEX (with 2B prefix): {tx_builder.create_message_with_prefix()}")
    except Exception as exc:
        print(f"BNET TX HEX unavailable: {exc}")

    context.last_request = request_for_send
    context.last_response = context.bnet.send(request_for_send)
