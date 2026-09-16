"""Which brain answers, and what it costs to move up a level.

Four rungs, cheapest first:

    RULES        deterministic code / SQL      0 tokens     ~0 ms
    LOCAL        small model on this board     0 tokens     ~2 s
    REMOTE       hosted, standard depth       quota        seconds
    REMOTE_DEEP  hosted, deep reasoning       quota x4     minutes

The two hosted rungs are genuinely different animals, and conflating them is
a mistake worth naming: the standard model answers in seconds, while the deep
one can run for minutes on a hard problem. Published third-party measurements
mix the two into one wide range, which makes the fast rung look unusable when
it is not.

Two rules govern movement between them, and both exist because of specific
failures rather than general caution.

**No automatic escalation to a paid rung.** A previous version of this system
had a router that quietly fell through to the paid tier whenever the local
model returned something short. That is a budget leak with no upper bound.
Here, moving from LOCAL to REMOTE requires the lower rung to *explicitly*
report insufficiency, and moving to REMOTE_DEEP requires a human. Silence is
never taken as a request to spend money.

**Latency is a policy input, not an afterthought.** Even the fast hosted rung
answers in seconds, and its tail is longer than that. A partner tapping a
button cannot wait for either. So a request marked `interactive` is
structurally forbidden from reaching a rung slower than the budget — not
discouraged, forbidden. Interactive paths answer from the ledger; thinking
happens afterwards and arrives as a notification. The numbers below start as
estimates and are replaced by what this board actually measures.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Mapping


class Rung(enum.Enum):
    RULES = "rules"
    LOCAL = "local"
    REMOTE = "remote"
    REMOTE_DEEP = "remote_deep"

    def costs_quota(self) -> bool:
        return self in (Rung.REMOTE, Rung.REMOTE_DEEP)


_ORDER: Mapping[Rung, int] = {
    Rung.RULES: 0, Rung.LOCAL: 1, Rung.REMOTE: 2, Rung.REMOTE_DEEP: 3,
}

# Worst-case latency per rung, used to keep slow rungs off the interactive
# path. These are *starting estimates*, not measurements — the same status as
# the token capacity in `quota.py`, and for the same reason: the provider
# publishes nothing and third-party reports disagree. `calibrate_latency()`
# below replaces them with observed numbers once the node has seen real calls.
#
# The tail is what matters here, not the median. A rung that usually answers
# in four seconds and occasionally takes ninety is not a rung a partner can
# wait on, because the ninety is the time they will remember.
WORST_CASE_MS: dict[Rung, int] = {
    Rung.RULES: 50,
    Rung.LOCAL: 8_000,
    Rung.REMOTE: 45_000,        # standard depth: seconds, with a slow tail
    Rung.REMOTE_DEEP: 1_800_000,  # deep reasoning: minutes, sometimes many
}


def calibrate_latency(rung: Rung, observed_ms: int) -> None:
    """Raise a rung's worst case to match reality. Never lowers it.

    One-directional on purpose. A single fast call proves nothing about the
    tail, so a good measurement must not be allowed to talk the system into
    putting a slow rung back on a partner's screen. Only evidence that a rung
    is *slower* than believed changes the routing decision.
    """
    if observed_ms < 0:
        raise ValueError("latency must not be negative")
    if observed_ms > WORST_CASE_MS[rung]:
        WORST_CASE_MS[rung] = int(observed_ms)

# Multiplier applied to a token estimate when the deep rung is used.
DEEP_COST_FACTOR = 4

# A request on a human's critical path may not use a rung slower than this.
INTERACTIVE_BUDGET_MS = 10_000


@dataclass(frozen=True)
class RouteRequest:
    task: str
    interactive: bool = False
    estimated_tokens: int = 0
    owner_approved_deep: bool = False
    max_rung: Rung = Rung.REMOTE


@dataclass(frozen=True)
class RouteDecision:
    rung: Rung | None
    allowed: bool
    reason: str
    rule: str = ""

    @property
    def costs_quota(self) -> bool:
        return self.allowed and self.rung is not None and self.rung.costs_quota()


def rung_at_least(a: Rung, b: Rung) -> bool:
    return _ORDER[a] >= _ORDER[b]


def fits_interactive(rung: Rung) -> bool:
    return WORST_CASE_MS[rung] <= INTERACTIVE_BUDGET_MS


def start_rung(req: RouteRequest) -> RouteDecision:
    """Where to begin. Always the cheapest rung that could plausibly work.

    Starting low is not only about cost: a deterministic answer is auditable
    in a way a generated one is not, so the cheapest rung is usually also the
    most defensible.
    """
    if req.interactive and not fits_interactive(Rung.RULES):
        return RouteDecision(None, False, "no rung is fast enough",
                             rule="route:no-fast-rung")
    return RouteDecision(Rung.RULES, True, "starting at the cheapest rung",
                         rule="route:start")


def may_escalate(
    current: Rung,
    req: RouteRequest,
    *,
    lower_reported_insufficient: bool,
) -> RouteDecision:
    """Decide whether to move up one rung. Fail-closed at every boundary."""
    order = _ORDER[current]
    if order >= _ORDER[Rung.REMOTE_DEEP]:
        return RouteDecision(None, False, "already at the deepest rung",
                             rule="route:at-top")
    nxt = {0: Rung.LOCAL, 1: Rung.REMOTE, 2: Rung.REMOTE_DEEP}[order]

    if not lower_reported_insufficient:
        return RouteDecision(
            None, False,
            f"{current.value} did not report insufficiency — silence is not a "
            f"request to escalate",
            rule="route:no-implicit-escalation")

    if rung_at_least(nxt, Rung.REMOTE) and not rung_at_least(req.max_rung, nxt):
        return RouteDecision(None, False,
                             f"caller capped routing at {req.max_rung.value}",
                             rule="route:capped")

    if req.interactive and not fits_interactive(nxt):
        return RouteDecision(
            None, False,
            f"{nxt.value} can take up to {WORST_CASE_MS[nxt] // 1000}s — too "
            f"slow for an interactive request; queue it instead",
            rule="route:too-slow-for-interactive")

    if nxt is Rung.REMOTE_DEEP and not req.owner_approved_deep:
        return RouteDecision(None, False,
                             "the deepest rung costs ~4x and needs the owner's "
                             "explicit approval",
                             rule="route:deep-needs-owner")

    return RouteDecision(nxt, True, f"escalating to {nxt.value}",
                         rule="route:escalate")


def token_estimate(req: RouteRequest, rung: Rung) -> int:
    """Visible-token estimate for a rung. Zero for the free rungs."""
    if not rung.costs_quota():
        return 0
    if rung is Rung.REMOTE_DEEP:
        return req.estimated_tokens * DEEP_COST_FACTOR
    return req.estimated_tokens
