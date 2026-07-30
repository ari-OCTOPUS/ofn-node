#!/usr/bin/env python3
"""test_cortex_circuit_breaker.py — وصل‌کردنِ circuit_breaker به model_router (۲۰۲۶-۰۷-۲۵).

شاهدِ زندهٔ ۲۰۲۶-۰۷-۲۵: Fugu (primary، role="orchestr") ۳ ساعتِ پشتِ هم timeout شد
(۱۵ رخ در governor-alerts.md از ۱۳:۳۴ تا ۱۷:۴۱). علت: `circuit_breaker.py` کامل بود ولی
هیچ‌جا در مسیرِ پولی وصل نبود (فقط legs/ingest_adapter.py آن را صدا می‌زد). `fugu_quota`
سراسری بود (موفقیتِ GLM consecutive_failures را صفر کرد) و recovery دستی بود (STOP-FUGU).

این فیکس circuit_breaker را per-provider وصل می‌کند: بعد از N شکست (۵) باز می‌شود،
۶۰s بعد خودکار half-open، و با موفقیت به closed برمی‌گردد.

این تست پنج چیز را ثابت می‌کند:
  ۱) breaker بعد از threshold (۵) باز می‌شود و فراخوانیِ بعدی بی‌شبکه None برمی‌گرداند.
  ۲) جدا بودنِ per-provider: OPEN روی "orchestr" نباید "glm" را ببندد.
  ۳) half-open recovery با success_to_close=2 (دو موفقیت لازم برای closed).
  ۴) یکپارچگی با model_router: با mock client، شکستِ پیاپی → OPEN → skip بی‌شبکه.
  ۵) موفقیت در closed، fail_count را reset می‌کند.

سبکِ تست: قراردادِ harness.run — هر تابع با assert کار می‌کند؛ harness AssertionError را
به‌عنوان fail و Exception دیگر را به‌عنوان crash می‌گیرد.

$0 و آفلاین. صفر نوشتن در درختِ زنده (harness sandbox).
"""
import os
import sys
import time as _t
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("cb-livefix")
OPS = Path(__file__).resolve().parent.parent
for _p in (OPS / "budget", OPS / "cortex"):
    sys.path.insert(0, str(_p))

import opslib  # noqa: E402,F401
import circuit_breaker as cb  # noqa: E402

# CB module-load-time path را در sandbox بازنویسی کن (STATE_PATH در import ثابت می‌ماند).
# harness.setup()، opslib.STATE_DIR را به sandbox تنظیم می‌کند.
_CB_STATE = opslib.STATE_DIR / "circuit-state.json"
cb.STATE_PATH = _CB_STATE

# thresholds از پیش‌فرضِ circuit_breaker می‌آیند (TEST_BUDGETSِ harness بخشِ resilience
# ندارد): failure_threshold=5, cooldown_seconds=60, half_open_max=3, success_to_close=2.


def _fresh_cb():
    """پاک‌کردنِ state breaker برای هر چکِ مستقل."""
    if _CB_STATE.exists():
        _CB_STATE.unlink()


# ═══ ۱) threshold → OPEN → fail-fast بی‌شبکه ════════════════════════════════
def t1_threshold_opens_and_fails_fast():
    _fresh_cb()
    target = "orchestr"
    # ۴ شکست: هنوز closed، allow
    for i in range(4):
        r = cb.check(target)
        assert r.get("allow") is True, f"check #{i+1} باید closed/allow باشد ({r})"
        cb.record_failure(target, f"TimeoutError #{i+1}")
    assert cb.status(target).get("state") == "closed", \
        "بعد از ۴ شکست (threshold=5) هنوز closed"
    # شکستِ پنجم → OPEN
    cb.record_failure(target, "TimeoutError #5")
    assert cb.status(target).get("state") == "open", \
        f"بعد از ۵ شکست state=open (got {cb.status(target).get('state')})"
    # check بعدی باید fail-fast بدهد (بی‌شبکه)
    r = cb.check(target)
    assert not r.get("allow"), f"OPEN باید fail-fast دهد (allow={r.get('allow')})"
    assert r.get("state") == "open", f"state در پاسخ=open (got {r.get('state')})"


# ═══ ۲) per-provider جدایی ══════════════════════════════════════════════════
def t2_per_provider_isolation():
    _fresh_cb()
    orch, glm = "orchestr", "glm"
    # ۵ شکست orchestr → OPEN (threshold=5)
    for i in range(5):
        cb.check(orch)
        cb.record_failure(orch, f"TimeoutError #{i+1}")
    assert cb.status(orch).get("state") == "open", "orchestr بعد از ۵ شکست open است"
    # glm باید هنوز closed باشد
    r = cb.check(glm)
    assert r.get("allow") is True, f"glm باید مستقل closed بماند (allow={r.get('allow')})"
    assert r.get("state") == "closed", f"glm state=closed (got {r.get('state')})"
    # موفقیت glm نباید orchestr را بهبود بدهد
    cb.record_success(glm)
    assert cb.status(orch).get("state") == "open", \
        "موفقیتِ glm نباید orchestr را از open بیرون بیاورد"


# ═══ ۳) half-open recovery ═══════════════════════════════════════════════════
def t3_half_open_recovery():
    _fresh_cb()
    target = "orchestr"
    # بازشون (۵ شکست، threshold=5)
    for i in range(5):
        cb.check(target)
        cb.record_failure(target, f"fail #{i+1}")
    assert cb.status(target).get("state") == "open", "open شد"
    # شبیه‌سازیِ گذشتِ cooldown (۶۰s پیش‌فرض): opened_at_ts را به گذشته ببر
    st = cb._load_state()
    st["targets"][target]["opened_at_ts"] = _t.time() - 120  # ۲ دقیقه پیش
    cb._save_state(st)
    # حالا check باید half-open بدهد و allow کند (یک probe)
    r = cb.check(target)
    assert r.get("allow") is True, f"بعد از cooldown half-open + allow ({r})"
    assert "half" in (r.get("state") or ""), f"state نیمه‌باز (got {r.get('state')})"
    # موفقیت در half-open → نیاز به success_to_close=2 موفقیت برای closed.
    cb.record_success(target)
    assert cb.status(target).get("success_count") == 1, \
        "اولین موفقیت → success_count=1 (هنوز half-open)"
    cb.record_success(target)
    assert cb.status(target).get("state") == "closed", \
        "دومین موفقیت (success_to_close=2) → closed"


# ═══ ۴) یکپارچگی با model_router._ask_paid ══════════════════════════════════
def t4_model_router_skips_open_circuit():
    """شکستِ پیاپی → breaker OPEN → فراخوانیِ بعدی بی‌شبکه None برمی‌گرداند.

    توجه: _ask_paid در داخلِ خودش `from client import MultiProviderClient` را با
    sys.path.insert(DEBATE_DIR) اجرا می‌کند. در sandboxِ harness، debate/client.py
    کپی نشده، پس ما یک moduleِ fake را در sys.modules['client'] تزریق می‌کنیم تا
    `_ask_paid` همان را بگیرد. این الگو (sys.modules injection) از
    test_paid_router_dark_config.py می‌آید."""
    _fresh_cb()
    import types
    _saved = {"FUGU_API_KEY": os.environ.get("FUGU_API_KEY")}
    _saved_mods = {k: sys.modules.get(k) for k in ("client", "model_router",
                                                   "organ_gate", "fugu_quota")}
    try:
        os.environ["FUGU_API_KEY"] = "test-key"

        # fake client module + class که همیشه timeout می‌دهد
        class _FakeClient:
            provider = "fugu-test"
            model = "fugu-test-model"
            use_gateway = False
            subscription = "metered"
            _call_count = 0

            def __init__(self, role=None, **kw):
                # MultiProviderClient(role=...) امضای سازنده را می‌پذیرد
                self.role = role

            def est_worst_case(self, *a, **k):
                return 0.01

            def complete(self, system, prompt, max_tokens=None):
                type(self)._call_count += 1
                raise TimeoutError("The read operation timed out")

        fake_client_mod = types.ModuleType("client")
        fake_client_mod.MultiProviderClient = _FakeClient
        sys.modules["client"] = fake_client_mod

        # model_router را تازه import کن تا fake client را ببیند
        for k in list(sys.modules):
            if k in ("model_router", "organ_gate", "fugu_quota"):
                del sys.modules[k]
        import model_router as mr
        import organ_gate
        import fugu_quota

        # نقاطِ تزریق: organ_gate/fugu_quota همیشه allow؛ paid_gate باز
        organ_gate.reserve = lambda *a, **k: {"allow": True}
        organ_gate.release = lambda *a, **k: {}
        organ_gate.settle = lambda *a, **k: {}
        fugu_quota.reserve = lambda *a, **k: {"allow": True, "used": 0}
        fugu_quota.fail = lambda *a, **k: {}
        fugu_quota.ok = lambda *a, **k: {}
        mr.paid_gate = lambda: (True, "test-open")
        # breaker را به همان state-path مستقر کن
        mr._cb.STATE_PATH = _CB_STATE

        calls_before = _FakeClient._call_count
        # ۵ شکست → breaker OPEN (threshold=5 پیش‌فرض)
        for i in range(5):
            out = mr._ask_paid("primary", "prompt", "system", max_tokens=100)
            assert out is None, f"شکستِ network باید None بدهد #{i+1}"
        assert _FakeClient._call_count - calls_before == 5, \
            f"۵ بار واقعاً network صدا زده شد (got {_FakeClient._call_count - calls_before})"
        # فراخوانیِ ششم: breaker OPEN → نباید network صدا زده شود
        calls_at_open = _FakeClient._call_count
        out = mr._ask_paid("primary", "prompt", "system", max_tokens=100)
        assert out is None, "OPEN هم None برمی‌گرداند"
        assert _FakeClient._call_count == calls_at_open, \
            f"breaker OPEN: هیچ network callی نشد (got {_FakeClient._call_count - calls_at_open})"
        assert cb.status("orchestr").get("state") == "open", \
            "state در واقع orchestr=open"
    finally:
        for k, v in _saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        for k, mod in _saved_mods.items():
            if mod is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = mod


# ═══ ۵) success در مسیرِ سالم → reset ══════════════════════════════════════
def t5_success_resets_in_closed():
    _fresh_cb()
    target = "glm"
    cb.check(target)
    cb.record_failure(target, "TransientError #1")
    cb.record_failure(target, "TransientError #2")
    assert cb.status(target).get("fail_count") == 2, "fail_count=2"
    cb.record_success(target)
    assert cb.status(target).get("fail_count") == 0, \
        "موفقیت در closed، fail_count را صفر کرد"
    assert cb.status(target).get("state") == "closed", "هنوز closed ماند"


if __name__ == "__main__":
    failed = harness.run([
        ("۱ threshold→OPEN→fail-fast", t1_threshold_opens_and_fails_fast),
        ("۲ جداییِ per-provider", t2_per_provider_isolation),
        ("۳ half-open recovery", t3_half_open_recovery),
        ("۴ یکپارچگیِ model_router (skip بی‌شبکه)", t4_model_router_skips_open_circuit),
        ("۵ موفقیت در closed → reset", t5_success_resets_in_closed),
    ])
    sys.exit(1 if failed else 0)
