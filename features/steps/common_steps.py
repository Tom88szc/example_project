from behave import given


@given("bnet is logged into the process")
def step_bnet_logged_in(context):
    # Jeśli hook już zalogował, nie loguj ponownie
    if getattr(context, "bnet_logged_in", False):
        return
    context.bnet.login()
    context.bnet_logged_in = True
