"""The weekly marketing scout: what to research, and what to refuse.

This is the content-production analogue of `scout.py`. Where the mining
scout holds "every candidate ever seen, and how it ended" so a model
cannot re-propose a dead end thirty times, this one holds "every trend
and idea ever shown to the partner, and how it ended" so the model's
weekly research does not become a loop.

Three things live here that the model is not trusted with:

**What we already know.** Every trend observation and every idea ever
proposed, with its disposition. An idea rejected for a structural reason
— platform bans it, no observed evidence, targets a forbidden framing —
is refused again automatically the next time it is proposed, without
spending a token on it.

**What to look at next.** Derived from measured gaps, not from what
sounds interesting. The partner's own four signals — felt-right, message,
number, trend — set the agenda. An axis that has never been tried is a
bigger question than a marginal refinement of one that has.

**What may never pass.** A trend with no `observed_at` is a guess dressed
as an observation. A trend with no count or rank is an assertion without
evidence. A "prediction" of what will trend is exactly the class of error
this whole project exists to refuse. The screen does not care how
enthusiastic the description is.

Kernel purity: no clock, no I/O, no randomness, no network, no product
names. The scout decides; the adapter calls the model.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

from .errors import FailClosedError


# A stable slug for deduplication. Same idea under a prettier title is still
# the same idea.
_KEY = re.compile(r"^[a-z0-9]([a-z0-9._-]{0,62}[a-z0-9])?$")

# How long a soft-rejected idea stays buried. A structural rejection never
# expires — "this framing is banned on every Layer-C platform" will still be
# true in a year. But "the trend source was in closed beta" is a fact about
# a moment, and may have changed.
SOFT_REJECT_COOLDOWN_S = 90 * 24 * 3600

# The minimum confidence a candidate must carry to reach the partner at all.
# Below this, the screen refuses it without spending human attention. This
# is deliberately not tunable per-call: a confidence threshold that a model
# can argue its way past is not a threshold.
DEFAULT_MIN_CONFIDENCE = 0.45


class Disposition(enum.Enum):
    UNSEEN = "unseen"
    PROPOSED = "proposed"             # waiting on the partner
    ACCEPTED = "accepted"             # partner is acting on it
    REJECTED_HARD = "rejected_hard"   # structural — never re-propose
    REJECTED_SOFT = "rejected_soft"   # circumstantial — may return later
    TRIED_FAILED = "tried_failed"     # tried, produced nothing

    def is_final(self) -> bool:
        return self in (Disposition.REJECTED_HARD, Disposition.TRIED_FAILED)


@dataclass(frozen=True)
class TrendObservation:
    """One piece of evidence that something is being seen.

    A candidate carries at least one of these; without evidence it is an
    assertion. `observed_at` is mandatory and is the structural defence
    against "the model predicted a trend": a thing with a timestamp was
    *seen*, not *foretold*.
    """

    source_id: str           # which source saw it (e.g. a feed id) — opaque to the kernel
    term: str                # the trend term / hashtag / topic, as observed
    observed_at: int         # epoch seconds — when it was seen
    count_value: float | None = None    # a volume / interest number, if the source gives one
    rank_value: int | None = None       # a rank, if the source ranks
    region: str | None = None
    source_url: str | None = None

    def __post_init__(self) -> None:
        if not self.observed_at:
            raise FailClosedError(
                "an observation without observed_at is a prediction, not "
                "an observation — refused")
        if self.count_value is None and self.rank_value is None:
            raise FailClosedError(
                f"observation of {self.term!r} carries neither a count nor "
                f"a rank — an assertion without evidence is refused")


@dataclass(frozen=True)
class Candidate:
    """One idea the scout thinks is worth the partner's attention.

    `key` is what makes memory work: a stable slug the same idea always
    gets, so the same proposal arriving under a prettier title is still
    recognised. It must be a safe slug, not free text.
    """

    key: str
    title: str
    style_id: str           # one of the marketing styles (data, not kernel knowledge)
    framing: str            # the framing this idea would use
    observations: tuple[TrendObservation, ...]
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not _KEY.match(self.key):
            raise FailClosedError(
                f"candidate key {self.key!r} is not a safe slug")
        if not self.title.strip():
            raise FailClosedError("a candidate with no title cannot be reviewed")
        if not 0.0 <= self.confidence <= 1.0:
            raise FailClosedError(
                f"candidate {self.key!r} confidence {self.confidence} is "
                f"out of [0, 1]")


@dataclass(frozen=True)
class Note:
    """What happened to a candidate, and when."""

    key: str
    disposition: Disposition
    reason: str
    at_epoch_s: int = 0


@dataclass
class Memory:
    """Everything the scout has ever concluded. Append-only in spirit.

    Deliberately not a cache with an eviction policy: forgetting a rejection
    is how a system starts proposing the same dead end every quarter.
    """

    notes: dict = field(default_factory=dict)

    def record(self, note: Note) -> None:
        prev = self.notes.get(note.key)
        if prev is not None and prev.disposition is Disposition.REJECTED_HARD:
            # The ratchet: dispositions may harden, never soften. A later,
            # sunnier note cannot revive something refused for a structural
            # reason.
            return
        self.notes[note.key] = note

    def disposition(self, key: str) -> Disposition:
        note = self.notes.get(key)
        return note.disposition if note is not None else Disposition.UNSEEN

    def known_keys(self) -> tuple[str, ...]:
        return tuple(sorted(self.notes))

    def summary(self) -> Mapping[str, int]:
        counts = {d.value: 0 for d in Disposition}
        for note in self.notes.values():
            counts[note.disposition.value] += 1
        return counts


@dataclass(frozen=True)
class Screen:
    accepted: bool
    reason: str
    rule: str
    hard: bool = False


def screen(candidate: Candidate,
           *,
           min_confidence: float = DEFAULT_MIN_CONFIDENCE) -> Screen:
    """Refuse what may never reach the partner, before a human sees it.

    Each refusal names the rule so the owner can see *which* line was hit
    rather than a general disapproval. Order is cheapest-to-explain first.
    """
    if not candidate.observations:
        return Screen(False, "carries no observation — an assertion, "
                      "not a finding", rule="scout:no-evidence", hard=True)

    for obs in candidate.observations:
        # TrendObservation's __post_init__ already enforces observed_at and
        # count/rank, but defence in depth: if one slipped through (e.g. a
        # future subclass), the screen still catches it.
        if not obs.observed_at:
            return Screen(False,
                          f"observation of {obs.term!r} has no observed_at",
                          rule="scout:missing-observed-at", hard=True)

    if candidate.confidence < min_confidence:
        return Screen(False,
                      f"confidence {candidate.confidence:.2f} below "
                      f"threshold {min_confidence:.2f}",
                      rule="scout:low-confidence", hard=False)

    return Screen(True, f"{len(candidate.observations)} observation(s)",
                  rule="scout:ok")


def triage(
    candidates: Sequence[Candidate],
    memory: Memory,
    *,
    now_epoch_s: int,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> tuple[tuple[Candidate, ...], tuple[tuple[Candidate, Screen], ...]]:
    """Split a week's harvest into "show the partner" and "already answered".

    Returns (fresh, refused). The refused list is returned rather than
    dropped because a scout that silently discards nine of ten proposals
    looks like a scout that found one thing, and the owner cannot tell the
    difference between a quiet week and a broken pipeline.
    """
    fresh: list[Candidate] = []
    refused: list[tuple[Candidate, Screen]] = []

    for c in sorted(candidates, key=lambda x: x.key):
        prior = memory.notes.get(c.key)
        if prior is not None:
            if prior.disposition.is_final():
                refused.append((c, Screen(
                    False, f"already settled: {prior.reason}",
                    rule="scout:already-final")))
                continue
            if prior.disposition is Disposition.REJECTED_SOFT:
                age = now_epoch_s - prior.at_epoch_s
                if age < SOFT_REJECT_COOLDOWN_S:
                    days = (SOFT_REJECT_COOLDOWN_S - age) // 86400
                    refused.append((c, Screen(
                        False, f"set aside: {prior.reason}; "
                        f"{days}d of cooldown left",
                        rule="scout:cooling-off")))
                    continue
            if prior.disposition in (Disposition.PROPOSED,
                                     Disposition.ACCEPTED):
                refused.append((c, Screen(
                    False, "already in front of the partner or already "
                    "being acted on",
                    rule="scout:duplicate")))
                continue

        verdict = screen(c, min_confidence=min_confidence)
        if verdict.accepted:
            fresh.append(c)
        else:
            refused.append((c, verdict))

    return tuple(fresh), tuple(refused)


def research_focus(
    memory: Memory,
    *,
    last_week_style: str | None,
    tried_styles: Mapping[str, int],
    max_questions: int = 3,
) -> tuple[str, ...]:
    """What to spend this week's research on. Derived from gaps, not novelty.

    The ordering is the argument: a style that has never been tried is a
    bigger hole than a marginal improvement to one that has, and a style
    that was tried and produced nothing is a more useful question than
    "what else is out there". Open-ended discovery comes last.
    """
    questions: list[str] = []

    untried = sorted(s for s in tried_styles if tried_styles[s] == 0)
    for s in untried:
        questions.append(
            f"style {s!r} has never been tried — what observed trend fits "
            f"it? require observed_at and a count or rank.")

    # Bounded, because a research budget spread across ten questions
    # answers none of them.
    if len(questions) < max_questions:
        seen = len(memory.known_keys())
        avoid = f" avoid repeating last week's style {last_week_style!r}." \
            if last_week_style else ""
        questions.append(
            f"we have evaluated {seen} candidates so far — what has appeared "
            f"since that we have not seen?{avoid} require observed_at and a "
            f"count or rank; do not predict.")

    return tuple(questions[:max_questions])


def brief(memory: Memory) -> Mapping[str, object]:
    """The context a research call needs, assembled without a model's help.

    Handing the rejection list to the researcher is what stops it re-finding
    what we already refused. It costs a few hundred tokens and saves a call.
    """
    rejected_hard = sorted(k for k, n in memory.notes.items()
                           if n.disposition is Disposition.REJECTED_HARD)
    proposed = sorted(k for k, n in memory.notes.items()
                      if n.disposition is Disposition.PROPOSED)
    accepted = sorted(k for k, n in memory.notes.items()
                      if n.disposition is Disposition.ACCEPTED)
    return {
        "already_rejected": rejected_hard,
        "already_proposed": proposed,
        "already_accepted": accepted,
        "counts": dict(memory.summary()),
        "rule": "observed trends only; each must carry observed_at and a "
                "count or rank; no predictions",
    }
