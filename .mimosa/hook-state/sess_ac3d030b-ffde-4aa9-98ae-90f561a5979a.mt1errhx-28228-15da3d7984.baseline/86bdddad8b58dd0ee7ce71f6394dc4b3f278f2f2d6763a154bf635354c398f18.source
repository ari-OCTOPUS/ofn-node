#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_epistemic_c6c7.py — read-only panel (C6) + shadow run harness (C7).

C6: GET /api/epistemic panel — فقط‌خواندنی، may_execute همیشه False.
C7: shadow_run harness — bounded health-check، digest برای tamper-evidence.
"""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for _p in (str(_OPS), str(_OPS / "tests"), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
ENV = harness.setup("epistemic-c6c7")


# ---------------------------------------------------------------------------
# C6 — read-only panel
# ---------------------------------------------------------------------------
def t_panel_returns_state_dict():
    from miniapp_state import get_epistemic_state
    st = get_epistemic_state()
    assert st["status"] in ("ok", "error")
    if st["status"] == "ok":
        assert st["schema_version"] == "epistemic.panel.v1"
        assert st["adr"] == "ADR-039"
        assert st["may_execute"] is False


def t_panel_may_execute_always_false():
    """invariant #10: پنل هرگز may_execute=True نمی‌دهد (حتی در خطا)."""
    from miniapp_state import get_epistemic_state
    st = get_epistemic_state()
    assert st.get("may_execute") is False


def t_panel_dispatch_registered():
    """مسیر /api/epistemic در dispatch_api ثبت شده."""
    from miniapp_state import dispatch_api
    code, body, ct = dispatch_api("/api/epistemic")
    assert code == 200
    assert ct == "application/json; charset=utf-8"
    import json
    data = json.loads(body.decode("utf-8"))
    assert data["may_execute"] is False


def t_panel_dispatch_unknown_404():
    """sanity: مسیر ناشناخته همچنان ۴۰۴."""
    from miniapp_state import dispatch_api
    code, _, _ = dispatch_api("/api/bogus-epistemic")
    assert code == 404


def t_gateway_read_api_includes_epistemic():
    """READ_API_PATHS شامل /api/epistemic است (owner-auth لازم)."""
    from miniapp_gateway import READ_API_PATHS
    assert "/api/epistemic" in READ_API_PATHS


def t_panel_shows_gate_status_honestly():
    """پنل وضعیتِ دروازه را صادقانه نشان میدهد (NO-GO + safety passed)."""
    from miniapp_state import get_epistemic_state
    st = get_epistemic_state()
    if st["status"] == "ok":
        g = st["gate"]
        assert g["safety_criteria_passed"] is True
        assert g["efficacy_threshold_met"] is False
        assert "NO-GO" in g["benchmark_verdict"]


# ---------------------------------------------------------------------------
# C7 — shadow run harness
# ---------------------------------------------------------------------------
def t_shadow_run_short_produces_report():
    from epistemics.shadow_run import run_shadow, format_report
    # run بسیار کوتاه با clock/sleep کنترل‌شده — بدون انتظارِ واقعی
    t = [0.0]
    def fake_clock():
        t[0] += 1.0
        return t[0]
    def fake_sleep(s):
        pass
    rep = run_shadow(seconds=3.0, tick_interval=1.0,
                     clock=fake_clock, sleep=fake_sleep)
    assert rep.n_ticks >= 1
    assert rep.may_execute_ever_true is False   # invariant
    assert rep.digest != ""
    txt = format_report(rep)
    assert "Shadow Run" in txt


def t_shadow_report_signing_is_tamper_evident():
    """دو run با دادهٔ یکسان → digest یکسان؛ دادهٔ متفاوت → digest متفاوت."""
    from epistemics.shadow_run import ShadowReport, ShadowTick
    tk = [ShadowTick(t=1.0, cycle_label=1, chain_ok=True, chain_n=0,
                     invariants_count=10, may_execute=False)]
    r1 = ShadowReport(1.0, 2.0, 1.0, 1, tk, 10, True, False, "").sign()
    r2 = ShadowReport(1.0, 2.0, 1.0, 1, tk, 10, True, False, "").sign()
    assert r1.digest == r2.digest   # deterministic
    tk2 = [ShadowTick(t=1.0, cycle_label=1, chain_ok=False, chain_n=0,
                      invariants_count=10, may_execute=False)]
    r3 = ShadowReport(1.0, 2.0, 1.0, 1, tk2, 10, True, False, "").sign()
    assert r3.digest != r1.digest   # tamper → digest متفاوت


def t_shadow_may_execute_violation_flagged():
    """اگر (به‌فرض) may_execute True شد، گزارش_flag می‌شود ( نباید رخ دهد)."""
    from epistemics.shadow_run import format_report, ShadowReport, ShadowTick
    tk = [ShadowTick(t=1.0, cycle_label=1, chain_ok=True, chain_n=0,
                     invariants_count=10, may_execute=True)]
    rep = ShadowReport(1.0, 2.0, 1.0, 1, tk, 10, True, True, "")
    txt = format_report(rep)
    assert "INVARIANT VIOLATION" in txt


TESTS = [
    t_panel_returns_state_dict,
    t_panel_may_execute_always_false,
    t_panel_dispatch_registered,
    t_panel_dispatch_unknown_404,
    t_gateway_read_api_includes_epistemic,
    t_panel_shows_gate_status_honestly,
    t_shadow_run_short_produces_report,
    t_shadow_report_signing_is_tamper_evident,
    t_shadow_may_execute_violation_flagged,
]

if __name__ == "__main__":
    failed = 0
    for _t in TESTS:
        try:
            _t()
            print(f"  PASS  {_t.__name__}")
        except Exception as exc:
            import traceback
            print(f"  FAIL  {_t.__name__}: {exc}")
            traceback.print_exc()
            failed += 1
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(failed)
