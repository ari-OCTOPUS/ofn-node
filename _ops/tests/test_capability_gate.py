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


# ─── ۲۰۲۶-۰۷-۲۸: مارکر را فقط سوئیت می‌نویسد ─────────────────────────────
# تا امروز «فقط از run_all» یک **قرارداد** بود نه گارد: تابع هیچ چکی نداشت و
# همان روز کسی مارکرِ گیتِ پول را با این نثر نوشت —
#   "green-canary: 5/5 held-out canaries pass; 2 pre-existing red (…)"
# یعنی متنی که خودش به دو قرمز اعتراف می‌کرد، مجوزِ عبور از گیتِ پول شد.

def t_prose_evidence_is_rejected_as_suite_proof():
    bad = ("green-canary: 5/5 held-out canaries pass; "
           "2 pre-existing red (test_x now fixed)")
    assert cg._is_suite_evidence(bad) is False


def t_a_real_suite_list_is_accepted():
    names = ",".join(f"test_{i}.py" for i in range(cg._MIN_SUITE_FILES + 5))
    assert cg._is_suite_evidence("green: " + names) is True


def t_a_short_list_is_not_enough():
    """پنج تستِ دستچین سوئیت نیست."""
    assert cg._is_suite_evidence("green: a.py,b.py,c.py,d.py,e.py") is False


def t_an_isolated_marker_is_not_guarded():
    """تستِ ایزوله باید آزاد باشد — نمی‌تواند به گیتِ واقعی دست بزند.
    اگر این گارد آن‌جا هم می‌بست، هر تستِ پول را قرمز می‌کرد."""
    assert cg._is_live_marker() is False, cg.CAPABILITY_MARKER
    assert cg.mark_capability("green: test") is True


def t_the_marker_is_not_written_when_evidence_is_rejected():
    """fail-closed: شواهدِ بد → هیچ مارکری، نه مارکرِ ضعیف."""
    real = cg._is_live_marker
    cg._is_live_marker = lambda: True          # وانمود کن زنده است
    try:
        cg.CAPABILITY_MARKER.unlink(missing_ok=True)
        assert cg.mark_capability("نثرِ دست‌نویس") is False
        assert not cg.CAPABILITY_MARKER.exists(), "مارکر با شواهدِ بد نوشته شد"
    finally:
        cg._is_live_marker = real


if __name__ == "__main__":
    failed = harness.run([
        ("نثرِ دست‌نویس شواهدِ سوئیت نیست", t_prose_evidence_is_rejected_as_suite_proof),
        ("فهرستِ واقعیِ سوئیت پذیرفته می‌شود", t_a_real_suite_list_is_accepted),
        ("فهرستِ کوتاه کافی نیست", t_a_short_list_is_not_enough),
        ("مارکرِ ایزوله گارد نمی‌خورد", t_an_isolated_marker_is_not_guarded),
        ("شواهدِ بد → هیچ مارکری", t_the_marker_is_not_written_when_evidence_is_rejected),
        ("بدونِ کانالِ وصل (paper) → بسته", t_closed_when_not_wired),
        ("بدونِ capability → بسته", t_closed_without_capability),
        ("بدونِ LIVE_ENABLED → بسته", t_closed_without_live_enabled),
        ("فقط با هر سه شرط → باز", t_open_only_with_all_three),
        ("تاریخ به‌تنهایی هیچ باز نمی‌کند", t_calendar_alone_opens_nothing),
        ("require زنجیرِ live_gate ∧ money_gate", t_require_chains_live_then_money),
        ("markerِ کهنه (fingerprint نامنطبق) → بی‌اعتبار", t_stale_capability_marker_revoked),
    ])
    sys.exit(1 if failed else 0)
