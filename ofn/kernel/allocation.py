"""Which unit mines what, learned by trial and error rather than predicted.

The owner's instruction was blunt and correct: you cannot predict which coin
will work, so the fleet has to find out by running. This module is that
search. It is deliberately not an optimiser.

**Why not an optimiser.** To maximise anything you need a single number to
compare arms on, and across coins that number does not exist: one unit of coin
A and one unit of coin B share no denominator, and building one means a price
model — the exact thing the owner said is irrelevant here, because the
electricity is solar and free. An optimiser built on a fabricated denominator
would produce confident rankings out of nothing.

So the objective is **feasibility and breadth**, which are measurable without
any price at all:

    does this arm actually produce accepted shares on this class of hardware?
    and are we spread across everything that does?

Sixteen independent machines make that cheap. They do not have to agree — a
few can be proving new arms while the rest run proven ones, so exploration
costs a fraction of the fleet rather than all of it.

**Why the search is deterministic.** No randomness anywhere: same inputs, same
assignment, replayable from the ledger a month later when someone asks why a
board was moved. A random explorer would be marginally better at avoiding
pathological orderings and much worse at being explained.

**The safety boundary is the arm list, not this module.** Arms come from a
pinned file the node cannot write. This module may move the fleet freely
between arms; it can never invent one. So the worst case of a bug here — or
of a compromised sensor feeding it lies — is hashpower pointed at a payout
address the owner already chose.

Kernel purity: no clock, no I/O, no randomness, no coin or pool names.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import Mapping, Sequence

from .errors import FailClosedError

_ID = re.compile(r"^[a-z0-9]([a-z0-9._-]{0,46}[a-z0-9])?$")

# An arm has to run for at least this long before its numbers mean anything.
# Miners ramp: DAG builds, pools take a few minutes to confirm the first
# shares, thermals settle. Judging inside that window measures the warm-up.
DEFAULT_MIN_DWELL_S = 3600

# Accepted shares needed before an arm counts as proven on a class.
DEFAULT_PROOF_SHARES = 10

# How much of the fleet may be exploring at once. A third is generous, but the
# alternative — proving arms one at a time — takes a month per candidate.
DEFAULT_EXPLORE_FRACTION = 0.25


# The floor below which an arm is technically working and practically pointless.
# Expressed as a share of what the whole network emitted over the same window,
# because that is the only figure comparable across coins: raw unit counts are a
# statement about a coin's supply schedule, not about how much of it we got. An
# established chain will hand a sixteen-board fleet a rounding error of its
# emission, and no amount of patience changes that.
DEFAULT_MIN_SHARE = 0.001          # 0.1% of network emission


class Feasibility(enum.Enum):
    UNPROVEN = "unproven"    # not enough evidence — the default, and honest
    WORKING = "working"      # produces, and our share of emission is meaningful
    MARGINAL = "marginal"    # produces, but we are a rounding error on it
    BROKEN = "broken"        # ran long enough, produced nothing

    def is_assignable(self) -> bool:
        return self is not Feasibility.BROKEN


@dataclass(frozen=True)
class Arm:
    """One (coin, pool, payout address) row from the pinned file.

    This module never sees the address and does not want to. It only needs to
    know which hardware classes the row is allowed on — some algorithms are
    pointless on a microcontroller and the pack says so.
    """

    arm_id: str
    classes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not _ID.match(self.arm_id):
            raise FailClosedError(f"arm id {self.arm_id!r} is not a safe slug")
        if not self.classes:
            raise FailClosedError(
                f"arm {self.arm_id!r} allows no hardware class — an arm no "
                f"unit can run is a configuration mistake, not an empty set")

    def allows(self, unit_class: str) -> bool:
        return unit_class in self.classes


@dataclass(frozen=True)
class Trial:
    """Accumulated evidence for one (arm, class) pair.

    Per class, not per arm: proving an algorithm works on a full Linux board
    says nothing about whether it works on a microcontroller, and merging the
    two would let a strong class vouch for a weak one.
    """

    arm_id: str
    unit_class: str
    seconds: int = 0
    accepted: int = 0
    rejected: int = 0
    units_earned: float = 0.0        # in the coin's own unit — for the owner to see
    network_emitted: float = 0.0     # what the whole chain emitted over the same window

    def __post_init__(self) -> None:
        if self.seconds < 0 or self.accepted < 0 or self.rejected < 0:
            raise FailClosedError("trial counters must not be negative")
        if self.units_earned < 0 or self.network_emitted < 0:
            raise FailClosedError("emission figures must not be negative")

    @property
    def share(self) -> float | None:
        """Our slice of everything the chain minted while we were mining it.

        `None` when the network figure is not known — and that is not the same
        as zero. An unknown share must never be read as a bad one, or every arm
        would be condemned on its first day before anyone had looked up what
        the chain actually emits.
        """
        if self.network_emitted <= 0:
            return None
        return self.units_earned / self.network_emitted

    def feasibility(
        self,
        *,
        min_dwell_s: int = DEFAULT_MIN_DWELL_S,
        proof_shares: int = DEFAULT_PROOF_SHARES,
        min_share: float = DEFAULT_MIN_SHARE,
    ) -> Feasibility:
        if self.accepted >= proof_shares:
            got = self.share
            if got is not None and got < min_share:
                # It works. We are simply too small to matter on it — the
                # established-chain case. Kept assignable, but only when there
                # is nothing better, because a board here is a board not
                # accumulating anywhere it counts.
                return Feasibility.MARGINAL
            return Feasibility.WORKING
        if self.seconds >= min_dwell_s * 2:
            # Ran twice as long as it needed and still produced nothing. That
            # is evidence, not impatience.
            return Feasibility.BROKEN
        return Feasibility.UNPROVEN


@dataclass(frozen=True)
class Assignment:
    unit: str
    arm_id: str
    reason: str
    rule: str


@dataclass(frozen=True)
class Placement:
    """Where a unit is now, and since when."""

    unit: str
    unit_class: str
    arm_id: str = ""
    since_epoch_s: int = 0

    def held_for(self, now_epoch_s: int) -> int:
        return max(0, now_epoch_s - self.since_epoch_s)


def _key(arm_id: str, unit_class: str) -> tuple:
    return (arm_id, unit_class)


def plan(
    placements: Sequence[Placement],
    arms: Sequence[Arm],
    trials: Mapping[tuple, Trial],
    *,
    now_epoch_s: int,
    min_dwell_s: int = DEFAULT_MIN_DWELL_S,
    explore_fraction: float = DEFAULT_EXPLORE_FRACTION,
    proof_shares: int = DEFAULT_PROOF_SHARES,
    min_share: float = DEFAULT_MIN_SHARE,
) -> tuple[Assignment, ...]:
    """Decide where every unit should be. Returns only the units that move.

    Four rules, applied in order:

      1. A unit on a BROKEN arm moves immediately — dwell time does not
         protect an arm that has already proven it does not work.
      2. A unit that has not served its dwell stays put. This is what stops
         the fleet thrashing between arms and measuring nothing but warm-ups.
      3. Everyone else: a bounded slice explores the least-tested arm its
         class allows; the rest spread over arms where our share is real.
      4. MARGINAL arms are a last resort. A board sitting on a chain where we
         collect a rounding error is a board not accumulating anywhere that
         counts — but it still beats an idle board, so it is a fallback rather
         than a refusal.
    """
    if not 0.0 <= explore_fraction <= 1.0:
        raise FailClosedError("explore_fraction must be between 0 and 1")

    def feas(arm: Arm, cls: str) -> Feasibility:
        t = trials.get(_key(arm.arm_id, cls))
        if t is None:
            return Feasibility.UNPROVEN
        return t.feasibility(min_dwell_s=min_dwell_s, proof_shares=proof_shares,
                             min_share=min_share)

    def share_of(arm: Arm, cls: str) -> float:
        t = trials.get(_key(arm.arm_id, cls))
        got = t.share if t is not None else None
        return got if got is not None else 0.0

    def tested_seconds(arm: Arm, cls: str) -> int:
        t = trials.get(_key(arm.arm_id, cls))
        return t.seconds if t is not None else 0

    moves: list[Assignment] = []
    # Deterministic order everywhere: the same fleet state must always produce
    # the same plan, or the ledger stops being an explanation.
    ordered = sorted(placements, key=lambda p: p.unit)

    movable: list[Placement] = []
    for p in ordered:
        allowed = [a for a in arms if a.allows(p.unit_class)]
        if not allowed:
            continue                       # nothing this class may run

        current = next((a for a in allowed if a.arm_id == p.arm_id), None)

        if current is not None and feas(current, p.unit_class) is Feasibility.BROKEN:
            movable.append(p)
            continue
        if not p.arm_id:
            movable.append(p)              # unassigned
            continue
        if current is None:
            movable.append(p)              # on an arm that no longer exists
            continue
        if p.held_for(now_epoch_s) < min_dwell_s:
            continue                       # still earning its measurement
        movable.append(p)

    explore_budget = int(len(ordered) * explore_fraction)
    exploring = 0
    # Count units already sitting on unproven arms against the budget, so the
    # fraction bounds total exploration rather than exploration per pass.
    for p in ordered:
        arm = next((a for a in arms if a.arm_id == p.arm_id), None)
        if arm is not None and feas(arm, p.unit_class) is Feasibility.UNPROVEN:
            exploring += 1

    # Spread: how many units each proven arm already holds, so "spread evenly"
    # is measured against reality rather than assumed.
    load: dict[tuple, int] = {}
    for p in ordered:
        if p.arm_id:
            k = _key(p.arm_id, p.unit_class)
            load[k] = load.get(k, 0) + 1

    for p in movable:
        allowed = [a for a in arms if a.allows(p.unit_class)]
        unproven = sorted(
            (a for a in allowed if feas(a, p.unit_class) is Feasibility.UNPROVEN),
            key=lambda a: (tested_seconds(a, p.unit_class), a.arm_id))
        # Spread first, share second: the goal is many coins accumulating at
        # once, not one optimum. Share only breaks ties between equally-loaded
        # arms — otherwise the whole fleet would pile onto today's best number
        # and the diversity the owner actually wants would quietly disappear.
        working = sorted(
            (a for a in allowed if feas(a, p.unit_class) is Feasibility.WORKING),
            key=lambda a: (load.get(_key(a.arm_id, p.unit_class), 0),
                           -share_of(a, p.unit_class), a.arm_id))
        marginal = sorted(
            (a for a in allowed if feas(a, p.unit_class) is Feasibility.MARGINAL),
            key=lambda a: (load.get(_key(a.arm_id, p.unit_class), 0), a.arm_id))

        target: Arm | None = None
        why = ""
        rule = ""
        if unproven and exploring < explore_budget:
            target = unproven[0]
            exploring += 1
            why = "least-tested arm this class allows"
            rule = "alloc:explore"
        elif working:
            target = working[0]
            why = "arm with a real share, carrying the fewest units"
            rule = "alloc:exploit"
        elif marginal:
            target = marginal[0]
            why = "only marginal arms left — we are a rounding error here"
            rule = "alloc:marginal"
        elif unproven:
            # Nothing is proven yet and the explore budget is spent. Running a
            # unit on an unproven arm still beats idling it — the fleet is
            # free to run and idle proves nothing.
            target = unproven[0]
            why = "nothing proven yet; an idle unit measures nothing"
            rule = "alloc:bootstrap"

        if target is None or target.arm_id == p.arm_id:
            continue

        if p.arm_id:
            k = _key(p.arm_id, p.unit_class)
            load[k] = max(0, load.get(k, 0) - 1)
        nk = _key(target.arm_id, p.unit_class)
        load[nk] = load.get(nk, 0) + 1
        moves.append(Assignment(p.unit, target.arm_id, why, rule))

    return tuple(moves)


def coverage(
    placements: Sequence[Placement],
    arms: Sequence[Arm],
    trials: Mapping[tuple, Trial],
    *,
    min_dwell_s: int = DEFAULT_MIN_DWELL_S,
    proof_shares: int = DEFAULT_PROOF_SHARES,
    min_share: float = DEFAULT_MIN_SHARE,
) -> Mapping[str, object]:
    """What the search knows so far. This is the honest progress report.

    `unproven` is the number that matters early on: it is how much of the
    candidate space has never been tried, and it should fall over time. If it
    stops falling, exploration has stalled and a human should know.
    """
    states: dict[str, int] = {f.value: 0 for f in Feasibility}
    pairs = 0
    units = 0.0
    for arm in arms:
        for cls in arm.classes:
            pairs += 1
            t = trials.get(_key(arm.arm_id, cls))
            f = (t.feasibility(min_dwell_s=min_dwell_s, proof_shares=proof_shares,
                               min_share=min_share)
                 if t is not None else Feasibility.UNPROVEN)
            states[f.value] += 1
            if t is not None:
                units += t.units_earned
    busy = sum(1 for p in placements if p.arm_id)
    return {
        "arm_class_pairs": pairs,
        # Raw units are reported because the owner asked to see them, and
        # ignored for decisions because they are not comparable across coins.
        "units_earned_total": units,
        "unproven": states[Feasibility.UNPROVEN.value],
        "working": states[Feasibility.WORKING.value],
        "broken": states[Feasibility.BROKEN.value],
        "units_assigned": busy,
        "units_idle": len(placements) - busy,
    }
