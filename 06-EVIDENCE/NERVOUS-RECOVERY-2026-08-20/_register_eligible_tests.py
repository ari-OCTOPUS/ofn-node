# -*- coding: utf-8 -*-
"""One-shot registrar for eligible Wave0 tests. Not imported by production."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_ops"))
from nervous_recovery.test_classify import classify_unregistered  # noqa: E402
from nervous_recovery.test_discovery import report  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
tests = ROOT / "_ops" / "tests"
run_all = tests / "run_all.py"

cl = classify_unregistered()
valid = cl["valid_to_register"]
print("counts", cl["counts"], "valid", len(valid), "unknown", cl["buckets"].get("unknown"))

pytest_native = []
for name in valid:
    src = (tests / name).read_text(encoding="utf-8", errors="replace")
    if ("import pytest" in src or "from pytest" in src) and "__main__" not in src:
        pytest_native.append(name)
print("pytest_native", len(pytest_native))

text = run_all.read_text(encoding="utf-8")
marker = '    "test_nervous_recovery.py",\n         ]'
if marker not in text:
    raise SystemExit("TESTS marker not found")
lines = ['    "test_nervous_recovery.py",',
         "    # 2026-08-20 OWNER WAVE0 — eligible unregistered tests (archived excluded)."]
for name in valid:
    lines.append(f'    "{name}",')
lines.append("         ]")
text = text.replace(marker, "\n".join(lines), 1)

pmark = '    "test_ratio_model.py",\n}'
if pytest_native and pmark in text:
    extra = "\n".join(f'    "{n}",' for n in pytest_native)
    text = text.replace(
        pmark,
        '    "test_ratio_model.py",\n    # 2026-08-20 OWNER WAVE0 pytest-native unregistered\n'
        + extra + "\n}",
        1,
    )

run_all.write_text(text, encoding="utf-8")
print(report())
