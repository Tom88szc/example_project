# BNET ISS Automation – Testing Guide

## 1. What this project is
This repository contains a Behave (BDD) test client and a TCP SUT server implementation.

- **Behave** runs scenarios from `features/`
- **SUT Server** listens on TCP and responds to ISO-like messages (currently JSON payload) using **2-byte length prefix framing**
- **Transport/Framing rule:** the 2-byte length prefix exists **only** in `src/transport/framing.py`

---

## 2. How to run locally

### Option A (recommended): run server separately
Terminal 1 (SUT server):
```bash
python run_sut_server.py
```

Terminal 2 (tests):
```bash
python run_tests.py
```

### Option B: auto-start server from test runner
```bash
python run_tests.py
```

If the port is already in use, the runner continues and assumes the server is already running.

---

## 3. Where tests live
Scenarios are grouped by domain folders:
```
features/
  credential_on_file/
  ...
```

Add new features as new folders under `features/` to keep the step architecture clean and avoid step conflicts.

---

## 4. Writing scenarios (template)

```gherkin
Scenario: Authorization happy path
  Given the transaction with the following data
    | FIELD | VALUE        |
    | MTI   | 0100         |
    | DE003 | 000000       |
    | DE004 | 000000000100 |
    | DE011 | {STAN}       |
    | DE037 | {RRN}        |
  When the transaction is sent
  Then the response should be validated
    | FIELD | EXPECTED_VALUE |
    | MTI   | 0110           |
    | DE039 | 00             |
```

---

## 5. Placeholders (for users)

### Generators
| Placeholder | Meaning |
|---|---|
| `{STAN}` | generates a new STAN |
| `{RRN}` | generates a new RRN |
| `{TRACE_ID}` | generates trace id |
| `{CARD}` | card number from `the card details` step |
| `{EXPIRY_DATE}` | expiry date from `the card details` step |

### Copy from last authorization (after saving auth context)
After step:
```gherkin
Then save the authorization context
```
you can use:
| Placeholder | Meaning |
|---|---|
| `{DE037}` | copied from last auth (0110 preferred, fallback 0100) |
| `{DE038}` | copied from last auth (0110 preferred, fallback 0100) |
| `{DE004}` | copied from last auth (0110 preferred, fallback 0100) |
| `{DE090}` | auto-built Original Data Elements from the last auth request |

### Auto-building DE090
Current framework builder creates:
```
MTI(4) + STAN(6) + RRN(12)
```
This is a stable test-framework format and can be replaced with the exact host spec later.

---

## 6. Reversal (0400/0410) patterns

### Full reversal
```gherkin
Then save the authorization context

Given the transaction with the following data
  | FIELD | VALUE   |
  | MTI   | 0400    |
  | DE003 | 000000  |
  | DE004 | {DE004} |
  | DE011 | {STAN}  |
  | DE037 | {DE037} |
  | DE038 | {DE038} |
  | DE090 | {DE090} |
```

### Partial reversal (smaller amount)
Use a smaller `DE004`, keep `DE037/DE038/DE090` copied from auth.

### Negative reversal (no original found)
Use an unknown `DE037`, expect `DE039=25`.

---

## 7. Debugging
Run Behave without capturing output:
```bash
behave -f pretty --no-capture --no-logcapture
```

---

## 8. CI concept (stage per Scenario)
GitLab CI runs **each Scenario as a separate stage/job**.

- `tests.1` -> `stage: test:1` -> runs one Scenario at `features/<file>.feature:<line>`
- `tests.2` -> `stage: test:2` -> runs next Scenario
- etc.

To add more tests, just add more `Scenario:` blocks in `.feature` files.
The pipeline will automatically create additional stages/jobs.
