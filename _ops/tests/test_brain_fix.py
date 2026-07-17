"""test_brain_fix.py — 2026-07-15: مغزِ پولیِ شکسته درست شد (offline).
باگ: synthesize به GLMِ بی‌کلید می‌رفت → fail → محلیِ آشغال. فیکس: routerِ کلید-آگاه
(اگر tier کلید ندارد، سراغِ tierِ پولیِ کلیددار برو) + aliasِ کلید (FUGU_API_KEY/GLM_API_KEY)."""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))
sys.path.insert(0, str(_HERE.parent / "debate"))

import harness
ENV = harness.setup("brain_fix")


def t_a_key_aware_uses_fugu_when_glm_absent():
    """synthesize → tierِ secondary(GLM) می‌خواهد ولی کلید ندارد → باید primary(Fugu) را امتحان کند."""
    import model_router as mr
    tried = []

    def fake_ask_paid(tier, *a, **k):
        tried.append(tier)
        return ({"text": "x", "tier": tier, "model": "fugu", "cost_usd": 0.0}
                if tier == "primary" else None)

    orig_ap, orig_kp = mr._ask_paid, mr.keys_present
    mr._ask_paid = fake_ask_paid
    mr.keys_present = lambda: {"fugu": True, "glm": False, "deepseek": False}
    try:
        r = mr.ask("synthesize", "hi", max_tokens=10)
        assert r.get("ok") and r.get("tier") == "primary", r
        assert "secondary" not in tried, tried    # GLMِ بی‌کلید skip شد
        assert "primary" in tried                  # Fugu امتحان شد
    finally:
        mr._ask_paid, mr.keys_present = orig_ap, orig_kp


def t_b_no_paid_key_falls_to_local_loudly():
    """هیچ کلیدِ پولی → بدونِ سوزاندنِ callِ الکی، مستقیم محلی + دلیلِ صادق."""
    import model_router as mr
    burned = []
    orig_ap, orig_kp, orig_local, orig_gate = mr._ask_paid, mr.keys_present, mr.local_llm.ask, mr.paid_gate
    mr._ask_paid = lambda *a, **k: burned.append(1) or None
    mr.keys_present = lambda: {"fugu": False, "glm": False, "deepseek": False}
    mr.paid_gate = lambda: (True, "open")          # گیت باز، ولی هیچ کلیدی نیست
    mr.local_llm.ask = lambda *a, **k: {"text": "local", "model": "qwen", "cost_usd": 0.0}
    try:
        r = mr.ask("synthesize", "hi", max_tokens=10)
        assert r.get("ok"), r
        assert r.get("fallback_from", "").endswith("no-paid-key"), r
        assert burned == []                        # هیچ callِ پولیِ الکی سوزانده نشد (کلید-آگاه)
    finally:
        mr._ask_paid, mr.keys_present, mr.local_llm.ask, mr.paid_gate = orig_ap, orig_kp, orig_local, orig_gate


def t_c_client_has_key_aliases():
    """client حالا FUGU_API_KEY / GLM_API_KEY را هم می‌خواند (نامِ مالک)."""
    from client import _PROVIDER_REGISTRY
    assert _PROVIDER_REGISTRY["sakana"]["env_key_alias"] == "FUGU_API_KEY"
    assert _PROVIDER_REGISTRY["glm"]["env_key_alias"] == "GLM_API_KEY"


def _lf_env(mr, local_ret):
    """نصبِ محیطِ محلی-اول: local mock + paid spy؛ برگرداندنی."""
    import os
    burned = []
    orig = (mr._ask_paid, mr.keys_present, mr.local_llm.ask, mr.paid_gate)
    mr._ask_paid = lambda tier, *a, **k: burned.append(tier) or {
        "text": "paid answer long enough", "tier": tier, "model": "spy", "cost_usd": 0.01}
    mr.keys_present = lambda: {"fugu": True, "glm": True, "deepseek": False}
    mr.paid_gate = lambda: (True, "open")
    mr.local_llm.ask = lambda prompt, system="", max_tokens=400, opener=None: local_ret
    os.environ["CORTEX_LOCAL_FIRST"] = "1"
    return burned, orig


def _lf_restore(mr, orig):
    import os
    mr._ask_paid, mr.keys_present, mr.local_llm.ask, mr.paid_gate = orig
    os.environ.pop("CORTEX_LOCAL_FIRST", None)


def t_d_local_first_good_output_skips_paid():
    """محلی-اول (2026-07-16): خروجیِ محلیِ باکیفیت → صفر callِ پولی + برچسبِ local_first.
    2026-07-18: فیکسچر «x×120» زیرِ گیتِ ساختاریِ جدید به‌درستی degenerate است —
    جایگزین با متنِ واقعاً باکیفیت (چندواژه، غیرِ echo)؛ نیتِ تست همان است."""
    import model_router as mr
    good = {"text": ("پیشنهادِ نخست: سنجشِ دوره‌ایِ کیفیتِ پاسخ با معیارِ ساختاری\n"
                     "پیشنهادِ دوم: ثبتِ نتیجه در ژورنالِ حافظه برای مرورِ هفتگی"),
            "model": "qwen7b", "tier": "local", "cost_usd": 0.0}
    burned, orig = _lf_env(mr, good)
    try:
        r = mr.ask("synthesize", "hi", max_tokens=200)
        assert r.get("ok") and r.get("local_first") is True, r
        assert burned == [], burned                     # هیچ پولی نسوخت
    finally:
        _lf_restore(mr, orig)


def t_e_local_first_short_output_escalates():
    """خروجیِ محلیِ کوتاه/بی‌کیفیت → گیتِ کیفیت رد → escalation به پولی (رفتارِ امروز)."""
    import model_router as mr
    short = {"text": "کوتاه", "model": "qwen7b", "tier": "local", "cost_usd": 0.0}
    burned, orig = _lf_env(mr, short)
    try:
        r = mr.ask("synthesize", "hi", max_tokens=200)
        assert r.get("ok") and not r.get("local_first"), r
        assert burned, "خروجیِ بی‌کیفیت باید به پولی escalate شود"
    finally:
        _lf_restore(mr, orig)


def t_f_primary_never_local_first():
    """کارِ بزرگ (primary: plan/deep/orchestrate) هرگز محلی-اول نمی‌شود — مستقیم API."""
    import model_router as mr
    good = {"text": "x" * 500, "model": "qwen7b", "tier": "local", "cost_usd": 0.0}
    burned, orig = _lf_env(mr, good)
    try:
        r = mr.ask("orchestrate", "hi", max_tokens=200)
        assert r.get("ok") and not r.get("local_first"), r
        assert burned == ["primary"], burned            # مستقیم مغزِ بزرگ
    finally:
        _lf_restore(mr, orig)


if __name__ == "__main__":
    for f in (t_a_key_aware_uses_fugu_when_glm_absent, t_b_no_paid_key_falls_to_local_loudly,
              t_c_client_has_key_aliases, t_d_local_first_good_output_skips_paid,
              t_e_local_first_short_output_escalates, t_f_primary_never_local_first):
        f()
        print("ok", f.__name__)
    print("PASS test_brain_fix")
