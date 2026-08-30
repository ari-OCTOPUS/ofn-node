#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_audit.py — رده‌بندِ green-lie (تست‌های دروغ‌سبز).

الهامِ ریاضی: در 1-WL، دو ورودیِ متفاوت به یک خروجی همگرا می‌شوند. در run_all.py،
یک تستِ واقعیِ سبز و یک اسکریپتِ no-op (بدونِ __main__، صفر assert) هر دو exit 0
می‌دهند — قابلِ تشخیص نیست. این رده‌بند هر فایلِ تست را پیش از اجرا طبقه‌بندی
می‌کند: real_unittest / real_pytest / no_op_or_bare / ambiguous.

قرارداد (MEGAPROMPT-GREEN-LIE-CLASSIFIER-2026-08-02):
  · read-only روی فایل‌های تست — هرگز تغیری نمی‌دهد.
  · هرگز green lie نساز: اگه مطمئن نیست، ambiguous بزن، نه real.
  · additive — run_all.py بازنویسی نمی‌شود؛ فقط گزارش جانبی.
  · flag-off (OCTOPUS_WIRE_TEST_AUDIT)، halt مقدم.

اعترافِ صادقانه: repo خودش تا حدِ زیادی این را حل کرده (PYTEST_TESTS، اجرای تجربی).
این ابزارِ ممیزیِ دوره‌ای است، نه یک نیازِ فوری.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_WIRE_TEST_AUDIT"


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def _read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""


def classify_test_file(path: "Path | str") -> dict:
    """رده‌بندیِ استاتیکِ یک فایلِ تست. همیشه dict، هرگز استثنا.

    سیگنال‌ها:
      - has_main: اگر `if __name__ == "__main__"` دارد
      - has_test_funcs: اگر توابعِ `t_*` یا `test_*` دارد
      - has_pytest_fixture: اگر `pytest.fixture` دارد
      - has_harness: اگر `import harness` دارد (الگوی استانداردِ repo)
      - has_asserts: اگر کلمهٔ `assert` دارد
    خروجی kind ∈ {real_unittest, real_pytest, no_op_or_bare, ambiguous}.
    """
    p = Path(path)
    signals: dict[str, Any] = {"path": str(p), "exists": p.exists()}
    if not p.exists() or p.suffix != ".py":
        signals["kind"] = "not_a_test"
        return signals
    text = _read_text_safe(p)
    has_main = bool(re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', text))
    has_test_funcs = bool(re.search(r'^\s*def\s+(t_|test_)\w+', text, re.MULTILINE))
    has_pytest_fixture = "pytest.fixture" in text or "@pytest" in text
    has_harness = "import harness" in text or "harness.setup" in text
    has_asserts = "assert " in text or "assert(" in text
    n_test_funcs = len(re.findall(r'^\s*def\s+(t_|test_)\w+', text, re.MULTILINE))

    signals.update({"has_main": has_main, "has_test_funcs": has_test_funcs,
                    "n_test_funcs": n_test_funcs, "has_pytest_fixture": has_pytest_fixture,
                    "has_harness": has_harness, "has_asserts": has_asserts,
                    "lines": text.count("\n") + 1})

    # رده‌بندی (fail-safe: اگه مطمئن نیست، ambiguous)
    if has_pytest_fixture and not has_main:
        kind = "real_pytest"
    elif has_main and has_test_funcs and n_test_funcs >= 1 and (has_asserts or has_harness):
        kind = "real_unittest"
    elif (not has_main) and (not has_test_funcs) and (not has_pytest_fixture):
        # no __main__, no test funcs, no pytest = احتمالاً no-op یا bare
        kind = "no_op_or_bare"
    elif (not has_main) and has_test_funcs and has_asserts:
        # test funcs + asserts ولی no __main__ = pytest-style یا bare (ambig)
        kind = "ambiguous_no_main"
    else:
        kind = "ambiguous"
    signals["kind"] = kind
    # green-lie risk: فایل‌هایی که می‌توانند exit 0 با صفر assert بدهند
    signals["green_lie_risk"] = kind in ("no_op_or_bare", "ambiguous_no_main")
    return signals


def audit_directory(tests_dir: "Path | str | None" = None) -> dict:
    """رده‌بندیِ همهٔ فایل‌های تست در tests_dir. خروجی = گزارشِ observable.

    خروجی: {scanned, counts: {kind: n}, green_lie_suspects: [...], files: [...]}.
    """
    d = Path(tests_dir) if tests_dir is not None else _HERE
    files = sorted(p for p in d.glob("test_*.py") if p.is_file())
    results = [classify_test_file(p) for p in files]
    counts: dict[str, int] = {}
    suspects = []
    for r in results:
        k = r.get("kind", "?")
        counts[k] = counts.get(k, 0) + 1
        if r.get("green_lie_risk"):
            suspects.append({"path": r["path"], "kind": k,
                             "n_test_funcs": r.get("n_test_funcs", 0),
                             "has_main": r.get("has_main", False)})
    return {"ok": True, "scanned": len(results), "counts": counts,
            "green_lie_suspects": suspects, "tests_dir": str(d),
            "enabled": enabled(), "flag": FLAG,
            "note": "repo run_all.py already handles most via PYTEST_TESTS + empirical run"}


if __name__ == "__main__":
    print(json.dumps(audit_directory(), ensure_ascii=False, indent=2))
