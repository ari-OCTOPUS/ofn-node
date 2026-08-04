"""Domain types. Frozen dataclasses, no behaviour that touches the world.

Rules that hold everywhere in this module:
  * Tokens are integers. A float near a quota ledger is a defect.
  * Nothing here reads a clock, an env var, or a file. Time arrives as a
    parameter (`now_epoch_s`), never as `time.time()`.
  * No business, partner, or product name appears in this package. Ever.
    `tests/test_kernel_purity.py` enforces that mechanically.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Mapping


class RiskTier(enum.Enum):
    """How much of the world an action can disturb.

    The kernel assigns this — never the model. A model claiming an action is
    GREEN carries no weight: agent self-reports are untrusted and the gate
    re-derives the tier from facts (INV-8).
    """

    GREEN = "green"    # reversible, no money, no PII, stays inside the node
    YELLOW = "yellow"  # leaves the node but is reversible
    RED = "red"        # irreversible, or money, or PII, or under a closed gate

    def at_least(self, other: "RiskTier") -> bool:
        return _TIER_ORDER[self] >= _TIER_ORDER[other]


_TIER_ORDER: Mapping[RiskTier, int] = {
    RiskTier.GREEN: 0,
    RiskTier.YELLOW: 1,
    RiskTier.RED: 2,
}


def max_tier(*tiers: RiskTier) -> RiskTier:
    """Risk only ever ratchets up. There is no de-escalation path by design."""
    if not tiers:
        return RiskTier.GREEN
    return max(tiers, key=lambda t: _TIER_ORDER[t])


class Confidence(enum.Enum):
    """How much a stored fact may be leaned on.

    Ordering matters: `publish` requires `OWNER_CONFIRMED`. Anything softer is
    a guess wearing a number, and guesses do not reach customers.
    """

    GUESSED = "guessed"
    INFERRED = "inferred"
    MEASURED = "measured"
    OWNER_CONFIRMED = "owner_confirmed"

    def meets(self, required: "Confidence") -> bool:
        return _CONF_ORDER[self] >= _CONF_ORDER[required]


_CONF_ORDER: Mapping[Confidence, int] = {
    Confidence.GUESSED: 0,
    Confidence.INFERRED: 1,
    Confidence.MEASURED: 2,
    Confidence.OWNER_CONFIRMED: 3,
}


@dataclass(frozen=True)
class TenantId:
    """An opaque, validated tenant handle.

    Deliberately a value object rather than a bare `str`: it makes
    `state_for(tenant)` impossible to call with a raw, unvalidated string
    that happens to contain a path traversal.
    """

    value: str

    _ALLOWED = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")

    def __post_init__(self) -> None:
        v = self.value
        if not v or len(v) > 32:
            raise ValueError(f"tenant id must be 1..32 chars, got {len(v)}")
        bad = set(v) - self._ALLOWED
        if bad:
            raise ValueError(f"tenant id has illegal chars: {sorted(bad)}")
        if v.startswith(("-", "_")) or v.endswith(("-", "_")):
            raise ValueError("tenant id must not start or end with - or _")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


@dataclass(frozen=True)
class Action:
    """Something a leg wants to do. Not yet permitted — just described.

    `evidence` maps a required fact key to the confidence actually available,
    so the gate can check the claim without trusting the caller's summary.
    """

    tenant: TenantId
    name: str
    reversible: bool = True
    touches_money: bool = False
    touches_pii: bool = False
    leaves_node: bool = False
    recipient_from_observed_content: bool = False
    evidence: Mapping[str, Confidence] = field(default_factory=dict)
    requested_units: int = 0
    estimated_tokens: int = 0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("action name is required")
        if self.requested_units < 0 or self.estimated_tokens < 0:
            raise ValueError("counts must be non-negative")


@dataclass(frozen=True)
class Decision:
    """A gate's answer. Always carries a reason a human can read.

    `rule` names the constraint that produced the outcome, so every denial in
    the ledger can be traced back to a line of policy rather than a vibe.
    """

    allowed: bool
    tier: RiskTier
    reason: str
    rule: str = ""
    checks: tuple[str, ...] = ()

    @property
    def needs_human(self) -> bool:
        """GREEN runs unattended. Everything else waits for a finger."""
        return self.allowed and self.tier is not RiskTier.GREEN

    @property
    def needs_double_confirm(self) -> bool:
        return self.allowed and self.tier is RiskTier.RED


@dataclass(frozen=True)
class TokenSpend:
    """One model call's cost, in the only unit that matters: what gets billed.

    `visible` is what the provider echoes back. `orchestration` is what it
    spent internally and does not show. For an orchestrating provider the
    second number is the larger one — dropping it silently under-counts spend
    by roughly 60% and poisons every downstream budget decision.
    """

    visible: int
    orchestration: int = 0

    def __post_init__(self) -> None:
        if self.visible < 0 or self.orchestration < 0:
            raise ValueError("token counts must be non-negative")

    @property
    def effective(self) -> int:
        return self.visible + self.orchestration


@dataclass(frozen=True)
class PackSpec:
    """The whole of a business's configuration, as the kernel sees it.

    The kernel never learns what the business *is* — only its shape: how much
    it can produce, which facts must exist before it may speak, which gates
    are wired, and which actions are forced to a higher tier.
    """

    tenant: TenantId
    capacity_units_per_week: int
    required_facts: Mapping[str, Confidence] = field(default_factory=dict)
    gates: tuple[str, ...] = ()
    risk_overrides: Mapping[str, RiskTier] = field(default_factory=dict)
    quota_share: float = 0.0
    # How to *ask* for each required fact, in the partner's own words. The
    # kernel derives which facts are missing; it cannot invent a sentence a
    # person would understand, and it must not try — the wording is business
    # content and belongs in the pack beside the fact it asks about. Absent
    # wording is not an error: the shell falls back to the fact key, which is
    # ugly but honest, and the ugliness is what gets the pack filled in.
    question_meta: Mapping[str, Mapping[str, object]] = field(
        default_factory=dict)

    def __post_init__(self) -> None:
        if self.capacity_units_per_week < 0:
            raise ValueError("capacity must be non-negative")
        if not 0.0 <= self.quota_share <= 1.0:
            raise ValueError("quota_share must be within 0..1")
        unknown = set(self.question_meta) - set(self.required_facts)
        if unknown:
            # Wording for a fact nobody asks for is dead weight that reads as
            # a live question. Almost always a typo in the fact key.
            raise ValueError(
                f"question wording for facts that are not required: "
                f"{sorted(unknown)}")
