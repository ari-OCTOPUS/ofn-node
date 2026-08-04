#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_miniapp_registration.py — سبزی که چهار روز دروغ گفت.

فاز ۲ (۲۰۲۶-۰۸-۰۴). `owner_readiness._check_miniapp` فقط دو چیز می‌سنجید:
آدرس `https://` است، و پورتِ گیت‌وی جواب می‌دهد. هر دو **دسترس‌پذیری**.
هیچ‌کدام نمی‌پرسید «تلگرام اصلاً این اپ را می‌شناسد؟» — و جوابِ زنده این بود:

    getMe().has_main_web_app = False   ·   getChatMenuButton().type = "commands"

و شاهدِ رفتاری: در ۸۸ ساعت لاگ، **یک** نشستِ احرازشده.

ناوردیِ مرکزیِ این فایل: **`unknown` هرگز `ok` نمی‌شود.** اگر شبکه جواب
ندهد، حکمِ «ثبت شده» صادر نمی‌شود — همان اشتباهی که اجازه داد چهار روز سبز
ببینیم. (درسِ ثبت‌شده: «نبودِ داده حکم نیست».)
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("miniapp-reg")
sys.path.insert(0, str(harness.REAL_VAULT / "_ops" / "telegram_center"))

import miniapp_registration as mr  # noqa: E402

QUICK = "https://div-corps-example.trycloudflare.com"
STABLE = "https://app.example.com"


def _fetch(*, main_app=False, menu="commands", menu_url=""):
    def f(method):
        if method == "getMe":
            return {"ok": True, "result": {"id": 1, "is_bot": True,
                                           "has_main_web_app": main_app}}
        if method == "getChatMenuButton":
            r = {"type": menu}
            if menu == "web_app":
                r["web_app"] = {"url": menu_url}
            return {"ok": True, "result": r}
        raise AssertionError(f"متدِ غیرمنتظره: {method}")
    return f


def t_a_only_read_only_methods_are_called():
    """⚠️ این ماژول در مسیرِ گزارشِ آمادگی است. اگر روزی متدی صدا بزند که
    چیزی را **تغییر** دهد، یک ابزارِ تشخیصی به یک عاملِ تغییر تبدیل شده."""
    seen = []

    def f(method):
        seen.append(method)
        return _fetch()(method)

    mr.status(f, url=QUICK)
    assert set(seen) <= {"getMe", "getChatMenuButton"}, seen

    # ⚠️ نسخهٔ اولِ این گارد زیررشته‌ای بود و روی **docstring ِ خودم** افتاد —
    # جایی که `setChatMenuButton` را فقط **توضیح** داده بودم. پنجمین باری
    # است که همین ضدالگو در این ریپو می‌زند. AST، و صریحاً بدونِ docstring:
    # کدِ خوب دربارهٔ خودش حرف می‌زند، پس assert ِ متنی به توضیح می‌خورد نه
    # به کد.
    import ast
    src = (harness.REAL_VAULT / "_ops" / "telegram_center"
           / "miniapp_registration.py").read_text("utf-8", errors="replace")
    tree = ast.parse(src)
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d is not None:
                docstrings.add(d)
    MUTATING = {"setChatMenuButton", "sendMessage", "editMessageText",
                "deleteMessage", "setMyCommands", "answerCallbackQuery",
                "setWebhook", "editMessageReplyMarkup"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in docstrings:
                continue
            assert node.value not in MUTATING, (
                node.value, f"متدِ تغییردهنده در کدِ ماژولِ فقط‌خواندنی "
                            f"(خطِ {node.lineno})")


def t_b_the_live_state_is_reported_as_unregistered():
    """همان چیزی که تلگرام امروز واقعاً گفت."""
    d = mr.status(_fetch(main_app=False, menu="commands"), url=QUICK)
    assert d["state"] == "unregistered", d
    assert d["ok"] is False
    assert d["has_main_web_app"] is False
    assert d["why"], "دلیل خالی است — مالک نمی‌فهمد چه کند"


def t_c_a_registered_main_app_is_green():
    d = mr.status(_fetch(main_app=True), url=STABLE)
    assert d["state"] == "registered" and d["ok"] is True, d


def t_d_a_matching_menu_button_is_green():
    d = mr.status(_fetch(menu="web_app", menu_url=STABLE + "/miniapp"),
                  url=STABLE)
    assert d["state"] == "registered" and d["ok"] is True, d
    assert d["menu_matches_live_url"] is True, d


def t_e_a_menu_pointing_elsewhere_is_a_mismatch_not_green():
    """⚠️ بدترین حالتِ ممکن برای مالک: دکمه هست، کلیک می‌کند، و به گیت‌وی
    نمی‌رسد. اگر این «سبز» شمرده شود، دقیقاً همان «هرکاری می‌کنم دیده
    نمی‌شود» است — این بار با یک چراغِ سبز بالای سرش."""
    d = mr.status(_fetch(menu="web_app", menu_url="https://old-host.example/x"),
                  url=STABLE)
    assert d["state"] == "mismatch", d
    assert d["ok"] is False, "ناهم‌خوانی سبز شمرده شد"


def t_f_unknown_is_never_ok():
    """قلبِ فایل. شبکه که جواب ندهد، حکم صادر نمی‌شود."""
    def boom(method):
        raise OSError("شبکه قطع")

    d = mr.status(boom, url=STABLE)
    assert d["state"] == "unknown", d
    assert d["ok"] is False, "نبودِ داده به «سالم» ترجمه شد"
    assert d["has_main_web_app"] is None, "مقدارِ ساختگی جای نامعلوم نشست"


def t_g_a_malformed_reply_is_unknown_not_green():
    d = mr.status(lambda m: {"ok": False, "description": "x"}, url=STABLE)
    assert d["state"] == "unknown" and d["ok"] is False, d


def t_h_an_ephemeral_host_is_flagged():
    """میزبانی که هر ری‌استارت عوض می‌شود، ساختاراً ثبت‌شدنی نیست."""
    for u in ("https://a-b-c.trycloudflare.com", "https://x.ngrok-free.app"):
        d = mr.status(_fetch(), url=u)
        assert d["ephemeral_host"] is True, (u, d)
    d = mr.status(_fetch(), url=STABLE)
    assert d["ephemeral_host"] is False, d


def t_i_the_url_is_never_returned_or_printed():
    """§۱۰ — آدرسِ مینی‌اپ در این پروژه secret طبقه‌بندی شده."""
    secret = "https://super-secret-host-4821.trycloudflare.com"
    d = mr.status(_fetch(menu="web_app", menu_url=secret), url=secret)
    blob = repr(d) + mr.summary_line(d)
    assert "super-secret-host-4821" not in blob, ("آدرس نشت کرد", blob[:300])


def t_k_the_menu_button_is_read_in_the_owners_chat_scope():
    """⚠️ اندازه‌گیریِ زندهٔ ۰۸-۰۴: `setChatMenuButton` روی دامنهٔ **پیش‌فرض**
    `ok:true` می‌دهد و **هیچ اثری ندارد** — خواندنِ بعدی هنوز `commands`
    برمی‌گرداند. همان فراخوان با `chat_id` ِ صریح کار می‌کند.

    پس اگر این ماژول دامنهٔ پیش‌فرض را بخواند، دکمه‌ای که واقعاً روی چتِ
    مالک نشسته را نمی‌بیند و ❌ ِ کاذب می‌دهد — دقیقاً برعکسِ سبزِ دروغینی
    که برای رفعش ساخته شد. یک گاردِ اندازه‌گیری که در جهتِ مخالف دروغ بگوید،
    همان‌قدر بی‌فایده است."""
    src = (harness.REAL_VAULT / "_ops" / "telegram_center"
           / "miniapp_registration.py").read_text("utf-8", errors="replace")
    import ast
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "_default_fetch")
    seg = ast.get_source_segment(src, fn) or ""
    assert "getChatMenuButton" in seg and "TELEGRAM_OWNER_CHAT_ID" in seg, (
        "دکمهٔ منو در دامنهٔ پیش‌فرض خوانده می‌شود ⇒ منفیِ کاذب")
    assert "chat_id" in seg, seg[:200]


def t_j_the_readiness_report_consumes_this():
    """⚠️ ماژولی که هیچ‌کس صدایش نمی‌زند یک «قابلیتِ تاریک» است — و این یکی
    مخصوصاً، چون دقیقاً برای تصحیحِ یک گزارشِ دروغ ساخته شده."""
    ro = (harness.REAL_VAULT / "_ops" / "telegram_center"
          / "owner_readiness.py").read_text("utf-8", errors="replace")
    assert "miniapp_registration" in ro, (
        "گزارشِ آمادگی هنوز فقط دسترس‌پذیری را می‌سنجد ⇒ همان سبزِ دروغین")


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
    print(f"\ntest_miniapp_registration: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
