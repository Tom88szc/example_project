from behave import given

@given("the card details")
def step_card_details(context):
    row = context.table[0]
    card_number = (row.get("CARD_NUMBER") or row.get("CARD") or row.get("PAN") or "").strip()
    expiry = (row.get("EXPIRY_DATE") or row.get("EXPIRY") or row.get("EXP") or "").strip()

    # If provided -> override default card in context
    if card_number and expiry:
        context.card = {"CARD_NUMBER": card_number, "EXPIRY_DATE": expiry}
    # else: keep default from environment.py
