"""The daily scout: what to research tomorrow, and what to refuse today.

A model asked "find me new opportunities" every morning will, by the end of the
month, have proposed the same dead ends thirty times. It has no memory of last
Tuesday, no knowledge of what the fleet actually measured, and every incentive
to sound useful. That failure mode is not fixed by a better prompt. It is fixed
by putting the memory and the refusals *outside* the model, in code that cannot
be talked out of them.

So this module holds three things the model is not trusted with:

**What we already know.** Every candidate ever seen, and how it ended. A
candidate that was rejected for a structural reason — needs capital, needs a
private key on the device — is refused again automatically the next time it is
proposed, without spending a token on it.

**What to look at next.** Derived from evidence, not from what sounds
interesting. If a class of hardware has nothing to run, that gap is the
question. If an arm has been running for days without producing, that failure
is the question. The fleet's own measurements set the agenda.

**What may never pass.** The hard constraints are screened here, before a
proposal reaches a human. Not because the model is malicious, but because it is
agreeable: asked for opportunities, it will surface one that needs a wallet key
on the device and describe it enthusiastically. The screen does not care how
good the description is.

Kernel purity: no clock, no I/O, no randomness, no network, no product names.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .errors import FailClosedError

_KEY = re.compile(r"^[a-z0-9]([a-z0-9._-]{0,62}[a-z0-9])?$")

# How long a candidate rejected for a *soft* reason stays buried. Structural
# rejections never expire — a thing that needs capital will still need capital
# in a year. But "the network was in closed beta" is a fact about a moment.
SOFT_REJECT_COOLDOWN_S = 90 * 24 * 3600

# An arm that has run this long without producing is a question worth asking
# the research budget about, rather than one more thing to quietly retry.
STALE_TRIAL_S = 3 * 24 * 3600

# The age window for an emerging chain, in weeks. Both ends are a real
# constraint rather than a preference:
#
#   too new — a chain on day one has no pool, no explorer, and no evidence it
#   will still exist on Friday. The share we would capture is enormous and the
#   probability it means anything is not.
#
#   too old — difficulty has climbed past the point where sixteen small boards
#   register at all, and we are back to collecting a rounding error.
MIN_AGE_WEEKS = 1
MAX_AGE_WEEKS = 8


class Disposition(enum.Enum):
    UNSEEN = "unseen"
    PROPOSED = "proposed"        # waiting on the owner
    ACCEPTED = "accepted"        # owner pinned it
    REJECTED_HARD = "rejected_hard"   # structural — never re-propose
    REJECTED_SOFT = "rejected_soft"   # circumstantial — may return later
    TRIED_FAILED = "tried_failed"     # pinned, run, produced nothing

    def is_final(self) -> bool:
        return self in (Disposition.REJECTED_HARD, Disposition.TRIED_FAILED)


@dataclass(frozen=True)
class Constraints:
    """The owner's non-negotiables, as data rather than as prose in a prompt.

    A prompt can be argued with; a dataclass cannot. Every field here started
    as a sentence in a brief that a model would eventually find a reading of.
    """

    allow_capital: bool = False
    allow_private_key_on_device: bool = False
    allow_kyc: bool = False
    known_classes: tuple[str, ...] = ()
    min_age_weeks: float = MIN_AGE_WEEKS
    max_age_weeks: float = MAX_AGE_WEEKS

    def __post_init__(self) -> None:
        if not self.known_classes:
            raise FailClosedError(
                "constraints must list the hardware classes that exist — "
                "otherwise every proposal matches and the screen is decorative")


@dataclass(frozen=True)
class Candidate:
    """One thing the scout thinks is worth trying.

    `key` is what makes memory work: a stable slug the same thing always gets,
    so the same proposal arriving under a prettier name is still recognised.
    """

    key: str
    title: str
    needs_capital: bool = False
    needs_private_key: bool = False
    needs_kyc: bool = False
    classes: tuple[str, ...] = ()
    source: str = ""
    age_weeks: float | None = None    # None = the researcher did not establish it

    def __post_init__(self) -> None:
        if not _KEY.match(self.key):
            raise FailClosedError(f"candidate key {self.key!r} is not a safe slug")
        if not self.title.strip():
            raise FailClosedError("a candidate with no title cannot be reviewed")


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

    Deliberately not a cache with an eviction policy: forgetting a rejection is
    how a system starts proposing the same dead end every quarter.
    """

    notes: dict = field(default_factory=dict)

    def record(self, note: Note) -> None:
        prev = self.notes.get(note.key)
        if prev is not None and prev.disposition is Disposition.REJECTED_HARD:
            # A structural refusal is not revisable by a later, sunnier note.
            # This is the ratchet: dispositions may harden, never soften.
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


def screen(candidate: Candidate, constraints: Constraints) -> Screen:
    """Refuse what may never pass, before a human spends attention on it.

    Order is cheapest-to-explain first. Each refusal names the rule so the
    owner can see *which* line was hit rather than a general disapproval.
    """
    if candidate.needs_private_key and not constraints.allow_private_key_on_device:
        return Screen(False, "requires a private key on an unattended device",
                      rule="scout:no-key-on-device", hard=True)

    if candidate.needs_capital and not constraints.allow_capital:
        return Screen(False, "requires locking up capital",
                      rule="scout:no-capital", hard=True)

    if candidate.needs_kyc and not constraints.allow_kyc:
        return Screen(False, "requires identity verification",
                      rule="scout:no-kyc", hard=True)

    if not candidate.classes:
        return Screen(False, "names no hardware class it would run on",
                      rule="scout:no-class", hard=False)

    usable = [c for c in candidate.classes if c in constraints.known_classes]
    if not usable:
        return Screen(False,
                      f"needs hardware we do not have ({', '.join(candidate.classes)})",
                      rule="scout:unknown-hardware", hard=True)

    if candidate.age_weeks is not None:
        if candidate.age_weeks < constraints.min_age_weeks:
            # Soft: a chain too young today is the right age next month, and
            # burying it permanently would throw away the best candidates.
            return Screen(False,
                          f"only {candidate.age_weeks:g} weeks old — no pool or "
                          f"explorer history to judge it by yet",
                          rule="scout:too-new", hard=False)
        if candidate.age_weeks > constraints.max_age_weeks:
            return Screen(False,
                          f"{candidate.age_weeks:g} weeks old — difficulty has "
                          f"moved past what this fleet can register on",
                          rule="scout:too-old", hard=True)

    return Screen(True, f"runs on {', '.join(usable)}", rule="scout:ok")


def triage(
    candidates: Sequence[Candidate],
    memory: Memory,
    constraints: Constraints,
    *,
    now_epoch_s: int,
) -> tuple[tuple[Candidate, ...], tuple[tuple[Candidate, Screen], ...]]:
    """Split a day's harvest into "show the owner" and "already answered".

    Returns (fresh, refused). The refused list is returned rather than dropped
    because a scout that silently discards nine of ten proposals looks like a
    scout that found one thing, and the owner cannot tell the difference
    between a quiet day and a broken pipeline.
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
                        False, f"set aside {prior.reason}; {days}d of cooldown left",
                        rule="scout:cooling-off")))
                    continue
            if prior.disposition in (Disposition.PROPOSED, Disposition.ACCEPTED):
                refused.append((c, Screen(
                    False, "already in front of the owner or already running",
                    rule="scout:duplicate")))
                continue

        verdict = screen(c, constraints)
        if verdict.accepted:
            fresh.append(c)
        else:
            refused.append((c, verdict))

    return tuple(fresh), tuple(refused)


def research_focus(
    memory: Memory,
    trials: Mapping[tuple, object],
    classes: Sequence[str],
    *,
    now_epoch_s: int,
    max_questions: int = 3,
) -> tuple[str, ...]:
    """What to spend today's research on. Derived from gaps, not from novelty.

    The ordering is the argument: a class of hardware sitting idle is a bigger
    hole than a marginal improvement to something already working, and a thing
    that ran for days and produced nothing is a more useful question than "what
    else is out there". Open-ended discovery comes last, when there is nothing
    specific left to ask.

    Bounded, because a research budget spread across ten questions answers none
    of them.
    """
    questions: list[str] = []

    covered = {cls for key in trials for cls in (key[1],)} if trials else set()
    for cls in sorted(classes):
        if cls not in covered:
            questions.append(
                f"hardware class {cls!r} is running nothing at all — what work "
                f"exists that this class can do?")

    stale = []
    for key, trial in sorted(trials.items()):
        seconds = getattr(trial, "seconds", 0)
        accepted = getattr(trial, "accepted", 0)
        if seconds >= STALE_TRIAL_S and accepted == 0:
            stale.append(key)
    for key in stale:
        questions.append(
            f"{key[0]!r} has run on {key[1]!r} for days and produced nothing — "
            f"is it misconfigured, or is it dead?")

    if len(questions) < max_questions:
        seen = len(memory.known_keys())
        questions.append(
            f"we have evaluated {seen} candidates so far — what has appeared "
            f"since that we have not seen?")

    return tuple(questions[:max_questions])


def brief(memory: Memory, constraints: Constraints) -> Mapping[str, object]:
    """The context a research call needs, assembled without a model's help.

    Handing the rejection list to the researcher is what stops it re-finding
    what we already refused. It costs a few hundred tokens and saves a call.
    """
    rejected = sorted(k for k, n in memory.notes.items()
                      if n.disposition is Disposition.REJECTED_HARD)
    running = sorted(k for k, n in memory.notes.items()
                     if n.disposition is Disposition.ACCEPTED)
    failed = sorted(k for k, n in memory.notes.items()
                    if n.disposition is Disposition.TRIED_FAILED)
    return {
        "hardware_classes": list(constraints.known_classes),
        "no_capital": not constraints.allow_capital,
        "no_private_key_on_device": not constraints.allow_private_key_on_device,
        "no_kyc": not constraints.allow_kyc,
        "age_window_weeks": [constraints.min_age_weeks, constraints.max_age_weeks],
        "already_rejected": rejected,
        "already_running": running,
        "tried_and_failed": failed,
        "counts": dict(memory.summary()),
    }
