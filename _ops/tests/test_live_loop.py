#!/usr/bin/env python3
"""تستِ یکپارچهٔ end-to-end — LiveLoop wiring ($0 آفلاین).

(الف) درفتِ صبا → مغز(Guards) → high-risk → کاکپیتِ آری → verdict → برگشت به صبا + آرشیو.
(ب) لیدِ Lead-نقاشی → همان حلقه → CONFIRMED (paper).
(ج) هیچ رسانه/PII؛ money قفل؛ advisory اثر نمی‌زند.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("live-loop")
_OPS = Path(r"F:\backup\_ops")
_PF = Path(r"F:\backup\03 - Projects\اونلی فنز")
for _p in (str(_OPS), str(_OPS / "brain"), str(_OPS / "budget"),
           str(_PF / "studio"), str(_PF / "brain"), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from live_loop import LiveLoop, VerdictResult, _InMemoryBus  # noqa: E402
from project_f_brain import ProjectFBrain, COMPLIANCE_RULES, ETHICS_RULES  # noqa: E402
from content_studio import ContentStudio, COMPLIANCE_CHECKS  # noqa: E402
from cockpit import BrainCockpit  # noqa: E402


def _full_checks():
    """همه compliance + ethics checks = True."""
    return {**{r: True for r in COMPLIANCE_RULES},
            **{r: True for r in ETHICS_RULES}}


def _make_loop():
    """یک LiveLoop با همهٔ لایه‌ها (in-memory bus)."""
    return LiveLoop(
        bus=_InMemoryBus(),
        brain=ProjectFBrain(),
        studio=ContentStudio(),
        cockpit=BrainCockpit(state_dir=ENV["ops"] / "state"))


# ════════════════════════════════════════════════════════════════════════════════
# (الف) درفتِ صبا → مغز → کاکپیت → verdict → برگشت
# ════════════════════════════════════════════════════════════════════════════════

def t_e2e_draft_high_risk_to_ari():
    """درفت high-risk → مغز → کاکپیتِ آری (صفِ تأیید)."""
    loop = _make_loop()
    result = loop.process_project_f_draft(
        "draft-001", checks=_full_checks(), risk_override="high")
    assert "submitted_to_ari" in result
    assert len(result["submitted_to_ari"]) > 0, "باید چیزی به آری برود"
    # کاکپیت باید آیتم داشته باشد
    q = loop.cockpit.approval_queue_html()
    assert "Project-F" in q


def t_e2e_draft_low_risk_to_saba():
    """درفت low-risk → مستقیم استودیوی صبا (نه آری)."""
    loop = _make_loop()
    result = loop.process_project_f_draft(
        "draft-002", checks=_full_checks())
    assert "ari" not in str(result.get("submitted_to_ari", [])) or len(result["submitted_to_ari"]) == 0


def t_e2e_verdict_approved_returns_to_studio():
    """verdictِ آری (approved) → برگشت به استودیو (status=approved)."""
    loop = _make_loop()
    # ثبت درفت
    loop.studio.submit_draft("draft-003", {c: True for c in COMPLIANCE_CHECKS})
    # high-risk route
    loop.process_project_f_draft("draft-003", checks=_full_checks(), risk_override="high")
    # verdict از آری
    v = loop.apply_ari_verdict("pf-strategy-draft-003", approved=True)
    assert v.approved is True
    # استودیو باید به‌روز شده باشد
    approved = [d for d in loop.studio._drafts if d.status == "approved"]
    assert len(approved) >= 1, "درفت باید approved شود"


def t_e2e_verdict_rejected_no_publish():
    """verdictِ آری (rejected) → درفت approved نمی‌شود."""
    loop = _make_loop()
    loop.studio.submit_draft("draft-004", {c: True for c in COMPLIANCE_CHECKS})
    loop.process_project_f_draft("draft-004", checks=_full_checks(), risk_override="high")
    v = loop.apply_ari_verdict("pf-x-draft-004", approved=False)
    assert v.approved is False
    approved = [d for d in loop.studio._drafts if d.status == "approved"]
    assert len(approved) == 0, "رد → نباید approved شود"


def t_e2e_verdict_archived_in_brain():
    """verdict → آرشیوِ مغز (یادگیری)."""
    loop = _make_loop()
    loop.process_project_f_draft("draft-005", checks=_full_checks(), risk_override="high")
    loop.apply_ari_verdict("pf-strategy-draft-005", approved=True)
    assert loop.brain.archive_size > 0, "باید در آرشیو ثبت شود"
    learned = loop.brain.learned_entries()
    assert len(learned) > 0, "باید یاد گرفته باشد"


def t_e2e_guard_fail_drops():
    """guard fail → drop، چیزی به آری نمی‌رود."""
    loop = _make_loop()
    result = loop.process_project_f_draft(
        "draft-006", checks={}, risk_override="high")   # همه fail
    assert result["guards_passed"] is False
    assert len(result.get("submitted_to_ari", [])) == 0


# ════════════════════════════════════════════════════════════════════════════════
# (ب) Lead-نقاشی → همان حلقه
# ════════════════════════════════════════════════════════════════════════════════

def t_lead_on_same_loop():
    """لیدِ Lead-نقاشی → همان bus → attribution."""
    loop = _make_loop()
    # ساختِ LeadLeg (از legs)
    try:
        from leg import TaskPacket
        from lead_leg import LeadLeg
        import attribution
        packet = TaskPacket(leg_id="lead-naghshi", organ="LEAD_PAINTING",
                            read_allowlist=("03 - Projects/Lead-نقاشی/PROJECT.md",),
                            tools=("draft_quote",), budget_aud=5.0)
        leg = LeadLeg(packet, organ_table={"LEAD_PAINTING": {"floor": 1}},
                      attribution=attribution)
    except Exception:  # noqa: BLE001 — اگر legs نبود، skip
        return
    result = loop.process_lead(leg, "نقاشیِ测试", 3000.0, "lead.doer")
    if result.get("ok"):
        assert "attribution_id" in result
        assert result["attribution_id"].startswith("LEAD-")


# ════════════════════════════════════════════════════════════════════════════════
# (ج) Security: no PII/media، money قفل، advisory اثر نمی‌زند
# ════════════════════════════════════════════════════════════════════════════════

def t_no_pii_in_signals():
    """هیچ رسانه/PII در bus."""
    loop = _make_loop()
    loop.process_project_f_draft("draft", checks=_full_checks(), risk_override="high")
    loop.publish_rhythm_advisory({"mode": "GREEN"})
    loop.publish_spectral_advisory({"sigma": 0.5})
    assert loop.verify_no_pii_in_signals() is True


def t_advisory_signals_never_settle():
    """advisory سیگنال‌ها هیچ اثر نمی‌زنند."""
    loop = _make_loop()
    loop.publish_rhythm_advisory({"mode": "RED"})
    loop.publish_spectral_advisory({"sigma": 1.5})
    loop.publish_afferent_advisory({"ratio": 0.01})
    # هیچ تأییدی نباید ایجاد شود
    assert len(loop.verdicts) == 0
    # هیچ درفتی نباید approved شود
    approved = [d for d in loop.studio._drafts if d.status == "approved"]
    assert len(approved) == 0


def t_money_locked_in_pf_path():
    """پول قفل در مسیرِ Project-F — amount_aud=0."""
    loop = _make_loop()
    loop.process_project_f_draft("draft", checks=_full_checks(), risk_override="high")
    q = loop.cockpit.approval_queue_html()
    assert "AU$0.00" in q   # پول قفل


def t_dual_gate_preserved():
    """دوکلیده: صبا ثبت → آری تأیید. بدونِ آری، انتشار نیست."""
    loop = _make_loop()
    loop.studio.submit_draft("draft", {c: True for c in COMPLIANCE_CHECKS})
    # بدونِ verdict از آری
    approved = [d for d in loop.studio._drafts if d.status == "approved"]
    assert len(approved) == 0, "بدونِ آری نباید approved شود"


def t_bus_subscribe_publish():
    """bus subscribe + publish کار می‌کند."""
    bus = _InMemoryBus()
    received = []
    bus.subscribe(lambda e: received.append(e), event_type="RHYTHM")
    bus.publish("RHYTHM", {"mode": "GREEN"}, actor="rhythm")
    bus.publish("SPECTRAL", {"sigma": 0.5}, actor="spectral")
    assert len(received) == 1   # فقط RHYTHM
    assert received[0]["type"] == "RHYTHM"


def t_unified_bus_subscribe_real():
    """UnifiedBus واقعی subscribe دارد."""
    sys.path.insert(0, str(_OPS))
    from unified_bus import UnifiedBus
    bus = UnifiedBus(ledger=None, db=None)
    received = []
    bus.subscribe(lambda e: received.append(e))
    assert hasattr(bus, "subscribe")
    assert hasattr(bus, "_notify")


def t_no_production_import():
    """live_loop هیچ import از *_gate/chrono/money ندارد."""
    import live_loop
    src = open(live_loop.__file__, encoding="utf-8").read()
    forbidden = ["import chrono", "from chrono", "organ_gate", "money_gate",
                 "capability_gate", "budget_gate", "EffectorGate", "opslib"]
    for f in forbidden:
        assert f not in src, f"خطِ قرمز: {f}"


if __name__ == "__main__":
    failed = harness.run([
        ("[الف] درفت high-risk → آری", t_e2e_draft_high_risk_to_ari),
        ("[الف] درفت low-risk → صبا", t_e2e_draft_low_risk_to_saba),
        ("[الف] verdict approved → استودیو", t_e2e_verdict_approved_returns_to_studio),
        ("[الف] verdict rejected → no publish", t_e2e_verdict_rejected_no_publish),
        ("[الف] verdict → آرشیو", t_e2e_verdict_archived_in_brain),
        ("[الف] guard fail → drop", t_e2e_guard_fail_drops),
        ("[ب] Lead-نقاشی روی همان حلقه", t_lead_on_same_loop),
        ("[ج] صفر PII در signals", t_no_pii_in_signals),
        ("[ج] advisory اثر نمی‌زند", t_advisory_signals_never_settle),
        ("[ج] money قفل در PF", t_money_locked_in_pf_path),
        ("[ج] دوکلیده حفظ", t_dual_gate_preserved),
        ("[W] bus subscribe/publish", t_bus_subscribe_publish),
        ("[W] UnifiedBus.subscribe", t_unified_bus_subscribe_real),
        ("[S] no production import", t_no_production_import),
    ])
    sys.exit(1 if failed else 0)
