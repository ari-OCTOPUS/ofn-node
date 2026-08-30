#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""trust_metrics.py — in-process counters for Health/Trust (OTLP-ready).

Alloy outage must not block Talk Discovery. Counters are local; OTLP optional.
Never attach DM/prompt text as attributes.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

_COUNTERS: dict[str, int] = defaultdict(int)

# Canonical names (ADR-033)
HEALTH = (
    "octopus.runtime.blocked_total",
    "octopus.state.store_unavailable_total",
    "octopus.policy.denied_total",
    "octopus.kill_switch.engaged",
)
TRUST = (
    "octopus.context.quarantined_total",
    "octopus.context.provenance_missing_total",
    "octopus.approval.expired_total",
    "octopus.approval.hash_mismatch_total",
)


def note_event(
    *,
    event_type: str,
    decision: str | None,
    reason_code: str | None,
) -> None:
    if decision == "deny" or (event_type or "").endswith("denied"):
        _COUNTERS["octopus.policy.denied_total"] += 1
    if decision == "quarantine" or "quarantine" in (event_type or ""):
        _COUNTERS["octopus.context.quarantined_total"] += 1
    if reason_code == "provenance_missing":
        _COUNTERS["octopus.context.provenance_missing_total"] += 1
    if reason_code == "proposal_expired":
        _COUNTERS["octopus.approval.expired_total"] += 1
    if reason_code in ("proposal_changed_after_approval", "hash_mismatch"):
        _COUNTERS["octopus.approval.hash_mismatch_total"] += 1
    if reason_code == "kill_switch_engaged":
        _COUNTERS["octopus.kill_switch.engaged"] += 1
    if reason_code in ("store_failure_blocked", "store_unavailable"):
        _COUNTERS["octopus.state.store_unavailable_total"] += 1
    if decision == "deny" and reason_code:
        _COUNTERS["octopus.runtime.blocked_total"] += 1


def snapshot() -> dict[str, int]:
    out = {k: int(_COUNTERS.get(k, 0)) for k in HEALTH + TRUST}
    return out


def reset_for_tests() -> None:
    _COUNTERS.clear()


def export_otlp_if_enabled() -> None:
    """Best-effort gauge export; never raises into caller."""
    try:
        import os
        if os.environ.get("OCTOPUS_WIRE_CRITICALITY_OTLP", "0") != "1":
            return
        # Reuse criticality meter path if present — skip if SDK missing.
        from telemetry import criticality_metrics as cm
        if not getattr(cm, "_gauges", None):
            cm.configure_criticality_meter()
    except Exception:  # noqa: BLE001
        pass


def as_dict() -> dict[str, Any]:
    return {"schema": "adr033.trust_metrics.v1", "counters": snapshot()}
