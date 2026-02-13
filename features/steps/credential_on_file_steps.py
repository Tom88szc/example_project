from behave import given
from src.utils.placeholder_resolver import resolve_placeholders


@given("the card details")
def step_card_details(context):
    # tabela: CARD_NUMBER | EXPIRY_DATE
    row = context.table[0]
    context.card_number = row["CARD_NUMBER"]
    context.expiry_date = row["EXPIRY_DATE"]


@given("the transaction with the following data")
def step_transaction_table(context):
    # tabela: FIELD | VALUE
    fields = {}
    for r in context.table:
        fields[r["FIELD"]] = r["VALUE"]

    # podstawienia z feature: {CARD}, {EXPIRE_DATE}, {TIME}, {DATE}, {STAN} itd.
    ctx = {
        "CARD": getattr(context, "card_number", ""),
        "EXPIRE_DATE": getattr(context, "expiry_date", ""),
    }
    fields = resolve_placeholders(fields, ctx)

    context.iso_fields = fields
