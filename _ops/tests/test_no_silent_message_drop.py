#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_no_silent_message_drop.py — هیچ پیامِ مالک بی‌صدا گم نشود.

VQ-SILENT-DROP-001 (۲۰۲۶-۰۸-۰۴). شکایتِ مالک: «انگار هرکاری می‌کنم دیده
نمی‌شود». حلقهٔ poll ِ `center.run_once` این بود:

    if isinstance(uid, int) and uid > max_id:
        max_id = uid            ← offset همین‌جا جلو می‌رفت
    try:
        self.handle_update(u)
    except Exception:
        pass                    ← شکست بی‌صدا بلعیده می‌شد

پس **هر** استثنا وسطِ پردازشِ یک پیام، آن پیام را برای همیشه می‌بلعید:
`max_id` از قبل جلو رفته بود، آخرِ حلقه در config ذخیره می‌شد، و تلگرام دیگر
هرگز تحویلش نمی‌داد. صفر لاگ، صفر شمارنده، صفر هشدار — از بیرون دقیقاً شبیهِ
«پیامی نفرستادی».

⚠️ چرا رفع، offset را روی شکست عقب **نمی‌برد**: یک پیامِ سمی آن‌وقت تا ابد
بازپخش می‌شود و حلقه را گیر می‌اندازد — بدتر از گم‌شدن. الگوی dead-letter:
offset جلو می‌رود (حلقه سالم)، ولی update ماندگار ذخیره و مالک خبردار می‌شود.

⚠️ و چرا هشدار cooldown دارد: شکایتِ **دومِ** مالک در همان پیام شلوغی بود.
گاردی که برای رفعِ سکوت، اسپم بسازد، خاموش می‌شود
(‏[[feedback-a-guard-that-cries-wolf-gets-switched-off]]).
"""
import ast
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("no-silent-drop")

CENTER = harness.REAL_VAULT / "_ops" / "telegram_center" / "center.py"


def _fn(name: str):
    tree = ast.parse(CENTER.read_text("utf-8", errors="replace"))
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def _handler_calls(h: ast.ExceptHandler):
    return [getattr(c.func, "attr", getattr(c.func, "id", "?"))
            for c in ast.walk(h) if isinstance(c, ast.Call)]


def t_a_run_once_exists_and_is_parseable():
    """گاردِ «اسکنر خراب است» — تابعِ جابه‌جاشده نباید سبزِ کاذب بدهد."""
    assert CENTER.exists(), CENTER
    assert _fn("run_once") is not None, "run_once پیدا نشد — این گارد کور شده"


#: فراخوان‌هایی که «این except کاری کرد» حساب می‌شوند.
_REPORTERS = {"alert", "_dead_letter", "_poll_failed", "log", "warning", "error"}


def t_b_no_except_on_the_message_path_is_silent():
    """قلبِ گارد. هر `except` روی مسیرِ پیام باید **کاری** بکند.

    ⚠️ ولی نه هر سکوتی: نسخهٔ اولِ همین تست قرمز شد و **مثبتِ کاذب بود**. آن
    `except` گاردِ خودِ `opslib.alert` است — و **باید** ساکت باشد، چون یک
    هشدارِ شکست‌خورده حق ندارد حلقهٔ poll را بکشد. سکوت آن‌جا طراحی است نه باگ.

    ناوردیِ درست: سکوت فقط در fallback ِ یک **گزارش‌دهنده** مجاز است. اگر
    بدنهٔ `try` ِ متناظر خودش alert/log صدا می‌زند، آن except یک گاردِ درجه‌دوم
    است؛ وگرنه مسیرِ اصلی است و سکوتش یعنی گم‌شدنِ بی‌صدا."""
    src = CENTER.read_text("utf-8", errors="replace")
    fn = _fn("run_once")
    silent = []
    for t in ast.walk(fn):
        if not isinstance(t, ast.Try):
            continue
        body_calls = {getattr(c.func, "attr", getattr(c.func, "id", ""))
                      for c in ast.walk(ast.Module(body=t.body, type_ignores=[]))
                      if isinstance(c, ast.Call)}
        guards_a_reporter = bool(body_calls & _REPORTERS)
        for h in t.handlers:
            if _handler_calls(h):
                continue
            if guards_a_reporter:
                continue          # fallback ِ گزارش‌دهنده — سکوتش عمدی است
            silent.append(h.lineno)
    assert not silent, (
        "این except ها روی مسیرِ اصلیِ پیام‌اند و هیچ فراخوانی ندارند ⇒ شکست "
        "بی‌صدا بلعیده می‌شود. در حلقهٔ poll یعنی پیامِ مالک برای همیشه گم "
        "می‌شود، چون offset از رویش رد شده", silent)


def t_c_the_update_handler_failure_goes_to_a_dead_letter():
    """شکستِ `handle_update` باید **ماندگار** ثبت شود، نه فقط لاگ شود.
    لاگی که کسی نمی‌خواند، همان سکوت است با مراحلِ بیشتر."""
    fn = _fn("run_once")
    found = False
    for h in ast.walk(fn):
        if isinstance(h, ast.ExceptHandler) and "_dead_letter" in _handler_calls(h):
            found = True
    assert found, "هیچ except ای در run_once به _dead_letter نمی‌رود"
    dl = _fn("_dead_letter")
    assert dl is not None, "_dead_letter تعریف نشده"
    src = ast.get_source_segment(CENTER.read_text("utf-8", errors="replace"), dl) or ""
    assert "alert" in src, "_dead_letter مالک را خبر نمی‌کند"

    # ⚠️ زیررشته این‌جا **بی‌دندان بود**: جهشِ «مسیرِ ماندگار را عوض کن» زنده
    # ماند، چون نامِ فایل در متنِ خودِ هشدار هم می‌آید و `in src` همچنان منطبق
    # می‌شد. پس نامِ فایل باید در یک **BinOp ِ ساختِ مسیر** دیده شود، نه در
    # هر رشته‌ای از تابع. (سومین بارِ همین تله در یک روز.)
    written_to = set()
    for n in ast.walk(dl):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
            r = n.right
            if isinstance(r, ast.Constant) and isinstance(r.value, str):
                written_to.add(r.value)
    assert "dead-letters.jsonl" in written_to, (
        "مسیرِ ماندگارِ نامهٔ مرده عوض شده — هشدار می‌آید ولی متنِ پیام جایی "
        f"ذخیره نمی‌شود که مالک بتواند بازش گرداند. مسیرهای ساخته‌شده: {sorted(written_to)}")
    # و باید واقعاً **نوشته** شود، نه فقط مسیرش ساخته شود.
    opened = [n for n in ast.walk(dl)
              if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "open"]
    assert opened, "_dead_letter هیچ فایلی باز نمی‌کند"


def t_d_the_alert_is_rate_limited_so_it_cannot_become_the_new_spam():
    """قرینه، و لازم: مالک در همان پیام از **شلوغی** هم شکایت کرد. گاردی که
    برای رفعِ سکوت اسپم بسازد، خاموش می‌شود و آن‌وقت هر دو مشکل را داریم."""
    src = CENTER.read_text("utf-8", errors="replace")
    dl = _fn("_dead_letter")
    seg = ast.get_source_segment(src, dl) or ""
    assert "_DL_ALERT_COOLDOWN_S" in seg, (
        "هشدارِ نامهٔ مرده cooldown ندارد — یک خطای تکرارشونده به یک رگبار "
        "تبدیل می‌شود")
    assert "COOLDOWN" in src.split("_DL_ALERT_COOLDOWN_S")[0][-400:] or \
        "_DL_ALERT_COOLDOWN_S =" in src, "ثابتِ cooldown تعریف نشده"


def t_e_a_transient_poll_failure_stays_quiet_but_a_persistent_one_shouts():
    """شکستِ گذرای شبکه نباید صدا کند (گرگ‌گرگ)، ولی شکستِ ممتد **باید** —
    چون از «پیامی نیست» غیرقابلِ تفکیک است، و همین یک‌بار ۳۱ ساعت قحطیِ
    دایجست ساخت."""
    src = CENTER.read_text("utf-8", errors="replace")
    assert "_POLL_FAIL_LOUD_AFTER" in src, "آستانهٔ شکستِ پیاپی تعریف نشده"
    pf = _fn("_poll_failed")
    assert pf is not None, "_poll_failed تعریف نشده"
    seg = ast.get_source_segment(src, pf) or ""
    assert "alert" in seg, "_poll_failed هرگز صدا نمی‌کند"
    assert "_POLL_FAIL_LOUD_AFTER" in seg, "آستانه در خودِ تابع استفاده نشده"
    # و موفقیت باید شمارنده را ریست کند، وگرنه یک شکستِ قدیمی برای همیشه
    # می‌ماند و آستانه بی‌معنی می‌شود.
    ro = ast.get_source_segment(src, _fn("run_once")) or ""
    assert "_poll_fails = 0" in ro, "موفقیتِ poll شمارنده را ریست نمی‌کند"


def t_f_the_offset_still_advances_so_a_poison_message_cannot_wedge_the_loop():
    """ناوردیِ ضدِ رفعِ اشتباه: وسوسه این است که روی شکست offset را عقب ببریم
    تا پیام گم نشود. آن‌وقت همان پیام تا ابد بازپخش می‌شود و حلقه گیر می‌کند —
    و هیچ پیامِ بعدی هرگز نمی‌رسد. این بدتر از باگِ اصلی است."""
    src = CENTER.read_text("utf-8", errors="replace")
    ro = ast.get_source_segment(src, _fn("run_once")) or ""
    assert "cfg[\"last_offset\"] = max_id + 1" in ro, "پیشرویِ offset حذف شده"
    assert "max_id = uid" in ro, "بروزرسانیِ max_id حذف شده"
    # و ذخیره باید **بعد** از حلقه باشد نه داخلش (crash وسطِ دسته = بازپخش).
    save_i = ro.find("_save_config")
    loop_i = ro.find("for u in ups")
    assert loop_i >= 0 and save_i > loop_i, (
        "‏_save_config باید بعد از حلقه بیاید — ذخیرهٔ داخلِ حلقه یعنی crash "
        "وسطِ دسته بقیهٔ پیام‌ها را می‌بلعد")


def t_g_this_test_only_reads():
    import ast as _a
    banned = {"write_text", "write_bytes", "unlink", "mkdir", "rename"}
    hits = [n.func.attr for n in _a.walk(_a.parse(Path(__file__).read_text("utf-8")))
            if isinstance(n, _a.Call) and isinstance(n.func, _a.Attribute)
            and n.func.attr in banned]
    assert not hits, hits


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__)
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\ntest_no_silent_message_drop: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
