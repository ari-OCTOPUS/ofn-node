#!/usr/bin/env python3
"""M4 — unified_bus_guard: additive, flag-OFF proxy over UnifiedBus so a genome-
ledger append via bus.publish(..., is_human=True) is authorized by
human_append_guard.default_guard().authorize() BEFORE it reaches lg.append —
closing the forgery seam.

CONTEXT (audit + workflow grounding)
  chrono.on_human_judgment already guards the human-append path. unified_bus.publish
  is the SECOND path into the same genome ledger and forwards is_human straight to
  lg.append with no authorize() (unified_bus.py:79-80). NOTE: the ONLY is_human=True
  publish in the whole tree today is a TEST (test_phase5) — no production code forges
  a human append via the bus — so this is DEFENSE-IN-DEPTH for future code, not a
  live hole. Built flag-off so it never changes today's behavior.

BEHAVIOR (only when the wiring.py:166 factory is flag-armed)
  wrap(bus) returns a proxy that delegates EVERYTHING to the real bus except
  publish(): on is_human=True it calls default_guard().authorize(event_type, True,
  token=token); if the guard denies (e.g. no valid token), it DOWNGRADES the append
  to is_human=False — a forged/unauthorized human append becomes an ordinary machine
  append and never advances the mortal age_tick. Non-human publishes pass straight
  through. fail-soft: a missing/erroring guard never breaks the bus (passthrough).

FLAG (default OFF — checked at the wiring.py:166 factory, not here)
  OCTOPUS_WIRE_BUS_GUARD=1 → make_unified_bus returns wrap(bus) instead of the raw
  bus. Default OFF → raw bus → byte-identical to today.

ROLLBACK: delete this module + restore wiring.py:166 to `return _bus`
  (grep OCTOPUS_WIRE_BUS_GUARD). Or just leave the flag unset.

$0 · stdlib-only · fail-soft.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/now_moves
_OPS = _HERE.parent                              # _ops

FLAG = "OCTOPUS_WIRE_BUS_GUARD"


def _default_guard():
    """The shared HumanAppendGuard (same instance configured at boot). fail-soft."""
    try:
        p = str(_OPS / "budget")
        if p not in sys.path:
            sys.path.insert(0, p)
        import human_append_guard
        return human_append_guard.default_guard()
    except Exception:
        return None


class _GuardedBus:
    """Transparent proxy over a UnifiedBus. Delegates every attribute to the real
    bus; only publish() is intercepted to authorize an is_human=True append."""

    def __init__(self, bus):
        self._bus = bus

    def __getattr__(self, name):
        return getattr(self._bus, name)          # delegate everything not defined here

    def publish(self, event_type, payload, actor="system", is_human=False,
                beat=False, token=None):
        if is_human:
            g = _default_guard()
            allow = True
            if g is not None:
                try:
                    allow, _reason = g.authorize(event_type, True, token=token)
                except Exception:
                    allow = True                 # fail-soft: never break the bus
            if not allow:
                is_human = False                 # downgrade forged/unauthorized human → machine
        return self._bus.publish(event_type, payload, actor=actor,
                                 is_human=is_human, beat=beat)


def wrap(bus):
    """Return a guard proxy over `bus` (or `bus` unchanged if None)."""
    return _GuardedBus(bus) if bus is not None else bus
