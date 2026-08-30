"""
Human Approval Queue -- Brushline (KB-05, INV-1)

Every draft MUST pass through here before any external action.
No auto-approve -- not even on SLA expiry (SLA only raises priority + notifies).

Operator actions (via Telegram):
  APPROVE  -> draft proceeds to Publish/Send/Sync
  EDIT     -> operator sends new content -> REGATE if material change
  REJECT   -> draft discarded; reason logged

State machine (KB-05 s1):
  PENDING -> APPROVED            (operator approves as-is)
  PENDING -> REJECTED            (operator rejects, reason required)
  PENDING -> EDITED              (operator submits new content)
    trivial edit  (formatting only) -> treated as approved, no REGATE
    material edit (claim/commercial text changed) -> REGATE:
      gate PASS       -> ready to publish (regate_status="pass")
      gate flags it   -> a NEW ApprovalAction is queued (PENDING) on the
                         edited content for fresh human review -- the
                         operator's edit is NEVER auto-approved past a flag
                         (KB-05 s1 note: a human edit must not sneak an
                         ACL-incomplete claim past the gate).

"Material edit" threshold (KB-05 s8 leaves this as an open config item):
  interim rule, deliberately conservative per INV-1 -- any change beyond
  whitespace/case normalisation is material. The deterministic gate is
  zero-cost (gate.py), so re-checking on every substantive edit is free
  and safe; only a true no-op (typo-casing/whitespace) skips REGATE.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta
from typing import Optional

from .config import config
from .database import get_connection
from .models import ApprovalAction, ApprovalStatus, Draft, DraftType
from . import audit


class ApprovalQueueError(Exception):
    pass


# -- material-edit heuristic (module-level, no DB dependency, unit-testable) ----

def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def is_material_edit(original: str, edited: str) -> bool:
    """True unless the edit is whitespace/case-only (KB-05 s1/s8)."""
    return _normalise(original) != _normalise(edited)


class ApprovalQueue:
    """
    Manages the HITL approval lifecycle for all Brushline drafts.

    No method here calls check_and_enforce(): approve/reject/edit are
    human decisions, not auto-executions (INV-3 governs spend-bearing
    external actions -- those live in Gate/Channel/LeadCapture). The kill
    switch and spend cap apply at the point something is actually
    published/sent/synced, not at the point a human records a decision.
    """

    # -- submit ------------------------------------------------------------------

    def submit(self, draft: Draft) -> ApprovalAction:
        """
        Submit a draft to the approval queue.
        Priority and SLA deadline are derived from draft_type (KB-05 s3).
        Returns the pending ApprovalAction.
        """
        draft_type = draft.draft_type.value if hasattr(draft.draft_type, "value") else str(draft.draft_type)
        priority = config.approval_priority(draft_type)
        sla_minutes = config.approval_sla_minutes(draft_type)
        created_at = datetime.utcnow()
        sla_deadline = created_at + timedelta(minutes=sla_minutes)

        action = ApprovalAction(
            id=str(uuid.uuid4()),
            draft_id=draft.id,
            status=ApprovalStatus.PENDING,
            created_at=created_at,
            priority=priority,
            sla_deadline=sla_deadline,
        )
        self._save(action)
        audit.append("APPROVAL_SUBMITTED", draft.id, {
            "action_id": action.id,
            "draft_type": draft_type,
            "priority": priority,
            "sla_deadline": sla_deadline.isoformat(),
        })
        return action

    # -- low-level decision recorder (immutable audit trail) ---------------------

    def record_decision(self, action_id: str, decision: ApprovalStatus,
                        operator_chat_id: int, edited_content: Optional[str] = None,
                        reason: Optional[str] = None) -> ApprovalAction:
        """
        Record operator's decision. Persists + audits unconditionally.
        Prefer approve()/reject()/edit_and_regate() for the validated,
        state-checked entrypoints -- this is the shared low-level writer.
        """
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM approval_actions WHERE id = ?", (action_id,)
            ).fetchone()
            if not row:
                raise ApprovalQueueError(f"ApprovalAction {action_id} not found")

            acted_at = datetime.utcnow().isoformat()
            conn.execute(
                """UPDATE approval_actions
                   SET status=?, operator_chat_id=?, edited_content=?,
                       reason=?, acted_at=?
                   WHERE id=?""",
                (decision.value, operator_chat_id, edited_content,
                 reason, acted_at, action_id)
            )
            conn.commit()
        finally:
            conn.close()

        audit.append("APPROVAL_DECISION", row["draft_id"], {
            "action_id": action_id,
            "decision": decision.value,
            "operator_chat_id": operator_chat_id,
            "has_edit": edited_content is not None,
            "reason": reason,
        })

        return ApprovalAction(
            id=action_id,
            draft_id=row["draft_id"],
            status=decision,
            operator_chat_id=operator_chat_id,
            edited_content=edited_content,
            reason=reason,
            acted_at=datetime.utcnow(),
            priority=row["priority"],
            sla_deadline=datetime.fromisoformat(row["sla_deadline"]) if row["sla_deadline"] else None,
            expired=bool(row["expired"]),
        )

    # -- validated entrypoints -----------------------------------------------------

    def approve(self, action_id: str, operator_chat_id: int) -> ApprovalAction:
        """PENDING -> APPROVED. Raises if the item isn't pending (no double-decide)."""
        action = self._require_pending(action_id)
        result = self.record_decision(action_id, ApprovalStatus.APPROVED, operator_chat_id)
        return result

    def reject(self, action_id: str, operator_chat_id: int, reason: str) -> ApprovalAction:
        """PENDING -> REJECTED. Reason is mandatory (KB-05 s2)."""
        if not reason or not reason.strip():
            raise ApprovalQueueError("Reject requires a non-empty reason (KB-05 s2).")
        self._require_pending(action_id)
        return self.record_decision(action_id, ApprovalStatus.REJECTED, operator_chat_id, reason=reason.strip())

    def edit_and_regate(self, action_id: str, operator_chat_id: int,
                        edited_content: str) -> dict:
        """
        PENDING -> EDITED. If the edit is material, the new content is
        re-submitted to the Constitution Gate (REGATE) before it can be
        treated as approved.

        Returns a dict (not just ApprovalAction, since a material edit may
        spawn a brand-new ApprovalAction for re-review):
          {
            "action_id": str,            # the original action (now EDITED)
            "draft_id": str,              # original draft id
            "regate": bool,               # whether REGATE ran
            "gate_status": str | None,    # GateStatus value if regate ran
            "ready_to_publish": bool,     # True only if no flags block it
            "new_draft_id": str | None,   # edited content's own Draft row
            "requeued_action_id": str | None,  # set if a new flag re-queued it
          }
        """
        original_action = self._require_pending(action_id)
        original_draft = self._get_draft(original_action["draft_id"])
        if original_draft is None:
            raise ApprovalQueueError(f"Draft {original_action['draft_id']} not found")

        # Immutable record of exactly what the operator submitted (KB-05 s2).
        self.record_decision(action_id, ApprovalStatus.EDITED, operator_chat_id,
                              edited_content=edited_content)

        material = is_material_edit(original_draft["content"], edited_content)

        if not material:
            audit.append("APPROVAL_EDIT_TRIVIAL", original_action["draft_id"], {
                "action_id": action_id,
            })
            return {
                "action_id": action_id,
                "draft_id": original_action["draft_id"],
                "regate": False,
                "gate_status": None,
                "ready_to_publish": True,
                "new_draft_id": None,
                "requeued_action_id": None,
            }

        # Material change -> REGATE on a new draft snapshot (preserve original
        # draft's history; the operator-authored text becomes its own record).
        from .gate import ConstitutionGate

        prior_gate = self._get_latest_gate_result(original_action["draft_id"])
        consent_verified = bool(prior_gate["spam_consent_ok"]) if prior_gate else True

        new_draft = Draft(
            lead_id=original_draft["lead_id"],
            draft_type=DraftType(original_draft["draft_type"]),
            content=edited_content,
            agent_id="human_operator",
            model_used="operator_edit",
        )
        self._save_draft(new_draft)
        gate_result = ConstitutionGate().check(new_draft, consent_verified=consent_verified)

        self._set_regate_result(action_id, gate_result.status.value, new_draft.id)

        audit.append("APPROVAL_EDIT_REGATE", original_action["draft_id"], {
            "action_id": action_id,
            "new_draft_id": new_draft.id,
            "gate_status": gate_result.status.value,
            "flags": gate_result.flags,
        })

        if gate_result.status.value == "pass":
            return {
                "action_id": action_id,
                "draft_id": original_action["draft_id"],
                "regate": True,
                "gate_status": gate_result.status.value,
                "ready_to_publish": True,
                "new_draft_id": new_draft.id,
                "requeued_action_id": None,
            }

        # New flag surfaced by the edit -> re-queue for fresh human review.
        # INV-1: never auto-approve past a flag, even one the operator caused.
        requeued = self.submit(new_draft)
        audit.append("APPROVAL_REQUEUED_AFTER_REGATE", original_action["draft_id"], {
            "original_action_id": action_id,
            "requeued_action_id": requeued.id,
            "gate_status": gate_result.status.value,
            "flags": gate_result.flags,
        })
        return {
            "action_id": action_id,
            "draft_id": original_action["draft_id"],
            "regate": True,
            "gate_status": gate_result.status.value,
            "ready_to_publish": False,
            "new_draft_id": new_draft.id,
            "requeued_action_id": requeued.id,
        }

    # -- SLA escalation (INV-1: priority + notify only, NEVER auto-approve) ------

    def escalate_overdue(self) -> list[dict]:
        """
        Find PENDING items past their SLA deadline, bump priority to
        'critical', mark expired=1, audit-log it, and return the list so a
        caller (Telegram bot polling loop) can notify the operator.
        This NEVER changes status -- only priority/expired (INV-1).
        """
        now_iso = datetime.utcnow().isoformat()
        conn = get_connection()
        try:
            rows = conn.execute(
                """SELECT a.id, a.draft_id, a.priority, a.sla_deadline,
                          d.draft_type
                   FROM approval_actions a JOIN drafts d ON d.id = a.draft_id
                   WHERE a.status = 'pending' AND a.expired = 0
                     AND a.sla_deadline IS NOT NULL AND a.sla_deadline < ?""",
                (now_iso,)
            ).fetchall()
            escalated = [dict(r) for r in rows]
            for item in escalated:
                conn.execute(
                    "UPDATE approval_actions SET priority='critical', expired=1 WHERE id=?",
                    (item["id"],)
                )
            conn.commit()
        finally:
            conn.close()

        for item in escalated:
            audit.append("APPROVAL_SLA_EXPIRED", item["draft_id"], {
                "action_id": item["id"],
                "draft_type": item["draft_type"],
                "previous_priority": item["priority"],
                "sla_deadline": item["sla_deadline"],
            })
        return escalated

    # -- reads ---------------------------------------------------------------------

    def get_pending(self) -> list[dict]:
        """Return all pending approval items, highest priority + oldest first."""
        conn = get_connection()
        try:
            rows = conn.execute(
                """SELECT a.id, a.draft_id, a.created_at, a.priority,
                          a.sla_deadline, a.expired,
                          d.draft_type, d.content, d.lead_id
                   FROM approval_actions a
                   JOIN drafts d ON d.id = a.draft_id
                   WHERE a.status = 'pending'
                   ORDER BY CASE a.priority
                       WHEN 'critical' THEN 0
                       WHEN 'high' THEN 1
                       WHEN 'medium' THEN 2
                       ELSE 3
                   END ASC, a.created_at ASC"""
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # -- internal helpers ------------------------------------------------------------

    def _require_pending(self, action_id: str) -> dict:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM approval_actions WHERE id = ?", (action_id,)
            ).fetchone()
        finally:
            conn.close()
        if not row:
            raise ApprovalQueueError(f"ApprovalAction {action_id} not found")
        if row["status"] != ApprovalStatus.PENDING.value:
            raise ApprovalQueueError(
                f"ApprovalAction {action_id} is not pending (status={row['status']}); "
                f"cannot be decided twice."
            )
        return dict(row)

    def _get_draft(self, draft_id: str) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def _get_latest_gate_result(self, draft_id: str) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM gate_results WHERE draft_id = ? ORDER BY checked_at DESC LIMIT 1",
                (draft_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def _set_regate_result(self, action_id: str, gate_status: str, new_draft_id: str) -> None:
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE approval_actions SET regate_status=?, regate_draft_id=? WHERE id=?",
                (gate_status, new_draft_id, action_id)
            )
            conn.commit()
        finally:
            conn.close()

    def _save(self, action: ApprovalAction) -> None:
        priority = action.priority.value if hasattr(action.priority, "value") else str(action.priority)
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO approval_actions
                   (id, draft_id, status, operator_chat_id, edited_content,
                    reason, acted_at, created_at, priority, sla_deadline,
                    expired, regate_status, regate_draft_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (action.id, action.draft_id, action.status.value,
                 action.operator_chat_id, action.edited_content,
                 action.reason, None, action.created_at.isoformat(),
                 priority,
                 action.sla_deadline.isoformat() if action.sla_deadline else None,
                 int(action.expired), action.regate_status, action.regate_draft_id)
            )
            conn.commit()
        finally:
            conn.close()

    def _save_draft(self, draft: Draft) -> None:
        """Persist an operator-authored draft (created during edit_and_regate)."""
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO drafts
                   (id, lead_id, draft_type, content, agent_id, model_used,
                    tokens_in, tokens_out, cost_usd, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (draft.id, draft.lead_id, draft.draft_type.value, draft.content,
                 draft.agent_id, draft.model_used, draft.tokens_in, draft.tokens_out,
                 draft.cost_usd, draft.created_at.isoformat())
            )
            conn.commit()
        finally:
            conn.close()
