#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_capability_bridge.py — «بله» ِ مالک باید به یک قابلیتِ واقعی برسد.

VQ-GRANT-IS-NOT-CAPABILITY-001 (۲۰۲۶-۰۸-۰۴).

اندازه‌گیری روی دفترِ زنده: **۳۶ درخواست همه `pending`، ۴ پاسخ همه `granted`**.
مالک «بله» گفته بود و هیچ کدی آن را مصرف نمی‌کرد. خودِ `approval_channel`
اعتراف می‌کرد: «تا وقتی ابزار واقعاً وصل نشود، این فقط یک رأی است نه یک
قابلیت.» پس اختاپوس ۳۶ بار همان چیز را خواست.

**کشفِ تعیین‌کننده:** آن قابلیت از قبل وجود داشت و **روشن بود**. هر ۳۶
درخواست «بخوان، پچ بزن، تست کن» می‌خواستند، و `cortex/code_autonomy` دقیقاً
همان را می‌دهد — با تستِ سایه‌ای، هشت گیتِ هم‌زمان، و کیل‌سوییچِ خودکار — و
`active()` همان لحظه `True` بود.

پس اختاپوس نسخهٔ **خام** چیزی را گدایی می‌کرد که نسخهٔ **امنش** را داشت.
`capabilities.py` همان خبر است.
"""
import ast
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("capability-bridge")
sys.path.insert(0, str(harness.REAL_VAULT / "_ops"))
import capabilities as cap  # noqa: E402

SRC = (harness.REAL_VAULT / "_ops" / "capabilities.py").read_text("utf-8", errors="replace")


def t_a_status_never_raises_and_has_the_shape():
    s = cap.status()
    assert s["schema"] == cap.SCHEMA
    for k in ("قابلیت‌ها", "رأی‌های_مالک", "شل_خام_چرا_نه"):
        assert k in s, (k, list(s))


def t_b_a_capability_is_gated_by_its_own_gate_not_by_the_grant():
    """⚠️ ناوردیِ ایمنیِ مرکزی: رأیِ مالک **شرطِ لازم** است نه کافی. اگر
    گیتِ خودِ قابلیت بسته باشد، هیچ `granted` ای بازش نمی‌کند."""
    calls = {"n": 0}

    def _closed():
        calls["n"] += 1
        return False, "بسته برای تست"

    spec = cap.REGISTRY["code.patch_and_test"]
    old = spec["gate_fn"]
    spec["gate_fn"] = _closed
    try:
        s = cap.status()
        assert calls["n"] >= 1, "گیتِ قابلیت اصلاً صدا زده نشد"
        c = s["قابلیت‌ها"]["code.patch_and_test"]
        assert c["در_دسترس"] is False, (
            "گیت بسته بود ولی قابلیت «در دسترس» اعلام شد — رأیِ مالک نباید "
            "گیت را دور بزند")
        assert "code.patch_and_test" not in cap.available()

        # ⚠️ و این‌جا موردِ **باربر**، که نسخهٔ اول نداشت و جهشِ خطرناک را
        # زنده گذاشت: بالا فقط گیتِ بسته را می‌سنجید، ولی روی درختِ زنده
        # `any_granted` **درست** است. پس جهشِ
        #     "در_دسترس": bool(ok)  →  bool(ok) or any_granted
        # با گیتِ بسته + رأیِ granted باید قرمز شود — و اگر رأیِ مالک را هم
        # صفر کنیم دیگر تفکیک‌پذیر نیست. یعنی باید **هر دو حالت** را ببندیم:
        # گیتِ بسته با رأیِ granted ⇒ همچنان بسته.
        _og = cap.granted_verdicts
        cap.granted_verdicts = lambda: {"هرچیزی": "granted"}
        try:
            c2 = cap.status()["قابلیت‌ها"]["code.patch_and_test"]
            assert c2["در_دسترس"] is False, (
                "با گیتِ **بسته** و رأیِ **granted**، قابلیت باز اعلام شد — "
                "یعنی `granted` گیت را دور می‌زند. این خطرناک‌ترین رگرسیونِ "
                "ممکن در این ماژول است: رأیِ مالک شرطِ لازم است نه کافی")
            assert c2["مالک_رأیِ_مرتبط_داده"] is True, (
                "رأی باید **گزارش** شود حتی وقتی گیت بسته است — وگرنه مالک "
                "نمی‌فهمد چرا تأییدش اثر نکرد")
        finally:
            cap.granted_verdicts = _og
    finally:
        spec["gate_fn"] = old


def t_c_a_broken_gate_fails_closed():
    """گیتی که استثنا می‌دهد یعنی «نمی‌دانم» — و نمی‌دانم هرگز «بله» نیست."""
    spec = cap.REGISTRY["code.patch_and_test"]
    old = spec["gate_fn"]

    def _boom():
        raise RuntimeError("gate exploded")

    spec["gate_fn"] = _boom
    try:
        c = cap.status()["قابلیت‌ها"]["code.patch_and_test"]
        assert c["در_دسترس"] is False, "گیتِ خراب باز فرض شد"
    finally:
        spec["gate_fn"] = old


def t_d_raw_shell_is_registered_but_only_through_its_own_gate():
    """⚠️ این ادعا در ۰۸-۰۴ **عوض شد** و باید بدانیم چرا.

    نسخهٔ قبلی assert می‌کرد shell ِ خام **ثبت نشود**. مالک بعد از طرحِ
    نگرانی دوباره تأیید کرد («shell خام رو هم بازش کن»)، پس ثبت شد. تغییرِ
    یک ادعا به‌خاطرِ رأیِ مالک درست است؛ **کندکردنِ** آن نه.

    پس دندان جابه‌جا شد نه کم: به‌جای «نباید باشد»، حالا سنجیده می‌شود که
    اگر هست، **از گیتِ خودش** بیاید و نه از رأی. و گیتش باید همان تابعِ
    واقعیِ ماژول باشد، نه یک کپیِ خوش‌بین."""
    assert "shell.raw" in cap.REGISTRY, "shell ِ ثبت‌شده ناپدید شد"
    spec = cap.REGISTRY["shell.raw"]

    # گیت باید به خودِ ماژول تفویض شود، نه یک `lambda: (True, ...)` ِ راحت.
    import shell_capability as sc
    assert spec["gate_fn"]() == sc.active(), (
        "گیتِ ثبت‌شده با گیتِ واقعیِ ماژول یکی نیست — یک کپیِ خوش‌بین می‌تواند "
        "وقتی کیل‌سوییچ خورده هم «در دسترس» بگوید")

    # و با کیل‌سوییچ باید بسته شود — رفتاری، نه متنی.
    sc.KILL.write_text("guard", "utf-8")
    try:
        ok, why = spec["gate_fn"]()
        assert ok is False, ("با STOP-RAW-SHELL هنوز باز است", why)
        assert "shell.raw" not in cap.available()
    finally:
        sc.KILL.unlink(missing_ok=True)

    # هشدارِ اصلی باید بماند — «باز شد» یعنی مهارشده، نه بی‌خطر.
    assert cap._WHY_NO_SHELL.strip(), "متنِ هشدار حذف شده"
    for token in ("env", "deny-list", "§۰"):
        assert token in cap._WHY_NO_SHELL, (token, "هشدار رقیق شد")


def t_e_the_module_never_executes_anything():
    """این پل فقط **خبر** می‌دهد. اگر روزی خودش چیزی اجرا کند، همان
    shell ای می‌شود که رد شد."""
    tree = ast.parse(SRC)
    banned = {"system", "popen", "Popen", "run", "check_output", "call",
              "exec", "eval", "spawn"}
    hits = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            nm = getattr(n.func, "attr", getattr(n.func, "id", ""))
            if nm in banned:
                hits.append((nm, n.lineno))
    assert not hits, ("این ماژول نباید چیزی اجرا کند", hits)


def t_f_the_effect_ledger_closes_the_loop():
    """نیمهٔ دومِ حلقه: بدونِ ثبتِ اثر، «قابلیت داری» یک ادعاست."""
    before = len(cap.effects(limit=9999))
    cap.record_effect("code.patch_and_test", action="shadow_test", ok=True,
                      detail="تستِ گارد")
    rows = cap.effects(limit=9999)
    assert len(rows) == before + 1, (before, len(rows))
    r = rows[-1]
    assert r["capability"] == "code.patch_and_test" and r["ok"] is True
    assert r["schema"].endswith(".effect")
    p = Path(cap._ledger_path())
    assert str(harness.REAL_VAULT).lower() not in str(p).lower(), (
        "دفترِ اثر داخلِ درختِ زنده افتاد", str(p))


def t_g_the_brain_context_actually_carries_the_capability():
    """گاردِ انتها-به-انتها: پل بی‌مصرف‌کننده همان قابلیتِ تاریکی است که
    این ریپو مکرر گرفتارش شده."""
    import tool_request as tr
    src = Path(tr.__file__).read_text("utf-8", errors="replace")
    fn = next((n for n in ast.walk(ast.parse(src))
               if isinstance(n, ast.FunctionDef) and n.name == "_context"), None)
    assert fn is not None
    seg = ast.get_source_segment(src, fn) or ""
    assert "capabilities" in seg, (
        "‏_context پل را صدا نمی‌زند ⇒ مغز هرگز نمی‌فهمد چه دارد و باز هم "
        "همان چیز را می‌خواهد")
    assert "قابلیت‌هایی_که_همین_حالا_داری" in seg


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t(); passed += 1; print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__); print(f"  FAIL {t.__name__}: {e}")
    print(f"\ntest_capability_bridge: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
