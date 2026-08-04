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


UNRESOLVED = "unresolved"
"""A locale field the owner has not answered yet.

Not a default and not a blank. Anything that needs the value raises rather
than proceeding, so an unanswered question can never quietly become a number
on a partner's screen. Same principle as an absent fact.
"""


class LocaleError(Exception):
    """A locale is unsupported, or a needed field of it is unresolved."""


@dataclass(frozen=True)
class Currency:
    code: str
    symbol: str
    decimals: int

    def __post_init__(self) -> None:
        if not self.code or len(self.code) != 3 or not self.code.isupper():
            raise ValueError(f"currency code must be 3 upper-case letters: {self.code!r}")
        if not 0 <= self.decimals <= 4:
            raise ValueError(f"implausible currency decimals: {self.decimals}")

    def format(self, amount: float) -> str:
        return f"{self.symbol}{amount:,.{self.decimals}f}"


@dataclass(frozen=True)
class Locale:
    """Everything that changes when the market changes — in one object.

    Currency is not a display parameter. A number shown to a partner is only
    meaningful together with the tax treatment that produced it, the timezone
    the week was counted in, and the law the claim has to survive. Splitting
    those apart is how a system ends up "parameterised" while still being
    hard-wired to one market, so they travel together or not at all.

    Exactly one locale is implemented. Any other id is refused at load time —
    a half-supported market is worse than a refused one, because it fails at
    the point where money is involved rather than at boot.
    """

    id: str
    currency: Currency
    # IANA zone id, or UNRESOLVED. "AEST" is not enough: it does not say
    # whether the clock moves in October, and a week boundary that shifts by
    # an hour twice a year silently mis-buckets capacity.
    timezone: str = UNRESOLVED
    # Whether this business is registered for the market's sales tax at all.
    # The rate is a fact about the country; whether it applies is a fact about
    # the business, and only the owner knows it.
    tax_status: str = UNRESOLVED
    tax_rate: float = 0.0
    tax_pricing: str = "inclusive"
    # Turnover at which registering stops being a choice. Not registering is
    # a decision that expires: the business grows into the obligation without
    # anyone deciding to, which is why the number lives here and gets watched
    # rather than living in somebody's memory.
    tax_registration_threshold: float = 0.0
    # Not chosen yet is a real state, distinct from none. Empty means the
    # decision has not been made — nothing may assume a rail or a platform.
    payment_rails: tuple[str, ...] = ()
    platforms: tuple[str, ...] = ()
    legal: tuple[str, ...] = ()

    def require_timezone(self) -> str:
        if self.timezone == UNRESOLVED:
            raise LocaleError(
                f"{self.id}: timezone is unresolved — ask the owner which "
                f"IANA zone this business operates in before bucketing a week")
        return self.timezone

    def require_tax(self) -> tuple[float, str]:
        """The rate that actually applies, or a refusal.

        Returns 0.0 for a business that is not registered: that is an answer,
        not an absence. UNRESOLVED is the absence, and it raises.
        """
        if self.tax_status == UNRESOLVED:
            raise LocaleError(
                f"{self.id}: tax status is unresolved — ask the owner whether "
                f"this business is registered before pricing anything")
        if self.tax_status == "not_registered":
            return 0.0, self.tax_pricing
        return self.tax_rate, self.tax_pricing

    def must_register_at(self, annual_turnover: float) -> bool:
        """True once not-registering has stopped being an available choice."""
        if self.tax_status != "not_registered":
            return False
        t = self.tax_registration_threshold
        return bool(t) and annual_turnover >= t


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
    # The market this business actually sells into. One object, because every
    # field in it only means anything in the presence of the others.
    locale: Locale = field(
        default_factory=lambda: Locale("en-AU", Currency("AUD", "$", 2)))
    # The line under which a price is not worth making, and how little stock
    # counts as running out. Parameters rather than constants because the
    # honest floor for a handmade box is not the honest floor for a day's
    # labour, and both are the owner's call.
    margin_floor: float = 0.30
    runway_warn_days: int = 7
    # Short code stamped on this business's product numbers (ZM-0001). Kept
    # in the pack because it is a thing the owner reads aloud on the phone,
    # not a thing the code should invent from a tenant name.
    sku_prefix: str = ""

    def __post_init__(self) -> None:
        if self.capacity_units_per_week < 0:
            raise ValueError("capacity must be non-negative")
        if not 0.0 <= self.quota_share <= 1.0:
            raise ValueError("quota_share must be within 0..1")
        if not 0.0 <= self.margin_floor < 1.0:
            raise ValueError("margin_floor must be within 0..1")
        if self.runway_warn_days < 0:
            raise ValueError("runway_warn_days must be non-negative")
        unknown = set(self.question_meta) - set(self.required_facts)
        if unknown:
            # Wording for a fact nobody asks for is dead weight that reads as
            # a live question. Almost always a typo in the fact key.
            raise ValueError(
                f"question wording for facts that are not required: "
                f"{sorted(unknown)}")
