#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""c6_probes.py — C2 · رجیستریِ سنجه‌های read-only برای تولیدکنندهٔ صادقِ فرضیهٔ C6.

قیدِ صداقت: هر سنجه فقط count می‌زند؛ هیچ نتیجهٔ صنعتی/بهبودِ ساختگی تولید نمی‌کند.
خروجیِ نامشخص/کرش → count=-1 (هیچ فرضیه‌ای ساخته نشود). صفر شبکه/پول/اثرِ بیرونی؛
stdlib-only؛ fail-soft؛ هر wrapper خواندنی که را override می‌کند در finally برمی‌گردد.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

OPS = Path(__file__).resolve().parent


def _sys(p: Path) -> None:
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


_sys(OPS / "budget")
import opslib  # noqa: E402


def _load_self_audit_module():
    for p in (OPS / "cortex",):
        _sys(p)
    return importlib.import_module("self_audit")


def _probe_self_audit_redundant_reads() -> dict:
    mod = _load_self_audit_module()
    orig_read, orig_grep = mod._read, mod._grep
    calls = {"_read": 0, "_grep": 0}
    try:
        def counting_read(p):
            calls["_read"] += 1
            return orig_read(p)

        def counting_grep(p, needle):
            calls["_grep"] += 1
            return orig_grep(p, needle)

        mod._read = counting_read
        mod._grep = counting_grep
        mod.main()
        return {"count": calls["_read"], "unit": "read",
                "detail": f"self_audit.main() full-matrix reads={calls['_read']} grep={calls['_grep']}"}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "read",
                "detail": f"probe-failed:{type(e).__name__}"}
    finally:
        mod._read, mod._grep = orig_read, orig_grep


def _probe_rfc_duplicate_surplus() -> dict:
    try:
        rd = opslib.STATE_DIR / "c6" / "rfcs"
        if not rd.exists():
            return {"count": -1, "unit": "rfc",
                    "detail": "rfc dir غایب — قضاوت غیرممکن (هیچ فرضیه‌ای)"}
        rows = []
        for p in sorted(rd.glob("c6-*.json")):
            try:
                d = json.loads(p.read_text("utf-8"))
                hyp = str(d.get("hypothesis", "")).strip().lower()
                if hyp:
                    rows.append((p.name, hyp))
            except (OSError, ValueError):
                continue
        if not rows:
            return {"count": -1, "unit": "rfc",
                    "detail": "هیچ c6-*.json با hypothesis غیرخالی — قضاوت غیرممکن"}
        from collections import Counter
        counts = Counter(h for _, h in rows)
        max_n = max(counts.values()) if counts else 0
        surplus = sum(n - 1 for n in counts.values())
        return {"count": max_n, "unit": "rfc",
                "detail": (f"max_duplicate_hypothesis={max_n} surplus_rfc={surplus} "
                           f"files={len(rows)}")}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "rfc",
                "detail": f"probe-failed:{type(e).__name__}"}


PROBES = {
    "self_audit_redundant_reads": {
        "measure": _probe_self_audit_redundant_reads,
        "subject": "reduce per-sweep redundant reads in self_audit.main()",
        "question": "آیا هر sweep کاملِ self_audit واقعاً خواندنی‌های زیادی می‌کند؟",
        "floor": 10,
    },
    "rfc_duplicate_surplus": {
        "measure": _probe_rfc_duplicate_surplus,
        "subject": "deduplicate identical RFC hypotheses in state/c6/rfcs",
        "question": "آیا فرضیه‌های یکسانِ C6 به‌طور تکراری RFC می‌شوند؟",
        "floor": 1,
    },
}
