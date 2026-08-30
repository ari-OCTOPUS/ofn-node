#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_telegram_truthful_receipts.py — بات نباید به مالک عددِ جعلی بدهد.

اسکنِ ۱۶-ایجنتهٔ ۲۰۲۶-۰۸-۰۴ دو دروغ و یک چرخنده روی سطحِ تلگرام پیدا کرد. هر
سه این‌جا قفل می‌شوند.

۱) **عددِ جعلی.** `tg-center-watchdog.ps1` مقدارِ `silent 999999s` را به‌عنوانِ
   سنتینلِ «نامعلوم» می‌نویسد (پیش‌فرضِ اولیه و مقدارِ catch). رسیدِ مرگ آن را
   `int(999999/60)` می‌کرد و **۱۶۶۶۶ دقیقه ≈ ۱۱٫۶ روز** به‌عنوانِ اندازه‌گیری
   روی گوشیِ مالک می‌گذاشت. دو از هشت قطعیِ ثبت‌شده همین سنتینل را داشتند.

۲) **ادعای بی‌پایه.** «پیام‌هایی که در آن بازه فرستادی را ندیده‌ام» — ولی
   `run_once` نشانگر را **بعد** از dispatch ذخیره می‌کند، یعنی صف بازپخش
   می‌شود؛ و طولانی‌ترین قطعی ۵٫۶۷ ساعت بود، خیلی داخلِ نگه‌داریِ ~۲۴ ساعتهٔ
   تلگرام. مالک چیزهایی را دوباره می‌فرستاد که رسیده بودند.

۳) **چرخنده.** `_refresh_leg_card` هش را فقط وقتی ذخیره می‌کرد که ارسال id
   برگردانده باشد. یک ارسالِ held عددِ صحیح نمی‌دهد ⇒ هش ذخیره نمی‌شود ⇒ دورِ
   بعد دوباره می‌فرستد. اندازه‌گیری: **۱۰۴ ارسالِ بایت‌به‌بایت یکسان** بینِ
   ۰۵:۳۹ و ۰۷:۰۰، ۱۰۳ تا held، فقط **یکی** تحویل.

⚠️ هیچ‌کدام از این سه رفع پیامی را از گوشیِ مالک **حذف** نمی‌کند — شکایتِ
اصلیِ او «دیده نمی‌شوم» بود، پس رفعی که سکوت بسازد، مشکل را بدتر می‌کند.
"""
import ast
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("truthful-receipts")
CENTER = harness.REAL_VAULT / "_ops" / "telegram_center" / "center.py"
SRC = CENTER.read_text("utf-8", errors="replace")


def _fn(name):
    for n in ast.walk(ast.parse(SRC)):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def t_a_the_file_parses_and_the_anchors_exist():
    assert CENTER.exists()
    assert _fn("_refresh_leg_card") is not None, "_refresh_leg_card گم شد"
    assert "مرده بودم و واچ‌داگ برم گرداند" in SRC, "رسیدِ مرگ گم شد"


def t_b_the_unknown_sentinel_is_never_rendered_as_a_duration():
    """قلبِ بندِ ۱: ۹۹۹۹۹۹ یعنی «نمی‌دانم»، نه ۱۱٫۶ روز.

    ⚠️ نسخهٔ اول `"999999" in SRC` بود و **بی‌دندان**: جهشِ «آستانه را به
    ۱۰**۱۸ ببر» زنده ماند، چون همان رقم در **کامنتِ** توضیحی هم می‌آید.
    چهارمین بارِ همین تله در یک روز. پس عدد باید در یک **مقایسهٔ واقعی**
    دیده شود، نه در متن."""
    assert "نامعلوم" in SRC, "حالتِ «نامعلوم» رندر نمی‌شود"
    found = []
    for n in ast.walk(ast.parse(SRC)):
        if isinstance(n, ast.Compare):
            for c in [n.left] + list(n.comparators):
                if isinstance(c, ast.Constant) and isinstance(c.value, int):
                    # سنتینل باید در بازهٔ معقولِ خودش باشد: به‌قدرِ کافی بزرگ
                    # که یک قطعیِ واقعی به آن نرسد، و به‌قدرِ کافی کوچک که
                    # سنتینلِ ۹۹۹۹۹۹ **زیرش** نیفتد.
                    if 100000 <= c.value <= 999999:
                        found.append((n.lineno, c.value))
    assert found, (
        "هیچ مقایسه‌ای با سنتینلِ «نامعلوم» پیدا نشد — `silent 999999s` دوباره "
        "به عدد تبدیل می‌شود و مالک «۱۶۶۶۶ دقیقه» می‌بیند به‌عنوانِ اندازه‌گیری")


def t_c_the_receipt_no_longer_claims_the_messages_were_unseen():
    """بندِ ۲: رسید می‌ماند (قطعیِ واقعی باید دیده شود) ولی ادعایش درست شد."""
    assert "ندیده‌ام — اگر مهم بود دوباره بگو" not in SRC, (
        "ادعای بی‌پایهٔ «ندیده‌ام» برگشت — نشانگر restart-safe است و صف "
        "بازپخش می‌شود؛ این جمله مالک را وادار به ارسالِ دوباره می‌کند")
    assert "بازپخش" in SRC, "رسید دیگر توضیح نمی‌دهد که صف بازپخش شده"


def t_d_the_death_receipt_is_not_deleted():
    """قرینه، و لازم: وسوسه این است که برای «تمیزی» کلِ رسید حذف شود. آن‌وقت
    یک قطعیِ واقعی نامرئی می‌شود — و ۰۷-۳۱ دقیقاً همین شد: بات ۳ ساعت و ۵۳
    دقیقه مرده بود و «مالک هرگز نفهمید»."""
    assert "مرده بودم و واچ‌داگ برم گرداند" in SRC, "رسیدِ مرگ حذف شده"


def t_e_the_leg_card_hash_is_saved_even_when_the_send_is_held():
    """بندِ ۳. هش باید **بی‌قید** ذخیره شود، وگرنه hold ⇒ چرخنده."""
    fn = _fn("_refresh_leg_card")
    seg = ast.get_source_segment(SRC, fn) or ""
    # `hashes[leg] = h` نباید داخلِ یک `if` ای باشد که به id شرط شده.
    tree = ast.parse(seg.strip())
    guarded = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.If):
            continue
        cond = ast.dump(n.test)
        if "ids" not in cond:
            continue
        for c in ast.walk(n):
            if (isinstance(c, ast.Assign)
                    and any(isinstance(t, ast.Subscript)
                            and getattr(t.value, "id", "") == "hashes"
                            for t in c.targets)):
                guarded.append(n.lineno)
    assert not guarded, (
        "ذخیرهٔ هش دوباره به موفقیتِ ارسال شرط شد ⇒ یک ارسالِ held کارت را به "
        "چرخنده تبدیل می‌کند (۱۰۴ ارسالِ یکسان در ۸۰ دقیقه، ۰۸-۰۴)", guarded)
    assert "hashes[leg] = h" in seg, "ذخیرهٔ هش کلاً حذف شده"


def t_f_a_changed_body_still_gets_sent():
    """قرینهٔ بندِ ۳، و مهم‌تر از خودش: رفع نباید به «دیگر هرگز نفرست» تبدیل
    شود. کلید باید **محتوا** باشد، پس بدنهٔ عوض‌شده هش را عوض می‌کند و همان
    دور دوباره می‌رود. اگر کلید زمان‌محور شود، کارت برای همیشه یخ می‌زند."""
    seg = ast.get_source_segment(SRC, _fn("_refresh_leg_card")) or ""
    assert "hashes.get(leg)" in seg or "hashes.get(" in seg, (
        "مقایسهٔ هشِ ذخیره‌شده با هشِ جدید پیدا نشد — بدونش یا همیشه می‌فرستد "
        "یا هرگز")
    for t in ("time.time", "last_sent", "cooldown"):
        assert t not in seg.split("hashes[leg] = h")[0][-300:], (
            f"کلیدِ زمان‌محور («{t}») کنارِ ذخیرهٔ هش — کلید باید محتوا باشد")


def t_g_this_test_only_reads():
    banned = {"write_text", "write_bytes", "unlink", "rename"}
    hits = [n.func.attr for n in ast.walk(ast.parse(Path(__file__).read_text("utf-8")))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr in banned]
    assert not hits, hits


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t(); passed += 1; print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__); print(f"  FAIL {t.__name__}: {e}")
    print(f"\ntest_telegram_truthful_receipts: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
