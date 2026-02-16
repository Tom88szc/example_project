from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

STEP_DECORATOR_RE = re.compile(
    r"@(?:given|when|then|step)\(\s*([\"'])(.+?)\1\s*\)",
    re.IGNORECASE,
)

def find_step_texts(steps_dir: Path) -> Dict[str, List[Tuple[str, int]]]:
    found: Dict[str, List[Tuple[str, int]]] = {}
    for py in steps_dir.glob("*.py"):
        text = py.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, line in enumerate(text, start=1):
            m = STEP_DECORATOR_RE.search(line)
            if not m:
                continue
            step_text = m.group(2).strip()
            found.setdefault(step_text, []).append((str(py), idx))
    return found

def main() -> int:
    steps_dir = Path("features/steps")
    if not steps_dir.exists():
        print("No features/steps directory found.")
        return 0

    found = find_step_texts(steps_dir)
    duplicates = {k:v for k,v in found.items() if len(v) > 1}

    if not duplicates:
        print("OK: No duplicate step texts found.")
        return 0

    print("ERROR: Duplicate step texts detected (AmbiguousStep risk):")
    for step_text, locations in sorted(duplicates.items()):
        print(f"\n- {step_text!r}")
        for path, line in locations:
            print(f"    {path}:{line}")
    print("\nFix: keep only ONE implementation per step text across features/steps.")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
