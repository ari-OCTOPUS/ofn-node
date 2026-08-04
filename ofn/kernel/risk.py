"""Risk tiering: the kernel decides how dangerous an action is.

Three tiers, one direction. An action's tier is computed from what the action
*does*, then ratcheted upward by mandatory rules. Nothing lowers a tier —
not a pack override, not a model's opinion, not a caller's assertion.

Why the ratchet is one-directional: the alternative is a system where some
path exists that turns RED into GREEN, and that path will eventually be taken
by accident. Making de-escalation unrepresentable is cheaper than auditing
for it.

The model is never consulted here. A model that says "this is safe to send"
has produced a self-report, and self-reports are re-verified by an external
gate rather than believed (INV-8).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .domain import Action, Confidence, PackSpec, RiskTier, max_tier


@dataclass(frozen=True)
class Escalation:
    """One reason a tier was raised. Kept for the ledger, not for display only."""

    rule: str
    to: RiskTier
    detail: str


@dataclass(frozen=True)
class RiskAssessment:
    tier: RiskTier
    base: RiskTier
    escalations: tuple[Escalation, ...] = ()

    @property
    def why(self) -> str:
        if not self.escalations:
            return f"base tier {self.base.value}"
        top = self.escalations[-1]
        return f"{top.rule}: {top.detail}"


def base_tier(action: Action) -> RiskTier:
    """Tier from the action's own shape, before any mandatory rule fires."""
    if not action.reversible:
        return RiskTier.RED
    if action.leaves_node:
        return RiskTier.YELLOW
    return RiskTier.GREEN


def assess(
    action: Action,
    pack: PackSpec,
    *,
    closed_gates: Sequence[str] = (),
    units_used_this_week: int = 0,
) -> RiskAssessment:
    """Classify an action. Deterministic: same inputs, same tier, always.

    `closed_gates` are the gate names currently shut node-wide (unrotated
    secrets, an unresolved precondition). If a pack wires a gate that is
    currently closed, everything that pack does becomes RED — the gate is not
    bypassed, it is escalated into a human's hands.
    """
    base = base_tier(action)
    esc: list[Escalation] = []
    tier = base

    # ── money is always RED, in any amount ────────────────────────────────
    if action.touches_money:
        tier = max_tier(tier, RiskTier.RED)
        esc.append(Escalation("money", RiskTier.RED,
                              "action moves or commits money"))

    # ── PII is always RED ─────────────────────────────────────────────────
    if action.touches_pii:
        tier = max_tier(tier, RiskTier.RED)
        esc.append(Escalation("pii", RiskTier.RED,
                              "action reads or transmits personal data"))

    # ── a recipient chosen by observed content is an injection vector ─────
    if action.recipient_from_observed_content:
        tier = max_tier(tier, RiskTier.RED)
        esc.append(Escalation("untrusted-recipient", RiskTier.RED,
                              "destination came from observed content, not the owner"))

    # ── unconfirmed evidence may not reach the outside world ──────────────
    for fact_key, required in sorted(pack.required_facts.items()):
        have = action.evidence.get(fact_key)
        if have is None:
            if action.leaves_node:
                tier = max_tier(tier, RiskTier.RED)
                esc.append(Escalation("missing-fact", RiskTier.RED,
                                      f"required fact {fact_key!r} is absent"))
            continue
        if not have.meets(required):
            tier = max_tier(tier, RiskTier.RED)
            esc.append(Escalation("weak-fact", RiskTier.RED,
                                  f"fact {fact_key!r} is {have.value}, "
                                  f"needs {required.value}"))

    # ── capacity: promising more than the owner confirmed ─────────────────
    if action.requested_units > 0:
        would_be = units_used_this_week + action.requested_units
        if would_be > pack.capacity_units_per_week:
            tier = max_tier(tier, RiskTier.RED)
            esc.append(Escalation("over-capacity", RiskTier.RED,
                                  f"{would_be} units exceeds confirmed "
                                  f"{pack.capacity_units_per_week}/week"))

    # ── a closed gate pulls the whole pack up ─────────────────────────────
    shut = sorted(set(closed_gates) & set(pack.gates))
    if shut:
        tier = max_tier(tier, RiskTier.RED)
        esc.append(Escalation("closed-gate", RiskTier.RED,
                              f"gate(s) closed: {', '.join(shut)}"))

    # ── pack overrides may only raise ─────────────────────────────────────
    override = pack.risk_overrides.get(action.name)
    if override is not None:
        if override.at_least(tier) and override is not tier:
            esc.append(Escalation("pack-override", override,
                                  f"pack pins {action.name!r} to {override.value}"))
            tier = max_tier(tier, override)
        # an override that would lower the tier is silently ignored — by design

    return RiskAssessment(tier=tier, base=base, escalations=tuple(esc))


def explain(assessment: RiskAssessment) -> Mapping[str, object]:
    """Ledger-shaped record of how a tier was reached."""
    return {
        "tier": assessment.tier.value,
        "base": assessment.base.value,
        "escalations": [
            {"rule": e.rule, "to": e.to.value, "detail": e.detail}
            for e in assessment.escalations
        ],
    }
