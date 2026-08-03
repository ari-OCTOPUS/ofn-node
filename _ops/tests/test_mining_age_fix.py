"""test_mining_age_fix — فیکسِ باگِ age_days در mining_leg.py.

باگ: mining_status() سنِ فایل را داخلِ فیلدِ note می‌نوشت. چون note هش
می‌شد، هر روز که سن عوض می‌شد dedup را دور می‌زد. فیکس: سن فقط در کلیدِ
age_days می‌ماند (که از هش بیرون است).
"""
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("age-fix")

_OPS = harness.SELF_OPS
_LEGS = _OPS / "legs"
for _p in (str(_OPS), str(_LEGS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import mining_leg as ml  # noqa: E402


# ─── ۱: note دیگر حاویِ تعدادِ روز نیست ─────────────────────────────────
def t_note_no_longer_contains_day_count():
    """note نباید حاوی الگوی عدد+روز باشد (سن از note رفت)."""
    # ساختِ سنِ مصنوعی: فایلی با mtime قدیمی
    tmpf = Path(tempfile.mktemp(prefix="test-age-"))
    tmpf.write_text("x", "utf-8")
    # mtime = 30 روز پیش
    old_mtime = time.time() - 30 * 86400
    os.utime(tmpf, (old_mtime, old_mtime))
    try:
        with mock.patch.object(ml, "DECISIONS_PATH", tmpf):
            st = ml.mining_status()
            note = st.get("note", "")
            # نباید حاوی عدد+روز باشد
            assert not re.search(r"\d+\s*روز", note), \
                f"note still contains day count: {note!r}"
    finally:
        tmpf.unlink(missing_ok=True)


# ─── ۲: age_days همچنان کلیدِ جداگانه است ────────────────────────────────
def t_age_days_key_still_present():
    """age_days همچنان کلیدِ جداگانه در خروجی است (یا None)."""
    tmpf = Path(tempfile.mktemp(prefix="test-age-"))
    tmpf.write_text("x", "utf-8")
    old_mtime = time.time() - 30 * 86400
    os.utime(tmpf, (old_mtime, old_mtime))
    try:
        with mock.patch.object(ml, "DECISIONS_PATH", tmpf):
            st = ml.mining_status()
            assert "age_days" in st, f"age_days missing from keys: {list(st.keys())}"
            assert st["age_days"] is not None
            assert abs(st["age_days"] - 30.0) < 1.0, f"age_days={st['age_days']}"
    finally:
        tmpf.unlink(missing_ok=True)


# ─── ۳: note با mtime‌های متفاوت ثابت می‌ماند ─────────────────────────────
def t_note_stable_across_a_day():
    """با mtime‌های متفاوت، note یکسان می‌ماند (لبِ فیکس)."""
    tmpf = Path(tempfile.mktemp(prefix="test-age-"))
    tmpf.write_text("x", "utf-8")
    try:
        # mtime = 10 روز پیش
        os.utime(tmpf, (time.time() - 10 * 86400,) * 2)
        with mock.patch.object(ml, "DECISIONS_PATH", tmpf):
            st1 = ml.mining_status()
            note1 = st1["note"]

        # mtime = 25 روز پیش (سن عوض شد)
        os.utime(tmpf, (time.time() - 25 * 86400,) * 2)
        with mock.patch.object(ml, "DECISIONS_PATH", tmpf):
            st2 = ml.mining_status()
            note2 = st2["note"]

        # note باید یکسان بماند (سن از note رفت)
        assert note1 == note2, \
            f"note changed across mtime change:\n  day10: {note1!r}\n  day25: {note2!r}"

        # ولی age_days باید عوض شده باشد
        assert st1["age_days"] != st2["age_days"], \
            f"age_days should differ: {st1['age_days']} vs {st2['age_days']}"
    finally:
        tmpf.unlink(missing_ok=True)


# ─── ۴: پایهٔ مثبت — live و signal دست‌نخورده ─────────────────────────────
def t_live_signal_unchanged():
    """live=False و signal='skeleton' دست‌نخورده‌اند."""
    st = ml.mining_status()
    assert st["live"] is False
    assert st["signal"] == "skeleton"
    assert st["leg"] == "mining"


# ─── ۵: فایلِ ناموجود → age_days=None ────────────────────────────────────
def t_missing_file_age_days_none():
    """فایلِ ناموجود → age_days=None، بدونِ crash."""
    tmpf = Path(tempfile.mktemp(prefix="test-age-nonexist-"))
    # فایل را نسازیم
    try:
        with mock.patch.object(ml, "DECISIONS_PATH", tmpf):
            st = ml.mining_status()
            assert st["age_days"] is None
            assert "فایل پیدا نشد" in st["note"]
    finally:
        tmpf.unlink(missing_ok=True)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_mining_age_fix: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
