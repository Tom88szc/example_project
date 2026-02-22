from behave import given

from src.utils.card_details_store import get_or_create_card_details


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

    if not card_number:
        return

    card_data, created = get_or_create_card_details(
        card_number=card_number,
        expiry_date=expiry,
        pvv=pvv,
    )

    context.card = card_data
    status = "created" if created else "loaded"
    print(f"Card details {status} for PAN ending {card_data['CARD_NUMBER'][-4:]}")
