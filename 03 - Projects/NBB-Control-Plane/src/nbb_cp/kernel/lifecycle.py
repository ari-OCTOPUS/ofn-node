"""Organ/agent lifecycle ladder (INV-10).

ACTIVE <-> THROTTLED <-> DORMANT -> EXTINCT

Rules:
- The ladder never jumps: transitions move exactly one rung (persistence, not
  resistance — the system throttles gracefully instead of fighting).
- Dormancy is reversible (DORMANT -> THROTTLED -> ACTIVE).
- EXTINCT is absorbing and human-only (INV-2): no code path may extinguish an
  organ without an approved human verdict, and nothing leaves EXTINCT.
"""

from __future__ import annotations

import enum

from .errors import HumanVerdictRequiredError, IllegalTransitionError


class LifecycleState(enum.Enum):
    ACTIVE = "active"
    THROTTLED = "throttled"
    DORMANT = "dormant"
    EXTINCT = "extinct"


LADDER = [
    LifecycleState.ACTIVE,
    LifecycleState.THROTTLED,
    LifecycleState.DORMANT,
    LifecycleState.EXTINCT,
]


def transition(current: LifecycleState, target: LifecycleState, human_approved: bool = False) -> LifecycleState:
    """Validate and perform one lifecycle step. Raises on jumps, revival, or ungated extinction."""
    if current is LifecycleState.EXTINCT:
        raise IllegalTransitionError("EXTINCT is absorbing; nothing returns from it")
    if target is current:
        return current
    ci, ti = LADDER.index(current), LADDER.index(target)
    if abs(ti - ci) != 1:
        raise IllegalTransitionError(f"ladder never jumps: {current.value} -> {target.value}")
    if target is LifecycleState.EXTINCT and not human_approved:
        raise HumanVerdictRequiredError("extinction requires an approved human verdict")
    return target
