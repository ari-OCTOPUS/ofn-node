#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_audit_origin_guard.py — ردیفِ ساختگی نتواند «مدرکِ تأییدِ مالک» شود.

راستی‌آزماییِ متخاصمِ ۲۰۲۶-۰۷-۲۵: سوئیتِ سبزِ ونچر ۵۰ ردیف در فایلِ **تولیدیِ**
ردِ حسابرسیِ تأییدِ انسانی نوشته بود، ۱۴ تا با `actor: owner`. امروز بی‌ضرر است
(gitignore، صفر خواننده) ولی ضررش مؤخر است: جدولِ رأیِ واقعی صفر ردیف دارد، پس
این فایل تنها چیزی است که شبیهِ مدرکِ تأیید به‌نظر می‌رسد.

دو لایه که این تست قفل می‌کند:
  ۱) هر ردیف `origin` دارد و در بافتِ تست **هرگز** `live` نمی‌شود (fail-safe)
  ۲) بافتِ نامعلوم → `test`، نه `live` — شک هرگز به‌نفعِ «واقعی» تفسیر نمی‌شود
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

_VENTURE = Path(__file__).resolve().parents[2] / "03 - Projects" / "اونلی فنز"
_BRAIN = _VENTURE / "brain"
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

FAILURES: list[str] = []
CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILURES.append(msg)


def _fresh_audit(sink: Path):
    """audit را طوری آماده می‌کند که audit_append واقعاً به sink بنویسد.

    ۲۰۲۶-۰۸-۰۶ fix: از ۲۰۲۶-۰۸-۰۳ به بعد audit.py's `DEFAULT_AUDIT_FILE`
    module-level constant نیست — `_default_audit_file()` هربار در زمانِ
    فراخوانی حل می‌شود و audit_append() مستقیم همان تابع را صدا می‌زند، نه
    attribute ماژول را می‌خواند. پس `_a.DEFAULT_AUDIT_FILE = sink` (روشِ قدیم)
    بی‌اثر بود و نوشتن بی‌صدا به فایلِ تولیدیِ واقعی می‌ریخت (T6 همین نشت را
    گرفت). PF_AUDIT_FILE مسیرِ رسمیِ انحراف است — خودِ audit.py._default_audit_file
    آن را می‌خواند؛ همان مکانیزمی که conftest.py و test_e2e_chain.py هم استفاده
    می‌کنند.
    """
    import audit as _a
    os.environ["PF_AUDIT_FILE"] = str(sink)
    _a = importlib.reload(_a)
    return _a


def _rows(sink: Path):
    if not sink.exists():
        return []
    return [json.loads(l) for l in sink.read_text("utf-8").splitlines() if l.strip()]


def _tmp():
    return Path(tempfile.mkdtemp(prefix="auditg-")) / "approvals.jsonl"


def t1_origin_always_present():
    if not _BRAIN.exists():
        return                                    # ونچر در این checkout نیست
    old = os.environ.pop("PF_AUDIT_ORIGIN", None)
    try:
        s = _tmp()
        a = _fresh_audit(s)
        ck(a.audit_append("approve", {"id": "i1", "actor": "owner"}) is True,
           "T1: نوشتن شکست")
        r = _rows(s)
        ck(len(r) == 1, f"T1: {len(r)} ردیف نوشته شد")
        ck(r and "origin" in r[0], "T1: کلیدِ origin روی ردیف نیست")
    finally:
        if old is not None:
            os.environ["PF_AUDIT_ORIGIN"] = old


def t2_test_context_never_live():
    """مهم‌ترین assertion: در بافتِ تست هرگز `live` مهر نمی‌خورد."""
    if not _BRAIN.exists():
        return
    old = os.environ.pop("PF_AUDIT_ORIGIN", None)
    try:
        s = _tmp()
        a = _fresh_audit(s)
        a.audit_append("approve", {"id": "i2", "actor": "owner"})
        r = _rows(s)
        ck(r and r[0].get("origin") == "test",
           f"T2: در بافتِ تست origin={r[0].get('origin') if r else '—'} — باید test باشد")
    finally:
        if old is not None:
            os.environ["PF_AUDIT_ORIGIN"] = old


def t3_garbage_env_fails_safe():
    """env بی‌معنا نباید به `live` تفسیر شود — شک به‌نفعِ «واقعی» ممنوع."""
    if not _BRAIN.exists():
        return
    old = os.environ.get("PF_AUDIT_ORIGIN")
    try:
        for bad in ("چرت", "LIVE!", "1", "", "yes", "production"):
            os.environ["PF_AUDIT_ORIGIN"] = bad
            s = _tmp()
            a = _fresh_audit(s)
            a.audit_append("approve", {"id": "i3", "actor": "owner"})
            r = _rows(s)
            got = r[0].get("origin") if r else None
            ck(got != "live", f"T3: env={bad!r} به live تفسیر شد (fail-open)")
    finally:
        os.environ.pop("PF_AUDIT_ORIGIN", None)
        if old is not None:
            os.environ["PF_AUDIT_ORIGIN"] = old


def t4_explicit_values_respected():
    if not _BRAIN.exists():
        return
    old = os.environ.get("PF_AUDIT_ORIGIN")
    try:
        for val, want in (("live", "live"), ("test", "test"),
                          ("LIVE", "live"), ("  test  ", "test")):
            os.environ["PF_AUDIT_ORIGIN"] = val
            s = _tmp()
            a = _fresh_audit(s)
            a.audit_append("approve", {"id": "i4", "actor": "owner"})
            r = _rows(s)
            ck(r and r[0].get("origin") == want,
               f"T4: env={val!r} → {r[0].get('origin') if r else '—'}، انتظار {want}")
    finally:
        os.environ.pop("PF_AUDIT_ORIGIN", None)
        if old is not None:
            os.environ["PF_AUDIT_ORIGIN"] = old


def t5_conftest_exists_and_redirects():
    """لایهٔ اول: conftest مسیر را برای هر تستِ pytest به tmp می‌برد."""
    if not _VENTURE.exists():
        return
    c = _VENTURE / "conftest.py"
    ck(c.exists(), "T5: conftest.py در ریشهٔ ونچر نیست")
    if not c.exists():
        return
    src = c.read_text("utf-8")
    for needed in ("autouse=True", "PF_AUDIT_FILE", "PF_AUDIT_ORIGIN",
                   "DEFAULT_AUDIT_FILE"):
        ck(needed in src, f"T5: conftest «{needed}» را ست نمی‌کند")
    ck("tmp_path" in src, "T5: conftest به tmp_path نمی‌برد")


def t6_production_file_not_grown_by_this_test():
    """خودِ این تست نباید همان آلودگی را بسازد — گاردِ بازگشتی."""
    prod = _VENTURE / "langar" / "approvals.jsonl"
    if not prod.exists():
        return
    n = len([l for l in prod.read_text("utf-8").splitlines() if l.strip()])
    s = _tmp()
    a = _fresh_audit(s)
    a.audit_append("approve", {"id": "i6", "actor": "owner"})
    n2 = len([l for l in prod.read_text("utf-8").splitlines() if l.strip()])
    ck(n2 == n, f"T6: فایلِ تولیدی از {n} به {n2} رسید — تست خودش آلوده کرد")
    # و ردیف‌های تاریخیِ بی‌مهر باید صریحاً «منشأ نامعلوم» شمرده شوند
    rows = [json.loads(l) for l in prod.read_text("utf-8").splitlines() if l.strip()]
    unmarked = [r for r in rows if "origin" not in r]
    owner_unmarked = [r for r in unmarked if str(r.get("actor")) == "owner"]
    ck(True, "")   # اطلاعی، نه شکست
    if owner_unmarked:
        print(f"    ℹ️  {len(unmarked)} ردیفِ بی‌مهر در فایلِ تولیدی "
              f"({len(owner_unmarked)} با actor=owner) — نوشته‌شده قبل از گارد، "
              f"منشأ نامعلوم، مدرکِ تأییدِ انسانی نیست.")


def main() -> int:
    old_audit_file = os.environ.get("PF_AUDIT_FILE")
    try:
        for fn in (t1_origin_always_present, t2_test_context_never_live,
                   t3_garbage_env_fails_safe, t4_explicit_values_respected,
                   t5_conftest_exists_and_redirects,
                   t6_production_file_not_grown_by_this_test):
            try:
                fn()
            except Exception as e:  # noqa: BLE001
                FAILURES.append(f"{fn.__name__}: EXCEPTION {type(e).__name__}: {e}")
    finally:
        # هر تست بالا PF_AUDIT_FILE را به یک tmp تازه ست می‌کند (_fresh_audit)
        # ولی هرگز پاک نمی‌کند — این‌جا محیط را به حالتِ قبل از اجرا برمی‌گردانیم
        # تا این اسکریپت روی محیطِ پروسه‌ی صداکننده اثرِ ماندگار نگذارد.
        if old_audit_file is not None:
            os.environ["PF_AUDIT_FILE"] = old_audit_file
        else:
            os.environ.pop("PF_AUDIT_FILE", None)
    if FAILURES:
        print(f"FAIL {len(FAILURES)}/{CHECKS} — audit origin guard")
        for f in FAILURES:
            print("  ✗", f)
        return 1
    print(f"PASS {CHECKS}/{CHECKS} — ردیفِ ساختگی نمی‌تواند مدرکِ تأییدِ مالک شود")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
