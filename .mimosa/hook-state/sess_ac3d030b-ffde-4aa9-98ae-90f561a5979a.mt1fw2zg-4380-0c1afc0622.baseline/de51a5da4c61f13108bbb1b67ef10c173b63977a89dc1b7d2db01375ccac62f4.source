#!/usr/bin/env python3
"""test_organ_dialogue_digest.py — T1 (2026-07-25): int() روی برچسبِ شدت.

گواه: governor-alerts.md سه‌سطر ۳۴۸ بار «doctor_digest_beat خطا: ValueError:
invalid literal for int() with base 10: 'متوسط'» — لولهٔ گزارشِ دکتر به مالک
هرگز برنمی‌گشت. این تست doctor_digest() را با severityهای متنوع صدا می‌زند:
هیچ‌کدام raise نمی‌کنند و هر پنج متنِ غیرخالی می‌دهند.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
sys.path.insert(0, str(OPS))
sys.path.insert(0, str(OPS / "budget"))

import opslib  # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="oct-t1-digest-"))
opslib.ORG_ROOT = _TMP
opslib.STATE_DIR = _TMP / "state"
opslib.STATE_DIR.mkdir(parents=True, exist_ok=True)

import organ_dialogue as od  # noqa: E402

fails = []


def check(cond, msg):
    if cond:
        print(f"  ✅ {msg}")
    else:
        fails.append(msg)
        print(f"  ❌ {msg}")


def _write_state(severity):
    sd = opslib.STATE_DIR / "doctor"
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "self-knowledge-latest.json").write_text(json.dumps({
        "version": 7, "snapshot_hash": "abc",
        "focus": "تست",
        "understanding": {"pathology": [
            {"severity": severity, "symptom": "علامتِ آزمایشی", "root_cause": "ریشهٔ آزمایشی"},
        ]},
    }), "utf-8")
    (sd / "rfcs.json").write_text(json.dumps({"rfcs": []}), "utf-8")


for label, sev in [("رشتهٔ انگلیسی high", "high"), ("رشتهٔ فارسی متوسط", "متوسط"),
                   ("عدد صحیح 3", 3), ("None", None), ("برچسب ناشناخته", "چرت")]:
    _write_state(sev)
    try:
        d = od.doctor_digest()
        txt = str(d.get("text") or "")
        check(bool(txt.strip()), f"severity={sev!r} ({label}): متنِ غیرخالی برمی‌گردد")
        check("علامتِ آزمایشی" in txt, f"severity={sev!r}: علامت در متن هست")
        if sev == "متوسط":
            check("(شدت 3)" in txt, "متوسط → عددِ ۳ نگاشت شد")
        elif sev == "high":
            check("(شدت 4)" in txt, "high → عددِ ۴ نگاشت شد")
        elif sev == "چرت":
            check("(شدت چرت)" in txt, "برچسبِ ناشناخته خودش نمایش داده شد (نه کرش، نه صفرِ ساختگی)")
    except Exception as e:  # noqa: BLE001
        fails.append(f"severity={sev!r}")
        print(f"  ❌ severity={sev!r} raise کرد: {type(e).__name__}: {e}")

print(f"\n{'PASS' if not fails else 'FAIL'} — test_organ_dialogue_digest")
for f in fails:
    print(f"  - {f}")
sys.exit(1 if fails else 0)
