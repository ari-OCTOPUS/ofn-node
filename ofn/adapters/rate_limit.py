"""Per-platform rate limiting — a fixed window verdict.

This is the cheap, stateless half of rate limiting: given a window that the
caller holds (current count, when it resets), is one more post allowed? The
*stateful* half — counting posts, rolling windows forward — lives in the
store, not here. That split is what keeps this testable without a clock and
without a database.

A fixed window (not sliding) is deliberate. Sliding windows are more
precise and more expensive, and precision is not the goal here: the goal is
to stay under a platform's per-day or per-hour cap with margin. A window
that resets on a boundary is easier to reason about and impossible to
accidentally drift past.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RateWindow:
    """One platform's current window, as the caller sees it.

    `reset_at` is an epoch second; the caller derives it (not this module),
    so the test for "has the window rolled over" needs no clock in here.
    """

    max_count: int
    window_seconds: int
    used: int
    reset_at: int


@dataclass(frozen=True)
class RateVerdict:
    ok: bool
    rule: str
    retry_after_s: int | None = None   # None when ok; seconds-to-wait when refused


RULE_OK_RESET = "rate:ok-after-reset"
RULE_OK = "rate:ok"
RULE_LIMIT = "rate:limit"


def may_consume(window: RateWindow, *, now: int, amount: int = 1) -> RateVerdict:
    """May `amount` posts be added to this window right now?

    `now` is passed in, not read from a clock — this is the same rule the
    rest of the kernel follows. The caller is the authority on what time
    it is; this module is the authority on whether the count fits.
    """
    if amount < 0:
        # A negative amount would *add* headroom, which is nonsense. Refuse
        # rather than silently allow a caller to game the window.
        return RateVerdict(False, "rate:negative-amount")
    if amount == 0:
        # A zero ask is always allowed and consumes nothing.
        return RateVerdict(True, RULE_OK)

    if now >= window.reset_at:
        # The window has rolled over. Whatever `used` says, the caller will
        # reset it; from this module's view the post fits.
        return RateVerdict(True, RULE_OK_RESET)

    if window.used + amount > window.max_count:
        return RateVerdict(False, RULE_LIMIT,
                           max(0, window.reset_at - now))
    return RateVerdict(True, RULE_OK)
