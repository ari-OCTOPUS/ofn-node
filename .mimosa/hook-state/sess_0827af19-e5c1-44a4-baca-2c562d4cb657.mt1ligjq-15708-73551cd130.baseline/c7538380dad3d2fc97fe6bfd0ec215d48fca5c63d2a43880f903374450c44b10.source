#!/usr/bin/env python3
"""run_ci.py — Wave 6 · C. CI & Drift Guard Agent

Runs verify_schema.py and verify_ui_contract.py.
Exits non-zero if either fails.
Can be added to refresh-live-data.bat as optional last step.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(script_name: str) -> tuple[bool, str]:
    path = HERE / script_name
    if not path.exists():
        return False, f"MISSING: {path}"
    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        ok = result.returncode == 0
        output = result.stdout + (f"\nSTDERR:\n{result.stderr}" if result.stderr else "")
        return ok, output
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT after 120s"
    except Exception as e:
        return False, f"EXCEPTION: {e}"


def main() -> int:
    print("=" * 60)
    print("OCTOPUS Wave 6 — CI / Drift Gate")
    print("=" * 60)

    scripts = [
        ("verify_schema.py", "Schema Contract Verification"),
        ("verify_ui_contract.py", "UI Contract Verification"),
    ]

    all_ok = True
    for script, label in scripts:
        print(f"\n--- {label} ({script}) ---")
        ok, output = run(script)
        print(output)
        if not ok:
            all_ok = False
            print(f"[FAIL] {label}")
        else:
            print(f"[PASS] {label}")

    print("\n" + "=" * 60)
    if all_ok:
        print("CI GATE: PASS")
        return 0
    else:
        print("CI GATE: FAIL — see errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
