#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Follow-up regressions for 2026-08-07 deep-scan leftovers.

These are narrow source/behavior checks for fixes that were reported as still open:
read-gate hardening, thread-safe cache, action spam limit, dashboard body cap,
PF table wrapping/orphan timer cleanup, and neural effect-shadow applied observability.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("deep-scan-followups-20260807")
OPS = Path(__file__).resolve().parent.parent


def _load(rel: str, name: str):
    p = OPS / rel
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.path.insert(0, str(p.parent))
    spec.loader.exec_module(mod)
    return mod


def t_miniapp_state_cache_has_a_lock_and_uses_it():
    ms = _load("telegram_center/miniapp_state.py", "follow_ms")
    assert hasattr(ms, "_CACHE_LOCK"), "کشِ ThreadingHTTPServer باید lock داشته باشد"
    src = Path(ms.__file__).read_text("utf-8")
    assert "with _CACHE_LOCK:" in src, "خواندن/نوشتن _CACHE باید زیر lock باشد"


def t_gateway_read_gate_zero_is_not_enough_without_dev_optin():
    mg = _load("telegram_center/miniapp_gateway.py", "follow_mg")
    old = {k: os.environ.get(k) for k in (mg.READ_GATE_FLAG, "OCTOPUS_MINIAPP_ALLOW_UNAUTH_READ_DEV")}
    try:
        os.environ[mg.READ_GATE_FLAG] = "0"
        os.environ.pop("OCTOPUS_MINIAPP_ALLOW_UNAUTH_READ_DEV", None)
        assert mg.read_gate_enabled() is True, "env=0 به‌تنهایی نباید READ API عمومی را باز کند"
        os.environ["OCTOPUS_MINIAPP_ALLOW_UNAUTH_READ_DEV"] = "1"
        assert mg.read_gate_enabled() is False, "بازکردن فقط با opt-in توسعه مجاز است"
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def t_gateway_fallback_redacts_bearer_and_email_patterns():
    mg = _load("telegram_center/miniapp_gateway.py", "follow_mg_redact")
    # Simulate crm import failure by removing budget path and shadowing import.
    import builtins
    real_import = builtins.__import__

    def blocked(name, *a, **kw):
        if name == "cockpit_readmodel":
            raise ImportError("simulated crm outage")
        return real_import(name, *a, **kw)

    builtins.__import__ = blocked
    try:
        bearer = "Bearer " + "Z" * 24
        out = mg._redact(f"auth={bearer} email=owner@example.invalid")
        assert bearer not in out, out
        assert "owner@example.invalid" not in out, out
    finally:
        builtins.__import__ = real_import


def t_live_action_rate_limiter_blocks_after_window_capacity():
    live = _load("live/server.py", "follow_live")
    live._ACTION_HITS[:] = []
    old_n = live._ACTION_MAX_PER_WINDOW
    old_w = live._ACTION_WINDOW_S
    try:
        live._ACTION_MAX_PER_WINDOW = 2
        live._ACTION_WINDOW_S = 10.0
        assert live._action_rate_limited(100.0) is False
        assert live._action_rate_limited(101.0) is False
        assert live._action_rate_limited(102.0) is True
        assert live._action_rate_limited(112.1) is False, "پنجره باید پاک شود"
    finally:
        live._ACTION_HITS[:] = []
        live._ACTION_MAX_PER_WINDOW = old_n
        live._ACTION_WINDOW_S = old_w


def t_dashboard_post_has_body_size_guard():
    src = (OPS / "dashboard/server.py").read_text("utf-8")
    assert "if length > 65536:" in src and "send_response(413)" in src, \
        "POST /save باید قبل از read سقف اندازه داشته باشد"


def t_project_f_tables_are_wrapped_and_render_clears_orphan_timers():
    app = (OPS / "telegram_center/miniapp/app.js").read_text("utf-8")
    css = (OPS / "telegram_center/miniapp/style.css").read_text("utf-8")
    assert "function clearDecisionTimers()" in app
    assert "clearDecisionTimers();" in app[app.index("function render(name)"):], \
        "render جدید باید intervalهای تصمیم قبلی را پاک کند"
    pf = app[app.index("function renderPF"):app.index("function renderSystemHead")]
    assert pf.count('class="tblwrap"') >= 5, "جدول‌های PF باید wrapper موبایل داشته باشند"
    assert ".tblwrap" in css and "overflow-x:auto" in css


def t_neural_effect_shadow_applied_reflects_apply_flag_not_constant_false():
    src = (OPS / "wiring.py").read_text("utf-8")
    shadow = src[src.index('if flag("OCTOPUS_NEURAL_EFFECT_SHADOW")'):src.index('return result', src.index('if flag("OCTOPUS_NEURAL_EFFECT_SHADOW")'))]
    assert '"applied": False' not in shadow, "applied نباید vestigial constant-false بماند"
    assert '"applied": _learned_applied' in shadow, "applied باید از apply flag/learned pressure مشتق شود"
    assert 'OCTOPUS_NEURAL_LEARNED_APPLY' in shadow and 'LEARNED_PRESSURE_CAPPED_KEY' in shadow


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    status = "OK" if not failed else "FAIL"
    print(f"\n{status} test_deep_scan_followups_20260807: {len(checks)-failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
