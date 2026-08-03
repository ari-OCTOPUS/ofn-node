"""
Arch-review quick wins (2026-07-02). OFFLINE.

  - Worker B: no LLM -> neutral stub (no governance side effects);
    with fake LLM -> check_and_enforce respected (kill switch blocks) AND
    cost logged to cost_events (INV-3 hole closed)
  - intake_enquiry persists the Lead so followups/sync can find it
  - daily-spend range query: event just before UTC midnight counted on the
    right day; spend visible immediately (sargable range, same semantics)
  - pooled connection: uncommitted transaction is rolled back at close()
    (no leakage into the next caller on the same thread)
  - indexes exist on hot-path tables
"""
import os
import sys
import tempfile
import types

_TMP_DB = tempfile.mkstemp(suffix="_brushline_qw.db")[1]
os.environ["BRUSHLINE_DB_PATH"] = _TMP_DB
os.environ["KILL_SWITCH_FILE"] = _TMP_DB + ".KILL"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["SERPER_API_KEY"] = ""
os.environ["ALLOWED_OPERATOR_CHAT_IDS"] = "123456"
os.environ["BUSINESS_NAME"] = "Sister Painting"
os.environ["BUSINESS_ABN"] = "11222333444"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, get_connection
from src import audit
from src.governance import (get_daily_spend_aud, activate_kill_switch,
                            deactivate_kill_switch, KillSwitchActivated)


def _check(label, cond):
    print(("PASS" if cond else "FAIL") + " :: " + label)
    if not cond:
        raise AssertionError(label)


def main():
    init_db()

    # 1) indexes exist
    conn = get_connection()
    idx = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index'").fetchall()}
    conn.close()
    for want in ("idx_cost_events_ts", "idx_approval_status",
                 "idx_consent_lead", "idx_audit_entity"):
        _check(f"index {want} exists", want in idx)

    # 2) Worker B offline stub -> no crash without SDK/key
    from src.agents.audience import AudienceAgent
    aud = AudienceAgent()
    r = aud.analyse_review("Great job painting our house!", "google")
    _check("Worker B offline -> neutral stub", r.sentiment == "neutral")

    # 3) Worker B with fake LLM: cost logged + kill switch enforced
    class FakeUsage:
        input_tokens = 200
        output_tokens = 50
        cache_creation_input_tokens = 0
        cache_read_input_tokens = 0

    class FakeMsg:
        content = [types.SimpleNamespace(
            text='{"sentiment": "positive", "score": 0.9, "key_themes": ["quality"]}')]
        usage = FakeUsage()

    aud._llm = types.SimpleNamespace(
        messages=types.SimpleNamespace(create=lambda **kw: FakeMsg()))
    spend0 = get_daily_spend_aud()
    r2 = aud.analyse_review("Lovely work, highly recommend.", "google")
    _check("Worker B live-sim -> positive", r2.sentiment == "positive")
    _check("Worker B cost now LOGGED to cost_events (INV-3 fix)",
           get_daily_spend_aud() > spend0)

    activate_kill_switch(123456, "test")
    raised = False
    try:
        aud.analyse_review("another one", "google")
    except KillSwitchActivated:
        raised = True
    deactivate_kill_switch(123456)
    _check("Worker B respects kill switch (INV-3 fix)", raised)

    # 4) intake_enquiry persists the Lead (followup/sync can find it)
    sys.modules.setdefault("anthropic", types.ModuleType("anthropic"))
    sys.modules["anthropic"].Anthropic = object
    sys.modules.setdefault("httpx", types.ModuleType("httpx"))
    from src.orchestrator import Orchestrator
    orch = Orchestrator()
    res = orch.intake_enquiry({
        "name": "Nima Tester", "phone": "0498765432",
        "suburb": "Enmore", "service_type": "interior",
        "source_channel": "gbp", "notes": "kitchen + hallway",
    })
    _check("intake_enquiry returns lead_id", "lead_id" in res)
    _check("intake_enquiry drafted + queued",
           res["status"] == "drafted" and res["queued"] is True)
    conn = get_connection()
    row = conn.execute("SELECT * FROM leads WHERE id=?", (res["lead_id"],)).fetchone()
    conn.close()
    _check("Lead row persisted by intake_enquiry", row is not None)
    lead_loaded = orch.content._load_lead(res["lead_id"])
    _check("followup _load_lead finds the lead now",
           bool(lead_loaded) and lead_loaded.get("suburb") == "Enmore")

    # 5) daily spend day-boundary semantics (range query)
    from src.governance import log_cost, _utc_today
    conn = get_connection()
    conn.execute(
        "INSERT INTO cost_events (id, event_type, agent_id, model, cost_usd, "
        "cost_aud, tokens_in, tokens_out, timestamp) VALUES "
        "('qw-yday','llm_call','x','m',1.0,1.45,0,0,?)",
        ((_utc_today().isoformat().replace(
            _utc_today().isoformat(), '2000-01-01')) + 'T23:59:59.999Z',))
    conn.commit()
    conn.close()
    import datetime as dt
    _check("event on old day NOT in today's total",
           get_daily_spend_aud(dt.date(2000, 1, 2)) == 0.0)
    _check("event counted on ITS OWN day",
           abs(get_daily_spend_aud(dt.date(2000, 1, 1)) - 1.45) < 1e-9)

    # 6) pooled connection: uncommitted tx rolled back at close()
    c1 = get_connection()
    c1.execute("INSERT INTO brushline_meta VALUES ('qw_tx_test', 'dirty')")
    # no commit -- hand back to pool
    c1.close()
    c2 = get_connection()
    _check("pool close() rolled back uncommitted write",
           not c2.in_transaction and c2.execute(
               "SELECT COUNT(*) c FROM brushline_meta WHERE key='qw_tx_test'"
           ).fetchone()["c"] == 0)
    c2.close()

    _check("verify_chain green", audit.verify_chain()[0] is True)
    print("\nALL ARCH QUICK-WIN CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    finally:
        for p in (_TMP_DB, _TMP_DB + "-wal", _TMP_DB + "-shm", _TMP_DB + ".KILL"):
            try:
                os.remove(p)
            except OSError:
                pass
