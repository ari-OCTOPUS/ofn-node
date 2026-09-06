"""A ceiling on how many model calls a day, counted per rung.

The token quota answers "how much have we spent". This answers a different
question — "how many times have we asked" — and they are not the same
ceiling. A loop that asks a cheap question ten thousand times stays inside a
token budget for a while and is still a runaway.

Counted **per rung**, not in one pool. The rungs are different models at
different prices, and one number covering both is the "get the unit right"
mistake: a thousand cheap calls and a thousand expensive ones are not the
same event, and a shared counter lets the cheap rung exhaust the budget the
expensive one needed.

Fail-closed everywhere:

    an unknown rung        →  refused, not allowed by default
    a day boundary unknown →  the caller supplies the clock, never this file
    a coerced clock        →  refused (bool/float/str are not a day)
    at the ceiling exactly →  refused

That last one is deliberate. "Ten calls a day" that permits an eleventh is a
limit somebody has to read the code to understand.

``int(True)`` is 1 and ``int("178")`` looks like a timestamp. Either would
move the day bucket without a boundary-supplied clock. The same exact-int
rule the envelope uses lives here so a budget cannot be the weaker witness.

HALT is not a parameter. Layer 3 stops STARTS; an in-flight record still
counts. This module never grants ``send_authorized``.

Kernel purity: no clock, no I/O. `now_epoch_s` arrives as an argument.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .errors import FailClosedError
from .routing import Rung

DAY = 86_400

# Deliberately small for the rungs that cost money. This node has three
# businesses and one owner; a hundred hosted calls in a day is already far
# more thinking than anybody has asked for, and the number exists to catch a
# loop rather than to ration normal use.
DEFAULT_CAPS: Mapping[Rung, int] = {
    Rung.RULES: 0,          # 0 means no ceiling: this rung costs nothing
    Rung.LOCAL: 0,
    Rung.REMOTE: 100,
    Rung.REMOTE_DEEP: 5,    # needs a human anyway; this is the second lock
}

# Ready is not authorized. Listing campaign_envelope_ready here keeps a
# budget Decision (or a future one) from smuggling draft-ready into a send.
SEND_STATES = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def require_epoch_s(value: object, name: str = "now_epoch_s") -> int:
    """Exact int, not bool/float/str. ``int(True)`` is not a clock."""
    if type(value) is not int:
        raise FailClosedError(f"{name} must be int: {value!r}")
    if value < 0:
        raise FailClosedError(f"{name} must be non-negative: {value!r}")
    return value


def day_index(now_epoch_s: int) -> int:
    return require_epoch_s(now_epoch_s) // DAY


def grants_send() -> bool:
    """A call-count ceiling is never a send authorization.

    Structurally False. HALT is not consulted — this is not a start gate.
    """
    return False


@dataclass
class CallBudget:
    """Per-rung call counting, one day at a time."""

    caps: Mapping[Rung, int] = field(default_factory=lambda: dict(DEFAULT_CAPS))
    _counts: dict[tuple[int, Rung], int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for rung, cap in self.caps.items():
            if not isinstance(cap, int) or isinstance(cap, bool) or cap < 0:
                raise FailClosedError(f"invalid cap for {rung}: {cap!r}")

    def cap_for(self, rung: Rung) -> int:
        """Refuses a rung nobody set a cap for.

        A rung added later and forgotten here would otherwise be unlimited —
        the one default that must never be the permissive one.
        """
        if rung not in self.caps:
            raise FailClosedError(f"no call budget declared for {rung}")
        return self.caps[rung]

    def spent(self, rung: Rung, now_epoch_s: int) -> int:
        return self._counts.get((day_index(now_epoch_s), rung), 0)

    def remaining(self, rung: Rung, now_epoch_s: int) -> int | None:
        """None means uncapped, which only free rungs are."""
        cap = self.cap_for(rung)
        if cap == 0:
            return None
        return max(0, cap - self.spent(rung, now_epoch_s))

    def allows(self, rung: Rung, now_epoch_s: int) -> bool:
        left = self.remaining(rung, now_epoch_s)
        return True if left is None else left > 0

    def record(self, rung: Rung, now_epoch_s: int) -> None:
        """Counted whether or not the call succeeded.

        A failed call still reached the provider and still cost a round trip;
        counting only successes turns a failing loop into an uncounted one,
        which is the loop most worth stopping.
        """
        self.cap_for(rung)              # refuse an undeclared rung here too
        key = (day_index(now_epoch_s), rung)
        self._counts[key] = self._counts.get(key, 0) + 1
        self._prune(now_epoch_s)

    def _prune(self, now_epoch_s: int) -> None:
        today = day_index(now_epoch_s)
        for key in [k for k in self._counts if k[0] < today - 1]:
            del self._counts[key]

    def report(self, now_epoch_s: int) -> dict:
        now = require_epoch_s(now_epoch_s)
        out = {
            rung.value: {
                "cap": self.cap_for(rung),
                "spent": self.spent(rung, now),
                "remaining": self.remaining(rung, now),
            }
            for rung in self.caps
        }
        leaked = SEND_STATES.intersection(out)
        if leaked:
            raise FailClosedError(
                f"call-budget report named a send/ready state {sorted(leaked)} "
                "— this module does not grant send_authorized")
        return out

    def grants_send(self) -> bool:
        """Instance pin of the module rule. Always False."""
        return grants_send()
