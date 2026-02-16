from behave import given, when
from src.utils.placeholder_resolver import resolve_placeholders

@given("the transaction with the following data")
def step_transaction_table(context):
    fields = {r["FIELD"]: r["VALUE"] for r in context.table}
    extra = {
        "CARD": context.card.get("CARD_NUMBER"),
        "EXPIRY_DATE": context.card.get("EXPIRY_DATE"),
        "EXPIRE_DATE": context.card.get("EXPIRY_DATE"),
    }
    context.iso_fields = resolve_placeholders(fields, extra)

@when("the transaction is sent")
def step_send(context):
    context.last_request = dict(context.iso_fields)
    context.last_response = context.bnet.send_and_wait(context.iso_fields, expect_mti="0110", timeout=10.0)

def _as_str(v) -> str:
    return "" if v is None else str(v)

def _build_de090_from_auth(context) -> str:
    """Auto-build DE090 (Original Data Elements) from last authorization request.
    NOTE: This is a simplified builder for test framework purposes.
    Format: MTI(4)+STAN(6)+RRN(12) -> 22 chars
    You can replace with full ISO8583 DE090 spec when available.
    """
    auth_req = getattr(context, "auth_request", None) or {}
    mti = _as_str(auth_req.get("MTI", "")).zfill(4)[:4]
    stan = _as_str(auth_req.get("DE011", "")).zfill(6)[:6]
    rrn = _as_str(auth_req.get("DE037", "")).zfill(12)[:12]
    return f"{mti}{stan}{rrn}"

def _resolve_placeholder(context, value: str) -> str:
    """Resolves placeholders like {STAN}, {RRN}, {DE038}, {DE090} using context."""
    if not isinstance(value, str):
        return _as_str(value)
    value = value.strip()
    if not (value.startswith("{") and value.endswith("}")):
        return value

    key = value[1:-1].strip()

    # generators
    if key == "STAN":
        return _as_str(_generate_stan())
    if key == "RRN":
        return _as_str(_generate_rrn())
    if key == "TRACE_ID":
        return _as_str(_generate_trace_id())
    if key == "CARD":
        return _as_str(getattr(context, "card_number", ""))
    if key == "EXPIRY_DATE":
        return _as_str(getattr(context, "expiry_date", ""))

    # auto-built DE090
    if key == "DE090" or key == "ORIGINAL_DATA":
        return _build_de090_from_auth(context)

    # copy-from-auth: {DE038} means pull DE038 from last auth response, fallback to request
    auth_resp = getattr(context, "auth_response", None) or {}
    auth_req = getattr(context, "auth_request", None) or {}
    if key in auth_resp:
        return _as_str(auth_resp.get(key))
    if key in auth_req:
        return _as_str(auth_req.get(key))

    raise ValueError(f"Cannot resolve placeholder {{{key}}}. Save auth context first if needed.")
