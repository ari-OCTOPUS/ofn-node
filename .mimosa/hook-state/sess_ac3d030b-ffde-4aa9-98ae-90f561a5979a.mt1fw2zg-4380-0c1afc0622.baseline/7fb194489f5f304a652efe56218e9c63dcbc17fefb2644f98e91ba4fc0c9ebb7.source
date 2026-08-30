# -*- coding: utf-8 -*-
"""Overlay budget in integer cents. Caps are ≤ live budget_gate, never looser.

Live SoT remains `04 - Architect System/scripts/budget_gate.py`.
This overlay does not open that file on the live tree; tests inject a temp path.
"""
from __future__ import annotations

import json
from pathlib import Path

from .exceptions import BudgetExceeded, LedgerClosed

# Match live HARD floors (AUD, converted at 100 cents = AU$1 for overlay math).
# Do NOT use the Gemini P0 figures (AU$15/day, AU$300/month) — those loosen law.
PER_ACTION_CENTS = 200    # AU$2
DAILY_CENTS = 200         # AU$2 — same as CEIL_DAY_AUD_HARD
MONTHLY_CENTS = 3000      # AU$30 — same as CEIL_MONTH_AUD_HARD (post-window)


class OverlayBudget:
    def __init__(
        self,
        state_path: Path,
        *,
        per_action_cents: int = PER_ACTION_CENTS,
        daily_cents: int = DAILY_CENTS,
        monthly_cents: int = MONTHLY_CENTS,
        day_key: str = "1970-01-01",
        month_key: str = "1970-01",
    ) -> None:
        if per_action_cents > PER_ACTION_CENTS or daily_cents > DAILY_CENTS or monthly_cents > MONTHLY_CENTS:
            raise BudgetExceeded("overlay cap must not exceed live HARD floors")
        self.path = Path(state_path)
        self.per_action_cents = int(per_action_cents)
        self.daily_cents = int(daily_cents)
        self.monthly_cents = int(monthly_cents)
        self.day_key = day_key
        self.month_key = month_key

    def _load(self) -> dict:
        if not self.path.exists():
            return {"reserved": 0, "settled_day": 0, "settled_month": 0, "day": self.day_key, "month": self.month_key}
        try:
            data = json.loads(self.path.read_text("utf-8"))
        except (OSError, ValueError) as exc:
            raise LedgerClosed(f"budget state unreadable: {exc}") from exc
        if data.get("day") != self.day_key:
            data["settled_day"] = 0
            data["reserved"] = 0
            data["day"] = self.day_key
        if data.get("month") != self.month_key:
            data["settled_month"] = 0
            data["month"] = self.month_key
        return data

    def _save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            tmp.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
            tmp.replace(self.path)
        except OSError as exc:
            raise LedgerClosed(f"budget state write failed: {exc}") from exc

    def check_and_reserve(self, cost_cents: int) -> None:
        if cost_cents < 0:
            raise BudgetExceeded("negative cost")
        if cost_cents > self.per_action_cents:
            raise BudgetExceeded(f"per-action {cost_cents}c > {self.per_action_cents}c")
        data = self._load()
        reserved = int(data.get("reserved", 0)) + cost_cents
        day_total = int(data.get("settled_day", 0)) + reserved
        month_total = int(data.get("settled_month", 0)) + reserved
        if day_total > self.daily_cents:
            raise BudgetExceeded(f"daily {day_total}c > {self.daily_cents}c")
        if month_total > self.monthly_cents:
            raise BudgetExceeded(f"monthly {month_total}c > {self.monthly_cents}c")
        data["reserved"] = reserved
        self._save(data)

    def settle(self, cost_cents: int) -> None:
        data = self._load()
        reserved = int(data.get("reserved", 0)) - cost_cents
        if reserved < 0:
            reserved = 0
        data["reserved"] = reserved
        data["settled_day"] = int(data.get("settled_day", 0)) + cost_cents
        data["settled_month"] = int(data.get("settled_month", 0)) + cost_cents
        self._save(data)

    def release(self, cost_cents: int) -> None:
        data = self._load()
        reserved = int(data.get("reserved", 0)) - cost_cents
        data["reserved"] = max(0, reserved)
        self._save(data)
