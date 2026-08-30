"""test_central_gate_client.py — CentralGateClient + LLMRouter opt-in wiring (۲۰۲۶-۰۸-۱۳).

بدونِ pytest — همان سبکِ stdlib-only که بقیهٔ اصلاحاتِ امشب استفاده کردند،
تا بدونِ نصب چیزِ اضافه با `python test_central_gate_client.py` اجرا شود.
"""
from __future__ import annotations

import _bootstrap  # noqa: F401  — ROOT روی sys.path + stub های httpx/dotenv
import os
import sys

_FAILED = []


def check(name, cond, detail=""):
    mark = "✅" if cond else "❌"
    print(f"  {mark} {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        _FAILED.append(name)


def t_default_off_uses_direct_fugu_client():
    os.environ.pop("FUGU_VIA_CENTRAL_GATE", None)
    import importlib
    import llm.router as router_mod
    importlib.reload(router_mod)
    r = router_mod.LLMRouter()
    check("پیش‌فرض (بدونِ فلگ): self.fugu همان FuguClientِ همیشگی است",
          type(r.fugu).__name__ == "FuguClient")


def t_flag_on_uses_central_gate():
    os.environ["FUGU_VIA_CENTRAL_GATE"] = "1"
    try:
        import importlib
        import llm.router as router_mod
        importlib.reload(router_mod)
        r = router_mod.LLMRouter()
        check("با FUGU_VIA_CENTRAL_GATE=1: self.fugu می‌شود CentralGateClient",
              type(r.fugu).__name__ == "CentralGateClient")
    finally:
        os.environ.pop("FUGU_VIA_CENTRAL_GATE", None)
        import importlib
        import llm.router as router_mod
        importlib.reload(router_mod)  # حالتِ بعدی تست‌ها را کثیف نکن


def t_chat_flattens_messages_and_calls_router_with_right_tier():
    from llm.central_gate_client import CentralGateClient
    calls = []

    class _Fake:
        @staticmethod
        def ask(task, prompt, system="", max_tokens=400, tier=None):
            calls.append({"task": task, "prompt": prompt, "system": system,
                          "tier": tier, "max_tokens": max_tokens})
            return {"ok": True, "text": "central reply"}

    c = CentralGateClient(tier="primary", task="fourd_llm")
    c._import_router = staticmethod(lambda: _Fake())
    out = c.chat([{"role": "system", "content": "sys-prompt"},
                  {"role": "user", "content": "hello"}], max_tokens=222)
    check("chat() متنِ واقعی از model_router برمی‌گرداند", out == "central reply")
    check("system جدا از prompt رفته", calls and calls[0]["system"] == "sys-prompt")
    check("prompt شاملِ متنِ user است", calls and "hello" in calls[0]["prompt"])
    check("tier=primary (Fugu) درست پاس شده", calls and calls[0]["tier"] == "primary")
    check("max_tokens درست عبور کرده", calls and calls[0]["max_tokens"] == 222)


def t_chat_fail_soft_on_router_denied():
    from llm.central_gate_client import CentralGateClient

    class _FakeDenied:
        @staticmethod
        def ask(*a, **k):
            return {"ok": False, "reason": "quota_daily-cap"}

    c = CentralGateClient()
    c._import_router = staticmethod(lambda: _FakeDenied())
    out = c.chat([{"role": "user", "content": "hi"}])
    check("رد‌شدن توسطِ گیتِ مرکزی ⇒ پیامِ خطاییِ خوانا، نه exception",
          out.startswith("[CentralGate") and "quota_daily-cap" in out)


def t_chat_fail_soft_on_import_failure():
    from llm.central_gate_client import CentralGateClient

    def _boom():
        raise ImportError("no _ops here")

    c = CentralGateClient()
    c._import_router = staticmethod(_boom)
    out = c.chat([{"role": "user", "content": "hi"}])
    check("شکستِ import ⇒ پیامِ آفلاینِ خوانا، نه crash",
          out.startswith("[CentralGate offline"))


if __name__ == "__main__":
    for t in (t_default_off_uses_direct_fugu_client,
              t_flag_on_uses_central_gate,
              t_chat_flattens_messages_and_calls_router_with_right_tier,
              t_chat_fail_soft_on_router_denied,
              t_chat_fail_soft_on_import_failure):
        t()
    print()
    if _FAILED:
        print(f"❌ test_central_gate_client: {len(_FAILED)} FAILED: {_FAILED}")
        sys.exit(1)
    print("✅ test_central_gate_client: all checks passed")
    sys.exit(0)
