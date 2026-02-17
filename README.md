# bnet_iss_enterprise_steps_project

Behave + TCP/IP ISO8583 mock (JSON line framing) + auto 0800->0810 + walidacje + HTML report (folder+assets, drill-down) + GitLab CI artifacts.

## Key: step architecture (no conflicts)
Read: `docs/STEP_ARCHITECTURE.md`  
We also run a guard in CI/local: `python tools/check_steps_unique.py` to fail fast if any step text is duplicated.

## Run locally
Terminal 1:
```bash
python -m server.tcp_server
```

Terminal 2:
```bash
python run_tests.py
```

Open report:
- `reports/html/index.html`

## Length prefix rule (2B)
This project enforces: **2-byte length prefix exists ONLY in transport/framing**.
- `BnetBinMessage` builds **payload bytes only** (no prefix).
- `BnetParserMessage` parses **payload bytes only** (no prefix).
- If you have an external builder that returns `HEX=[2B prefix][payload]`, use `ExternalBnetBinMessageAdapter` which strips the first 4 hex chars.

## Server mode (SUT)
This project can run with **SUT acting as the server** (TCP, 2B length + JSON payload).

### Option A: Run server separately
Terminal 1:
```bash
python run_sut_server.py
```

Terminal 2:
```bash
python run_tests.py
```

### Option B: Auto-start server from run_tests.py
Just run:
```bash
python run_tests.py
```
`run_tests.py` will try to start the server on `BN_HOST/BN_PORT`. If the port is already in use, it will continue and assume the server is already running.


📘 See: `TESTING_GUIDE.md` for writing tests, placeholders and running instructions.


## Python 3.12 notes
This project is refactored for Python 3.12 and does not use `from __future__ import annotations`.
