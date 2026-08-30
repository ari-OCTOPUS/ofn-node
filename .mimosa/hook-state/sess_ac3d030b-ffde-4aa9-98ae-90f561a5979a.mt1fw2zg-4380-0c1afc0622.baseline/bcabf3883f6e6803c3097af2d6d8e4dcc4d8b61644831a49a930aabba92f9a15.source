"""Isolated flash budget. Not K=9 (80 / AU$2). Lab jsonl only — no _ops/state writes."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "flash-budget.v1"
# Owner flash envelope — SEPARATE from PRE-REG-K9 (80 calls / AU$2.00).
MAX_CALLS = 12
HARD_STOP_AUD = 0.50
MAX_CONCURRENCY = 1
TIMEOUT_SECONDS = 60
MAX_RETRIES = 1
K9_MAX_CALLS = 80
K9_MAX_AUD = 2.00


@dataclass
class FlashBudget:
    max_calls: int = MAX_CALLS
    hard_stop_aud: float = HARD_STOP_AUD
    max_concurrency: int = MAX_CONCURRENCY
    timeout_seconds: int = TIMEOUT_SECONDS
    max_retries: int = MAX_RETRIES
    calls_used: int = 0
    aud_reserved: float = 0.0
    aud_spent: float = 0.0
    k9_mixed: bool = False

    def remaining_calls(self) -> int:
        return max(0, self.max_calls - self.calls_used)

    def remaining_aud(self) -> float:
        return max(0.0, round(self.hard_stop_aud - self.aud_spent - self.aud_reserved, 6))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema"] = SCHEMA
        d["remaining_calls"] = self.remaining_calls()
        d["remaining_aud"] = self.remaining_aud()
        d["k9_envelope_not_this"] = {"max_calls": K9_MAX_CALLS, "max_cost_aud": K9_MAX_AUD}
        return d


class BudgetError(RuntimeError):
    pass


def reserve(store: Path, *, est_aud: float, stage: str, budget: FlashBudget | None = None) -> dict[str, Any]:
    """Fresh reservation for one flash call. Does not mix K=9. No network."""
    b = budget or load(store)
    est = float(est_aud)
    if est < 0:
        raise BudgetError("negative reservation")
    if b.calls_used + 1 > b.max_calls:
        raise BudgetError("max_calls exhausted")
    if b.aud_spent + b.aud_reserved + est > b.hard_stop_aud + 1e-12:
        raise BudgetError("hard_stop_aud would be exceeded")
    rec = {
        "schema": SCHEMA,
        "kind": "reserve",
        "stage": stage,
        "est_aud": round(est, 6),
        "ts": datetime.now(timezone.utc).isoformat(),
        "k9_mixed": False,
        "executable": False,
    }
    b.aud_reserved = round(b.aud_reserved + est, 6)
    save(store, b)
    _append(store, rec)
    rec["budget"] = b.to_dict()
    rec["ok"] = True
    return rec


def settle(store: Path, *, spent_aud: float, calls: int = 1, budget: FlashBudget | None = None) -> dict[str, Any]:
    b = budget or load(store)
    spent = max(0.0, float(spent_aud))
    b.calls_used += int(calls)
    b.aud_spent = round(b.aud_spent + spent, 6)
    b.aud_reserved = max(0.0, round(b.aud_reserved - spent, 6))
    if b.aud_spent > b.hard_stop_aud + 1e-12 or b.calls_used > b.max_calls:
        raise BudgetError("hard stop after settle")
    save(store, b)
    rec = {
        "schema": SCHEMA,
        "kind": "settle",
        "spent_aud": round(spent, 6),
        "calls": int(calls),
        "ts": datetime.now(timezone.utc).isoformat(),
        "budget": b.to_dict(),
        "ok": True,
    }
    _append(store, rec)
    return rec


def load(store: Path) -> FlashBudget:
    p = Path(store) / "flash-budget.json"
    if not p.exists():
        return FlashBudget()
    raw = json.loads(p.read_text(encoding="utf-8"))
    return FlashBudget(
        max_calls=int(raw.get("max_calls", MAX_CALLS)),
        hard_stop_aud=float(raw.get("hard_stop_aud", HARD_STOP_AUD)),
        max_concurrency=int(raw.get("max_concurrency", MAX_CONCURRENCY)),
        timeout_seconds=int(raw.get("timeout_seconds", TIMEOUT_SECONDS)),
        max_retries=int(raw.get("max_retries", MAX_RETRIES)),
        calls_used=int(raw.get("calls_used", 0)),
        aud_reserved=float(raw.get("aud_reserved", 0.0)),
        aud_spent=float(raw.get("aud_spent", 0.0)),
        k9_mixed=bool(raw.get("k9_mixed", False)),
    )


def save(store: Path, budget: FlashBudget) -> None:
    store = Path(store)
    store.mkdir(parents=True, exist_ok=True)
    p = store / "flash-budget.json"
    p.write_text(json.dumps(budget.to_dict(), indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _append(store: Path, rec: dict[str, Any]) -> None:
    store = Path(store)
    store.mkdir(parents=True, exist_ok=True)
    p = store / "flash-budget.jsonl"
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")
