"""survival-loop → Telegram cockpit bridge.

The owner's Telegram surface is the cockpit (the panel WebApp the bot's
button opens). This bridge routes loop events into the EXISTING owner
queue — the surface the cockpit already renders and the owner already
decides on — instead of opening any new send path. No gate opens: items
land as GREEN manual-delivery entries, exactly like every other thing the
owner approves.

Why queue and not sendMessage: every outbound gate (auto_post/auto_dm/
live_*) stays closed by owner ruling; the queue is the one channel that
was always owner-facing. Rate-capped so a chatty loop cannot flood the
cockpit.
"""
from __future__ import annotations

from typing import Callable, Mapping, Protocol

from ofn.adapters.outbox import Outbox          # noqa: F401 (type hint)
from ofn.kernel.domain import RiskTier
from ofn.kernel.tenancy import TenantScope

MAX_EVENTS_PER_DAY = 20


class _QueueLike(Protocol):
    def enqueue(self, scope, idem_key: str, kind: str, payload: Mapping,
                tier: RiskTier, now_iso: str) -> bool: ...


class SurvivalTelegramBridge:
    """Loop events → owner queue (cockpit-visible), rate-capped."""

    def __init__(self, queue: _QueueLike, scope: TenantScope, *,
                 now_epoch_s: Callable[[], int],
                 now_iso: Callable[[], str],
                 max_per_day: int = MAX_EVENTS_PER_DAY) -> None:
        self._queue = queue
        self._scope = scope
        self._now_s = now_epoch_s
        self._now_iso = now_iso
        self._max = max_per_day
        self._day: int | None = None
        self._sent_today = 0

    def _budget_ok(self) -> bool:
        day = self._now_s() // 86_400
        if day != self._day:
            self._day, self._sent_today = day, 0
        return self._sent_today < self._max

    def notify(self, run_id: str, kind: str, detail: Mapping[str, object]) -> bool:
        """One loop event → one owner-queue item. False = rate-capped or
        duplicate (idempotent by run_id+kind+tick)."""
        if not self._budget_ok():
            return False
        ok = self._queue.enqueue(
            self._scope,
            idem_key=f"survival:{run_id}:{kind}:{self._now_s()}",
            kind="survival_loop_event",
            payload={"run_id": run_id, "event": kind,
                     "message": self.render(run_id, kind, detail),
                     **dict(detail)},
            tier=RiskTier.GREEN,          # informational; never auto-sent
            now_iso=self._now_iso())
        if ok:
            self._sent_today += 1
        return ok

    @staticmethod
    def render(run_id: str, kind: str, detail: Mapping[str, object]) -> str:
        """One screen-readable line for the cockpit."""
        head = {"RUN_REGISTERED": "🧪 آزمایش جدید پیش‌ثبت شد",
                "PAYMENT_RECEIVED": "💵 پرداخت دریافت شد",
                "RUN_HALTED": "⛔ حلقه متوقف شد"}.get(kind, f"∘ {kind}")
        key_bits = " · ".join(f"{k}={v}" for k, v in sorted(detail.items())
                              if k in ("exp_id", "authority", "amount_aud",
                                       "S", "reason"))[:180]
        return f"{head} — {run_id}{(' · ' + key_bits) if key_bits else ''}"
