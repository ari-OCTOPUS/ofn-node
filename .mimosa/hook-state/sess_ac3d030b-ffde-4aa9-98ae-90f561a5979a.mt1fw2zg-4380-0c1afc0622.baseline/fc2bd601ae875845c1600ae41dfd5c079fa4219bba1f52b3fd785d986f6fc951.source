"""
Phase 2 review-response slice test -- OFFLINE (zero spend). [P1]

Forces ANTHROPIC_API_KEY="" so Worker C uses its compliant template fallback
(no live LLM call). Uses a throwaway temp DB.

Asserts the review-slice contract (public platform reply):
  - draft_review_response carries the business name + ABN, but NO opt-out
    (a public reply is not a direct commercial message -- Spam Act)
  - Gate PASS for a review reply even when consent_verified=False
    (consent does not apply to a public reply) -- KEY distinction vs direct
  - Gate does NOT require an opt-out on a review reply (PASS without STOP)
  - Gate STILL requires the ABN on a review reply -> HARD_BLOCK if missing
  - Gate SOFT_FLAG on ACL superlatives and on PII patterns (all types)
  - positive vs negative fallbacks are distinct in tone
  - orchestrator.kickoff_review_response wired end-to-end: sentiment -> draft
    -> Gate -> Queue, with review priority=high and SLA=120 min (2h)
  - no cost_events recorded (offline => zero AUD spend)
"""
import os
import sys
import tempfile

# Env MUST be set before importing config (singleton reads env at import).
_TMP_DB = tempfile.mkstemp(suffix="_brushline_review_test.db")[1]
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


def main():
    assert config.ANTHROPIC_API_KEY == "", "test must run offline"
    init_db()

    c = ContentAgent()
    g = ConstitutionGate()

    ABN = config.BUSINESS_ABN

    # helper: persist a synthetic REVIEW_RESPONSE draft; default consent=False to
    # prove a public reply does not need consent.
    def review_gate(content, consent=False):
        sd = Draft(draft_type=DraftType.REVIEW_RESPONSE, content=content,
                   agent_id="C_content", model_used="x")
        c._save(sd)
        return g.check(sd, consent_verified=consent)

    # 1) positive review draft: name + ABN present, NO opt-out, offline fallback
    dpos = c.draft_review_response(
        review_text="The team was tidy and the finish looks great.",
        sentiment="positive", platform="google", reviewer_name="Jordan",
        key_themes=["quality_praise", "cleanliness"],
    )
    _check("review body non-empty", len(dpos.content) > 40)
    _check("review carries ABN", ABN in dpos.content)
    _check("review carries business name", "Sister Painting" in dpos.content)
    _check("review has NO opt-out (public reply)", "STOP" not in dpos.content.upper()
           and "unsubscribe" not in dpos.content.lower())
    _check("review used fallback (offline)", "fallback" in dpos.model_used)
    _check("review zero cost (offline)", dpos.cost_usd == 0.0)

    # 2) Gate PASS on the real draft WITHOUT consent (public reply != direct msg)
    rp = g.check(dpos, consent_verified=False)
    _check("review gate PASS without consent", rp.status.value == "pass")
    _check("review spam_consent_ok True (n/a for public)", rp.spam_consent_ok is True)

    # 3) opt-out NOT required: ABN present, no STOP -> PASS
    r_noopt = review_gate("Thanks so much for the review, we appreciate it. "
                          "-- Sister Painting ABN " + ABN, consent=False)
    _check("review without opt-out still PASS", r_noopt.status.value == "pass")

    # 4) ABN STILL required: missing ABN -> HARD_BLOCK (sender-ID)
    r_noabn = review_gate("Thanks for the review, we really appreciate it.")
    _check("review missing ABN -> HARD_BLOCK", r_noabn.status.value == "hard_block")
    _check("review missing ABN flag", any("SENDER_ID_MISSING_ABN" in f for f in r_noabn.flags))

    # 5) ACL superlative in a review reply -> SOFT_FLAG
    r_acl = review_gate("We are the best painters in Sydney. -- Sister Painting ABN " + ABN)
    _check("review ACL superlative -> SOFT_FLAG", r_acl.status.value == "soft_flag")
    _check("review acl_ok False", r_acl.acl_ok is False)

    # 6) PII pattern (reviewer email) in a review reply -> SOFT_FLAG
    r_pii = review_gate("Thanks -- email us at bob@example.com. -- Sister Painting ABN " + ABN)
    _check("review PII email -> SOFT_FLAG", r_pii.status.value == "soft_flag")
    _check("review privacy_ok False", r_pii.privacy_ok is False)

    # 7) positive vs negative fallback tone differs
    dneg = c.draft_review_response(
        review_text="Paint peeled after a month. Disappointed.",
        sentiment="negative", platform="google", reviewer_name="Alex",
        key_themes=["quality_complaint"],
    )
    _check("positive/negative fallbacks distinct", dpos.content != dneg.content)
    _check("negative fallback still carries ABN", ABN in dneg.content)
    _check("negative fallback has NO opt-out", "STOP" not in dneg.content.upper())

    # 8) orchestrator wiring (offline): stub SDK modules, force NEGATIVE sentiment
    import types
    fake_anthropic = types.ModuleType("anthropic")
    fake_anthropic.Anthropic = object          # never instantiated (key="")
    sys.modules.setdefault("anthropic", fake_anthropic)
    sys.modules.setdefault("httpx", types.ModuleType("httpx"))
    from src.orchestrator import Orchestrator
    from src.agents.audience import SentimentResult
    orch = Orchestrator()
    orch.audience.analyse_review = lambda review_text, platform: SentimentResult(
        source=platform, sentiment="negative", score=0.15,
        key_themes=["quality_complaint"], agent_id="B_audience",
    )

    res = orch.kickoff_review_response({
        "text": "Paint peeled after a month, very disappointed.",
        "platform": "google", "reviewer_name": "Alex",
    })
    _check("orch.kickoff_review_response status drafted", res["status"] == "drafted")
    _check("orch review gate PASS", res["gate_status"] == "pass")
    _check("orch review content has ABN", ABN in res["content"])
    _check("orch review content has NO opt-out", "STOP" not in res["content"].upper())
    _check("orch review queued", res["queued"] is True)
    _check("orch review action id present", bool(res["approval_action_id"]))

    # 9) negative review queued as priority=high, SLA=120 min (2h)
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT priority, created_at, sla_deadline FROM approval_actions WHERE id=?",
            (res["approval_action_id"],),
        ).fetchone()
    finally:
        conn.close()
    _check("review action priority = high", row["priority"] == "high")
    sla_min = (datetime.fromisoformat(row["sla_deadline"])
               - datetime.fromisoformat(row["created_at"])).total_seconds() / 60.0
    _check("review SLA = 120 min (2h)", abs(sla_min - 120.0) < 1.0)

    # 10) offline => zero AUD spend recorded
    _check("zero daily spend (offline, no LLM)", get_daily_spend_aud() == 0.0)

    print("\nALL REVIEW-SLICE CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    finally:
        for p in (_TMP_DB, _TMP_DB + "-wal", _TMP_DB + "-shm", _TMP_DB + ".KILL"):
            try:
                os.remove(p)
            except OSError:
                pass
