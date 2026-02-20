from behave import given


def _get_first_value(row, *keys):
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


@given("the card details")
def step_card_details(context):
    row = context.table[0]
    card_number = _get_first_value(row, "CARD_NUMBER", "CARD", "PAN")
    expiry = _get_first_value(row, "EXPIRY_DATE", "EXPIRY", "EXP")
    pvv = _get_first_value(row, "PVV", "Pvv", "PvV", "pvv")

    # If provided -> override default card in context
    current_card = getattr(context, "card", {}) or {}
    updated_card = dict(current_card)

    if card_number:
        updated_card["CARD_NUMBER"] = card_number
    if expiry:
        updated_card["EXPIRY_DATE"] = expiry
    if pvv:
        updated_card["PVV"] = pvv

    if updated_card != current_card:
        context.card = updated_card
    # else: keep default from environment.py
