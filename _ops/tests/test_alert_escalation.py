#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_alert_escalation.py — dedupِ امضامحورِ alert() با escalation، نه سرکوبِ خاموش.

قیود (2026-07-29، ریشه: اسکنِ دکتر یک امضا ×۳۴۶ در دفترِ هشدار دید):
  متنِ نو فوراً می‌آید · سه تکرارِ اول نوشته می‌شوند · بعد فقط شمارش، با سطرِ
  escalation در ×۱۰ · چرخشِ دفترِ بزرگ = انتقال به آرشیو، نه حذف · هر خطای مسیرِ
  dedup → appendِ ساده (fail-open). $0 آفلاین، همه‌چیز temp.
"""
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("alert-escalation")

import opslib       # noqa: E402


def _tmp():
    try:
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    except TypeError:
        return tempfile.TemporaryDirectory()


class _Patched:
    """ALERTS_MD و STATE_DIR را به temp پین می‌کند — هرگز دفترِ زنده لمس نمی‌شود."""

    def __init__(self, td):
        self.td = Path(td)

    def __enter__(self):
        self.p_md = opslib.ALERTS_MD
        self.p_sd = opslib.STATE_DIR
        opslib.ALERTS_MD = self.td / "governor" / "governor-alerts.md"
        opslib.STATE_DIR = self.td / "state"
        return self

    def __exit__(self, *a):
        opslib.ALERTS_MD = self.p_md
        opslib.STATE_DIR = self.p_sd


def t_a_novel_alert_written_immediately():
    with _tmp() as td, _Patched(td):
        opslib.alert(["اولین خطای تازه"])
        text = opslib.ALERTS_MD.read_text("utf-8")
        assert "اولین خطای تازه" in text


def t_b_repeat_suppressed_after_three():
    with _tmp() as td, _Patched(td):
        for _ in range(6):
            opslib.alert(["same failure X"])
        text = opslib.ALERTS_MD.read_text("utf-8")
        assert text.count("same failure X") == 3, \
            f"سه تکرارِ اول نوشته، بعد شمارش (got {text.count('same failure X')})"


def t_c_escalation_mark_at_ten():
    with _tmp() as td, _Patched(td):
        for _ in range(10):
            opslib.alert(["same failure Y"])
        text = opslib.ALERTS_MD.read_text("utf-8")
        assert "×10" in text and "escalation" in text, "دهمین تکرار باید سطرِ ×۱۰ بیاورد"
        assert text.count("same failure Y") == 4        # ۳ اولیه + ۱ escalation


def t_d_different_text_always_passes():
    with _tmp() as td, _Patched(td):
        for _ in range(5):
            opslib.alert(["storm Z"])
        opslib.alert(["هشدارِ واقعیِ متفاوت"])
        text = opslib.ALERTS_MD.read_text("utf-8")
        assert "هشدارِ واقعیِ متفاوت" in text, "متنِ نو هرگز نباید زیرِ طوفان دفن شود"


def t_e_rotation_archives_not_deletes():
    with _tmp() as td, _Patched(td):
        opslib.ALERTS_MD.parent.mkdir(parents=True, exist_ok=True)
        opslib.ALERTS_MD.write_text("x" * 200, "utf-8")
        prev = opslib._ALERT_ROTATE_BYTES
        opslib._ALERT_ROTATE_BYTES = 100
        try:
            opslib.alert(["after rotation"])
        finally:
            opslib._ALERT_ROTATE_BYTES = prev
        archives = list(opslib.ALERTS_MD.parent.glob("governor-alerts-archive-*.md"))
        assert archives, "چرخش باید آرشیوِ تاریخ‌دار بسازد (انتقال، نه حذف)"
        assert archives[0].read_text("utf-8").startswith("x"), "محتوای قدیمی باید در آرشیو بماند"
        assert "after rotation" in opslib.ALERTS_MD.read_text("utf-8")


def t_f_dedup_failure_is_fail_open():
    with _tmp() as td, _Patched(td):
        # STATE_DIR را به یک «فایل» می‌چسبانیم تا مسیرِ dedup مطمئناً خطا بدهد
        bad = Path(td) / "not-a-dir"
        bad.write_text("", "utf-8")
        opslib.STATE_DIR = bad / "child"
        opslib.alert(["آلارمِ حیاتی"])
        assert "آلارمِ حیاتی" in opslib.ALERTS_MD.read_text("utf-8"), \
            "خطای dedup هرگز نباید آلارم را بخورد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_alert_escalation: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
