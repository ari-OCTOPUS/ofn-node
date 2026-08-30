"""base.py — قرارداد پایهٔ آداپتور پا (propose-only؛ بدون هیچ اجرا).

قواعد (از طراحی V3 + بازدارنده‌های شورا):
  · هیچ متدی در base اثر جانبی ندارد — فقط داده/پیشنهاد.
  · heartbeat منقضی ⇒ وضعیت «stale» (نه حذف؛ سکوت ≠ مرگ — درس C-014).
  · سقف بودجهٔ per-leg در ثبت لحظه‌ای خوانده می‌شود، نه در base.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

HEARTBEAT_STALE_AFTER_S = 90.0  # رأی V5: لینک همیشه-برقرار؛ سکوت > ۹۰s = هشدار


@dataclass
class HeartbeatStatus:
    leg_id: str
    alive: bool
    stale: bool
    last_beat_ts: float
    observed_ts: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "leg_id": self.leg_id,
            "alive": self.alive,
            "stale": self.stale,
            "last_beat_ts": self.last_beat_ts,
            "observed_ts": self.observed_ts,
        }


@dataclass
class LegProposal:
    proposal_id: str
    leg_id: str
    action: str
    payload: dict[str, Any]
    created_ts: float
    executed: bool = False          # همیشه False در این لایه — اجرا فقط از مسیر گیت

    def as_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "leg_id": self.leg_id,
            "action": self.action,
            "payload": self.payload,
            "created_ts": self.created_ts,
            "executed": self.executed,
        }


class LegAdapter:
    """پایهٔ مشترک همهٔ پاها. زیرکلاس‌ها فقط رفتار خاص را اضافه می‌کنند."""

    leg_id: str = "base"
    budget_cap_aud: float = 0.0     # per-leg؛ صفر = بدون بودجهٔ مصرفی

    def __init__(self) -> None:
        self._last_beat_ts: float = 0.0
        self._proposals: dict[str, LegProposal] = {}

    # ── لینک راه‌دور (OFN) ────────────────────────────────────────────
    def heartbeat(self, ts: Optional[float] = None) -> HeartbeatStatus:
        """ثبت ضربان از سمت پا (روی برد). سکوت > ۹۰s ⇒ stale."""
        now = ts if ts is not None else time.time()
        self._last_beat_ts = now
        return self.status(now)

    def status(self, now: Optional[float] = None) -> HeartbeatStatus:
        now = now if now is not None else time.time()
        alive = self._last_beat_ts > 0.0
        stale = alive and (now - self._last_beat_ts) > HEARTBEAT_STALE_AFTER_S
        return HeartbeatStatus(self.leg_id, alive, stale, self._last_beat_ts, now)

    # ── پیشنهاد (هرگز اجرا) ──────────────────────────────────────────
    def propose(self, action: str, payload: Optional[dict[str, Any]] = None) -> LegProposal:
        """ثبت پیشنهاد. اجرا فقط از مسیر گیت‌های V2/V4 — این لایه بی‌دندان است."""
        p = LegProposal(
            proposal_id=f"prop-{self.leg_id}-{uuid.uuid4().hex[:8]}",
            leg_id=self.leg_id,
            action=str(action),
            payload=dict(payload or {}),
            created_ts=time.time(),
        )
        self._proposals[p.proposal_id] = p
        return p

    def proposal(self, proposal_id: str) -> Optional[LegProposal]:
        return self._proposals.get(proposal_id)

    def pending_proposals(self) -> list[LegProposal]:
        return [p for p in self._proposals.values() if not p.executed]

    # ── رفتار خاص per-leg (قابل بازنویسی) ────────────────────────────
    def transform_outbound(self, text: str) -> str:
        """تبدیل متنِ خروجی به قالب پا — پیش‌فرض: بدون تغییر."""
        return text
