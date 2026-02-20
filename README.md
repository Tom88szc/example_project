
# BNET ISO8583 Test Framework (Full Working Project)

This project is a **runnable baseline** that keeps the correct architecture:
- transport sends/receives raw payload bytes (no 2-byte length prefix)
- Protocol integration point is `src/protocol` (BnetBinMessage/BnetParserMessage)
- Behave tests in `features/`

Default protocol implementation uses JSON (so it runs). Replace parser/builder internals with your real ISO8583 stack.

## Run locally (Windows)

Terminal 1:
- `python run_sut_server.py`

Terminal 2:
- `python run_tests.py`

## Env vars
- `BN_HOST` (default 127.0.0.1)
- `BN_PORT` (default 5000)
- `BN_CONNECT_TIMEOUT` (default 5)
- `BN_READ_TIMEOUT` (default 10)
