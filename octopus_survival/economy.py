"""PAINT-L5-001 episode school — one shared record, five roles, no new envelope.

D-27: bounded growing economic autonomy. The survival loop already owns
halt, campaign Envelope, and 'draft is not sent'. This module owns the
apprentice rungs A0–A6 and the teacher loop. It does not send, does not
open WIRE, and does not mint revenue without a receipt id.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from ofn.config import (
    D27_DAILY_SEND_CAP,
    D27_DAILY_SPEND_CAP_AUD,
    D27_PER_BOARD_BUDGET_DEFAULT,
)

MISSION = "PAINT-L5-001"
KILL_METRIC = "wrong_recipient"

EPISODE_FIELDS = (
    "episode_id",
    "lead_evidence",
    "decision",
    "proposed_action",
    "approval",
    "execution_receipt",
    "cost",
    "revenue",
    "outcome",
    "teacher_correction",
    "lesson",
)

ROLES = frozenset({"sensing", "selling", "execution", "finance", "learning"})
ROLE_WRITES = {
    "sensing": frozenset({"lead_evidence"}),
    "selling": frozenset({"decision", "proposed_action"}),
    "execution": frozenset({"approval", "execution_receipt"}),
    "finance": frozenset({"cost", "revenue"}),
    "learning": frozenset({"teacher_correction", "lesson", "outcome"}),
}

# Distinct from octopus_survival.loop A0–A7 (experiment authority).
RUNGS = ("A0", "A1", "A2", "A3", "A4", "A5", "A6")
DEFAULT_GRANTED = "A1"
CLEAN_TO_PROPOSE_PROMOTION = 3

INDEPENDENT_REWARDS = frozenset({
    "qualified_lead",
    "reply_received",
    "quote_accepted",
    "booking_confirmed",
    "payment_received",
    "profit_after_cost",
    "repeat_customer",
})
FAKE_REWARDS = frozenset({"owner_approved", "tests_green", "docs_complete"})

DANGEROUS = frozenset({
    "wrong_recipient",
    "sent_without_approval",
    "revenue_without_receipt",
    "wire_without_gate",
})


class EconomyError(ValueError):
    """Fail-closed episode or rung refusal."""


def _require_rung(value: str) -> str:
    if value not in RUNGS:
        raise EconomyError(f"unknown-rung: {value!r}")
    return value


def next_rung(current: str) -> str | None:
    _require_rung(current)
    idx = RUNGS.index(current)
    if idx >= len(RUNGS) - 1:
        return None
    return RUNGS[idx + 1]


def prev_rung(current: str) -> str:
    _require_rung(current)
    idx = RUNGS.index(current)
    return RUNGS[0] if idx == 0 else RUNGS[idx - 1]


@dataclass
class Episode:
    episode_id: str
    lead_evidence: Any = None
    decision: Any = None
    proposed_action: Any = None
    approval: Any = None
    execution_receipt: Any = None
    cost: Any = None
    revenue: Any = None
    outcome: Any = None
    teacher_correction: Any = None
    lesson: Any = None
    rewards: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class Economy:
    """One school. All episodes live under state_dir as append-only jsonl."""

    def __init__(
        self,
        state_dir: Path,
        *,
        clock: Callable[[], int],
        granted_level: str = DEFAULT_GRANTED,
        wire_open: bool = False,
        daily_send_cap: int = D27_DAILY_SEND_CAP,
        daily_spend_cap_aud: int = D27_DAILY_SPEND_CAP_AUD,
        per_board_budget_default: int = D27_PER_BOARD_BUDGET_DEFAULT,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._clock = clock
        self.granted_level = _require_rung(granted_level)
        self.wire_open = bool(wire_open)
        self.daily_send_cap = int(daily_send_cap)
        self.daily_spend_cap_aud = int(daily_spend_cap_aud)
        self.per_board_budget_default = int(per_board_budget_default)
        self._episodes: dict[str, Episode] = {}
        self._day: str | None = None
        self._sends_today = 0
        self._spend_today_cents = 0
        # GOV-V6 debt fix 1: a promotion streak is consumed by the grant that
        # used it; already-counted episodes cannot re-propose the next rung.
        self._grant_consumed: set[str] = set()
        # GOV-V6 debt fix 3: each episode's send/spend burns the daily cap once,
        # no matter how many times the slot is re-applied.
        self._capped: set[tuple[str, str]] = set()

    def _path(self, episode_id: str) -> Path:
        return self.state_dir / f"episode-{episode_id}.jsonl"

    def _append(self, episode_id: str, kind: str, payload: Mapping[str, Any]) -> None:
        row = {"kind": kind, "t": self._clock(), "mission": MISSION, **dict(payload)}
        with self._path(episode_id).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    def open(self, episode_id: str) -> Episode:
        if not episode_id or not str(episode_id).strip():
            raise EconomyError("episode-refused: episode_id required")
        if episode_id in self._episodes:
            raise EconomyError(f"episode-exists: {episode_id}")
        ep = Episode(episode_id=episode_id)
        self._episodes[episode_id] = ep
        self._append(episode_id, "EPISODE_OPENED", {"episode_id": episode_id})
        return ep

    def get(self, episode_id: str) -> Episode:
        try:
            return self._episodes[episode_id]
        except KeyError:
            raise EconomyError(f"episode-missing: {episode_id}") from None

    def apply(self, episode_id: str, role: str, fields: Mapping[str, Any]) -> Episode:
        if role not in ROLES:
            raise EconomyError(f"unknown-role: {role!r}")
        allowed = ROLE_WRITES[role]
        extra = set(fields) - allowed
        if extra:
            raise EconomyError(f"role-{role}-cannot-write: {sorted(extra)}")
        ep = self.get(episode_id)

        if role == "sensing":
            evidence = fields.get("lead_evidence")
            if isinstance(evidence, Mapping) and _looks_supply_side(evidence):
                raise EconomyError(KILL_METRIC)
        if role == "execution":
            self._guard_execution(ep, fields)
        if role == "finance":
            self._guard_finance(fields)

        for key, value in fields.items():
            setattr(ep, key, value)
        self._note_caps(episode_id, role, fields)
        self._append(episode_id, "ROLE_APPLY", {"role": role, **dict(fields)})
        return ep

    def _day_key(self) -> str:
        return datetime.fromtimestamp(self._clock(), tz=timezone.utc).strftime(
            "%Y-%m-%d"
        )

    def _roll_day(self) -> None:
        key = self._day_key()
        if self._day != key:
            self._day = key
            self._sends_today = 0
            self._spend_today_cents = 0
            self._capped = set()

    def _note_caps(self, episode_id: str, role: str, fields: Mapping[str, Any]) -> None:
        self._roll_day()
        receipt = fields.get("execution_receipt")
        if (
            role == "execution"
            and isinstance(receipt, Mapping)
            and receipt.get("kind") == "send"
            and (self._day, episode_id, "send") not in self._capped
        ):
            self._capped.add((self._day, episode_id, "send"))
            self._sends_today += 1
        cost = fields.get("cost")
        if (
            role == "finance"
            and isinstance(cost, Mapping)
            and (self._day, episode_id, "spend") not in self._capped
        ):
            self._capped.add((self._day, episode_id, "spend"))
            self._spend_today_cents += int(cost.get("amount_cents") or 0)

    def board_may_spend(self, board_id: str, amount_cents: int) -> None:
        if not board_id or not str(board_id).strip():
            raise EconomyError("board-id-required")
        if amount_cents <= 0:
            raise EconomyError("PARSE_DRIFT: board spend amount_cents")
        if self.per_board_budget_default <= 0:
            raise EconomyError("board-budget-zero")

    def _guard_execution(self, ep: Episode, fields: Mapping[str, Any]) -> None:
        receipt = fields.get("execution_receipt")
        if receipt in (None, "", {}, False):
            return
        if self.granted_level in {"A0", "A1"}:
            raise EconomyError("execution-refused: granted level is draft-only")
        # approval recorded on the episode by an earlier apply still counts
        approved = bool(fields.get("approval") or ep.approval)
        if not approved and self.granted_level == "A2":
            raise EconomyError("execution-refused: A2 needs approval")
        sending = isinstance(receipt, Mapping) and receipt.get("kind") == "send"
        if self.granted_level >= "A3" or sending:
            if not self.wire_open:
                raise EconomyError("execution-refused: WIRE closed")
        if sending:
            self._roll_day()
            if self._sends_today >= self.daily_send_cap:
                raise EconomyError("send-cap")

    def _guard_finance(self, fields: Mapping[str, Any]) -> None:
        cost = fields.get("cost")
        if isinstance(cost, Mapping):
            spend = cost.get("amount_cents")
            if not isinstance(spend, int) or spend < 0:
                raise EconomyError("PARSE_DRIFT: cost amount_cents")
            if spend:
                self._roll_day()
                if self._spend_today_cents + spend > self.daily_spend_cap_aud * 100:
                    raise EconomyError("spend-cap")
        revenue = fields.get("revenue")
        if revenue in (None, "", {}, 0):
            return
        if not isinstance(revenue, Mapping) or not revenue.get("receipt_id"):
            raise EconomyError("revenue_without_receipt")
        cents = revenue.get("amount_cents")
        if not isinstance(cents, int) or cents <= 0:
            raise EconomyError("PARSE_DRIFT: revenue amount_cents")

    def teach(
        self,
        episode_id: str,
        *,
        agent_decision: str,
        teacher_decision: str,
        reason_code: str,
        real_outcome: str,
        lesson: str,
    ) -> Episode:
        if not reason_code or not lesson:
            raise EconomyError("teacher-refused: reason_code and lesson required")
        correction = {
            "agent_decision": agent_decision,
            "teacher_decision": teacher_decision,
            "reason_code": reason_code,
            "real_outcome": real_outcome,
            "lesson": lesson,
        }
        return self.apply(episode_id, "learning", {
            "teacher_correction": correction,
            "lesson": lesson,
            "outcome": real_outcome,
        })

    def reward(self, episode_id: str, kind: str) -> Episode:
        if kind in FAKE_REWARDS:
            raise EconomyError(f"reward-refused: {kind} is not independent")
        if kind not in INDEPENDENT_REWARDS:
            raise EconomyError(f"unknown-reward: {kind}")
        ep = self.get(episode_id)
        if kind not in ep.rewards:
            ep.rewards = ep.rewards + (kind,)
        self._append(episode_id, "REWARD", {"kind": kind})
        return ep

    def mark_dangerous(self, episode_id: str, code: str) -> str:
        if code not in DANGEROUS:
            raise EconomyError(f"unknown-dangerous: {code}")
        self._append(episode_id, "DANGEROUS", {"code": code})
        self.granted_level = prev_rung(self.granted_level)
        return self.granted_level

    def propose_promotion(self) -> str | None:
        """After enough clean taught episodes, propose the next rung.

        A3 stays ungranted while WIRE is closed. Proposal is not a grant.
        Episodes already consumed by an earlier grant never count again
        (GOV-V6 debt fix 1: the streak is single-use per rung).
        """
        clean = 0
        for episode_id, ep in self._episodes.items():
            if episode_id in self._grant_consumed:
                continue
            if ep.decision is None:
                continue
            if ep.teacher_correction is None:
                clean += 1
                continue
            corr = ep.teacher_correction
            if corr.get("agent_decision") == corr.get("teacher_decision"):
                clean += 1
            else:
                clean = 0
        if clean < CLEAN_TO_PROPOSE_PROMOTION:
            return None
        nxt = next_rung(self.granted_level)
        if nxt == "A3" and not self.wire_open:
            return None
        return nxt

    def grant(self, level: str) -> str:
        nxt = _require_rung(level)
        if nxt == "A3" and not self.wire_open:
            raise EconomyError("grant-refused: A3 needs WIRE")
        if RUNGS.index(nxt) > RUNGS.index(self.granted_level) + 1:
            raise EconomyError("grant-refused: skip-rung")
        proposed = self.propose_promotion()
        if nxt != self.granted_level and nxt != proposed:
            raise EconomyError("grant-refused: not proposed")
        if nxt != self.granted_level:
            # consume the streak this grant rode on: every episode that already
            # carries a decision can never re-propose the next rung
            self._grant_consumed.update(
                eid for eid, ep in self._episodes.items() if ep.decision is not None
            )
        self.granted_level = nxt
        return nxt

    def metrics(self) -> dict[str, Any]:
        decided = [ep for ep in self._episodes.values() if ep.decision is not None]
        autonomous = 0
        for ep in decided:
            corr = ep.teacher_correction
            if corr is None or corr.get("agent_decision") == corr.get("teacher_decision"):
                autonomous += 1
        income = 0
        cost = 0
        for ep in self._episodes.values():
            if isinstance(ep.revenue, Mapping) and ep.revenue.get("receipt_id"):
                income += int(ep.revenue.get("amount_cents") or 0)
            if isinstance(ep.cost, Mapping):
                cost += int(ep.cost.get("amount_cents") or 0)
        return {
            "mission": MISSION,
            "granted_level": self.granted_level,
            "episodes": len(self._episodes),
            "autonomous_correct_rate": (
                autonomous / len(decided) if decided else None
            ),
            "verified_net_income_cents": income - cost,
            "wire_open": self.wire_open,
            "daily_send_cap": self.daily_send_cap,
            "daily_spend_cap_aud": self.daily_spend_cap_aud,
            "per_board_budget_default": self.per_board_budget_default,
            "sends_today": self._sends_today,
            "spend_today_cents": self._spend_today_cents,
        }


def _looks_supply_side(evidence: Mapping[str, Any]) -> bool:
    try:
        from ofn.agents.demand_harvest import is_supply_side
    except ImportError:
        text = " ".join(str(v) for v in evidence.values()).lower()
        return "we are hiring" in text or "salary" in text
    return is_supply_side(evidence)


def answers_lead_to_revenue(change: str) -> bool:
    """PR filter: a change that does not touch this loop is not current priority."""
    needles = (
        "lead_evidence", "proposed_action", "approval", "execution_receipt",
        "receipt", "teacher_correction", "lesson", "PAINT-L5", "episode",
        "qualified_lead", "payment_received",
    )
    blob = change.lower()
    return any(n.lower() in blob for n in needles)
