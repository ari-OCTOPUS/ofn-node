#!/usr/bin/env python3
"""test_providers.py — call_chat_via_router (۲۰۲۶-۰۸-۱۳، رأیِ مالک).

این اپ (doctor_lite pilot) تا امروز هیچ‌وقت واقعاً اجرا نشده (ممیزیِ
۲۰۲۶-۰۸-۱۳ تأیید کرد: صفر state/log از روزِ ساخت) — پس این تست هیچ رفتارِ
زنده‌ای را نمی‌شکند. فقط تأیید می‌کند: (۱) fail-soft هیچ‌وقت raise نمی‌کند،
(۲) نگاشتِ task→tier درست است، (۳) doctor_lite فقط با فلگِ صریح از این
مسیر استفاده می‌کند.

اجرا: python test_providers.py (بدون pytest — stdlib فقط، هم‌راستا با
سبکِ خودِ providers.py).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import providers as PROV  # noqa: E402

_FAILED = []


def check(name, cond):
    mark = "✅" if cond else "❌"
    print(f"  {mark} {name}")
    if not cond:
        _FAILED.append(name)


def t_router_import_failure_is_fail_soft_not_raise():
    """اگر _ops/cortex اصلاً پیدا نشود (مسیرِ غلط)، None برگردد نه raise."""
    orig = PROV.__file__
    try:
        # شبیه‌سازی: مسیرِ فایل را به جایی بی‌ربط منتقل کن تا resolve چهار
        # سطحِ dirname به یک ریشهٔ نامعتبر برسد.
        PROV.__dict__["__file__"] = "/does/not/exist/app/providers.py"
        try:
            out = PROV.call_chat_via_router("think", "sys", "user", max_tokens=10)
            ok = out is None
        except Exception as e:  # noqa: BLE001
            ok = False
            print("    (raised instead of fail-soft:", type(e).__name__, e, ")")
        check("import-failure-returns-none-not-raise", ok)
    finally:
        PROV.__dict__["__file__"] = orig


def t_task_to_tier_mapping():
    """think → secondary (DeepSeek)، هر چیزِ دیگر (از جمله hard) → primary (Fugu)."""
    calls = []

    class _FakeModelRouter:
        @staticmethod
        def ask(task, prompt, system="", max_tokens=400, tier=None):
            calls.append((task, tier))
            return {"ok": True, "text": "stub", "tier": tier, "model": "stub-model"}

    sys.modules["model_router"] = _FakeModelRouter()
    try:
        PROV.call_chat_via_router("think", "s", "u")
        PROV.call_chat_via_router("hard", "s", "u")
    finally:
        sys.modules.pop("model_router", None)
    check("think-maps-to-secondary", calls[0] == ("doctor_lite_think", "secondary"))
    check("hard-maps-to-primary", calls[1] == ("doctor_lite_hard", "primary"))


def t_denied_or_malformed_response_is_none_not_crash():
    class _FakeModelRouterDeny:
        @staticmethod
        def ask(*a, **k):
            return {"ok": False, "reason": "quota_daily-cap"}

    sys.modules["model_router"] = _FakeModelRouterDeny()
    try:
        out = PROV.call_chat_via_router("think", "s", "u")
    finally:
        sys.modules.pop("model_router", None)
    check("denied-router-call-returns-none", out is None)


def t_doctor_lite_defaults_to_direct_path_when_flag_off():
    """پیش‌فرض (بدون DOCTOR_LITE_USE_CENTRAL_ROUTER=1) نباید اصلاً import model_router کند."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import doctor_lite as DL  # noqa: E402
    os.environ.pop("DOCTOR_LITE_USE_CENTRAL_ROUTER", None)

    called_direct = []

    class _FakePROV:
        @staticmethod
        def route(task):
            return "deepseek"

        @staticmethod
        def call_chat(p, system, user, max_tokens=800):
            called_direct.append(p)
            return {"text": "[HARD] test?", "usage": {}}

        @staticmethod
        def call_chat_via_router(*a, **k):
            raise AssertionError("نباید صدا زده شود وقتی فلگ خاموش است")

    orig = DL.PROV
    DL.PROV = _FakePROV()
    try:
        out = DL.think("topic", "some web findings", live=True)
        check("flag-off-uses-direct-path", called_direct == ["deepseek"])
        check("flag-off-result-has-hard-question", out.get("hard_question") == "test?")
    finally:
        DL.PROV = orig


if __name__ == "__main__":
    tests = [
        t_router_import_failure_is_fail_soft_not_raise,
        t_task_to_tier_mapping,
        t_denied_or_malformed_response_is_none_not_crash,
        t_doctor_lite_defaults_to_direct_path_when_flag_off,
    ]
    for t in tests:
        t()
    print()
    if _FAILED:
        print(f"❌ test_providers: {len(_FAILED)} FAILED: {_FAILED}")
        sys.exit(1)
    print(f"✅ test_providers: {len(tests)} groups, all checks passed")
    sys.exit(0)
