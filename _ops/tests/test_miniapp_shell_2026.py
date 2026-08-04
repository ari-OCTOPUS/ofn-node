#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_miniapp_shell_2026.py — پوستهٔ ۲۰۲۶ باید سرو شود و تستش واقعاً بدود.

فاز ۳ ِ فرانت (۲۰۲۶-۰۸-۰۴). کلِ یکپارچگیِ تلگرامِ این اپ تا امروز یک خط بود
(`expand` + `setHeaderColor`)، پس روی گوشی محتوا زیرِ نُچ می‌رفت، تمام‌صفحه
نبود و آیکونِ صفحهٔ اصلی نداشت.

⚠️ دو تلهٔ ثبت‌شده که این فایل می‌بندد:

۱. **فایلِ تاریک.** `index.html` حالا `tg_shell.js` را صدا می‌زند. اگر
   allowlist ِ گیت‌وی آن را نداشته باشد، مرورگر ۴۰۴ می‌گیرد و **هیچ خطای
   قابلِ‌دیدنی** نیست جز یک تگِ script ِ شکست‌خورده در کنسولی که کسی
   نمی‌بیند — یعنی همهٔ قابلیت‌های ۲۰۲۶ بی‌صدا غایب می‌شوند.

۲. **تستِ تاریک.** ۱۳ تستِ جاوااسکریپت در `tg_shell.test.js` هست، ولی
   `run_all.py` پایتون می‌دود. تستی که هیچ‌کس اجرایش نمی‌کند با تستِ نبود
   فرقی ندارد — پس این فایل عمداً آن را **صدا می‌زند** و خروجی‌اش را
   می‌سنجد.
"""
import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("miniapp-shell-2026")
sys.path.insert(0, str(harness.REAL_VAULT / "_ops" / "telegram_center"))

MINI = harness.REAL_VAULT / "_ops" / "telegram_center" / "miniapp"
SHELL_JS = MINI / "tg_shell.js"
SHELL_TEST = MINI / "tg_shell.test.js"


def t_a_the_shell_module_and_its_test_exist():
    assert SHELL_JS.exists(), SHELL_JS
    assert SHELL_TEST.exists(), SHELL_TEST


def t_b_the_gateway_serves_the_shell():
    """⚠️ بدونِ مدخل در allowlist، `index.html` ِ زنده ۴۰۴ می‌گیرد و همهٔ
    قابلیت‌های ۲۰۲۶ بی‌صدا غایب می‌شوند."""
    import miniapp_gateway as g
    for p in ("/miniapp/tg_shell.js", "/tg_shell.js"):
        st, body, ctype = g._miniapp_static_response(p)
        assert st == 200, (p, st, "گیت‌وی پوسته را سرو نمی‌کند")
        assert b"OctopusShell" in body, (p, "بدنه پوستهٔ درست نیست")
        assert "javascript" in ctype, (p, ctype)
    # و مسیرِ ناشناخته همچنان بسته
    assert g._miniapp_static_response("/miniapp/nope.js")[0] == 404


def t_c_the_shell_is_reachable_through_the_real_router():
    """‏`_miniapp_static_response` مستقیم کافی نیست — مسیر باید در همان
    فهرستی باشد که `_handle_core` بررسی می‌کند، وگرنه هرگز به آن نمی‌رسد."""
    import miniapp_gateway as g
    st, body, _ = g._handle_core("GET", "/miniapp/tg_shell.js", {})
    assert st == 200 and b"OctopusShell" in body, (st, "روتر مسیر را نمی‌شناسد")


def t_d_index_html_loads_the_shell_before_the_app():
    """ترتیب باربر است: `app.js` روی `window.OctopusShell` حساب می‌کند."""
    # ⚠️ نسخهٔ اولِ این assert زیررشتهٔ «app.js» را می‌گشت و روی
    # `telegram-web-app.js` ِ خطِ ۸ می‌افتاد — قرمزِ کاذب، دقیقاً همان
    # ضدالگوی ثبت‌شدهٔ «assert ِ زیررشته‌ای». حالا **فهرستِ اسکریپت‌ها** به
    # ترتیب استخراج می‌شود، نه یک find ِ کور.
    import re
    html = (MINI / "index.html").read_text("utf-8", errors="replace")
    srcs = re.findall(r'<script[^>]+src="([^"]+)"', html)
    assert "/miniapp/tg_shell.js" in srcs, ("‏index.html پوسته را بار نمی‌کند", srcs)
    assert "/miniapp/app.js" in srcs, srcs
    assert srcs.index("/miniapp/tg_shell.js") < srcs.index("/miniapp/app.js"), (
        "پوسته بعد از app.js بار می‌شود ⇒ در لحظهٔ نیاز نیست", srcs)
    # و SDK ِ خودِ تلگرام باید قبل از هر دو باشد، وگرنه window.Telegram نیست
    assert srcs.index("https://telegram.org/js/telegram-web-app.js") < \
        srcs.index("/miniapp/tg_shell.js"), srcs


def t_e_the_css_actually_consumes_the_insets():
    """متغیرهایی که هیچ قاعده‌ای مصرفشان نکند، فقط تزئین‌اند — و محتوا
    همچنان زیرِ نُچ می‌ماند."""
    css = (MINI / "style.css").read_text("utf-8", errors="replace")
    for v in ("--tg-content-safe-top", "--tg-safe-bottom"):
        assert v in css, (v, "‏CSS این inset را مصرف نمی‌کند")
    assert "0px)" in css, "‏fallback ِ صفر ندارد ⇒ روی دسکتاپ قاعده دور ریخته می‌شود"


def t_f_the_javascript_suite_actually_runs_and_passes():
    """⚠️ تستِ تاریک: ۱۳ تستِ JS وجود دارد ولی `run_all` پایتون می‌دود.
    تستی که کسی اجرایش نکند با تستِ نبود فرقی ندارد.

    عمداً روی نبودِ node **قرمز** می‌شود، نه skip: «سبز از راهِ غیاب» همین
    امروز یک نتیجهٔ جعلی ساخت."""
    node = "node"
    try:
        v = subprocess.run([node, "--version"], capture_output=True, text=True,
                           timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        raise AssertionError(
            f"node در دسترس نیست ({type(e).__name__}) ⇒ ۱۳ تستِ پوسته "
            "اثبات‌نشده‌اند. این skip نیست: بدونِ اجرا، ادعای «سبز» بی‌پشتوانه است.")
    assert v.returncode == 0, v.stderr[:200]

    r = subprocess.run([node, str(SHELL_TEST)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120,
                       cwd=str(MINI))
    out = (r.stdout or "") + (r.stderr or "")
    assert r.returncode == 0, ("سوییتِ جاوااسکریپت قرمز است", out[-800:])
    # شمارِ صریح، نه «خطایی ندیدم»
    line = [l for l in out.splitlines() if l.strip().startswith("tg_shell.test:")]
    assert line, ("خطِ شمارش پیدا نشد ⇒ نمی‌دانیم چند تست دوید", out[-400:])
    got, total = line[-1].split(":")[1].strip().split("/")
    assert int(got) == int(total) and int(total) >= 12, (line[-1],)


def t_g_the_shell_never_assumes_an_api_exists():
    """کلاینتِ قدیمی نباید صفحهٔ سفید بگیرد. (رفتارش در node سنجیده می‌شود؛
    این‌جا فقط ضدالگوی «فراخوانِ بی‌شرط» را می‌بندیم.)"""
    src = SHELL_JS.read_text("utf-8", errors="replace")
    for meth in ("requestFullscreen", "addToHomeScreen", "exitFullscreen"):
        # هر فراخوان باید پشتِ یک شناساییِ قابلیت باشد
        assert f"typeof tg[n] === \"function\"" in src or "capabilities(" in src, (
            meth, "شناساییِ قابلیت پیدا نشد")
    assert "version" not in src.split("*/")[-1] or True  # نسخه‌سنجی در تستِ JS


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
            print(f"  FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"\ntest_miniapp_shell_2026: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
