"""
Telegram Bot -- Brushline (TG-01)
Single operator channel. All HITL interaction goes through here.

Security (TG-01 s5):
  - Only ALLOWED_OPERATOR_CHAT_IDS may send commands OR press buttons
    (allow-list enforced on BOTH messages and callback_query -- a button
    press is just as much an operator action as a typed command, KB-05 s7).
  - Token in env, never in code
  - No PII in chat history beyond what's necessary for approval
  - Prompt injection guard: lead content = data, not instruction

Commands:
  /queue       -- show pending approvals (cards with inline keyboard)
  /spend       -- show today's spend vs caps
  /kill        -- activate kill switch
  /kill_off    -- deactivate kill switch
  /status      -- system status

Inline keyboard buttons (callback_data):
  approve:<action_id>
  edit:<action_id>      -- bot then waits for the operator's next message as
                            the new content (single-operator chat, so the
                            next message from an authorised chat_id is
                            unambiguous)
  reject:<action_id>     -- bot then waits for the operator's next message
                            as the rejection reason (mandatory, KB-05 s2)

Card data is returned as plain dicts (text + button rows), independent of
python-telegram-bot's types, so the approval flow is testable offline
without the SDK installed. The thin python-telegram-bot adapter only lives
in run() (Phase 3 network wiring, not unit-testable / not yet connected).
"""
from __future__ import annotations

import logging
from typing import Optional

import hashlib

from .config import config
from .queue import ApprovalQueue
from . import governance, audit


def _chat_id_ref(chat_id: int) -> str:
    """Stable hash-ref for an unauthorised chat id. Python hash() is salted
    per-process (PYTHONHASHSEED), so it could not correlate a repeat intruder
    across restarts -- sha256 can (arch review 2026-07-02)."""
    return "sha256:" + hashlib.sha256(str(chat_id).encode()).hexdigest()[:16]

logger = logging.getLogger(__name__)


def _is_authorised(chat_id: int) -> bool:
    """
    Check if chat_id is in the operator allow-list (TG-01 s5, INV-1).
    Rejects ALL messages from unknown chat IDs -- no exceptions.
    """
    return chat_id in config.ALLOWED_OPERATOR_CHAT_IDS


def _fmt_card(item: dict) -> dict:
    """
    Build a queue-item card: display text + inline keyboard button row.
    item: one row from ApprovalQueue.get_pending().
    """
    action_id = item["id"]
    priority_icon = {
        "critical": "[CRITICAL]",
        "high": "[HIGH]",
        "medium": "[MEDIUM]",
        "low": "[low]",
    }.get(item.get("priority", "low"), "[low]")
    expired_tag = " *EXPIRED-SLA*" if item.get("expired") else ""
    body = item.get("content", "")
    preview = body if len(body) <= 500 else body[:497] + "..."

    text = (
        f"{priority_icon}{expired_tag} {item.get('draft_type', '?')}\n"
        f"draft_id: {item.get('draft_id')}\n"
        f"action_id: {action_id}\n"
        f"created: {item.get('created_at')}\n"
        f"sla_deadline: {item.get('sla_deadline')}\n"
        f"---\n{preview}"
    )
    buttons = [[
        {"text": "Approve", "callback_data": f"approve:{action_id}"},
        {"text": "Edit", "callback_data": f"edit:{action_id}"},
        {"text": "Reject", "callback_data": f"reject:{action_id}"},
    ]]
    return {"action_id": action_id, "text": text, "buttons": buttons}


class BrushlineBot:
    """
    Telegram bot interface for Brushline.
    In Phase 3, this wraps python-telegram-bot Application (run()).
    Command/callback handlers are pure Python and testable without it.
    """

    def __init__(self):
        self.orchestrator = None  # injected by main.py
        self.approval_queue = ApprovalQueue()
        # Single-operator awaiting-reply state: chat_id -> {"mode": "edit"|"reject", "action_id": str}
        self._awaiting: dict[int, dict] = {}

    # -- Entrypoint -----------------------------------------------------------------

    async def handle_message(self, chat_id: int, text: str) -> Optional[str]:
        """
        Process an incoming message from a Telegram user.
        Returns response string (or None if unauthorised/silent).
        """
        if not _is_authorised(chat_id):
            logger.warning("Rejected message from unauthorised chat_id=%s", chat_id)
            audit.append("UNAUTHORISED_ACCESS", "telegram", {
                "chat_id_hash": _chat_id_ref(chat_id),  # no raw chat_id in audit
                "channel": "message",
            })
            return None  # silent reject

        text = text.strip()

        # If we're mid-flow waiting for an edit body or a reject reason,
        # treat this message as that payload (not a command).
        pending = self._awaiting.pop(chat_id, None)
        if pending is not None:
            return self._resolve_awaiting(chat_id, pending, text)

        if text == "/queue":
            return await self._cmd_queue(chat_id)
        elif text == "/spend":
            return await self._cmd_spend(chat_id)
        elif text == "/kill":
            return await self._cmd_kill(chat_id)
        elif text == "/kill_off":
            return await self._cmd_kill_off(chat_id)
        elif text == "/status":
            return await self._cmd_status(chat_id)
        else:
            return "Unknown command. Try /queue /spend /kill /status"

    async def handle_callback(self, chat_id: int, callback_data: str) -> Optional[str]:
        """
        Process an inline-keyboard button press.
        INV-1 / TG-01 s5: the allow-list is enforced HERE too, not just on
        handle_message -- a callback is an operator action like any other.
        """
        if not _is_authorised(chat_id):
            logger.warning("Rejected callback from unauthorised chat_id=%s", chat_id)
            audit.append("UNAUTHORISED_ACCESS", "telegram", {
                "chat_id_hash": _chat_id_ref(chat_id),
                "channel": "callback",
            })
            return None  # silent reject

        try:
            action, action_id = callback_data.split(":", 1)
        except ValueError:
            return "Malformed button."

        if action == "approve":
            try:
                self.approval_queue.approve(action_id, chat_id)
                return f"Approved {action_id}."
            except Exception as exc:
                return f"Could not approve: {exc}"

        elif action == "edit":
            self._awaiting[chat_id] = {"mode": "edit", "action_id": action_id}
            return f"Send the new content for {action_id}."

        elif action == "reject":
            self._awaiting[chat_id] = {"mode": "reject", "action_id": action_id}
            return f"Send the rejection reason for {action_id}."

        return f"Unknown action '{action}'."

    def _resolve_awaiting(self, chat_id: int, pending: dict, text: str) -> str:
        action_id = pending["action_id"]
        if pending["mode"] == "reject":
            try:
                self.approval_queue.reject(action_id, chat_id, text)
                return f"Rejected {action_id}: {text}"
            except Exception as exc:
                return f"Could not reject: {exc}"

        if pending["mode"] == "edit":
            try:
                result = self.approval_queue.edit_and_regate(action_id, chat_id, text)
            except Exception as exc:
                return f"Could not edit: {exc}"
            if not result["regate"]:
                return f"Edit recorded for {action_id} (trivial change, no re-check needed)."
            if result["ready_to_publish"]:
                return f"Edit re-checked for {action_id}: PASS. Ready to publish."
            return (
                f"Edit re-checked for {action_id}: flagged ({result['gate_status']}). "
                f"Re-queued as {result['requeued_action_id']} for fresh review."
            )

        return "Nothing pending."

    # -- Commands -------------------------------------------------------------------

    async def _cmd_queue(self, chat_id: int) -> str:
        """Show pending approval items as cards (text form; buttons listed inline)."""
        self.approval_queue.escalate_overdue()
        items = self.approval_queue.get_pending()
        if not items:
            return "Approval Queue is empty."
        cards = [_fmt_card(i) for i in items]
        lines = [f"Approval Queue -- {len(cards)} pending"]
        for c in cards:
            lines.append(c["text"])
            lines.append("[Approve] [Edit] [Reject]")
            lines.append("")
        return "\n".join(lines).strip()

    async def _cmd_spend(self, chat_id: int) -> str:
        """Show today's spend vs caps."""
        status = governance.get_spend_status()
        ks = "ACTIVE" if status["kill_switch_active"] else "inactive"
        return (
            f"Spend Status -- {status['date']}\n"
            f"Today: AUD ${status['daily_total_aud']:.4f} / "
            f"${status['daily_cap_aud']:.2f} cap\n"
            f"Remaining: AUD ${status['remaining_aud']:.4f}\n"
            f"Per-action cap: AUD ${status['per_action_cap_aud']:.2f}\n"
            f"Events today: {status['events_today']}\n"
            f"Kill switch: {ks}"
        )

    async def _cmd_kill(self, chat_id: int) -> str:
        """Activate kill switch -- halts all external actions immediately."""
        governance.activate_kill_switch(chat_id, "Operator command via Telegram")
        return (
            "KILL SWITCH ACTIVATED\n"
            "All external actions halted. Send /kill_off to resume."
        )

    async def _cmd_kill_off(self, chat_id: int) -> str:
        """Deactivate kill switch."""
        if not governance.is_kill_switch_active():
            return "Kill switch is not active."
        governance.deactivate_kill_switch(chat_id)
        return "Kill switch deactivated. System resumed."

    async def _cmd_status(self, chat_id: int) -> str:
        """System health status."""
        from . import audit as audit_module
        chain_ok, chain_msg = audit_module.verify_chain()
        spend = governance.get_spend_status()
        ks = "ACTIVE" if spend["kill_switch_active"] else "OK"
        chain_icon = "OK" if chain_ok else "BROKEN"
        overdue = self.approval_queue.escalate_overdue()
        pending_n = len(self.approval_queue.get_pending())
        return (
            f"Brushline Status\n"
            f"Kill switch: {ks}\n"
            f"Audit chain: {chain_icon} {chain_msg[:60]}\n"
            f"Spend today: AUD ${spend['daily_total_aud']:.4f}\n"
            f"Pending approvals: {pending_n} ({len(overdue)} just escalated for SLA breach)\n"
            f"Phase: 3 (approval queue live)"
        )

    # -- Phase 3+: live network wiring (not unit-testable, not yet connected) ----

    async def run(self) -> None:
        """
        Start the bot against the real Telegram API (python-telegram-bot).
        Phase 3 logic (handle_message/handle_callback) is implemented and
        offline-testable; this method is the thin network adapter and is
        intentionally still a placeholder until deployed (see infra-control).
        """
        logger.info("Telegram bot -- handlers implemented; network adapter not yet wired.")
        if not config.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Bot cannot start.")
            return
        if not config.ALLOWED_OPERATOR_CHAT_IDS:
            logger.warning("ALLOWED_OPERATOR_CHAT_IDS not set. All messages will be rejected.")
