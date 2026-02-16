from behave import then

@then("save the authorization context")
def step_save_auth_context(context):
    # Save last request/response as authorization reference for later dependent messages (e.g., reversal 0400)
    context.auth_request = getattr(context, "last_request", None)
    context.auth_response = getattr(context, "last_response", None)
