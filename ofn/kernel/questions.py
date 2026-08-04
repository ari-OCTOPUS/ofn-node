"""What to ask a partner, and in what order. Deterministic, no model involved.

A question is not generated. It is *derived*: the pack declares which facts
must exist before the business may act, the fact store says which of those are
missing or too weak, and the difference is the question list. Same inputs,
same questions, every time — which means a partner is never asked something
random, and the reason for every question can be shown as a sentence.

Ordering is by leverage: how many gated actions a fact unblocks, then how
stale the current answer is. Asking the highest-leverage question first is the
difference between a partner answering two things and the business moving,
versus answering nine things and nothing changing.

The hard rule this module enforces is scarcity. Partners are people running
businesses, not a data-entry surface. `plan()` caps how many questions exist
at once, because a screen with nine questions gets none of them answered.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Mapping, Sequence

from .domain import Confidence, PackSpec, RiskTier

# One screen, one decision. More than a handful and the list becomes a chore
# to dismiss rather than a thing to answer.
DEFAULT_MAX_QUESTIONS = 3


class Kind(enum.Enum):
    """How the answer should be collected. The shell renders accordingly."""

    NUMBER = "number"
    CHOICE = "choice"
    TEXT = "text"
    CONFIRM = "confirm"


@dataclass(frozen=True)
class Question:
    key: str                       # "subject.predicate"
    kind: Kind
    required: Confidence
    have: Confidence | None
    unblocks: tuple[str, ...]      # actions currently gated on this fact
    leverage: int

    @property
    def is_missing(self) -> bool:
        return self.have is None

    @property
    def why(self) -> str:
        """One sentence a non-technical person can read."""
        acts = ", ".join(self.unblocks[:3]) if self.unblocks else ""
        tail = f" — این جواب {acts} را باز می‌کند" if acts else ""
        if self.is_missing:
            return f"هنوز ثبت نشده{tail}"
        return f"ثبت شده ولی هنوز تأیید نشده{tail}"


def _kind_for(key: str) -> Kind:
    """Infer the input control from the fact's name.

    Deliberately crude and deliberately here rather than in the pack: a pack
    author should describe their business, not their form widgets. When this
    guesses wrong the fix is a better rule here, not a new field in every pack.
    """
    tail = key.rsplit(".", 1)[-1].lower()
    if any(w in tail for w in ("capacity", "count", "hours", "radius", "price",
                               "cogs", "minutes", "per_week")):
        return Kind.NUMBER
    if any(w in tail for w in ("model", "mode", "type", "family")):
        return Kind.CHOICE
    if tail.startswith(("is_", "has_")) or "confirm" in tail:
        return Kind.CONFIRM
    return Kind.TEXT


def gated_actions(pack: PackSpec) -> tuple[str, ...]:
    """Actions the pack pins above GREEN — the ones a missing fact holds up."""
    return tuple(sorted(
        name for name, tier in pack.risk_overrides.items()
        if tier.at_least(RiskTier.YELLOW)))


# How often a fact must be re-asked, when the pack says so. Named periods
# rather than numbers, because "quarter" is a thing a person means and
# "7776000" is a thing somebody typed.
ASK_EVERY_SECONDS: Mapping[str, int] = {
    "day": 86_400,
    "week": 7 * 86_400,
    "month": 30 * 86_400,
    "quarter": 90 * 86_400,
    "year": 365 * 86_400,
}


def is_stale(period: object, age_seconds: int) -> bool:
    """Whether an answer given this long ago has to be asked again.

    An unknown period returns False rather than raising: a typo in a pack
    must not stop the node, and the safe direction here is *not* re-asking —
    a question that reappears every screen is how a partner learns to dismiss
    questions without reading them. The typo is caught by the pack loader.

    A negative age is treated as fresh. The clock on this board has no
    battery, and an answer that appears to come from the future is a clock
    problem, not a reason to interrogate somebody.
    """
    if not isinstance(period, str):
        return False
    limit = ASK_EVERY_SECONDS.get(period)
    if limit is None:
        return False
    return age_seconds > limit


def plan(
    pack: PackSpec,
    evidence: Mapping[str, Confidence],
    *,
    max_questions: int = DEFAULT_MAX_QUESTIONS,
) -> Sequence[Question]:
    """The questions worth asking right now, highest leverage first.

    A fact already held at or above its required confidence produces no
    question. Re-asking a settled question is how a partner learns the app is
    not listening.
    """
    if max_questions < 1:
        raise ValueError("max_questions must be at least 1")

    blocked = gated_actions(pack)
    out: list[Question] = []

    for key, required in sorted(pack.required_facts.items()):
        have = evidence.get(key)
        if have is not None and have.meets(required):
            continue
        # Leverage: missing outranks weak, because a missing fact blocks
        # outright while a weak one merely forces a human into the loop.
        leverage = len(blocked) * (2 if have is None else 1)
        out.append(Question(
            key=key, kind=_kind_for(key), required=required, have=have,
            unblocks=blocked, leverage=leverage))

    out.sort(key=lambda q: (-q.leverage, q.key))
    return tuple(out[:max_questions])


def readiness(pack: PackSpec,
              evidence: Mapping[str, Confidence]) -> tuple[int, int]:
    """(satisfied, required) — the progress a partner can see.

    Progress that only moves when *everything* is done reads as broken, so
    this is deliberately a fraction rather than a boolean.
    """
    required = pack.required_facts
    if not required:
        return (0, 0)
    done = sum(1 for k, need in required.items()
               if (have := evidence.get(k)) is not None and have.meets(need))
    return (done, len(required))


def is_ready(pack: PackSpec, evidence: Mapping[str, Confidence]) -> bool:
    done, total = readiness(pack, evidence)
    return total > 0 and done == total
