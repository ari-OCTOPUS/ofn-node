"""
Phase 2 suburb-page slice + semantic ACL test -- OFFLINE (zero real spend). [P2]

Worker C draft_suburb_page uses its compliant template fallback when no LLM key
is set. The Gate's semantic ACL (Sonnet) layer is exercised with a FAKE LLM
client injected into the gate (no network), so we can assert it:
  - catches a subtle unsubstantiated claim the deterministic superlative scan
    misses ("trusted by thousands") -> SOFT_FLAG + ACL_SEMANTIC flag
  - logs the Sonnet cost to cost_events (check_and_enforce ran first, INV-3)
  - runs ONLY on high-risk marketing types (skips speed_to_lead -> no cost)
  - is additive: deterministic superlative scan still works standalone
  - a clean page (empty claims) -> PASS
Also: draft_suburb_page fallback is compliant (gate PASS deterministically),
and orchestrator.kickoff_suburb_page is wired end-to-end (offline).
"""
import os
import sys
import tempfile

_TMP_DB = tempfile.mkstemp(suffix="_brushline_suburb_test.db")[1]
os.environ["BRUSHLINE_DB_PATH"] = _TMP_DB
os.environ["KILL_SWITCH_FILE"] = _TMP_DB + ".KILL"
os.environ["ANTHROPIC_API_KEY"] = ""            # offline: fallback + gate._llm=None
os.environ["SERPER_API_KEY"] = ""               # offline: Worker A returns [] (no live search)
os.environ["BUSINESS_NAME"] = "Sister Painting"
os.environ["BUSINESS_ABN"] = "11222333444"
os.environ["ALLOWED_OPERATOR_CHAT_IDS"] = ""
os.environ["SPEND_CAP_PER_ACTION_AUD"] = "5.00"
os.environ["SPEND_CAP_PER_DAY_AUD"] = "20.00"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import config
from src.database import init_db
from src.agents.content import ContentAgent
from src.gate import ConstitutionGate
from src.models import Draft, DraftType
from src.governance import get_daily_spend_aud


def _check(label, cond):
    print(("PASS" if cond else "FAIL") + " :: " + label)
    if not cond:
        raise AssertionError(label)


# -- fake Sonnet client (no network); shape matches anthropic messages.create --
class _FakeResp:
    def __init__(self, text):
        self.content = [type("X", (), {"text": text})()]
        self.usage = type("U", (), {"input_tokens": 150, "output_tokens": 25})()

class _FakeMessages:
    def __init__(self, text):
        self._text = text
    def create(self, **kw):
        return _FakeResp(self._text)

class FakeLLM:
    def __init__(self, text):
        self.messages = _FakeMessages(text)


def main():
    assert config.ANTHROPIC_API_KEY == "", "test must run offline"
    init_db()
    c = ContentAgent()

    def suburb_draft(content):
        d = Draft(draft_type=DraftType.SUBURB_PAGE, content=content,
                  agent_id="C_content", model_used="x")
        c._save(d)
        return d

    ABN = config.BUSINESS_ABN

    # 1) draft_suburb_page offline -> compliant fallback
    dp = c.draft_suburb_page("Marrickville", research={"competitor": [
        {"content": "Rival Painters -- best painters in Sydney, 500 five-star reviews"}]})
    _check("suburb page body non-empty", len(dp.content) > 80)
    _check("suburb page names the suburb", "Marrickville" in dp.content)
    _check("suburb page used fallback (offline)", "fallback" in dp.model_used)
    _check("suburb page zero cost (offline)", dp.cost_usd == 0.0)
    _check("suburb page did NOT copy competitor superlative",
           "best painters" not in dp.content.lower())

    # 2) fallback page passes the (offline, deterministic-only) gate
    g_offline = ConstitutionGate()            # no key -> _llm None -> no semantic pass
    _check("gate offline has no LLM", g_offline._llm is None)
    r1 = g_offline.check(dp)
    _check("fallback suburb page gate PASS", r1.status.value == "pass")

    # 3) deterministic superlative still fires on a suburb page (no LLM needed)
    r_det = g_offline.check(suburb_draft("We are the best painters in Marrickville."))
    _check("deterministic superlative -> SOFT_FLAG", r_det.status.value == "soft_flag")
    _check("deterministic ACL flag present",
           any("ACL_SUPERLATIVE" in f for f in r_det.flags))

    # 4) orchestrator.kickoff_suburb_page wired end-to-end (offline)
    import types
    sys.modules.setdefault("anthropic", types.ModuleType("anthropic"))
    sys.modules["anthropic"].Anthropic = object
    sys.modules.setdefault("httpx", types.ModuleType("httpx"))
    from src.orchestrator import Orchestrator
    orch = Orchestrator()
    ores = orch.kickoff_suburb_page("Glebe", "interior")
    _check("orch suburb status drafted", ores["status"] == "drafted")
    _check("orch suburb gate PASS (offline)", ores["gate_status"] == "pass")
    _check("orch suburb queued", ores["queued"] is True)
    _check("orch suburb names suburb", "Glebe" in ores["content"])

    # offline so far => zero AUD spend
    _check("zero spend before semantic-ACL (offline)", get_daily_spend_aud() == 0.0)

    # 5) semantic ACL catches a SUBTLE claim the superlative scan misses
    g_sem = ConstitutionGate()
    g_sem._llm = FakeLLM('{"claims": ["trusted by thousands"]}')
    subtle = suburb_draft("We are trusted by thousands of Sydney homeowners for "
                          "quality house painting in Marrickville.")
    # sanity: deterministic scan alone would NOT flag this
    _check("subtle claim not caught by deterministic",
           not any(t in subtle.content.lower() for t in ConstitutionGate._BANNED_SUPERLATIVES))
    r_sem = g_sem.check(subtle)
    _check("semantic ACL -> SOFT_FLAG", r_sem.status.value == "soft_flag")
    _check("semantic ACL flag present", any("ACL_SEMANTIC" in f for f in r_sem.flags))
    _check("semantic ACL sets acl_ok False", r_sem.acl_ok is False)

    # 6) semantic ACL logged the Sonnet cost to cost_events (INV-3 accounting)
    _check("semantic ACL logged spend > 0", get_daily_spend_aud() > 0.0)

    # 7) clean page + empty claims -> PASS
    g_clean = ConstitutionGate()
    g_clean.__dict__["_llm"] = FakeLLM('{"claims": []}')
    r_clean = g_clean.check(suburb_draft(
        "Interior and exterior house painting for homes in Glebe. "
        "Get in touch for a free, no-obligation quote."))
    _check("clean suburb page + empty claims -> PASS", r_clean.status.value == "pass")

    # 8) semantic ACL is TYPE-GATED: does NOT run on speed_to_lead (cost control)
    spend_before = get_daily_spend_aud()
    g_type = ConstitutionGate()
    g_type._llm = FakeLLM('{"claims": ["should never be used here"]}')
    lead_draft = Draft(draft_type=DraftType.SPEED_TO_LEAD,
                       content="Hi, thanks for your enquiry. ABN " + ABN +
                               ". Reply STOP to opt out.",
                       agent_id="C_content", model_used="x")
    c._save(lead_draft)
    r_type = g_type.check(lead_draft, consent_verified=True)
    _check("speed_to_lead gate PASS", r_type.status.value == "pass")
    _check("no semantic flag on non-marketing type",
           not any("ACL_SEMANTIC" in f for f in r_type.flags))
    _check("no extra spend from type-gated skip",
           get_daily_spend_aud() == spend_before)

    print("\nALL SUBURB-SLICE + SEMANTIC-ACL CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    finally:
        for p in (_TMP_DB, _TMP_DB + "-wal", _TMP_DB + "-shm", _TMP_DB + ".KILL"):
            try:
                os.remove(p)
            except OSError:
                pass
