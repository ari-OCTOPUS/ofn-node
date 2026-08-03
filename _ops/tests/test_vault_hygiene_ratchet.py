#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_vault_hygiene_ratchet.py — لینکِ شکسته و فرانت‌مترِ خراب فقط پایین می‌روند.

§۱۱ منشور می‌گوید هر دو validator بعد از ویرایشِ دسته‌ای اجرا شوند و «جلسه وقتی
تمام است که هر دو پاس شوند». ولی هیچ‌چیز اجرایش نمی‌کرد: `grep` روی کلِ
`_ops/tests` نشان داد هیچ تستی این دو اسکریپت را صدا نمی‌زند. یعنی قاعده در متن
بود و صفر صداکننده داشت — همان کلاسی که این ریپو مکرر گرفتارش شده.

چرا الان: ممیزیِ ۲۰۲۶-۰۸-۰۴ چهار پیشنهادِ **مستقل** تولید کرد که همه می‌خواستند
فایل به `_Archive/` منتقل کنند. یکی‌شان سنجیده شد و **۳۴ ویکی‌لینک در ۶ فایل**
را می‌شکست — ستونِ شواهدِ یک دفترِ تصمیمِ زنده. مکانیزمش ساکت است:
`find_broken_links.py:31` ایندکسِ هدف را از `rglob("*")` منهای
`EXCLUDE = ("_Archive","_Duplicates",".git","_code",".obsidian",".claude")`
می‌سازد، پس انتقال به `_Archive` هدف را از ایندکس **حذف** می‌کند ⇒ لینک‌ها
یک‌شبه از ۳۰ به ~۶۴ می‌رفت. و `alwaysUpdateLinks` نجات نمی‌داد: آن فقط روی
جابه‌جاییِ **داخلِ برنامه** شلیک می‌کند، نه `git mv`.

⚠️ ratchet است نه گیتِ صفر: ۳۰ لینکِ شکسته و ۲۷ خطای فرانت‌متر بدهیِ
پیش‌موجودند. صفرکردنشان کارِ دیگری است؛ کارِ این فایل فقط این است که **بدتر
نشوند**. عددها با پایین‌رفتنِ واقعی باید این‌جا هم پایین بیایند (دوطرفه، مثلِ
`test_phantom_guards`).
"""
import re
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("vault-hygiene-ratchet")

VAULT = harness.REAL_VAULT
SCRIPTS = VAULT / "04 - Architect System" / "scripts"
LINKS = SCRIPTS / "find_broken_links.py"
FRONT = SCRIPTS / "validate_frontmatter.py"

# ── دفترِ منجمد (سنجیده ۲۰۲۶-۰۸-۰۴ روی همین درخت) ─────────────────────────────
MAX_CURATED_BROKEN = 5     # لایهٔ دست‌چین — همانی که §۱۱ رویش گیت می‌گذارد
MAX_TOTAL_BROKEN = 30      # دست‌چین + عملیاتی
MAX_FRONTMATTER = 27

# کفِ **ضدِ سبزِ کاذب**. بدونِ این، یک validator که زود می‌ترکد یا به درختِ
# اشتباه اشاره می‌کند «۰ لینکِ شکسته» گزارش می‌دهد و ratchet سبز می‌شود.
# این ریپو دقیقاً از همین راه یک بار گول خورده.
MIN_LINK_NOTES = 2000      # سنجیده: ۲۳۸۳
MIN_FRONT_NOTES = 400      # سنجیده: ۴۶۱


def _run(script, *args):
    """ریشه **صریح** pin می‌شود، نه ارثی.

    `find_broken_links.py:29` اول `VAULT_LINK_ROOT` را می‌خواند و تنها بعدش به
    `__file__` برمی‌گردد. اگر آن متغیر در env ِ والد ست باشد — و harness یک
    env ِ کاملِ دست‌ساز می‌سازد — این تست بی‌صدا درختِ دیگری را می‌سنجید و
    «۰ لینکِ شکسته» می‌گرفت. pin کردن هم قطعیت می‌دهد و هم کفِ زیر را
    **قابلِ‌جهش** می‌کند: کافی است این مقدار به یک درختِ خالی برود تا
    `t_a` قرمز شود. بدونِ این خط، کف اثبات‌ناپذیر بود.
    (`validate_frontmatter.py:12` چنین متغیری ندارد و از `__file__` می‌آید.)
    """
    import os
    env = dict(os.environ)
    env["VAULT_LINK_ROOT"] = str(VAULT)
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, str(script), *args],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(VAULT), env=env, timeout=300)
    return (r.stdout or "") + (r.stderr or "")


def _num(pattern, text, what):
    m = re.search(pattern, text)
    assert m, (f"خروجیِ validator شکلِ منتظره را ندارد — «{what}» پیدا نشد. "
               "یا اسکریپت عوض شده یا اصلاً ندویده؛ هر دو یعنی این گارد کور است.")
    return int(m.group(1))


def _links():
    out = _run(LINKS)
    return {
        "scanned": _num(r"بررسی شد:\s*(\d+)\s*نوت", out, "شمارِ نوتِ اسکن‌شده"),
        "curated": _num(r"لایهٔ دست‌چین \(§۱۱\):\s*(\d+)", out, "لینکِ شکستهٔ دست‌چین")
        if "لایهٔ دست‌چین" in out else 0,
        "ops": _num(r"لایهٔ عملیاتی[^:]*:\s*(\d+)", out, "لینکِ شکستهٔ عملیاتی")
        if "لایهٔ عملیاتی" in out else 0,
        "clean": "لینک شکسته‌ای نیست" in out,
    }


def _front():
    out = _run(FRONT)
    return {
        "scanned": _num(r"بررسی شد:\s*(\d+)\s*نوت", out, "شمارِ نوتِ فرانت‌متر"),
        "errors": _num(r"خطا:\s*(\d+)", out, "شمارِ خطا") if "خطا:" in out else 0,
        "clean": "همه نوت‌ها معتبرند" in out,
    }


def t_a_the_link_validator_actually_ran_over_the_vault():
    """گاردِ «اسکنر خراب است» — قبل از هر آستانه‌ای."""
    d = _links()
    assert d["scanned"] >= MIN_LINK_NOTES, (
        f"فقط {d['scanned']} نوت اسکن شد (کف {MIN_LINK_NOTES}) — validator به "
        "درختِ اشتباه اشاره می‌کند یا زود ترکیده. «۰ لینکِ شکسته» این‌جا دروغ است.")


def t_b_the_frontmatter_validator_actually_ran():
    d = _front()
    assert d["scanned"] >= MIN_FRONT_NOTES, (
        f"فقط {d['scanned']} نوت اسکن شد (کف {MIN_FRONT_NOTES})")


def t_c_curated_broken_links_never_grow():
    """لایهٔ دست‌چین همانی است که §۱۱ رویش گیت می‌گذارد. جدا از totalَ سنجیده
    می‌شود چون وگرنه یک شکستِ دست‌چین می‌تواند پشتِ یک رفعِ عملیاتی پنهان شود."""
    d = _links()
    assert d["curated"] <= MAX_CURATED_BROKEN, (
        f"لینکِ شکستهٔ دست‌چین {d['curated']} > دفترِ {MAX_CURATED_BROKEN}. "
        "اگر فایلی به _Archive منتقل شده، هدف از ایندکسِ validator افتاده "
        "(find_broken_links.py:31 EXCLUDE) — انتقال را برگردان یا لینک‌ها را به‌روز کن.")


def t_d_total_broken_links_never_grow():
    d = _links()
    total = d["curated"] + d["ops"]
    assert total <= MAX_TOTAL_BROKEN, (
        f"لینکِ شکستهٔ کل {total} > دفترِ {MAX_TOTAL_BROKEN}")


def t_e_frontmatter_violations_never_grow():
    d = _front()
    assert d["errors"] <= MAX_FRONTMATTER, (
        f"خطای فرانت‌متر {d['errors']} > دفترِ {MAX_FRONTMATTER}. "
        "§۶: status فقط idea|active|paused|done|archived با حروفِ کوچک — "
        "Bases به حروف حساس است.")


def t_f_the_ledger_comes_down_when_the_debt_is_paid():
    """دوطرفه، مثلِ test_phantom_guards. اگر بدهی واقعاً پرداخت شد ولی این
    عددها پایین نیامدند، دفتر از واقعیت جدا افتاده و دیگر چیزی قفل نمی‌کند."""
    l, f = _links(), _front()
    total = l["curated"] + l["ops"]
    assert not (total < MAX_TOTAL_BROKEN - 5), (
        f"لینکِ شکسته به {total} رسید ولی دفتر هنوز {MAX_TOTAL_BROKEN} است — "
        "MAX_TOTAL_BROKEN را در همین فایل پایین بیاور")
    assert not (f["errors"] < MAX_FRONTMATTER - 5), (
        f"خطای فرانت‌متر به {f['errors']} رسید ولی دفتر هنوز {MAX_FRONTMATTER} "
        "است — MAX_FRONTMATTER را پایین بیاور")


def t_g_this_test_only_reads():
    import ast
    banned = {"write_text", "write_bytes", "unlink", "mkdir", "rename"}
    hits = []
    for n in ast.walk(ast.parse(Path(__file__).read_text("utf-8"))):
        if isinstance(n, ast.Call):
            fn = n.func
            if isinstance(fn, ast.Attribute) and fn.attr in banned:
                hits.append(fn.attr)
    assert not hits, ("این تست فقط validator را می‌دواند و می‌خواند", hits)


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
    print(f"\ntest_vault_hygiene_ratchet: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
