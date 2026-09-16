#!/usr/bin/env python3
"""Pure policy for bounded owner guidance versus a frozen preregistration."""
from __future__ import annotations

_FORBIDDEN_KEYS = {"goal", "goal_key", "metric", "metric_path", "metric_key",
                   "baseline", "target", "prereg_id", "owner_gate", "risk"}
_ALLOWED = {"focus", "think_every_n", "paused"}


def apply(prereg: dict, guidance: dict | None) -> dict:
    """Guidance can steer cognition now, but goal changes are deferred to the next cycle.

    Any forbidden field is ignored and surfaced. The prereg row is returned byte-semantically
    unchanged as `frozen`; this function never mutates inputs.
    """
    frozen = dict(prereg or {})
    g = dict(guidance or {})
    effective = {k: g[k] for k in _ALLOWED if k in g}
    attempted = sorted(k for k in g if k in _FORBIDDEN_KEYS)
    deferred = {k: g[k] for k in attempted}
    return {"frozen": frozen, "effective_now": effective,
            "deferred_next_cycle": deferred,
            "blocked_overrides": attempted,
            "goal_unchanged": all(frozen.get(k) == (prereg or {}).get(k)
                                  for k in ("goal_key", "baseline", "target", "metric_key"))}
