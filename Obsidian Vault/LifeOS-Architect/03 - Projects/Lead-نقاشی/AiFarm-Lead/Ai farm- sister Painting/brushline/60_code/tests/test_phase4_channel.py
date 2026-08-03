"""
Phase 4 -- Worker E (Channel), DRAFT-only + INV-1-gated publish. OFFLINE.

  - draft_gbp_post / draft_social_post create channel DRAFTS (never post)
  - a clean GBP post passes the Gate; a superlative one SOFT_FLAGs (ACL)
  - publish() REFUSES a draft with no APPROVED action (INV-1) -> ChannelError
  - after Gate -> Queue -> APPROVE, publish() returns a PREVIEW (live_posted=False)
  - orchestrator.kickoff_gbp_post drafts -> Gate -> Queue (nothing posted)
  - there is no publish path that bypasses approval
"""
import os
import sys
import tempfile

_TMP_DB = tempfile.mkstemp(suffix="_brushline_p4.db")[1]
os.environ["BRUSHLINE_DB_PATH"] = _TMP_DB
os.environ["KILL_SWITCH_FILE"] = _TMP_DB + ".KILL"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["SERPER_API_KEY"] = ""
os.environ["ALLOWED_OPERATOR_CHAT_IDS"] = ""
os.environ["BUSINESS_NAME"] = "Sister Painting"
os.environ["BUSINESS_ABN"] = "11222333444"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, get_connection
from src.agents.channel import ChannelAgent, ChannelError
from src.gate import ConstitutionGate
from src.queue import ApprovalQueue
from src.models import DraftType


def _check(label, cond):
    print(("PASS" if cond else "FAIL") + " :: " + label)
    if not cond:
        raise AssertionError(label)


def main():
    init_db()
    ch = ChannelAgent()
    g = ConstitutionGate()
    q = ApprovalQueue()

    # 1) draft_gbp_post -> GBP_POST DRAFT (never posts)
    d = ch.draft_gbp_post("Fresh interior repaint in Marrickville this week.")
    _check("gbp draft type = gbp_post", d.draft_type == DraftType.GBP_POST)
    _check("gbp draft persisted + has content", len(d.content) > 20)
    _check("gbp draft carries the CTA", "free" in d.content.lower())

    # 2) clean GBP passes the (offline, deterministic) gate; superlative SOFT_FLAGs
    _check("clean gbp gate PASS", g.check(d).status.value == "pass")
    d_bad = ch.draft_gbp_post("We are the best painters in Sydney, guaranteed.")
    _check("superlative gbp -> SOFT_FLAG", g.check(d_bad).status.value == "soft_flag")

    # 3) publish WITHOUT approval -> ChannelError (INV-1)
    raised = False
    try:
        ch.publish(d.id)
    except ChannelError:
        raised = True
    _check("publish without approval REFUSED (INV-1)", raised)

    # 4) Gate -> Queue -> APPROVE -> publish() returns a preview (no live post)
    action = q.submit(d)
    # still pending -> publish must still refuse
    raised2 = False
    try:
        ch.publish(d.id)
    except ChannelError:
        raised2 = True
    _check("publish refused while only PENDING (not approved)", raised2)

    q.approve(action.id, operator_chat_id=123456)
    preview = ch.publish(d.id, operator_chat_id=123456)
    _check("publish after APPROVE returns preview", preview["draft_id"] == d.id)
    _check("preview is NOT live-posted (MVP)", preview["live_posted"] is False)
    _check("preview channel = gbp", preview["channel"] == "gbp")

    # audit recorded the PUBLISH as preview-only
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT payload FROM audit_entries WHERE event_type='PUBLISH' "
            "AND entity_id=? ORDER BY rowid DESC LIMIT 1", (d.id,)
        ).fetchone()
    finally:
        conn.close()
    _check("PUBLISH audit entry exists", row is not None)
    _check("PUBLISH audit marked preview_only", "preview_only" in row["payload"])

    # 5) orchestrator.kickoff_gbp_post: draft -> Gate -> Queue (nothing posted)
    import types
    sys.modules.setdefault("anthropic", types.ModuleType("anthropic"))
    sys.modules["anthropic"].Anthropic = object
    sys.modules.setdefault("httpx", types.ModuleType("httpx"))
    from src.orchestrator import Orchestrator
    orch = Orchestrator()
    res = orch.kickoff_gbp_post("Autumn is a great time to repaint your Glebe home.")
    _check("orch gbp status drafted", res["status"] == "drafted")
    _check("orch gbp gate PASS", res["gate_status"] == "pass")
    _check("orch gbp queued", res["queued"] is True)
    _check("orch gbp draft_type gbp_post", res["draft_type"] == "gbp_post")

    # 6) the orchestrator-queued (but unapproved) gbp draft cannot be published
    raised3 = False
    try:
        ch.publish(res["draft_id"])
    except ChannelError:
        raised3 = True
    _check("orch-queued draft not publishable until approved", raised3)

    print("\nALL CHANNEL (P4) CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    finally:
        for p in (_TMP_DB, _TMP_DB + "-wal", _TMP_DB + "-shm", _TMP_DB + ".KILL"):
            try:
                os.remove(p)
            except OSError:
                pass
