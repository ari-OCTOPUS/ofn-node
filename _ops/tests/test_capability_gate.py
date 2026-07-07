#!/usr/bin/env python3
"""تست A3 · capability_gate / live_gate (open-decision #2 قفل‌شده).
اثبات: بسته اگر هرکدام از سه شرط غایب باشد · باز فقط با هر سه (capability ∧ LIVE_ENABLED ∧ approval) ·
calendar به‌تنهایی هیچ باز نمی‌کند · require() هر دو گیت (live+money) را زنجیر می‌کند · fail-closed."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("capability-gate")
import capability_gate as cg  # noqa: E402
from approval_channel import Approval, NotWiredStub, MockApprovalChannel  # noqa: E402

ACTION = "LEAD-20260707-009"
AMT = 50.0


def _clear():
    cg.revoke_capability()
    try:
        cg.LIVE_ENABLED_FLAG.unlink()
    except OSError:
        pass


def _cap_on():
    cg.mark_capability("test-green")


def _live_on():
    cg.LIVE_ENABLED_FLAG.parent.mkdir(parents=True, exist_ok=True)
    cg.LIVE_ENABLED_FLAG.write_text("owner", "utf-8")


def t_closed_when_not_wired():
    _clear(); _cap_on(); _live_on()                       # cap+live روشن، ولی کانال وصل نیست
    ok, why = cg.is_open(ACTION, AMT)                      # NotWiredStub پیش‌فرض
    assert ok is False and "approval" in why, why


def t_closed_without_capability():
    _clear(); _live_on()                                  # capability off
    ch = MockApprovalChannel([Approval(ACTION, AMT, "approved")])
    ok, why = cg.is_open(ACTION, AMT, ch)
    assert ok is False and "capability" in why, why


def t_closed_without_live_enabled():
    _clear(); _cap_on()                                   # LIVE_ENABLED off
    ch = MockApprovalChannel([Approval(ACTION, AMT, "approved")])
    ok, why = cg.is_open(ACTION, AMT, ch)
    assert ok is False and "LIVE_ENABLED" in why, why


def t_open_only_with_all_three():
    _clear(); _cap_on(); _live_on()
    ch = MockApprovalChannel([Approval(ACTION, AMT, "sent")])
    ok, why = cg.is_open(ACTION, AMT, ch)
    assert ok is True and why == "open", why


def t_calendar_alone_opens_nothing():
    _clear()                                              # هیچ پرچمی نیست (تاریخ هرچه باشد)
    ch = MockApprovalChannel([Approval(ACTION, AMT, "approved")])
    ok, why = cg.is_open(ACTION, AMT, ch)
    assert ok is False, why


def t_require_chains_live_then_money():
    _clear(); _cap_on(); _live_on()
    ch = MockApprovalChannel([Approval(ACTION, AMT, "approved")])
    assert cg.require(ACTION, AMT, ch)["allow"] is True   # هر دو گیت باز
    r = cg.require(ACTION, AMT, NotWiredStub())           # approval برداشته شد
    assert r["allow"] is False and r["gate"] == "live_gate", r


def t_stale_capability_marker_revoked():
    _clear(); _live_on()
    # markerِ سبز ولی fingerprintِ غلط = شبیه‌سازیِ کدِ پول که پس از سبزی تغییر کرده → بی‌اعتبار (fail-closed)
    cg.CAPABILITY_MARKER.parent.mkdir(parents=True, exist_ok=True)
    cg.CAPABILITY_MARKER.write_text('{"ts":"x","evidence":"stale","fingerprint":"deadbeef"}', "utf-8")
    ch = MockApprovalChannel([Approval(ACTION, AMT, "approved")])
    ok, why = cg.is_open(ACTION, AMT, ch)
    assert ok is False and "capability" in why, why


if __name__ == "__main__":
    failed = harness.run([
        ("بدونِ کانالِ وصل (paper) → بسته", t_closed_when_not_wired),
        ("بدونِ capability → بسته", t_closed_without_capability),
        ("بدونِ LIVE_ENABLED → بسته", t_closed_without_live_enabled),
        ("فقط با هر سه شرط → باز", t_open_only_with_all_three),
        ("تاریخ به‌تنهایی هیچ باز نمی‌کند", t_calendar_alone_opens_nothing),
        ("require زنجیرِ live_gate ∧ money_gate", t_require_chains_live_then_money),
        ("markerِ کهنه (fingerprint نامنطبق) → بی‌اعتبار", t_stale_capability_marker_revoked),
    ])
    sys.exit(1 if failed else 0)
