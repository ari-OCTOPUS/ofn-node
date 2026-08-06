#!/usr/bin/env python3
"""تست Content Studio v2 + Project-F Brain ($0 آفلاین).

Studio: درفت+self-cert، تقویم، PPV، آنالیزِ تجمیعی، محدوده halt.
Brain: control-plane + ۷ زیرعامل، HITL tiered، دو Guard، archive، ۲٪-cap.
صفر رسانه/PII. دوکلیده. محدودهٔ صبا مقدم.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("project-f")
_STUDIO = (harness.REAL_VAULT / r"03 - Projects\اونلی فنز\studio")
_BRAIN = (harness.REAL_VAULT / r"03 - Projects\اونلی فنز\brain")
for _p in (str(_STUDIO), str(_BRAIN)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from content_studio import (ContentStudio, DraftSubmission, COMPLIANCE_CHECKS)  # noqa: E402
from project_f_brain import (ProjectFBrain, Proposal, PricingResult, ArchiveEntry,  # noqa: E402
                              COMPLIANCE_RULES, ETHICS_RULES, LAMBDA_PERSIST)


# ════════════════════════════════════════════════════════════════════════════════
# Content Studio v2
# ════════════════════════════════════════════════════════════════════════════════

def t_studio_submit_draft_with_cert():
    """درفت با self-cert کامل → ثبت می‌شود."""
    st = ContentStudio()
    r = st.submit_draft("title", {c: True for c in COMPLIANCE_CHECKS})
    assert r["ok"] is True and r["status"] == "pending"


def t_studio_submit_draft_without_cert_fails():
    """self-cert ناقص → fail-closed."""
    st = ContentStudio()
    r = st.submit_draft("title", {"faceless": True})   # ناقص
    assert r["ok"] is False and "ناقص" in r["error"]


def t_studio_draft_pending_until_ari():
    """درفت تا تأییدِ آری «pending» می‌ماند (دوکلیده)."""
    st = ContentStudio()
    st.submit_draft("t", {c: True for c in COMPLIANCE_CHECKS})
    html = st.drafts_html()
    assert "pending" in html or "⏳" in html


def t_studio_no_media_in_output():
    """صفر رسانه در خروجی — فقط متادیتا."""
    st = ContentStudio()
    st.submit_draft("t", {c: True for c in COMPLIANCE_CHECKS})
    for output in [st.drafts_html(), st.main_menu(), st.rules_html()]:
        for forbidden in ("photo", "video", "media", "face.jpg", "raw"):
            assert forbidden.lower() not in output.lower(), f"رسانه لو رفت: {forbidden}"


def t_studio_halt_stops():
    """محدوده halt → بات متوقف."""
    st = ContentStudio()
    r = st.halt()
    assert st.is_halted is True
    assert "متوقف" in r


def t_studio_analytics_aggregate_only():
    """آنالیز فقط تجمیعی (صفر PII)."""
    st = ContentStudio()
    a = st.analytics_html()
    assert "churn" in a and "ARPU" in a
    for forbidden in ("name", "email", "phone", "address", "subscriber"):
        assert forbidden.lower() not in a.lower()


def t_studio_ppv_three_tiers():
    """PPV سه‌لایه از config."""
    st = ContentStudio()
    html = st.ppv_plan_html()
    assert "low" in html and "premium" in html and "mid" in html


def t_studio_geo_block_in_rules():
    """geo-block ایران در قواعد."""
    st = ContentStudio()
    r = st.rules_html()
    assert "iran" in r.lower() or "ایران" in r


# ════════════════════════════════════════════════════════════════════════════════
# Project-F Brain
# ════════════════════════════════════════════════════════════════════════════════

def t_brain_strategist():
    """Strategist: نردبانِ ارزش."""
    brain = ProjectFBrain()
    p = brain.strategist("draft-1")
    assert p.kind == "strategy" and "wall" in p.content.lower()


def t_brain_pricer_three_layer():
    """Pricer: contextual bandit سه‌لایه."""
    brain = ProjectFBrain()
    result = brain.pricer(content_type="premium", time_slot="evening")
    assert result.suggested_price > 0
    assert result.tier in ("low", "mid", "premium")
    # evening multiplier > morning
    morning = brain.pricer(time_slot="morning")
    assert result.time_multiplier > morning.time_multiplier


def t_brain_compliance_guard_drops():
    """Compliance-Guard: قاعده‌ای نشد → drop."""
    brain = ProjectFBrain()
    p = Proposal(kind="copy", content="test")
    brain.compliance_guard(p, {"faceless": True})   # ناقص
    assert p.status == "dropped" and p.compliance_passed is False


def t_brain_compliance_guard_passes():
    """Compliance-Guard: همه قواعد → pass."""
    brain = ProjectFBrain()
    p = Proposal(kind="copy", content="test")
    checks = {r: True for r in COMPLIANCE_RULES}
    brain.compliance_guard(p, checks)
    assert p.compliance_passed is True


def t_brain_ethics_guard_drops():
    """Ethics-Guard: dark-pattern → drop."""
    brain = ProjectFBrain()
    p = Proposal(kind="copy", content="test")
    brain.ethics_guard(p, {"no_dark_pattern": True})   # ناقص
    assert p.status == "dropped"


def t_brain_hitl_low_risk_to_saba():
    """HITL: low-risk → صبا."""
    brain = ProjectFBrain()
    checks = {**{r: True for r in COMPLIANCE_RULES}, **{r: True for r in ETHICS_RULES}}
    result = brain.process_draft("draft-1", checks=checks)
    routes = [r["route"] for r in result["routed_to"]]
    assert "saba" in routes


def t_brain_hitl_high_risk_to_ari():
    """HITL: high-risk → آری."""
    brain = ProjectFBrain()
    checks = {**{r: True for r in COMPLIANCE_RULES}, **{r: True for r in ETHICS_RULES}}
    result = brain.process_draft("draft-1", checks=checks, risk_override="high")
    routes = [r["route"] for r in result["routed_to"]]
    assert "ari" in routes


def t_brain_hitl_guard_fail_drops():
    """HITL: guard fail → drop."""
    brain = ProjectFBrain()
    result = brain.process_draft("draft-1", checks={})   # همه fail
    assert result["guards_passed"] is False
    assert any(r["route"] == "dropped" for r in result["routed_to"])


def t_brain_archive_learned_only():
    """آرشیو: فقط از تأییدشده‌ها یاد می‌گیرد."""
    # پاک‌سازیِ archive persisted برای تستِ ایزوله — فقط sandboxِ ماژول (PF_BRAIN_DIR)،
    # هرگز نسخهٔ داخلِ repo/vault
    import project_f_brain as _pfb
    arch_path = _pfb._archive_path()
    arch_path.unlink(missing_ok=True)
    brain = ProjectFBrain()
    brain.archive("price", "approved", 10, 15)
    brain.archive("copy", "rejected", 5, 5)
    learned = brain.learned_entries()
    assert len(learned) >= 1
    assert any(e.proposal_kind == "price" for e in learned)
    arch_path.unlink(missing_ok=True)  # cleanup


def t_brain_budget_2pct_cap():
    """۲٪-cap fail-closed."""
    brain = ProjectFBrain()
    assert brain.spend(1500) is True
    assert brain.spend(600) is False   # 1500+600 > 2000


def t_brain_lambda_persist_negative():
    """λ_persist منفی."""
    assert LAMBDA_PERSIST == -1.0


def t_brain_no_pii_in_proposals():
    """صفر PII در خروجیِ brain."""
    brain = ProjectFBrain()
    p = brain.copywriter("topic")
    for forbidden in ("name", "email", "phone", "subscriber", "fan"):
        assert forbidden.lower() not in p.content.lower()


def t_brain_no_production_import():
    """brain هیچ import از *_gate/chrono/money ندارد."""
    import project_f_brain
    src = open(project_f_brain.__file__, encoding="utf-8").read()
    forbidden = ["import chrono", "from chrono", "organ_gate", "money_gate",
                 "capability_gate", "budget_gate", "EffectorGate", "opslib"]
    for f in forbidden:
        assert f not in src, f"خطِ قرمز: {f}"


if __name__ == "__main__":
    failed = harness.run([
        # Studio
        ("[S] درفت با self-cert", t_studio_submit_draft_with_cert),
        ("[S] self-cert ناقص → fail", t_studio_submit_draft_without_cert_fails),
        ("[S] درفت pending تا آری", t_studio_draft_pending_until_ari),
        ("[S] صفر رسانه در خروجی", t_studio_no_media_in_output),
        ("[S] halt متوقف می‌کند", t_studio_halt_stops),
        ("[S] آنالیز تجمیعی", t_studio_analytics_aggregate_only),
        ("[S] PPV سه‌لایه", t_studio_ppv_three_tiers),
        ("[S] geo-block در قواعد", t_studio_geo_block_in_rules),
        # Brain
        ("[B] Strategist", t_brain_strategist),
        ("[B] Pricer سه‌لایه", t_brain_pricer_three_layer),
        ("[B] Compliance drop", t_brain_compliance_guard_drops),
        ("[B] Compliance pass", t_brain_compliance_guard_passes),
        ("[B] Ethics drop", t_brain_ethics_guard_drops),
        ("[B] HITL low→صبا", t_brain_hitl_low_risk_to_saba),
        ("[B] HITL high→آری", t_brain_hitl_high_risk_to_ari),
        ("[B] HITL guard fail→drop", t_brain_hitl_guard_fail_drops),
        ("[B] archive learned only", t_brain_archive_learned_only),
        ("[B] budget 2% cap", t_brain_budget_2pct_cap),
        ("[B] λ_persist منفی", t_brain_lambda_persist_negative),
        ("[B] صفر PII در proposals", t_brain_no_pii_in_proposals),
        ("[B] no production import", t_brain_no_production_import),
    ])
    sys.exit(1 if failed else 0)
