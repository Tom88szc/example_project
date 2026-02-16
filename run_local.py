import os
import sys
from behave.__main__ import main as behave_main

# Ustawienia domyślne dla localhost
os.environ.setdefault("ENV", "SIT")
os.environ.setdefault("BN_HOST", "127.0.0.1")
os.environ.setdefault("BN_PORT", "5000")
os.environ.setdefault("LOG_LEVEL", "INFO")

# behave args: full output
sys.argv = [
  sys.argv[0],
  "-f", "pretty",
  "-o", "reports/pretty.txt",
  "-f", "json.pretty",
  "-o", "reports/json/results.json",
  "--no-capture",
  "--no-capture-stderr",
  "--no-logcapture",
]

raise SystemExit(behave_main())
