"""D-2 dollar ceilings, in exact hundredths; pure admission, never authority.

This is the single source of API monetary ceiling values. The owner clarified
USD on 2026-09-17. Request and usage must both name USD; business quote values
are outside this scope. No currency conversion or paid call occurs here.
Usage is a fresh, complete ledger snapshot supplied by an adapter. Admission
does NOT reserve funds; a real transport must reserve atomically before send.
The monthly window is a UTC calendar month, and the daily window rolls 24h.
"""
from __future__ import annotations

from dataclasses import dataclass

from .errors import FailClosedError

POLICY_ID = "S1-OWNER-RULINGS-20260917/D-2"
CURRENCY = "USD"


def _amount(value: object) -> int:
    if type(value) is not int or value < 0:
        raise FailClosedError("budget amounts must be non-negative exact integers")
    return value


@dataclass(frozen=True)
class BudgetLimits:
    monthly: int
    rolling_24h: int
    per_task: int

    def __post_init__(self) -> None:
        for value in (self.monthly, self.rolling_24h, self.per_task):
            _amount(value)


# One canonical file, no fallback copies in executors or call-count guards.
CANONICAL_LIMITS = BudgetLimits(monthly=10_000, rolling_24h=1_000, per_task=200)


def effective_limits(runtime: BudgetLimits | None = None) -> BudgetLimits:
    if runtime is None:
        return CANONICAL_LIMITS
    if type(runtime) is not BudgetLimits:
        raise FailClosedError("runtime budget limits are invalid")
    return BudgetLimits(*(min(a, b) for a, b in zip(
        (CANONICAL_LIMITS.monthly, CANONICAL_LIMITS.rolling_24h,
         CANONICAL_LIMITS.per_task),
        (runtime.monthly, runtime.rolling_24h, runtime.per_task))))


@dataclass(frozen=True)
class BudgetRequest:
    task_id: str
    currency: str
    amount: int  # Conservative upper bound, not an optimistic cost estimate.


@dataclass(frozen=True)
class BudgetUsage:
    task_id: str
    currency: str
    observed_at_epoch_s: int
    monthly: int
    rolling_24h: int
    per_task: int
    complete: bool  # Includes outstanding reservations and unknown outcomes.


@dataclass(frozen=True)
class BudgetVerdict:
    allowed: bool
    reason: str
    limits: BudgetLimits
    policy_id: str = POLICY_ID


def admit_spend(*, request: BudgetRequest, usage: BudgetUsage | None,
                now_epoch_s: int, runtime_limits: BudgetLimits | None = None
                ) -> BudgetVerdict:
    """Intersect all ceilings; unknown, stale or cross-task usage denies.

Zero is a real ceiling, never unlimited. Calling this twice is not a
reservation. The caller must obtain fresh usage under its ledger lock.
"""
    limits = effective_limits(runtime_limits)

    def deny(reason: str) -> BudgetVerdict:
        return BudgetVerdict(False, reason, limits)

    if type(request) is not BudgetRequest or type(usage) is not BudgetUsage:
        return deny("budget-evidence-missing")
    if type(now_epoch_s) is not int or now_epoch_s < 0:
        return deny("budget-clock-invalid")
    if type(usage.observed_at_epoch_s) is not int or usage.observed_at_epoch_s != now_epoch_s:
        return deny("budget-evidence-stale")
    if usage.complete is not True:
        return deny("budget-evidence-incomplete")
    if not isinstance(request.task_id, str) or not request.task_id.strip() or request.task_id != usage.task_id:
        return deny("budget-task-mismatch")
    if request.currency != CURRENCY or usage.currency != CURRENCY:
        return deny("budget-currency-mismatch")
    try:
        amount = _amount(request.amount)
        for spent in (usage.monthly, usage.rolling_24h, usage.per_task):
            _amount(spent)
    except FailClosedError:
        return deny("budget-amount-invalid")
    for name in ("monthly", "rolling_24h", "per_task"):
        if getattr(usage, name) + amount > getattr(limits, name):
            return deny("budget-" + name + "-exceeded")
    return BudgetVerdict(True, "budget-fits", limits)
