"""
Phase 5 -- Worker F (Lead Capture) + CRM sync, INV-2 enforced. OFFLINE.

  - capture() stores the lead; audit ENQUIRY_RECEIVED has no raw PII
  - sync WITHOUT ConsentRecord -> SyncBlocked (INV-2), SYNC_BLOCKED audited
  - sync WITH consent, no API key -> dry_run SyncJob persisted (no network)
  - live-mode sim: fake transport -> SYNCED + external ids + idempotency key
  - retry sim: 429 then success -> ONE SyncJob, same idempotency key reused
  - NO audit payload anywhere contains raw phone/email/name (INV-2 scan)
  - verify_chain stays green
  - orchestrator.sync_lead refuses a non-allow-listed operator (fail-closed)
"""
import os
import sys
import tempfile

_TMP_DB = tempfile.mkstemp(suffix="_brushline_p5.db")[1]
os.environ["BRUSHLINE_DB_PATH"] = _TMP_DB
os.environ["KILL_SWITCH_FILE"] = _TMP_DB + ".KILL"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["SERPER_API_KEY"] = ""
os.environ["SERVICEM8_API_KEY"] = ""
os.environ["TRADIFY_API_KEY"] = ""
os.environ["ALLOWED_OPERATOR_CHAT_IDS"] = "123456"
os.environ["BUSINESS_NAME"] = "Sister Painting"
os.environ["BUSINESS_ABN"] = "11222333444"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PII_NAME = "Maryam Testovna"
PII_PHONE = "0412345678"
PII_EMAIL = "maryam.testovna@example.com"

from src.database import init_db, get_connection
from src.agents.lead_capture import LeadCaptureAgent, SyncBlocked
from src.models import ConsentMethod, SyncStatus
from src import audit


def _check(label, cond):
    print(("PASS" if cond else "FAIL") + " :: " + label)
    if not cond:
        raise AssertionError(label)


def _all_audit_payloads():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT event_type, payload FROM audit_entries").fetchall()
        return [(r["event_type"], r["payload"] or "") for r in rows]
    finally:
        conn.close()


def _no_raw_pii(payloads):
    bad = [
        (et, p) for et, p in payloads
        if PII_PHONE in p or PII_EMAIL in p or PII_NAME in p
    ]
    return len(bad) == 0, bad


def main():
    init_db()
    f = LeadCaptureAgent()

    # 1) capture -> lead persisted, audit clean of PII
    lead = f.capture({
        "name": PII_NAME, "phone": PII_PHONE, "email": PII_EMAIL,
        "suburb": "Marrickville", "service_type": "interior",
        "source_channel": "gbp", "notes": "2 bedrooms + hallway",
    })
    _check("lead persisted", lead.id and len(lead.id) > 10)
    ok, bad = _no_raw_pii(_all_audit_payloads())
    _check("ENQUIRY_RECEIVED audit has no raw PII", ok)

    # 2) sync WITHOUT consent -> SyncBlocked (both targets)
    for target_fn in (f.sync_to_servicem8, f.sync_to_tradify):
        raised = False
        try:
            target_fn(lead)
        except SyncBlocked:
            raised = True
        _check(f"{target_fn.__name__} blocked without ConsentRecord (INV-2)", raised)
    payloads = _all_audit_payloads()
    _check("SYNC_BLOCKED audited",
           any(et == "SYNC_BLOCKED" for et, _ in payloads))
    _check("no SyncJob row created while blocked",
           get_connection().execute("SELECT COUNT(*) c FROM sync_jobs").fetchone()["c"] == 0)

    # 3) record consent -> dry-run sync (no API key -> NO network call)
    consent = f.record_consent(lead.id, ConsentMethod.EXPRESS,
                               "web form submission 2026-07-02")
    _check("consent recorded", f.get_consent(lead.id)["id"] == consent.id)
    job = f.sync_to_servicem8(lead)
    _check("dry-run sync returns SyncJob", job.lead_id == lead.id)
    _check("dry-run status stays PENDING", job.status == SyncStatus.PENDING)
    conn = get_connection()
    row = conn.execute("SELECT * FROM sync_jobs WHERE id = ?", (job.id,)).fetchone()
    conn.close()
    _check("dry-run SyncJob persisted", row is not None)
    _check("SYNC audit mode=dry_run",
           any(et == "SYNC" and "dry_run" in p for et, p in _all_audit_payloads()))

    # 4) live-mode simulation: fake transport, no real network
    os.environ["SERVICEM8_API_KEY"] = "fake-key-for-test"
    from src.config import config
    config.SERVICEM8_API_KEY = "fake-key-for-test"
    calls = {"n": 0, "idem_keys": []}

    def fake_post(target, api_key, payload, idem_key):
        calls["n"] += 1
        calls["idem_keys"].append(idem_key)
        # payload must be whitelist-only
        from src.agents.lead_capture import SYNC_FIELD_WHITELIST
        assert set(payload.keys()) == set(SYNC_FIELD_WHITELIST)
        return {"client_id": "sm8-client-1", "job_id": "sm8-job-1"}

    f._post = fake_post
    job2 = f.sync_to_servicem8(lead)
    _check("live sync -> SYNCED", job2.status == SyncStatus.SYNCED)
    _check("external ids captured",
           job2.external_client_id == "sm8-client-1" and
           job2.external_job_id == "sm8-job-1")
    _check("exactly one transport call", calls["n"] == 1)

    # 5) retry simulation: first attempt 429, then success; idem key stable
    calls2 = {"n": 0, "idem_keys": []}

    class Fake429(Exception):
        status_code = 429

    def flaky_post(target, api_key, payload, idem_key):
        calls2["n"] += 1
        calls2["idem_keys"].append(idem_key)
        if calls2["n"] == 1:
            raise Fake429("simulated rate limit")
        return {"client_id": "sm8-client-2", "job_id": "sm8-job-2"}

    import src.agents.lead_capture as lc_mod
    orig_retry = lc_mod.call_with_retry
    lc_mod.call_with_retry = lambda op, **kw: orig_retry(
        op, **{**kw, "sleep": lambda s: None})
    f._post = flaky_post
    job3 = f.sync_to_servicem8(lead)
    lc_mod.call_with_retry = orig_retry
    _check("retry: eventual success -> SYNCED", job3.status == SyncStatus.SYNCED)
    _check("retry: two attempts made", calls2["n"] == 2)
    _check("retry: SAME idempotency key on both attempts",
           len(set(calls2["idem_keys"])) == 1)
    conn = get_connection()
    n_jobs = conn.execute(
        "SELECT COUNT(*) c FROM sync_jobs WHERE external_job_id='sm8-job-2'"
    ).fetchone()["c"]
    conn.close()
    _check("retry: exactly ONE SyncJob row (no duplicate)", n_jobs == 1)

    # 6) INV-2 global scan: nothing in audit contains raw PII
    ok, bad = _no_raw_pii(_all_audit_payloads())
    _check("NO audit payload contains raw phone/email/name", ok)

    # 7) hash chain intact after all of the above
    _check("verify_chain green", audit.verify_chain()[0] is True)

    # 8) orchestrator entry-point: operator allow-list (fail-closed)
    import types
    sys.modules.setdefault("anthropic", types.ModuleType("anthropic"))
    sys.modules["anthropic"].Anthropic = object
    sys.modules.setdefault("httpx", types.ModuleType("httpx"))
    from src.orchestrator import Orchestrator
    orch = Orchestrator()
    orch.lead_capture._post = fake_post
    raised = False
    try:
        orch.sync_lead(lead.id, "servicem8", operator_chat_id=999999)
    except SyncBlocked:
        raised = True
    _check("orch.sync_lead refuses non-allow-listed operator", raised)
    res = orch.sync_lead(lead.id, "servicem8", operator_chat_id=123456)
    _check("orch.sync_lead allowed operator -> synced", res["status"] == "synced")
    raised2 = False
    try:
        orch.sync_lead("no-such-lead", "servicem8", operator_chat_id=123456)
    except SyncBlocked:
        raised2 = True
    _check("orch.sync_lead unknown lead -> SyncBlocked", raised2)

    # final: chain still green including orchestrator events
    _check("verify_chain green (final)", audit.verify_chain()[0] is True)

    print("\nALL LEAD-SYNC (P5) CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    finally:
        for p in (_TMP_DB, _TMP_DB + "-wal", _TMP_DB + "-shm", _TMP_DB + ".KILL"):
            try:
                os.remove(p)
            except OSError:
                pass
