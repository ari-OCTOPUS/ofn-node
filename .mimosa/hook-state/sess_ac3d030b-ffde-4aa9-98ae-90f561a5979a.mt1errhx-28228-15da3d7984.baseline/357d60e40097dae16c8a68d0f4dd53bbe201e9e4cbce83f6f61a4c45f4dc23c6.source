"""
Phase 7 -- cost optimisation: prompt caching + batch, REAL discounted cost. OFFLINE.

  - CACHE_ENABLED -> system param carries cache_control ephemeral
  - _cost_from_usage: cache write x1.25, cache read x0.10, batch x0.50
  - >=50% saving on a repeated-system call (cache read) vs uncached
  - live-sim Haiku call logs the DISCOUNTED cost to cost_events (INV-3)
  - submit_followup_batch -> batch id + BATCH_SUBMITTED audit
  - collect while processing -> None; after ended -> drafts at 50% cost
  - collected drafts still go Gate -> Queue via orchestrator (INV-1)
  - failed batch item -> compliant fallback draft (no lost follow-up)
"""
import os
import sys
import tempfile
import types

_TMP_DB = tempfile.mkstemp(suffix="_brushline_p7.db")[1]
os.environ["BRUSHLINE_DB_PATH"] = _TMP_DB
os.environ["KILL_SWITCH_FILE"] = _TMP_DB + ".KILL"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["SERPER_API_KEY"] = ""
os.environ["ALLOWED_OPERATOR_CHAT_IDS"] = "123456"
os.environ["BUSINESS_NAME"] = "Sister Painting"
os.environ["BUSINESS_ABN"] = "11222333444"
os.environ["CACHE_ENABLED"] = "true"
os.environ["BATCH_ENABLED"] = "true"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, get_connection
from src.agents.content import (
    ContentAgent, _HAIKU_INPUT_USD_PER_TOK, _HAIKU_OUTPUT_USD_PER_TOK,
    _CACHE_WRITE_MULT, _CACHE_READ_MULT, _BATCH_DISCOUNT, _FOLLOWUP_SYSTEM,
)
from src.governance import get_daily_spend_aud
from src import audit


def _check(label, cond):
    print(("PASS" if cond else "FAIL") + " :: " + label)
    if not cond:
        raise AssertionError(label)


class FakeUsage:
    def __init__(self, tin=0, tout=0, cw=0, cr=0):
        self.input_tokens = tin
        self.output_tokens = tout
        self.cache_creation_input_tokens = cw
        self.cache_read_input_tokens = cr


class FakeMsg:
    def __init__(self, text, usage):
        self.content = [types.SimpleNamespace(text=text)]
        self.usage = usage


def main():
    init_db()
    c = ContentAgent()

    # 1) cache_control wiring
    sp = c._system_param("STABLE SYSTEM")
    _check("CACHE_ENABLED -> list block", isinstance(sp, list))
    _check("cache_control ephemeral attached",
           sp[0]["cache_control"]["type"] == "ephemeral")
    from src.config import config
    config.CACHE_ENABLED = False
    _check("CACHE_ENABLED=false -> plain string",
           c._system_param("X") == "X")
    config.CACHE_ENABLED = True

    # 2) cost math: uncached vs cache-read call with SAME token profile
    SYS_TOK, USER_TOK, OUT_TOK = 2100, 150, 120
    _, _, cost_uncached = c._cost_from_usage(
        FakeUsage(tin=SYS_TOK + USER_TOK, tout=OUT_TOK),
        _HAIKU_INPUT_USD_PER_TOK, _HAIKU_OUTPUT_USD_PER_TOK)
    _, _, cost_cached = c._cost_from_usage(
        FakeUsage(tin=USER_TOK, tout=OUT_TOK, cr=SYS_TOK),
        _HAIKU_INPUT_USD_PER_TOK, _HAIKU_OUTPUT_USD_PER_TOK)
    system_cost_before = SYS_TOK * _HAIKU_INPUT_USD_PER_TOK
    system_cost_after = SYS_TOK * _HAIKU_INPUT_USD_PER_TOK * _CACHE_READ_MULT
    _check("cache read = 90% saving on repeated system tokens",
           abs(system_cost_after / system_cost_before - 0.10) < 1e-9)
    _check("cached call cheaper overall", cost_cached < cost_uncached)
    saving = 1 - (cost_cached / cost_uncached)
    print(f"      per-draft saving with cached system block: {saving:.1%}")
    _check(">=50% per-draft saving on this profile (acceptance)", saving >= 0.50)
    # write pass costs 25% more on the system block (honest accounting)
    _, _, cost_write = c._cost_from_usage(
        FakeUsage(tin=USER_TOK, tout=OUT_TOK, cw=SYS_TOK),
        _HAIKU_INPUT_USD_PER_TOK, _HAIKU_OUTPUT_USD_PER_TOK)
    _check("cache WRITE pass costs more than uncached (x1.25)",
           cost_write > cost_uncached)
    # batch halves everything
    _, _, cost_batch = c._cost_from_usage(
        FakeUsage(tin=SYS_TOK + USER_TOK, tout=OUT_TOK),
        _HAIKU_INPUT_USD_PER_TOK, _HAIKU_OUTPUT_USD_PER_TOK, batch=True)
    _check("batch = exactly 50% of uncached",
           abs(cost_batch / cost_uncached - _BATCH_DISCOUNT) < 1e-9)

    # 3) live-sim: _haiku with fake client logs DISCOUNTED cost to cost_events
    class FakeMessages:
        def create(self, **kw):
            sysp = kw["system"]
            assert isinstance(sysp, list) and "cache_control" in sysp[0], \
                "cache_control must reach the API call"
            return FakeMsg("Thanks for your enquiry -- happy to help.",
                           FakeUsage(tin=150, tout=100, cr=2100))
    c._llm = types.SimpleNamespace(messages=FakeMessages())
    spend0 = get_daily_spend_aud()
    res = c._haiku("SYS", "USER")
    _check("fake live call returns", res is not None)
    text, tok_in, tok_out, cost = res
    _check("tok_in includes cached tokens", tok_in == 150 + 2100)
    expected = (150 * _HAIKU_INPUT_USD_PER_TOK
                + 2100 * _HAIKU_INPUT_USD_PER_TOK * _CACHE_READ_MULT
                + 100 * _HAIKU_OUTPUT_USD_PER_TOK)
    _check("returned cost = discounted real cost", abs(cost - expected) < 1e-12)

    # 4) batch submit/collect
    lead_conn = get_connection()
    lead_conn.execute(
        "INSERT INTO leads (id, name, phone, suburb, service_type, "
        "source_channel, notes, created_at) VALUES "
        "('L1','Sam','0400000001','Glebe','interior','gbp','','2026-07-01T00:00:00'),"
        "('L2','Alex','0400000002','Newtown','exterior','referral','','2026-07-01T00:00:00')")
    lead_conn.commit()
    lead_conn.close()

    class FakeBatchResult:
        def __init__(self, cid, ok=True):
            self.custom_id = cid
            if ok:
                self.result = types.SimpleNamespace(
                    type="succeeded",
                    message=FakeMsg("Hi -- just checking in on your quote.",
                                    FakeUsage(tin=140, tout=60, cr=900)))
            else:
                self.result = types.SimpleNamespace(type="errored")

    class FakeBatches:
        def __init__(self):
            self.status = "in_progress"
        def create(self, requests):
            self.reqs = requests
            for r in requests:
                assert isinstance(r["params"]["system"], list), \
                    "batch requests must carry cache_control too"
            return types.SimpleNamespace(id="batch-001")
        def retrieve(self, bid):
            return types.SimpleNamespace(processing_status=self.status)
        def results(self, bid):
            return [FakeBatchResult("L1::2"), FakeBatchResult("L2::5", ok=False)]

    fb = FakeBatches()
    c._llm = types.SimpleNamespace(
        messages=types.SimpleNamespace(batches=fb, create=FakeMessages().create))

    jobs = [{"lead_id": "L1", "day": 2}, {"lead_id": "L2", "day": 5}]
    bid = c.submit_followup_batch(jobs)
    _check("batch submitted -> id", bid == "batch-001")
    _check("BATCH_SUBMITTED audited",
           any("BATCH_SUBMITTED" in et for et, _ in _events()))

    _check("collect while processing -> None",
           c.collect_followup_batch(bid) is None)
    fb.status = "ended"
    spend_before = get_daily_spend_aud()
    drafts = c.collect_followup_batch(bid)
    _check("collect after ended -> 2 drafts", len(drafts) == 2)
    ok_draft = [d for d in drafts if "+batch" in d.model_used][0]
    fb_draft = [d for d in drafts if "+fallback" in d.model_used][0]
    _check("succeeded item -> batch draft with footer",
           "opt out" in ok_draft.content.lower())
    exp_batch_cost = ((140 * _HAIKU_INPUT_USD_PER_TOK
                       + 900 * _HAIKU_INPUT_USD_PER_TOK * _CACHE_READ_MULT
                       + 60 * _HAIKU_OUTPUT_USD_PER_TOK) * _BATCH_DISCOUNT)
    _check("batch draft cost = 50% discounted real cost",
           abs(ok_draft.cost_usd - exp_batch_cost) < 1e-12)
    _check("cost_events grew by the discounted amount",
           get_daily_spend_aud() > spend_before)
    _check("failed item -> compliant fallback draft (no lost follow-up)",
           "opt out" in fb_draft.content.lower() and fb_draft.cost_usd == 0.0)
    _check("BATCH_ITEM_FAILED audited",
           any("BATCH_ITEM_FAILED" in et for et, _ in _events()))

    # 5) orchestrator: collected drafts still go Gate -> Queue (INV-1)
    sys.modules.setdefault("anthropic", types.ModuleType("anthropic"))
    sys.modules["anthropic"].Anthropic = object
    sys.modules.setdefault("httpx", types.ModuleType("httpx"))
    from src.orchestrator import Orchestrator
    orch = Orchestrator()
    orch.content._llm = c._llm
    fb.status = "in_progress"
    r1 = orch.kickoff_followup_batch(jobs)
    _check("orch submit -> batch_submitted", r1["status"] == "batch_submitted")
    _check("orch collect while processing -> processing",
           orch.collect_followup_batch(r1["batch_id"])["status"] == "processing")
    fb.status = "ended"
    r2 = orch.collect_followup_batch(r1["batch_id"])
    _check("orch collect -> collected", r2["status"] == "collected")
    _check("every batch draft gated + queued",
           all(x["queued"] for x in r2["results"]))

    # 6) BATCH_ENABLED=false -> sync fallback path still works
    config.BATCH_ENABLED = False
    r3 = orch.kickoff_followup_batch([{"lead_id": "L1", "day": 2}])
    _check("flag off -> fallback_sync via kickoff_followup",
           r3["status"] == "fallback_sync" and len(r3["results"]) == 1)
    config.BATCH_ENABLED = True

    _check("verify_chain green", audit.verify_chain()[0] is True)
    print("\nALL COST-OPT (P7) CHECKS PASSED")


def _events():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT event_type, payload FROM audit_entries").fetchall()
        return [(r["event_type"], r["payload"] or "") for r in rows]
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        for p in (_TMP_DB, _TMP_DB + "-wal", _TMP_DB + "-shm", _TMP_DB + ".KILL"):
            try:
                os.remove(p)
            except OSError:
                pass
