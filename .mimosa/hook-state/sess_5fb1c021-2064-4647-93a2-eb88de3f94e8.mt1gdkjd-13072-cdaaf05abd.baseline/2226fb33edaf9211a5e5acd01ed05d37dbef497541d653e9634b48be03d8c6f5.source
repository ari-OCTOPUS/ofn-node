#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""approval_state_machine.py — ماشینِ حالتِ صریحِ تأییدِ انسانی (HITL) برای OCTOPUS.

هدف: هیچ پرشِ بی‌صدا (silent jump) بین وضعیت‌های تأیید ممکن نیست.
هر transition باید صریح، لاگ‌شده، و با هویتِ actor مشخص باشد.

قرارداد:
  - canonical statuses: suggested → queued → owner_approved → executed
                         + rejected, expired, superseded, dry_run
  - verdicts: approve, deny, expire, supersede
  - هر transition → append به _ops/state/approval-log.jsonl
  - mapping با دنیایِ قدیمی (pending/approved/denied/settled) حفظ می‌شود

$0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

# ─── bootstrap مسیر برای opslib ─────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import opslib  # noqa: E402

logger = logging.getLogger(__name__)

# ─── مسیرها ──────────────────────────────────────────────────────────────
APPROVAL_LOG_PATH = opslib.STATE_DIR / "approval-log.jsonl"


# ═══════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════

class ActionStatus(str, Enum):
    """وضعیتِ کانونیکالِ یک action."""
    SUGGESTED = "suggested"
    QUEUED = "queued"
    OWNER_APPROVED = "owner_approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    DRY_RUN = "dry_run"


class Verdict(str, Enum):
    """رأیِ صریحِ مالک."""
    APPROVE = "approve"
    DENY = "deny"
    EXPIRE = "expire"
    SUPERSEDE = "supersede"


class RollbackClass(str, Enum):
    """دسته‌بندیِ برگشت‌پذیریِ action."""
    REVERSIBLE = "reversible"
    IRREVERSIBLE = "irreversible"
    REQUIRES_MANUAL = "requires_manual"
    UNKNOWN = "unknown"


# ═══════════════════════════════════════════════════════════════════════════
# Dataclass: canonical action object
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ActionObject:
    """یک action در صفِ تأیید — مدلِ کانونیکالِ Wave 6.

    Fields:
        action_id: unique identifier
        action_type: money | code_change | rfc | operational | system
        source: _ops | 4d_system | telegram | system
        amount_aud: مبلغ به AUD (برای money items)
        proposal_rationale: توضیحِ کوتاهِ پیشنهاد
        requested_at: ISO timestampِ ایجاد
        status: canonical status enum
        verdict: رأیِ صریح (approve/deny/expire/supersede) — فقط وقتی status تغییر کرد
        verdict_owner: هویتِ رأی‌دهنده (owner_telegram / owner_ui / system / agent)
        verdict_timestamp: ISO timestampِ رأی
        verdict_rationale: توضیحِ رأی (مثلاً دلیلِ رد)
        execution_result: success | failure | cancelled | expired
        execution_timestamp: ISO timestampِ اجرا
        rollback_class: reversible | irreversible | requires_manual | unknown
        dry_run: True = فقط shadow/dry-run، اجرایِ واقعی نبود
        meta: dictِ اضافی (effect_id، token، gate_status، ...)
    """
    action_id: str
    action_type: str = "operational"
    source: str = "_ops"
    amount_aud: float = 0.0
    proposal_rationale: str = ""
    requested_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    status: ActionStatus = ActionStatus.SUGGESTED
    verdict: Verdict | None = None
    verdict_owner: str = ""
    verdict_timestamp: str = ""
    verdict_rationale: str = ""
    execution_result: str = ""
    execution_timestamp: str = ""
    rollback_class: RollbackClass = RollbackClass.UNKNOWN
    dry_run: bool = True
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        d["verdict"] = self.verdict.value if self.verdict else None
        d["rollback_class"] = self.rollback_class.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ActionObject:
        allowed = cls.__dataclass_fields__
        kwargs: dict[str, Any] = {}
        for k, v in d.items():
            if k not in allowed:
                continue
            if k == "status" and v:
                kwargs[k] = ActionStatus(v)
            elif k == "verdict" and v:
                kwargs[k] = Verdict(v)
            elif k == "rollback_class" and v:
                kwargs[k] = RollbackClass(v)
            else:
                kwargs[k] = v
        return cls(**kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# State transition graph
# ═══════════════════════════════════════════════════════════════════════════

# allowed_transitions[from_status] = {to_status: required_verdict_or_None}
# None = system-driven (no owner verdict needed)
# "any" = any verdict that logically matches the to_status
_ALLOWED_TRANSITIONS: dict[ActionStatus, dict[ActionStatus, str | None]] = {
    ActionStatus.SUGGESTED: {
        ActionStatus.QUEUED: None,
        ActionStatus.REJECTED: Verdict.DENY.value,
        ActionStatus.EXPIRED: Verdict.EXPIRE.value,
        ActionStatus.SUPERSEDED: Verdict.SUPERSEDE.value,
    },
    ActionStatus.QUEUED: {
        ActionStatus.OWNER_APPROVED: Verdict.APPROVE.value,
        ActionStatus.REJECTED: Verdict.DENY.value,
        ActionStatus.EXPIRED: Verdict.EXPIRE.value,
        ActionStatus.SUPERSEDED: Verdict.SUPERSEDE.value,
        ActionStatus.DRY_RUN: Verdict.APPROVE.value,  # owner says "test first"
    },
    ActionStatus.OWNER_APPROVED: {
        ActionStatus.EXECUTED: None,
        ActionStatus.DRY_RUN: None,
        ActionStatus.REJECTED: Verdict.DENY.value,  # owner changed mind before exec
    },
    ActionStatus.DRY_RUN: {
        ActionStatus.EXECUTED: Verdict.APPROVE.value,  # after dry-run, owner confirms
        ActionStatus.REJECTED: Verdict.DENY.value,
    },
    # Terminal states — no outbound transitions
    ActionStatus.EXECUTED: {},
    ActionStatus.REJECTED: {},
    ActionStatus.EXPIRED: {},
    ActionStatus.SUPERSEDED: {},
}


class InvalidTransitionError(ValueError):
    """پرشِ حالتِ غیرمجاز."""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# State machine
# ═══════════════════════════════════════════════════════════════════════════

class ApprovalStateMachine:
    """ماشینِ حالتِ صریح. هر transition لاگ می‌شود."""

    def __init__(self, log_path: Path | str | None = None):
        self.log_path = Path(log_path) if log_path else APPROVAL_LOG_PATH

    def validate_transition(
        self,
        from_status: ActionStatus,
        to_status: ActionStatus,
        verdict: Verdict | None = None,
    ) -> None:
        """بررسی می‌کند که transition مجاز است. اگر نه → InvalidTransitionError."""
        allowed = _ALLOWED_TRANSITIONS.get(from_status, {})
        if to_status not in allowed:
            raise InvalidTransitionError(
                f"Transition {from_status.value} → {to_status.value} is not allowed."
            )
        required = allowed[to_status]
        if required is not None:
            if verdict is None:
                raise InvalidTransitionError(
                    f"Transition {from_status.value} → {to_status.value} "
                    f"requires a verdict (expected: {required})."
                )
            if verdict.value != required:
                raise InvalidTransitionError(
                    f"Transition {from_status.value} → {to_status.value} "
                    f"requires verdict={required}, got {verdict.value}."
                )

    def transition(
        self,
        action: ActionObject,
        to_status: ActionStatus,
        verdict: Verdict | None = None,
        verdict_owner: str = "",
        verdict_rationale: str = "",
        dry_run: bool | None = None,
    ) -> ActionObject:
        """یک action را به وضعیتِ جدید می‌برد (با validation) و لاگ می‌نویسد.

        Returns:
            ActionObject updated ( mutated in-place برای سادگی).
        """
        self.validate_transition(action.status, to_status, verdict=verdict)

        now = datetime.now(timezone.utc).isoformat()

        # update action
        old_status = action.status
        action.status = to_status
        if verdict is not None:
            action.verdict = verdict
        if verdict_owner:
            action.verdict_owner = verdict_owner
        if verdict_rationale:
            action.verdict_rationale = verdict_rationale
        if verdict is not None or to_status in (ActionStatus.EXECUTED, ActionStatus.DRY_RUN):
            action.verdict_timestamp = now
        if dry_run is not None:
            action.dry_run = dry_run
        if to_status == ActionStatus.EXECUTED:
            action.execution_result = "success"
            action.execution_timestamp = now
            action.dry_run = False
        if to_status == ActionStatus.DRY_RUN:
            action.execution_result = "dry_run"
            action.execution_timestamp = now
            action.dry_run = True

        # log transition
        self._log_transition(
            action=action,
            old_status=old_status,
            new_status=to_status,
            verdict=verdict,
            verdict_owner=verdict_owner,
            verdict_rationale=verdict_rationale,
            timestamp=now,
        )
        return action

    def _log_transition(
        self,
        action: ActionObject,
        old_status: ActionStatus,
        new_status: ActionStatus,
        verdict: Verdict | None,
        verdict_owner: str,
        verdict_rationale: str,
        timestamp: str,
    ) -> None:
        """append یک خطِ structured log به approval-log.jsonl."""
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "ts": timestamp,
                "action_id": action.action_id,
                "actor": verdict_owner or "system",
                "action_type": action.action_type,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "verdict": verdict.value if verdict else None,
                "verdict_rationale": verdict_rationale,
                "amount_aud": action.amount_aud,
                "source": action.source,
                "dry_run": action.dry_run,
                "rollback_class": action.rollback_class.value,
            }
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        except OSError as exc:
            logger.warning("approval-log append failed: %s", exc)

    # ═══════════════════════════════════════════════════════════════════════
    # convenience helpers (mapping old world → new)
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def map_old_status(old: str) -> ActionStatus:
        """تبدیلِ وضعیتِ قدیمی (UnifiedQueueItem) به canonical."""
        mapping = {
            "pending": ActionStatus.QUEUED,
            "approved": ActionStatus.OWNER_APPROVED,
            "denied": ActionStatus.REJECTED,
            "settled": ActionStatus.EXECUTED,
            "rejected": ActionStatus.REJECTED,
        }
        return mapping.get(old, ActionStatus.SUGGESTED)

    @staticmethod
    def map_canonical_to_old(status: ActionStatus) -> str:
        """تبدیلِ canonical به وضعیتِ قدیمی (برای backward-compat)."""
        mapping = {
            ActionStatus.SUGGESTED: "pending",
            ActionStatus.QUEUED: "pending",
            ActionStatus.OWNER_APPROVED: "approved",
            ActionStatus.EXECUTED: "settled",
            ActionStatus.REJECTED: "denied",
            ActionStatus.EXPIRED: "denied",
            ActionStatus.SUPERSEDED: "denied",
            ActionStatus.DRY_RUN: "approved",
        }
        return mapping.get(status, "pending")

    @staticmethod
    def required_action_label(status: ActionStatus) -> str:
        """برچسبِ «مالک چه کاری باید بکند» برای UI."""
        labels = {
            ActionStatus.SUGGESTED: "system review",
            ActionStatus.QUEUED: "owner verdict required",
            ActionStatus.OWNER_APPROVED: "awaiting execution",
            ActionStatus.EXECUTED: "completed",
            ActionStatus.REJECTED: "rejected — no action",
            ActionStatus.EXPIRED: "expired — no action",
            ActionStatus.SUPERSEDED: "superseded — no action",
            ActionStatus.DRY_RUN: "dry-run completed — owner confirm to execute",
        }
        return labels.get(status, "unknown")

    @staticmethod
    def rollback_class_for_action(action_type: str) -> RollbackClass:
        """دسته‌بندیِ برگشت‌پذیری بر اساسِ نوعِ action."""
        reversible = {"refresh", "toggle", "copy", "display", "export", "baseline"}
        irreversible = {"spend", "transfer", "delete", "merge", "settle", "execute"}
        manual = {"mining_start", "wallet_transfer", "telegram_send", "lead_publish"}
        at = action_type.lower()
        if at in reversible:
            return RollbackClass.REVERSIBLE
        if at in irreversible:
            return RollbackClass.IRREVERSIBLE
        if at in manual:
            return RollbackClass.REQUIRES_MANUAL
        return RollbackClass.UNKNOWN


# ═══════════════════════════════════════════════════════════════════════════
# Log reader (for extractors / UI)
# ═══════════════════════════════════════════════════════════════════════════

class ApprovalLogReader:
    """خواندنِ approval-log.jsonl برای extractorها."""

    def __init__(self, log_path: Path | str | None = None):
        self.log_path = Path(log_path) if log_path else APPROVAL_LOG_PATH

    def read_all(self) -> list[dict[str, Any]]:
        """همهٔ لاگ‌ها."""
        if not self.log_path.exists():
            return []
        out: list[dict[str, Any]] = []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            pass
        return out

    def recent(self, n: int = 50) -> list[dict[str, Any]]:
        """n لاگِ اخیر."""
        all_logs = self.read_all()
        return all_logs[-n:] if all_logs else []

    def stats(self) -> dict[str, Any]:
        """آمارِ سریع از لاگ."""
        logs = self.read_all()
        total = len(logs)
        by_status: dict[str, int] = {}
        by_verdict: dict[str, int] = {}
        dry_run_count = 0
        live_count = 0
        for rec in logs:
            by_status[rec.get("new_status", "unknown")] = (
                by_status.get(rec.get("new_status", "unknown"), 0) + 1
            )
            v = rec.get("verdict")
            if v:
                by_verdict[v] = by_verdict.get(v, 0) + 1
            if rec.get("dry_run"):
                dry_run_count += 1
            else:
                live_count += 1
        return {
            "total_transitions": total,
            "by_new_status": by_status,
            "by_verdict": by_verdict,
            "dry_run_count": dry_run_count,
            "live_count": live_count,
            "dry_run_ratio": dry_run_count / total if total else 0.0,
        }

    def denial_reasons(self, action_id: str) -> list[str]:
        """دلایلِ رد برای یک action_id (از لاگ)."""
        reasons: list[str] = []
        for rec in self.read_all():
            if rec.get("action_id") == action_id and rec.get("verdict") == "deny":
                r = rec.get("verdict_rationale", "")
                if r:
                    reasons.append(r)
        return reasons


# ═══════════════════════════════════════════════════════════════════════════
# CLI / test helper
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Approval state machine CLI")
    sub = parser.add_subparsers(dest="cmd")

    p_validate = sub.add_parser("validate", help="Validate a transition")
    p_validate.add_argument("--from", dest="from_status", required=True)
    p_validate.add_argument("--to", dest="to_status", required=True)
    p_validate.add_argument("--verdict", default=None)

    p_stats = sub.add_parser("stats", help="Show approval-log stats")

    args = parser.parse_args()
    sm = ApprovalStateMachine()

    if args.cmd == "validate":
        try:
            fs = ActionStatus(args.from_status)
            ts = ActionStatus(args.to_status)
            vd = Verdict(args.verdict) if args.verdict else None
            sm.validate_transition(fs, ts, verdict=vd)
            print(f"OK: {fs.value} → {ts.value} is valid")
        except InvalidTransitionError as exc:
            print(f"INVALID: {exc}")
            raise SystemExit(1)
        except ValueError as exc:
            print(f"BAD_ARG: {exc}")
            raise SystemExit(2)

    elif args.cmd == "stats":
        reader = ApprovalLogReader()
        print(json.dumps(reader.stats(), ensure_ascii=False, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
