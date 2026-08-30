"""Core domain values and entities. Frozen dataclasses; money is integer cents."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from .errors import FailClosedError


class Mode(enum.Enum):
    SHADOW = "shadow"
    LIVE = "live"


class ProposalKind(enum.Enum):
    GRANT = "grant"    # allocate budget to an organ
    EFFECT = "effect"  # outward side effect (send, publish, pay, ...)
    SPAWN = "spawn"    # create a sub-agent — always propose-only (INV-6)


class ProposalStatus(enum.Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTED = "executed"


class RevenueState(enum.Enum):
    """Five-state money attribution. Only CONFIRMED/ATTRIBUTED feed fitness (INV-7)."""

    REPORTED = "reported"      # an agent claims value happened (untrusted, INV-8)
    APPROVED = "approved"      # human acknowledged the claim
    SETTLED = "settled"        # counterparty paid, not yet visible in the bank
    CONFIRMED = "confirmed"    # real AUD visible in the bank account
    ATTRIBUTED = "attributed"  # confirmed AND traced to an organ via carried token


FITNESS_COUNTABLE = frozenset({RevenueState.CONFIRMED, RevenueState.ATTRIBUTED})


@dataclass(frozen=True)
class Money:
    """Integer cents; no floats anywhere near the ledger."""

    cents: int
    currency: str = "AUD"

    def __post_init__(self) -> None:
        if not isinstance(self.cents, int) or isinstance(self.cents, bool):
            raise FailClosedError(f"Money.cents must be int, got {type(self.cents).__name__}")
        if self.cents < 0:
            raise FailClosedError("Money cannot be negative")

    def add(self, other: "Money") -> "Money":
        self._same_currency(other)
        return Money(self.cents + other.cents, self.currency)

    def sub(self, other: "Money") -> "Money":
        self._same_currency(other)
        if other.cents > self.cents:
            raise FailClosedError("Money subtraction would go negative")
        return Money(self.cents - other.cents, self.currency)

    def _same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise FailClosedError(f"currency mismatch: {self.currency} vs {other.currency}")


ZERO = Money(0)


@dataclass(frozen=True)
class Organ:
    """A venture/project — the unit that receives budget and produces revenue."""

    organ_id: str
    name: str
    floor: Money = ZERO      # protected minimum allocation
    vital: bool = True       # vital organs are excluded from cull/prune loops

    def __post_init__(self) -> None:
        if not self.organ_id:
            raise FailClosedError("organ_id must be non-empty")


@dataclass(frozen=True)
class EvidencePack:
    """Structured justification a proposal carries for the human reviewer — the
    2026 HITL 'evidence pack'. Every field is optional so a bare proposal still
    works; when present it compresses the reviewer's decision (impact, how to undo,
    what else was weighed) instead of forcing them to reconstruct it. This is also
    the B6 primitive the Second Brain's Evidence-Card / Approval-Packet ride on."""

    expected_value_cents: int = 0        # estimated upside / impact
    reversibility: str = "unknown"       # "reversible" | "irreversible" | "unknown"
    alternatives: tuple[str, ...] = ()   # other options the proposer weighed
    rollback: str = ""                   # how to undo it if it goes wrong


@dataclass(frozen=True)
class Proposal:
    """Something the Governor *proposes*. The Governor never executes (INV-4)."""

    proposal_id: str
    organ_id: str
    kind: ProposalKind
    amount: Money
    rationale: str
    epoch: int
    irreversible: bool = False
    parent_agent_id: str | None = None
    spawn_depth: int = 0
    # Optional HITL metadata (additive; None/absent preserves prior behavior):
    approval_ttl_epochs: int | None = None   # a verdict older than this many epochs is stale
    evidence: EvidencePack | None = None

    def __post_init__(self) -> None:
        if not self.proposal_id:
            raise FailClosedError("proposal_id must be non-empty")
        if self.epoch < 0:
            raise FailClosedError("epoch must be >= 0")
        if self.kind is ProposalKind.SPAWN and self.parent_agent_id is None:
            raise FailClosedError("spawn proposal requires parent_agent_id")
        if self.approval_ttl_epochs is not None and self.approval_ttl_epochs < 0:
            raise FailClosedError("approval_ttl_epochs must be >= 0")


@dataclass(frozen=True)
class Verdict:
    """A human decision about a proposal. The only source of APPROVED for gated actions."""

    proposal_id: str
    approved: bool
    by: str
    ts: str
    note: str = ""
    epoch: int = 0   # epoch the verdict was issued in — used to age out stale approvals

    def __post_init__(self) -> None:
        if not self.by:
            raise FailClosedError("verdict must name the human who issued it")


@dataclass(frozen=True)
class BudgetState:
    """Global budget under one hard cap, with an optimistic-concurrency token.

    `version` must be checked by the store on write (compare-and-swap); the
    kernel bumps it on every derived state so lost updates surface as
    ConcurrencyConflictError in the adapter instead of silent double-spend.
    """

    cap: Money
    committed: Money = ZERO
    version: int = 0

    def __post_init__(self) -> None:
        if self.committed.cents > self.cap.cents:
            raise FailClosedError("committed exceeds cap (INV-1 violated at construction)")


UNTRUSTED_OPEN = "<<<UNTRUSTED-DATA"
UNTRUSTED_CLOSE = "UNTRUSTED-DATA>>>"


@dataclass(frozen=True)
class ExternalText:
    """Text that crossed a trust boundary. It is data, never instructions (INV-9)."""

    value: str
    source: str

    def quarantined(self) -> str:
        """Render for inclusion in any prompt/report: always inside explicit delimiters."""
        return f"{UNTRUSTED_OPEN} source={self.source}\n{self.value}\n{UNTRUSTED_CLOSE}"


@dataclass(frozen=True)
class GateDecision:
    """Outcome of a gate check. `shadow=True` means allowed but must be simulated."""

    allowed: bool
    reason: str
    invariant: str | None = None
    shadow: bool = False
    checks: tuple[str, ...] = field(default_factory=tuple)
