"""TaskEnvelope v1 — the one place a run is born.

The blueprint's hardest-won rule lives here: the arm does not mint its own
run_id. `create_envelope()` is the trust boundary's factory; it takes the
randomness as an argument (`rand`) precisely so the kernel stays pure and
the boundary (adapters/service layer, which owns os.urandom) stays the only
minter. A run_id is an identity, and identity collisions were a real bug in
the sister project (two different contradictions both called C-008 on
2026-08-15) — so the format is strict and the store rejects strangers.

Kernel purity: no clock, no I/O, no randomness. Everything arrives as an
argument; validation fails closed via FailClosedError.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Tuple

from .errors import FailClosedError
from .routing import Rung

RISK_TIERS = ("GREEN", "YELLOW", "RED")
AUTHORITY_LEVELS = ("A0", "A1", "A2", "A3")

RUN_ID_RE = re.compile(r"^run-[0-9]{10,12}-[a-z0-9]{10,}$")
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
DEADLINE_ISO_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)

# Deliberately conservative: external authority rides the deepest rung, so
# it inherits the smallest cap (DEFAULT_CAPS[REMOTE_DEEP] == 5). If this
# mapping ever loosens, that is a policy change and belongs in a review.
_AUTHORITY_TO_RUNG: Mapping[str, Rung] = {
    "A0": Rung.RULES,
    "A1": Rung.LOCAL,
    "A2": Rung.REMOTE,
    "A3": Rung.REMOTE_DEEP,
}


def rung_for_authority(level: str) -> Rung:
    try:
        return _AUTHORITY_TO_RUNG[level]
    except KeyError:
        raise FailClosedError(f"unknown authority level: {level!r}") from None


def mint_run_id(now_epoch_s: int, rand: str) -> str:
    """Format a run_id from boundary-supplied time and randomness.

    The kernel formats; it does not generate. `rand` must be at least ten
    lowercase hex/base32-ish characters — os.urandom(8).hex() at the call
    site is the intended shape.
    """
    run_id = f"run-{int(now_epoch_s)}-{rand}"
    if not RUN_ID_RE.match(run_id):
        raise FailClosedError(f"refusing malformed run_id: {run_id!r}")
    return run_id


@dataclass(frozen=True)
class TaskEnvelope:
    """The signed contract a run executes under.

    acceptance_criteria_hash is hashed BEFORE any output exists — the
    pre-registration rule (Aspect 6): a metric that can never go red is
    not a metric, and acceptance you write after the fact is not
    acceptance.
    """

    version: int
    run_id: str
    goal: str
    risk_tier: str
    authority_level: str
    idempotency_key: str
    acceptance_criteria_hash: str
    budget_tokens: int
    budget_aud_cents: int
    deadline_iso: str
    allowed_tools: Tuple[str, ...]
    parent_evidence: Tuple[str, ...]
    rollback_plan: str | None = None
    rollback_ref: str | None = None

    def __post_init__(self) -> None:
        if self.version != 1:
            raise FailClosedError(f"unsupported envelope version: {self.version!r}")
        if not RUN_ID_RE.match(self.run_id or ""):
            raise FailClosedError(f"run_id not minted at the boundary: {self.run_id!r}")
        if not (self.goal or "").strip():
            raise FailClosedError("goal is required")
        if self.risk_tier not in RISK_TIERS:
            raise FailClosedError(f"unknown risk tier: {self.risk_tier!r}")
        if self.authority_level not in AUTHORITY_LEVELS:
            raise FailClosedError(f"unknown authority level: {self.authority_level!r}")
        if not (self.idempotency_key or "").strip():
            raise FailClosedError("idempotency_key is required")
        if not SHA256_HEX_RE.match(self.acceptance_criteria_hash or ""):
            raise FailClosedError(
                "acceptance_criteria_hash must be a sha256 hex digest "
                "(hash it BEFORE the run, not after)"
            )
        for name, value in (("budget_tokens", self.budget_tokens),
                            ("budget_aud_cents", self.budget_aud_cents)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise FailClosedError(f"{name} must be a non-negative int: {value!r}")
        if not DEADLINE_ISO_RE.match(self.deadline_iso or ""):
            raise FailClosedError(f"deadline_iso not ISO-8601: {self.deadline_iso!r}")
        for tool in self.allowed_tools:
            if not isinstance(tool, str) or not tool.strip():
                raise FailClosedError(f"allowed_tools entries must be names: {tool!r}")
        for evidence_id in self.parent_evidence:
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                raise FailClosedError(
                    f"parent_evidence entries must be ids: {evidence_id!r}")
        # The irreversible tier does not run without a way back — and the
        # way back must be a registered artifact, not a promise in prose.
        if self.authority_level == "A3":
            if not (self.rollback_plan or "").strip():
                raise FailClosedError(
                    "rollback_plan is required_for_external (authority A3)")
            if not (self.rollback_ref or "").strip():
                raise FailClosedError(
                    "rollback_ref is required_for_external (authority A3) — "
                    "an id of a registered rollback artifact, not prose")

    def rung(self) -> Rung:
        return rung_for_authority(self.authority_level)

    def may_spend(self, budget, now_epoch_s: int) -> bool:
        """Wiring to CallBudget — the envelope never bypasses the cap."""
        return budget.allows(self.rung(), now_epoch_s)


def create_envelope(
    *,
    goal: str,
    risk_tier: str,
    authority_level: str,
    idempotency_key: str,
    acceptance_criteria_hash: str,
    now_epoch_s: int,
    rand: str,
    deadline_iso: str,
    budget_tokens: int = 0,
    budget_aud_cents: int = 0,
    allowed_tools: Tuple[str, ...] = (),
    parent_evidence: Tuple[str, ...] = (),
    rollback_plan: str | None = None,
    rollback_ref: str | None = None,
) -> TaskEnvelope:
    """The boundary's only sanctioned constructor. Arms call this; they
    cannot inject a run_id because the parameter does not exist."""
    return TaskEnvelope(
        version=1,
        run_id=mint_run_id(now_epoch_s, rand),
        goal=goal,
        risk_tier=risk_tier,
        authority_level=authority_level,
        idempotency_key=idempotency_key,
        acceptance_criteria_hash=acceptance_criteria_hash,
        budget_tokens=budget_tokens,
        budget_aud_cents=budget_aud_cents,
        deadline_iso=deadline_iso,
        allowed_tools=tuple(allowed_tools),
        parent_evidence=tuple(parent_evidence),
        rollback_plan=rollback_plan,
        rollback_ref=rollback_ref,
    )
