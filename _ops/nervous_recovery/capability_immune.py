# -*- coding: utf-8 -*-
"""Capability Immune System — declared ≠ alive."""
from __future__ import annotations

from typing import Any

TRUTH = ("VERIFIED", "DEGRADED", "DORMANT", "BLOCKED", "UNKNOWN")


def card(name: str, spec: dict[str, Any], *,
         observed_recently: bool | None = None,
         receipt_backed: bool | None = None,
         tested: str | None = None) -> dict[str, Any]:
    actuator = spec.get("actuator")
    callable_ = actuator not in (None, "", False)
    st = str(spec.get("status") or "")

    if receipt_backed is True and observed_recently is True and callable_:
        truth = "VERIFIED"
    elif st == "dead-output":
        truth = "BLOCKED"
    elif receipt_backed is True and callable_ and observed_recently is False:
        truth = "DEGRADED"
    elif receipt_backed is not True:
        # Code or docs exist; no live receipt → not VERIFIED.
        truth = "DORMANT"
        if observed_recently is None and receipt_backed is None and not st:
            truth = "UNKNOWN"
    else:
        truth = "UNKNOWN"

    return {
        "capability": name,
        "declared": True,
        "callable": callable_,
        "observed_recently": observed_recently if observed_recently is not None else "UNKNOWN",
        "tested": tested if tested is not None else "UNKNOWN",
        "receipt_backed": bool(receipt_backed),
        "dependency_state": spec.get("gate") or "none",
        "registry_status": st or "UNKNOWN",
        "truth_status": truth,
        "propose_only": spec.get("propose_only"),
    }


def inventory(effectors: dict[str, dict], **flags) -> dict[str, Any]:
    cards = [card(k, v, **flags) for k, v in effectors.items()]
    counts: dict[str, int] = {t: 0 for t in TRUTH}
    for c in cards:
        counts[str(c["truth_status"])] = counts.get(str(c["truth_status"]), 0) + 1
    return {
        "schema": "capability-immune/1",
        "total": len(cards),
        "parse_ok": True,
        "counts": counts,
        "cards": cards,
    }
