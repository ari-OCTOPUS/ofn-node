#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_both_bots_log_inbound.py — چشم باید روی باتی باشد که حرف می‌زند.

VQ-NO-INBOUND-LOG-002 (۲۰۲۶-۰۸-۰۴).

نسخهٔ اولِ لاگِ ورودی فقط روی `center.py` (باتِ **بیرونی**) گذاشته شد. مالک
گفت «حس می‌کنم هنوز کور است» — و درست گفت. cursorها نشان دادند ترافیکِ واقعی
از **poller ِ دیگر** می‌گذرد:

    center-config.json      last_offset = 223883195   (ساکت، صفر ردیف)
    telegram_offset.json    offset      = 732409511   (حرکت می‌کند)

یعنی چشم روی باتی بود که حرف نمی‌زند. این ریپو **دو** poller دارد و هر
ابزارِ رصدی باید هر دو را بپوشاند، وگرنه دقیقاً همان سکوتی می‌ماند که قرار
بود رفع شود.

⚠️ و یک تلهٔ دوم که همان‌جا گرفته شد: نسخهٔ اول `self.owner_id` نوشت، ولی
attribute ِ واقعی `self._owner` است. `AttributeError` داخلِ `except` ِ
fail-soft بلعیده می‌شد و **کلِ ردیف** بی‌صدا نوشته نمی‌شد — یعنی لاگی که برای
رفعِ سکوت ساخته شده بود، خودش ساکت می‌مرد. `getattr(..., "")` جایش نشست.
"""
import ast
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("both-bots-inbound")

POLLERS = {
    "center (outer)": harness.REAL_VAULT / "_ops" / "telegram_center" / "center.py",
    "approval_channel (inner)": harness.REAL_VAULT / "_ops" / "budget" / "approval_channel.py",
}
LOG_NAME = "inbound-log.jsonl"


def _src(p):
    return p.read_text("utf-8", errors="replace")


def t_a_both_poller_files_exist():
    missing = [k for k, p in POLLERS.items() if not p.exists()]
    assert not missing, missing


def t_b_every_poller_writes_the_inbound_log():
    """قلبِ گارد. یک poller ِ بی‌لاگ یعنی نیمی از پیام‌ها نامرئی‌اند."""
    silent = [k for k, p in POLLERS.items() if LOG_NAME not in _src(p)]
    assert not silent, (
        "این pollerها ورودی را ثبت نمی‌کنند ⇒ «پیامم رسید؟» برای ترافیکِ آن‌ها "
        "جواب ندارد. این ریپو دو poller دارد و رصد باید هر دو را بپوشاند", silent)


def _log_region(p: Path) -> str:
    """سورسِ **تابعی** که لاگ را می‌نویسد — نه یک پنجرهٔ کاراکتری.

    ⚠️ نسخهٔ اولِ این فایل `s[i-1800:i+400]` می‌گرفت و قرمزِ کاذب داد، چون
    بلوکِ کامنتِ فارسی پنجره را جابه‌جا می‌کرد. همان ضدالگویی که امروز چهار
    بار در همین ریپو گرفته شد: پنجرهٔ کاراکتری همان شکنندگیِ شماره‌خط را دارد.
    """
    src = _src(p)
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef):
            seg = ast.get_source_segment(src, n) or ""
            if LOG_NAME in seg:
                return seg
    return ""


def t_c_both_write_to_the_same_file():
    """دو فایلِ لاگ یعنی دو حقیقت. مالک نباید بداند کدام بات پیامش را گرفت."""
    for k, p in POLLERS.items():
        seg = _log_region(p)
        assert seg, (k, "هیچ تابعی لاگ را نمی‌نویسد")
        assert '"telegram"' in seg, (k, "مسیرِ لاگ زیرِ state/telegram/ نیست")


def t_d_neither_stores_the_message_text():
    """§۱۰. هدف «آیا رسید؟» است نه بایگانیِ مکالمه."""
    for k, p in POLLERS.items():
        seg = _log_region(p)
        assert seg, k
        assert '"text": text' not in seg and '"text": _t' not in seg, (
            k, "متنِ پیام در لاگِ ورودی ذخیره می‌شود — نشتیِ PII")
        assert '"chars"' in seg, (k, "طول ثبت نمی‌شود")


def t_e_the_owner_flag_reads_a_real_attribute():
    """⚠️ تلهٔ زندهٔ همین رفع: نامِ غلطِ attribute یک `AttributeError` می‌سازد
    که `except` ِ fail-soft می‌بلعد ⇒ **کلِ ردیف** نوشته نمی‌شود. پس نه فقط
    باید چیزی نوشته شود، بلکه نامش باید واقعاً روی کلاس وجود داشته باشد."""
    p = POLLERS["approval_channel (inner)"]
    s = _src(p)
    assert 'getattr(self, "_owner"' in s, (
        "پرچمِ from_owner از attribute ِ ناموجود می‌خواند — ردیف بی‌صدا "
        "نوشته نمی‌شود (کلاس `self._owner` دارد، نه `owner_id`)")
    # و خودِ attribute باید واقعاً در __init__ ست شود
    assert "self._owner = " in s, "کلاس اصلاً _owner را ست نمی‌کند"


def t_f_the_log_is_bounded_on_both_paths():
    for k, p in POLLERS.items():
        seg = _log_region(p)
        assert "st_size" in seg, (k, "چرخشِ لاگ ندارد — روی دیسکِ مکانیکی رشد می‌کند")


def t_g_this_test_only_reads():
    banned = {"write_text", "write_bytes", "unlink", "rename"}
    hits = [n.func.attr for n in ast.walk(ast.parse(Path(__file__).read_text("utf-8")))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr in banned]
    assert not hits, hits


def t_h_a_silenced_update_records_why():
    """VQ-ARRIVED-BUT-WHY-001 (۲۰۲۶-۰۸-۰۴، از مشاهدهٔ خودِ مالک).

    لاگِ ورودی می‌گفت «رسید» و بس. رسیدِ ردِ سیاستِ ورودی وجود داشت ولی در
    لاگِ **خروجی** با مهرِ زمانیِ اپاک — یعنی برای فهمیدنِ «رسید ولی چرا
    هیچ نشد؟» باید دو فایل با دو فرمتِ زمانی دستی جوین می‌شد.

    هر مسیری که update را **بی‌جواب** برمی‌گرداند باید دلیلش را کنارِ همان
    ردیفِ رسید بگذارد، با همان `update_id` تا جوین‌شدنی باشد. (همان درسِ
    `_context`: دو فهرستِ درست که به‌هم وصل نمی‌شوند، عملاً هیچ‌اند.)"""
    center = harness.REAL_VAULT / "_ops" / "telegram_center" / "center.py"
    src = center.read_text("utf-8", errors="replace")
    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "_log_disposition"), None)
    assert fn is not None, "‏_log_disposition تعریف نشده"
    seg = ast.get_source_segment(src, fn) or ""
    assert '"update_id"' in seg, "بدونِ update_id ردیف جوین‌شدنی نیست"
    assert LOG_NAME in seg, "دلیل باید در **همان** فایلِ رسید بنشیند نه فایلِ سوم"
    assert '"reason"' in seg and '"outcome"' in seg

    # و باید واقعاً از مسیرهای سکوت صدا زده شود — نه فقط تعریف شده باشد.
    hu = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "handle_update")
    hseg = ast.get_source_segment(src, hu) or ""
    assert hseg.count("_log_disposition") >= 2, (
        "کمتر از دو مسیرِ سکوت دلیل ثبت می‌کنند — «غیرمالک» و «ردِ سیاستِ "
        "ورودی» هر دو باید بنویسند")


def t_i_the_disposition_row_stores_no_message_text():
    """§۱۰ برای این ردیف هم برقرار است — دلیلِ ساختاری، نه متنِ پیام."""
    center = harness.REAL_VAULT / "_ops" / "telegram_center" / "center.py"
    src = center.read_text("utf-8", errors="replace")
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "_log_disposition")
    seg = ast.get_source_segment(src, fn) or ""
    for leak in ('"text"', "msg.get(\"text\")", '"chars"'):
        assert leak not in seg, (leak, "متن/محتوا در ردیفِ دلیل")


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t(); passed += 1; print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__); print(f"  FAIL {t.__name__}: {e}")
    print(f"\ntest_both_bots_log_inbound: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
