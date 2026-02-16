# Step architecture (Behave) – corporate, no conflicts

Behave loads **all** Python files under `features/steps/`.  
If two files define the same step text (e.g. `@given("the card details")`) you get `AmbiguousStep`.

## Rules (team standard)
1) **One step text = one implementation in the entire repo**  
2) Steps are grouped by **domain**, not by feature:
   - `common_steps.py` – login/background, generic session stuff
   - `card_steps.py` – card data tables
   - `transaction_steps.py` – ISO fields tables + sending
   - `validation_steps.py` – response validation
3) Feature-specific logic goes into **data tables / placeholders**, not new steps when possible.
4) If you must introduce a new step, make it **specific** (avoid generic phrases):
   - BAD: `Given the transaction with the following data`
   - BETTER: `Given the cof purchase transaction with the following data`
   (or keep the generic one but NEVER re-implement it elsewhere)
5) Use placeholders to keep steps reusable:
   - `{CARD}`, `{EXPIRY_DATE}`, `{STAN}`, `{RRN}`, `{TRACE_ID}`
6) Default data strategy:
   - Provide in `environment.py` (`context.card`), allow scenario override via `Given the card details`.
7) **Guardrail**: we run `tools/check_steps_unique.py` in CI and locally.  
   It scans decorators and fails with a readable list of duplicates.

## Folder structure
```
features/
  environment.py
  credential_on_file/
    credential_on_file.feature
  steps/
    __init__.py
    common_steps.py
    card_steps.py
    transaction_steps.py
    validation_steps.py
src/
  client/ bnet_client.py
  transport/ ...
  utils/ ...
  validators/ ...
tools/
  check_steps_unique.py
  generate_html_report.py
server/
  tcp_server.py
```

## Pattern to add new features safely
- Add only `.feature` files under `features/<domain>/...`
- Reuse existing step texts
- When new behavior is needed:
  - Prefer adding a new **placeholder** or new **table column**
  - Otherwise add a new step in the correct domain file, and run `python tools/check_steps_unique.py`
