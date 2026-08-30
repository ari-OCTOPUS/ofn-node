#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_flag_shortfall_smtp_exemption — R26 (2026-08-16، تفویض مالک).

معافیتِ کلیدهای SMTPِ poison از شمارشِ shortfall گیتِ ری‌استارت:
  ۱. باریک: فقط همان ۴ نام — کلیدِ گم‌شدهٔ دیگر همچنان شمرده می‌شود (منفی).
  ۲. شفاف: معاف‌ها در خروجی گزارش می‌شوند، نه پنهان.
  ۳. منقضی‌شونده: تاریخِ بازبینی گذشته باشد ⇒ تست قرمز (تمدید آگاهانه).
  ۴. پایه: فایلِ زندهٔ flags.cmd این ۴ کلید را همچنان «تعریف‌شده-خالی» دارد
     (ساختارِ poison دست‌نخورده؛ معافیت = شمردن، نه حذفِ تعریف).
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("flag-shortfall-smtp-exemption")
sys.path.insert(0, str(ENV["ops"]))
import flag_drift  # noqa: E402

LIVE_FLAGS = Path(r"F:\backup\_ops\OCTOPUS-flags.cmd")


def t_exemption_is_narrow_and_exact():
    assert flag_drift.INTENTIONALLY_EMPTY_FLAGS == frozenset({
        "OCTOPUS_SMTP_FROM", "OCTOPUS_SMTP_HOST",
        "OCTOPUS_SMTP_PORT", "OCTOPUS_SMTP_USER",
    }), flag_drift.INTENTIONALLY_EMPTY_FLAGS


def t_smtp_keys_not_counted_as_missing():
    file_flags = {"OCTOPUS_SMTP_FROM": "", "OCTOPUS_SMTP_HOST": "",
                  "OCTOPUS_SMTP_PORT": "", "OCTOPUS_SMTP_USER": "",
                  "OCTOPUS_X1": "1", "OCTOPUS_X2": "1"}
    env = {"OCTOPUS_X1": "1", "OCTOPUS_X2": "1"}
    sf = flag_drift.load_shortfall(file_flags, env)
    assert sf["missing_count"] == 0, sf
    assert sf["intentionally_empty"] == [
        "OCTOPUS_SMTP_FROM", "OCTOPUS_SMTP_HOST",
        "OCTOPUS_SMTP_PORT", "OCTOPUS_SMTP_USER"], sf


def t_non_exempt_missing_still_counts():  # منفی — معافیت دهانهٔ باز نیست
    file_flags = {"OCTOPUS_SMTP_FROM": "", "OCTOPUS_REAL_KEY": "1"}
    env = {}
    sf = flag_drift.load_shortfall(file_flags, env)
    assert sf["missing_count"] == 1, sf
    assert "OCTOPUS_REAL_KEY" in sf["missing_sample"], sf


def t_exemption_is_expiring():
    review = date.fromisoformat(flag_drift.INTENTIONALLY_EMPTY_REVIEW)
    assert review > date.today(), (
        f"معافیتِ SMTP منقضی شده ({review}) — تمدید آگاهانه یا حذف معافیت لازم است")


def t_live_flags_cmd_still_defines_them_empty():
    """ساختارِ poison در فایلِ زنده پابرجا — معافیت تعریف را حذف نکرده."""
    if not LIVE_FLAGS.exists():  # محیطِ هرمتیک بدونِ فایلِ زنده — چک اینجا خنثی است
        return
    flags, _ = flag_drift.parse_flags_file(LIVE_FLAGS)
    for k in flag_drift.INTENTIONALLY_EMPTY_FLAGS:
        assert k in flags, f"{k} دیگر در flags.cmd تعریف نشده — معافیت را هم بردار"


CHECKS = [
    ("معافیت باریک و دقیق", t_exemption_is_narrow_and_exact),
    ("کلیدهای SMTP شمرده نمی‌شوند", t_smtp_keys_not_counted_as_missing),
    ("کلیدِ غیرمعافِ گم‌شده همچنان می‌شمارد", t_non_exempt_missing_still_counts),
    ("معافیت منقضی‌شونده است", t_exemption_is_expiring),
    ("flags.cmd poison پابرجا", t_live_flags_cmd_still_defines_them_empty),
]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    sys.exit(1 if failed else 0)
