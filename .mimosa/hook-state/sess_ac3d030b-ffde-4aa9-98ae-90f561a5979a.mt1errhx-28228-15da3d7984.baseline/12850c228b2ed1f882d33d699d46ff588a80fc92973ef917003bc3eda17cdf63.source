"""
Phase 3 approval-queue test -- OFFLINE (zero spend).

Covers the P3 acceptance criteria:
  - cycle: drafted -> queued -> approved / edited(regate) / rejected
  - reject of an inline-keyboard callback from an unauthorised chat_id is
    silently refused (no state change, audit logged)

Mirrors the offline pattern from test_phase2_leadpath.py: forces
ANTHROPIC_API_KEY="" (Worker C compliant-template fallback, $0 spend),
throwaway temp DB, manually seeded lead.
"""
import asyncio
import os
import sys
import tempfile

# Env MUST be set before importing config (singleton reads env at import).
_TMP_DB = tempfile.mkstemp(suffix="_brushline_test3.db")[1]
os.environ["BRUSHLINE_DB_PATH"] = _TMP_DB
os.environ["KILL_SWITCH_FILE"] = _TMP_DB + ".KILL"
os.environ["ANTHROPIC_API_KEY"] = ""            # force fallback -> offline, $0
os.environ["BUSINESS_NAME"] = "Sister Painting"
os.environ["BUSINESS_ABN"] = "11222333444"
os.environ["ALLOWED_OPERATOR_CHAT_IDS"] = "111222333"   # ONE authorised operator
os.environ["SPEND_CAP_PER_ACTION_AUD"] = "5.00"
os.environ["SPEND_CAP_PER_DAY_AUD"] = "20.00"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import types
fake_anthropic = types.ModuleType("anthropic")
fake_anthropic.Anthropic = object          # never instantiated (key="")
sys.modules.setdefault("anthropic", fake_anthropic)
sys.modules.setdefault("httpx", types.ModuleType("httpx"))

from datetime import datetime, timedelta

from src.config import config
from src.database import init_db, get_connection
from src.agents.content import ContentAgent
from src.gate import ConstitutionGate
from src.models import ApprovalStatus
from src.queue import ApprovalQueue, ApprovalQueueError, is_material_edit
from src.telegram_bot import BrushlineBot
from src import audit as audit_module

AUTHORISED_CHAT_ID = 111222333
UNAUTHORISED_CHAT_ID = 999888777


def _check(label, cond):
    print(("PASS" if cond else "FAIL") + " :: " + label)
    if not cond:
        raise AssertionError(label)


def _seed_lead(lead_id, name, suburb, service):
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


def _approval_row(action_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM approval_actions WHERE id=?", (action_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def main():
    assert config.ANTHROPIC_API_KEY == "", "test must run offline"
    init_db()
    _seed_lead("lead-q1", "Jordan", "Marrickville", "interior repaint")

    c = ContentAgent()
    g = ConstitutionGate()
    q = ApprovalQueue()

    # -- material-edit heuristic, unit-level ---------------------------------
    _check("whitespace-only is NOT material",
           is_material_edit("Hello   world.", "Hello world.") is False)
    _check("casing-only is NOT material",
           is_material_edit("Hello world.", "hello world.") is False)
    _check("content change IS material",
           is_material_edit("Hello world.", "Hello there, world!") is True)

    # === 1) drafted -> queued -> APPROVED ===================================
    d1 = c.draft_speed_to_lead({"id": "lead-q1", "name": "Jordan",
                                 "suburb": "Marrickville",
                                 "service_type": "interior repaint"})
    r1 = g.check(d1, consent_verified=True)
    _check("draft1 gate PASS", r1.status.value == "pass")

    a1 = q.submit(d1)
    _check("submit -> PENDING", a1.status == ApprovalStatus.PENDING)
    _check("speed_to_lead -> priority critical", a1.priority == "critical")
    _check("sla_deadline set", a1.sla_deadline is not None)
    pending_ids = [i["id"] for i in q.get_pending()]
    _check("queued item visible in get_pending", a1.id in pending_ids)

    approved = q.approve(a1.id, AUTHORISED_CHAT_ID)
    _check("approve -> APPROVED", approved.status == ApprovalStatus.APPROVED)
    pending_ids = [i["id"] for i in q.get_pending()]
    _check("approved item leaves pending queue", a1.id not in pending_ids)

    # double-decide must raise (no re-approving / re-rejecting)
    raised = False
    try:
        q.approve(a1.id, AUTHORISED_CHAT_ID)
    except ApprovalQueueError:
        raised = True
    _check("double-approve raises ApprovalQueueError", raised)

    # === 2) drafted -> queued -> REJECTED ====================================
    d2 = c.draft_followup("lead-q1", 2)
    r2 = g.check(d2, consent_verified=True)
    _check("draft2 gate PASS", r2.status.value == "pass")
    a2 = q.submit(d2)
    _check("followup -> priority medium", a2.priority == "medium")

    # reject without reason must raise
    raised = False
    try:
        q.reject(a2.id, AUTHORISED_CHAT_ID, "")
    except ApprovalQueueError:
        raised = True
    _check("reject without reason raises", raised)

    rejected = q.reject(a2.id, AUTHORISED_CHAT_ID, "Customer already signed with another painter")
    _check("reject -> REJECTED", rejected.status == ApprovalStatus.REJECTED)
    _check("reject persists reason", rejected.reason.startswith("Customer already"))

    # === 3) drafted -> queued -> EDITED, trivial (no regate) =================
    d3 = c.draft_speed_to_lead({"id": "lead-q1", "name": "Sam", "suburb": "Glebe",
                                 "service_type": "exterior"})
    g.check(d3, consent_verified=True)
    a3 = q.submit(d3)
    trivial_edit = d3.content.replace("  ", " ") + " "   # whitespace-only change
    res3 = q.edit_and_regate(a3.id, AUTHORISED_CHAT_ID, trivial_edit)
    _check("trivial edit -> no regate", res3["regate"] is False)
    _check("trivial edit -> ready_to_publish", res3["ready_to_publish"] is True)
    row3 = _approval_row(a3.id)
    _check("trivial edit -> status EDITED", row3["status"] == "edited")

    # === 4) drafted -> queued -> EDITED, material -> REGATE PASS =============
    d4 = c.draft_speed_to_lead({"id": "lead-q1", "name": "Alex", "suburb": "Newtown",
                                 "service_type": "interior repaint"})
    g.check(d4, consent_verified=True)
    a4 = q.submit(d4)
    # Keep it compliant (footer carries ABN+opt-out already on d4.content) but
    # rewrite the body materially.
    footer = d4.content.split("--\n", 1)[1] if "--\n" in d4.content else ""
    material_edit_ok = "Hi Alex, thanks for your enquiry about interior repainting in Newtown. " \
                        "We'll be in touch shortly to arrange a free quote.\n\n--\n" + footer
    res4 = q.edit_and_regate(a4.id, AUTHORISED_CHAT_ID, material_edit_ok)
    _check("material+compliant edit -> regate ran", res4["regate"] is True)
    _check("material+compliant edit -> gate PASS", res4["gate_status"] == "pass")
    _check("material+compliant edit -> ready_to_publish", res4["ready_to_publish"] is True)
    _check("material+compliant edit -> new_draft_id set", res4["new_draft_id"] is not None)

    # === 5) drafted -> queued -> EDITED, material -> REGATE flags -> requeue =
    d5 = c.draft_speed_to_lead({"id": "lead-q1", "name": "Riley", "suburb": "Balmain",
                                 "service_type": "exterior"})
    g.check(d5, consent_verified=True)
    a5 = q.submit(d5)
    bad_edit = "We are the best and cheapest painters in Sydney, guaranteed! ABN 11222333444. Reply STOP to opt out."
    res5 = q.edit_and_regate(a5.id, AUTHORISED_CHAT_ID, bad_edit)
    _check("flagged edit -> regate ran", res5["regate"] is True)
    _check("flagged edit -> gate NOT pass", res5["gate_status"] != "pass")
    _check("flagged edit -> NOT ready_to_publish", res5["ready_to_publish"] is False)
    _check("flagged edit -> requeued_action_id set", res5["requeued_action_id"] is not None)
    pending_ids = [i["id"] for i in q.get_pending()]
    _check("requeued item is now pending", res5["requeued_action_id"] in pending_ids)

    # === 6) SLA escalation -- priority + notify, NEVER auto-approve ==========
    d6 = c.draft_speed_to_lead({"id": "lead-q1", "name": "Drew", "suburb": "Erskineville",
                                 "service_type": "interior repaint"})
    g.check(d6, consent_verified=True)
    a6 = q.submit(d6)
    # Backdate the SLA deadline directly (simulate time passing offline).
    conn = get_connection()
    try:
        conn.execute("UPDATE approval_actions SET sla_deadline=? WHERE id=?",
                     ((datetime.utcnow() - timedelta(minutes=5)).isoformat(), a6.id))
        conn.commit()
    finally:
        conn.close()
    escalated = q.escalate_overdue()
    escalated_ids = [e["id"] for e in escalated]
    _check("overdue item escalated", a6.id in escalated_ids)
    row6 = _approval_row(a6.id)
    _check("escalation does NOT change status (no auto-approve, INV-1)", row6["status"] == "pending")
    _check("escalation sets expired=1", row6["expired"] == 1)
    _check("escalation forces priority critical", row6["priority"] == "critical")

    # === 7) Telegram callback auth -- unauthorised chat_id is refused ========
    bot = BrushlineBot()
    d7 = c.draft_speed_to_lead({"id": "lead-q1", "name": "Casey", "suburb": "Redfern",
                                 "service_type": "exterior"})
    g.check(d7, consent_verified=True)
    a7 = bot.approval_queue.submit(d7)

    resp_unauth = asyncio.run(bot.handle_callback(UNAUTHORISED_CHAT_ID, f"approve:{a7.id}"))
    _check("unauthorised callback returns None (silent reject)", resp_unauth is None)
    row7 = _approval_row(a7.id)
    _check("unauthorised callback does NOT change status", row7["status"] == "pending")

    # confirm it WAS logged for audit/security visibility
    recent = audit_module.query(event_type="UNAUTHORISED_ACCESS", limit=10)
    _check("unauthorised callback logged to audit", any(
        '"channel": "callback"' in e["payload"] or "callback" in e["payload"] for e in recent
    ))

    # authorised callback DOES work
    resp_auth = asyncio.run(bot.handle_callback(AUTHORISED_CHAT_ID, f"approve:{a7.id}"))
    _check("authorised callback approves", resp_auth is not None and "Approved" in resp_auth)
    row7b = _approval_row(a7.id)
    _check("authorised callback -> APPROVED", row7b["status"] == "approved")

    # authorised callback edit-flow round trip (edit button -> next message)
    d8 = c.draft_speed_to_lead({"id": "lead-q1", "name": "Morgan", "suburb": "Annandale",
                                 "service_type": "interior repaint"})
    g.check(d8, consent_verified=True)
    a8 = bot.approval_queue.submit(d8)
    btn_resp = asyncio.run(bot.handle_callback(AUTHORISED_CHAT_ID, f"edit:{a8.id}"))
    _check("edit button prompts for new text", "new content" in btn_resp.lower())
    msg_resp = asyncio.run(bot.handle_message(AUTHORISED_CHAT_ID, d8.content + " "))
    _check("follow-up message resolves the edit", "edit" in msg_resp.lower() or "re-checked" in msg_resp.lower())

    # === 8) Orchestrator wiring: handle_enquiry queues PASS drafts ===========
    from src.orchestrator import Orchestrator
    orch = Orchestrator()
    enq = {"id": "lead-q1", "name": "Taylor", "suburb": "Leichhardt",
           "service_type": "exterior", "source_channel": "gbp"}
    ores = orch.handle_enquiry(enq)
    _check("orch.handle_enquiry status drafted (unchanged contract)", ores["status"] == "drafted")
    _check("orch.handle_enquiry queued True on PASS", ores["queued"] is True)
    _check("orch.handle_enquiry has approval_action_id", ores["approval_action_id"] is not None)
    pending_ids = [i["id"] for i in orch.queue.get_pending()]
    _check("orchestrator-queued item visible in queue", ores["approval_action_id"] in pending_ids)

    # HARD_BLOCK path must NOT be queued
    fblock = orch.kickoff_followup("lead-q1", 5, consent_verified=False)
    _check("HARD_BLOCK followup not queued", fblock["queued"] is False)
    _check("HARD_BLOCK followup has no approval_action_id", fblock["approval_action_id"] is None)

    # === 9) Audit chain integrity after all of the above ======================
    chain_ok, chain_msg = audit_module.verify_chain()
    _check("audit chain intact after full Phase 3 cycle: " + chain_msg, chain_ok)

    print("\nALL PHASE-3 APPROVAL QUEUE CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    finally:
        for p in (_TMP_DB, _TMP_DB + "-wal", _TMP_DB + "-shm", _TMP_DB + ".KILL"):
            try:
                os.remove(p)
            except OSError:
                pass
