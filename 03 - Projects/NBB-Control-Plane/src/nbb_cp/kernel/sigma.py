"""Branching ratio sigma — literal population control for agent spawning (INV-6).

sigma := executed spawns per active agent over a window.
sigma < 1: population shrinks. sigma > 1: uncontrolled replication (the cancer
axis) — forbidden. Target is sigma ~= 1.

The spawn gate judges the *prospective* sigma — the value sigma would take if
this spawn executed — otherwise the population always overshoots the limit by
one before the freeze engages.
"""

from __future__ import annotations

from typing import Iterable

from .events import EventKind, LedgerEvent

SIGMA_LIMIT = 1.0


def branching_ratio(executed_spawns: int, active_agents: int) -> float:
    if executed_spawns < 0 or active_agents < 0:
        raise ValueError("counts must be non-negative")
    if active_agents == 0:
        return 0.0
    return executed_spawns / active_agents


def executed_spawns_in_window(
    events: Iterable[LedgerEvent], window_epochs: int, current_epoch: int
) -> int:
    floor_epoch = max(0, current_epoch - window_epochs + 1)
    return sum(
        1
        for e in events
        if e.kind is EventKind.SPAWN
        and e.payload.get("executed") is True
        and floor_epoch <= int(e.payload.get("epoch", -1)) <= current_epoch
    )


def sigma_from_events(
    events: Iterable[LedgerEvent], active_agents: int, window_epochs: int, current_epoch: int
) -> float:
    """Current sigma: executed SPAWN events in the trailing window, normalized."""
    return branching_ratio(
        executed_spawns_in_window(events, window_epochs, current_epoch), active_agents
    )


def prospective_sigma_from_events(
    events: Iterable[LedgerEvent], active_agents: int, window_epochs: int, current_epoch: int
) -> float:
    """Sigma as it would stand *after* one more spawn — what the gate must judge."""
    return branching_ratio(
        executed_spawns_in_window(events, window_epochs, current_epoch) + 1, active_agents
    )


def sigma_allows_spawn(sigma: float, limit: float = SIGMA_LIMIT) -> bool:
    """A spawn is admissible only while (prospective) sigma stays at or under the limit."""
    return sigma <= limit
