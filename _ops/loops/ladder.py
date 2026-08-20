# -*- coding: utf-8 -*-
"""Seven-rung loop ladder. CLOSED requires L6 OWNER_VISIBLE.

L0 DECLARED → L1 IMPLEMENTED → L2 WIRED → L3 OBSERVED → L4 TESTED
→ L5 VERIFIED → L6 OWNER_VISIBLE

A card without telegram_surface and miniapp_route cannot be CLOSED.
PRODUCTION_CLOSED is an L6 event, not an L5 test suite.
"""
from __future__ import annotations

from typing import Any

RUNGS = (
    "declared",      # L0
    "implemented",   # L1
    "wired",         # L2
    "observed",      # L3
    "tested",        # L4
    "verified",      # L5
    "owner_visible", # L6
)

LADDER_INDEX = {name: i for i, name in enumerate(RUNGS)}


def stuck_at(levels: dict[str, Any]) -> str:
    """First false rung. If every rung is true → L6_COMPLETE."""
    for i, name in enumerate(RUNGS):
        if not bool(levels.get(name)):
            return f"L{i}_{name.upper()}"
    return "L6_COMPLETE"


def terminal(levels: dict[str, Any], *, status: str = "") -> str:
    st = str(status or "").lower()
    if st in ("production_closed", "closed_by_owner") and levels.get("owner_visible"):
        return "CLOSED_BY_OWNER"
    if st in ("production_closed",) and not levels.get("owner_visible"):
        return "L5_CLAIM_WITHOUT_L6"
    if st in ("contained_verified", "quarantined"):
        return "ACCEPTED_DEBT" if "quarantine" in st or st == "contained_verified" else "ESCALATED"
    sa = stuck_at(levels)
    if sa in ("L6_OWNER_VISIBLE", "L6_COMPLETE"):
        return "READY_FOR_OWNER"  # still not CLOSED_AUTO — owner must declare close
    return "OPEN"


def require_surfaces(telegram_surface: str | None, miniapp_route: str | None) -> bool:
    if not telegram_surface or telegram_surface == "UNROUTED":
        return False
    if not miniapp_route or miniapp_route == "UNROUTED":
        return False
    return True
