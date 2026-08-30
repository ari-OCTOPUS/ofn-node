"""Budget arithmetic under one hard cap (INV-1). Pure functions over BudgetState.

Concurrency contract: every derived state bumps `version`. Stores must write
with compare-and-swap on the old version so two racing reservations cannot both
land — the loser gets ConcurrencyConflictError from the adapter and re-reads.
This is the optimistic-lock discipline the v0.1 review flagged as a real bug
class; it is load-bearing, do not "simplify" it away.
"""

from __future__ import annotations

from .domain import BudgetState, Money
from .errors import CapExceededError, FailClosedError


def headroom(state: BudgetState) -> Money:
    return state.cap.sub(state.committed)


def reserve(state: BudgetState, amount: Money) -> BudgetState:
    """Commit `amount` against the cap. Raises CapExceededError past the ceiling."""
    if amount.cents <= 0:
        raise FailClosedError("reserve amount must be positive")
    new_committed = state.committed.add(amount)
    if new_committed.cents > state.cap.cents:
        raise CapExceededError(
            f"reserve {amount.cents}c would exceed cap: "
            f"{state.committed.cents}c committed of {state.cap.cents}c"
        )
    return BudgetState(cap=state.cap, committed=new_committed, version=state.version + 1)


def release(state: BudgetState, amount: Money) -> BudgetState:
    """Return unused commitment to headroom (e.g., denied or expired grants)."""
    if amount.cents <= 0:
        raise FailClosedError("release amount must be positive")
    return BudgetState(
        cap=state.cap,
        committed=state.committed.sub(amount),
        version=state.version + 1,
    )
