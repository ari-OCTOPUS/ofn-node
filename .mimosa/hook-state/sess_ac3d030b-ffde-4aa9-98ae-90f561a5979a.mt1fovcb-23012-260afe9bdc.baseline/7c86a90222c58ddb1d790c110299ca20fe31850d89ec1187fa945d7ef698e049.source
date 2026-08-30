"""
Phase 2 lead-path test -- OFFLINE (zero spend).

Forces ANTHROPIC_API_KEY="" so Worker C uses its compliant template fallback
(no live LLM call). Uses a throwaway temp DB. Simulates Worker F (lead capture,
Phase 5) by inserting lead rows, since the real pipeline is F -> C -> Gate and
both drafts.lead_id and gate_results.draft_id are FK-constrained.

Asserts the lead-path contract:
  - speed-to-lead + follow-up carry the sender-ID footer (name + ABN + opt-out)
  - Gate PASS when consent + ABN + opt-out present
  - Gate HARD_BLOCK on missing consent / missing ABN / missing opt-out
  - Gate SOFT_FLAG on ACL superlatives and on PII patterns
  - no cost_events recorded (offline => zero AUD spend)
  - orchestrator handle_enquiry / kickoff_followup wired end-to-end
"""
import os
import sys
import tempfile

# Env MUST be set before importing config (singleton reads env at import).
_TMP_DB = tempfile.mkstemp(suffix="_brushline_test.db")[1]
os.environ["BRUSHLINE_DB_PATH"] = _TMP_DB
os.environ["KILL_SWITCH_FILE"] = _TMP_DB + ".KILL"
os.environ["ANTHROPIC_API_KEY"] = ""            # force fallback -> offline, $0
os.environ["BUSINESS_NAME"] = "Sister Painting"
os.environ["BUSINESS_ABN"] = "11222333444"
os.environ["ALLOWED_OPERATOR_CHAT_IDS"] = ""    # avoid .env placeholder parse
os.environ["SPEND_CAP_PER_ACTION_AUD"] = "5.00"
os.environ["SPEND_CAP_PER_DAY_AUD"] = "20.00"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

from src.config import config
from src.database import init_db, get_connection
from src.agents.content import ContentAgent
from src.gate import ConstitutionGate
from src.models import Draft, DraftType
from src.governance import get_daily_spend_aud


def _check(label, cond):
    print(("PASS" if cond else "FAIL") + " :: " + label)
    if not cond:
        raise AssertionError(label)


def _seed_lead(lead_id, name, suburb, service):
    """Simulate Worker F (lead capture) persisting a lead (PII stays local)."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO leads
               (id, name, phone, email, suburb, service_type, source_channel,
                consent_status, notes, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (lead_id, name, "0400000000", None, suburb, service, "gbp",
             "inferred_business_relationship", "", datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def main():
    assert config.ANTHROPIC_API_KEY == "", "test must run offline"
    init_db()
    _seed_lead("lead-1", "Jordan", "Marrickville", "interior repaint")
    _seed_lead("lead-2", "Sam", "Glebe", "exterior")

    c = ContentAgent()
    g = ConstitutionGate()

    # 1) speed-to-lead: footer present (name + ABN + opt-out), body non-empty
    enquiry = {"id": "lead-1", "name": "Jordan", "suburb": "Marrickville",
               "service_type": "interior repaint", "notes": "3 bedrooms"}
    d = c.draft_speed_to_lead(enquiry)
    _check("speed-to-lead body non-empty", len(d.content) > 40)
    _check("speed-to-lead carries ABN", config.BUSINESS_ABN in d.content)
    _check("speed-to-lead carries business name", "Sister Painting" in d.content)
    _check("speed-to-lead carries opt-out", "STOP" in d.content.upper())
    _check("speed-to-lead used fallback (offline)", "fallback" in d.model_used)
    _check("speed-to-lead zero cost (offline)", d.cost_usd == 0.0)

    # 2) Gate PASS with inferred consent
    r = g.check(d, consent_verified=True)
    _check("speed-to-lead gate PASS (consent+ABN+optout)", r.status.value == "pass")

    # 3) Gate HARD_BLOCK without consent
    r2 = g.check(d, consent_verified=False)
    _check("no consent -> HARD_BLOCK", r2.status.value == "hard_block")
    _check("no consent flag present", any("SPAM_NO_CONSENT" in f for f in r2.flags))

    # 4) follow-up day 2/5/10: footer present, distinct bodies, gate PASS
    bodies = []
    for day in (2, 5, 10):
        f = c.draft_followup("lead-1", day)
        _check(f"followup d{day} carries ABN", config.BUSINESS_ABN in f.content)
        _check(f"followup d{day} carries opt-out", "STOP" in f.content.upper())
        rr = g.check(f, consent_verified=True)
        _check(f"followup d{day} gate PASS", rr.status.value == "pass")
        bodies.append(f.content)
    _check("follow-up days produce distinct copy", len(set(bodies)) == 3)

    # helper: persist a synthetic draft (Gate only sees persisted drafts)
    def gate_of(content):
        sd = Draft(draft_type=DraftType.SPEED_TO_LEAD, content=content,
                   agent_id="C_content", model_used="x")
        c._save(sd)
        return g.check(sd, consent_verified=True)

    # 5) missing ABN -> HARD_BLOCK (sender ID)
    r3 = gate_of("Hi, thanks for your enquiry. Reply STOP to opt out.")
    _check("missing ABN -> HARD_BLOCK", r3.status.value == "hard_block")
    _check("missing ABN flag", any("SENDER_ID_MISSING_ABN" in f for f in r3.flags))

    # 6) missing opt-out -> HARD_BLOCK
    r4 = gate_of("Hi, thanks for your enquiry. ABN 11222333444")
    _check("missing opt-out -> HARD_BLOCK", r4.status.value == "hard_block")
    _check("missing opt-out flag", any("NO_OPT_OUT" in f for f in r4.flags))

    # 7) ACL superlative -> SOFT_FLAG
    r5 = gate_of("We are the best and cheapest painters. ABN 11222333444. Reply STOP to opt out.")
    _check("ACL superlative -> SOFT_FLAG", r5.status.value == "soft_flag")
    _check("ACL acl_ok False", r5.acl_ok is False)

    # 8) PII pattern (email) -> SOFT_FLAG
    r6 = gate_of("Email me at jordan@example.com. ABN 11222333444. Reply STOP to opt out.")
    _check("PII email -> SOFT_FLAG", r6.status.value == "soft_flag")
    _check("PII privacy_ok False", r6.privacy_ok is False)

    # 9) offline => zero AUD spend recorded
    _check("zero daily spend (offline, no LLM)", get_daily_spend_aud() == 0.0)

    # 10) orchestrator wiring (offline): stub absent SDKs, run both paths
    import types
    fake_anthropic = types.ModuleType("anthropic")
    fake_anthropic.Anthropic = object          # never instantiated (key="")
    sys.modules.setdefault("anthropic", fake_anthropic)
    sys.modules.setdefault("httpx", types.ModuleType("httpx"))
    from src.orchestrator import Orchestrator
    orch = Orchestrator()

    enq = {"id": "lead-2", "name": "Sam", "suburb": "Glebe",
           "service_type": "exterior", "source_channel": "gbp"}
    res = orch.handle_enquiry(enq)
    _check("orch.handle_enquiry status drafted", res["status"] == "drafted")
    _check("orch.handle_enquiry gate PASS", res["gate_status"] == "pass")
    _check("orch.handle_enquiry content has ABN", config.BUSINESS_ABN in res["content"])

    fres = orch.kickoff_followup("lead-2", 5)
    _check("orch.kickoff_followup gate PASS (consent default)", fres["gate_status"] == "pass")
    fblock = orch.kickoff_followup("lead-2", 5, consent_verified=False)
    _check("orch.kickoff_followup HARD_BLOCK when consent=False",
           fblock["gate_status"] == "hard_block")

    print("\nALL LEAD-PATH CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    finally:
        for p in (_TMP_DB, _TMP_DB + "-wal", _TMP_DB + "-shm", _TMP_DB + ".KILL"):
            try:
                os.remove(p)
            except OSError:
                pass
