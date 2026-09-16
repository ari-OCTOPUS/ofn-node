"""Fleet health, judged from measurements this node actually took.

A fleet of small machines fails differently from a server. Nothing crashes
loudly; things just quietly stop earning while still answering pings. So the
judgements here are deliberately about *evidence of work*, not liveness:

    a board that reports in but produces nothing is not healthy, it is broken
    a board that has never been measured is not healthy, it is unknown

That second one is the rule this module exists to enforce. The registry for
this fleet is 162 units of which zero have ever been benchmarked, and every
hashrate figure in the project's research is a secondary source about somebody
else's hardware. Judging a unit "degraded" against a number from a blog post
produces a confident-looking alert that means nothing. So:

    no baseline  →  UNKNOWN, and the degraded check refuses to run

A unit earns its baseline by running. Until then this module says so.

Kernel purity: no clock, no I/O, no hardware model names. Unit classes are
opaque validated strings supplied by a pack, so adding a Raspberry Pi or a
Zero 3 is a data change, not a code change.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import Mapping, Sequence

from .errors import FailClosedError

_ID = re.compile(r"^[a-z0-9]([a-z0-9-]{0,30}[a-z0-9])?$")

# A unit that has not reported for this long is not "a bit late" — on a fleet
# reporting every 30s, twenty missed beats means something is actually wrong.
DEFAULT_SILENCE_S = 600

# Below this fraction of its OWN measured baseline, a unit is degraded.
DEFAULT_DEGRADED_AT = 0.80

# A baseline built from fewer samples than this is not a baseline, it is a
# coincidence. Deliberately high: one lucky minute must not become the number
# every future alert is judged against.
MIN_BASELINE_SAMPLES = 20


class UnitHealth(enum.Enum):
    UNKNOWN = "unknown"      # never measured — the honest default
    HEALTHY = "healthy"
    DEGRADED = "degraded"    # working, but below its own proven baseline
    OFFLINE = "offline"      # stopped reporting
    BROKEN = "broken"        # reporting, but producing nothing

    def needs_a_human(self) -> bool:
        """Whether this state is one a person has to physically go and look at.

        UNKNOWN is not in this set on purpose: an unmeasured unit needs
        *running*, not diagnosing.
        """
        return self in (UnitHealth.OFFLINE, UnitHealth.BROKEN,
                        UnitHealth.DEGRADED)


@dataclass(frozen=True)
class UnitId:
    value: str

    def __post_init__(self) -> None:
        if not _ID.match(self.value):
            raise FailClosedError(
                f"unit id {self.value!r} is not a safe slug — it ends up in "
                f"storage keys and file paths")


@dataclass(frozen=True)
class UnitClass:
    """A hardware family, named by a pack rather than by this module.

    The kernel must not know that a `zero3` is smaller than an `opi5pro`. It
    only knows that units of different classes are not comparable to each
    other, which is the one fact that affects a decision here.
    """

    value: str

    def __post_init__(self) -> None:
        if not _ID.match(self.value):
            raise FailClosedError(f"unit class {self.value!r} is not a safe slug")


@dataclass(frozen=True)
class Reading:
    """One telemetry sample. Everything a unit can honestly report about itself.

    `accepted` and `rejected` are share counters. They are the only fields
    that prove work happened — hashrate is what a miner *claims*, accepted
    shares are what a pool *confirms*. When the two disagree, the pool wins.
    """

    unit: str
    at_epoch_s: int
    hashrate: float = 0.0
    temp_c: float | None = None
    accepted: int = 0
    rejected: int = 0
    arm_id: str = ""

    def __post_init__(self) -> None:
        if self.at_epoch_s < 0:
            raise FailClosedError("reading timestamp must not be negative")
        if self.hashrate < 0 or self.accepted < 0 or self.rejected < 0:
            raise FailClosedError("counters must not be negative")


@dataclass(frozen=True)
class Baseline:
    """What a unit has been proven capable of, on one arm.

    Per (unit, arm) rather than per unit: the same board running a different
    algorithm has a different honest baseline, and comparing across them is
    the mistake this type exists to prevent.
    """

    unit: str
    arm_id: str
    samples: int
    median_hashrate: float

    @property
    def is_trustworthy(self) -> bool:
        return self.samples >= MIN_BASELINE_SAMPLES and self.median_hashrate > 0


@dataclass(frozen=True)
class Verdict:
    unit: str
    health: UnitHealth
    reason: str
    rule: str


def judge(
    unit: UnitId,
    latest: Reading | None,
    baseline: Baseline | None,
    *,
    now_epoch_s: int,
    silence_s: int = DEFAULT_SILENCE_S,
    degraded_at: float = DEFAULT_DEGRADED_AT,
) -> Verdict:
    """Decide one unit's health. Deterministic, and never guesses.

    Order matters and is not arbitrary. Silence is checked first because a
    unit that stopped reporting cannot be judged on its last reading — that
    reading described a machine that may no longer exist.
    """
    u = unit.value

    if latest is None:
        return Verdict(u, UnitHealth.UNKNOWN, "no reading has ever arrived",
                       rule="fleet:never-seen")

    age = now_epoch_s - latest.at_epoch_s
    if age > silence_s:
        return Verdict(u, UnitHealth.OFFLINE,
                       f"silent for {age}s (limit {silence_s}s)",
                       rule="fleet:silent")

    # Reporting, but the pool has confirmed nothing. This is the failure that
    # a liveness check would call healthy, which is why it is checked before
    # anything to do with hashrate.
    if latest.accepted == 0 and latest.hashrate > 0:
        return Verdict(u, UnitHealth.BROKEN,
                       "claims a hashrate but no accepted shares",
                       rule="fleet:no-accepted-shares")

    if baseline is None or not baseline.is_trustworthy:
        have = baseline.samples if baseline is not None else 0
        return Verdict(u, UnitHealth.UNKNOWN,
                       f"no trustworthy baseline yet ({have}/"
                       f"{MIN_BASELINE_SAMPLES} samples) — cannot call this "
                       f"unit slow without knowing what fast means for it",
                       rule="fleet:no-baseline")

    if baseline.arm_id != latest.arm_id:
        return Verdict(u, UnitHealth.UNKNOWN,
                       f"baseline is for {baseline.arm_id!r} but the unit is "
                       f"running {latest.arm_id!r} — not comparable",
                       rule="fleet:baseline-mismatch")

    ratio = latest.hashrate / baseline.median_hashrate
    if ratio < degraded_at:
        return Verdict(u, UnitHealth.DEGRADED,
                       f"at {int(ratio * 100)}% of its own proven baseline",
                       rule="fleet:below-baseline")

    return Verdict(u, UnitHealth.HEALTHY, "reporting and producing",
                   rule="fleet:ok")


def judge_all(
    latest: Mapping[str, Reading],
    baselines: Mapping[tuple, Baseline],
    units: Sequence[tuple],
    *,
    now_epoch_s: int,
    silence_s: int = DEFAULT_SILENCE_S,
) -> tuple[Verdict, ...]:
    """Judge every registered unit, including ones that have never reported.

    Iterating the registry rather than the readings is the whole point: a unit
    that has never sent anything produces no reading to iterate over, and is
    exactly the unit most likely to be sitting dead on a shelf.
    """
    out: list[Verdict] = []
    for unit_id, _cls in units:
        reading = latest.get(unit_id)
        key = (unit_id, reading.arm_id if reading is not None else "")
        out.append(judge(UnitId(unit_id), reading, baselines.get(key),
                         now_epoch_s=now_epoch_s, silence_s=silence_s))
    return tuple(out)


def class_is_dark(
    verdicts: Sequence[Verdict],
    units: Sequence[tuple],
    unit_class: UnitClass,
) -> bool:
    """True when every unit of a class is offline or unknown.

    A whole class going dark is a different event from units going dark one at
    a time — it usually means a switch, a power rail, or a bad rollout, not a
    hundred and forty independent failures. Worth its own signal.
    """
    members = {u for u, c in units if c == unit_class.value}
    if not members:
        return False
    live = {v.unit for v in verdicts
            if v.unit in members
            and v.health in (UnitHealth.HEALTHY, UnitHealth.DEGRADED,
                             UnitHealth.BROKEN)}
    return not live


def summarise(verdicts: Sequence[Verdict]) -> Mapping[str, int]:
    counts = {h.value: 0 for h in UnitHealth}
    for v in verdicts:
        counts[v.health.value] += 1
    return counts
