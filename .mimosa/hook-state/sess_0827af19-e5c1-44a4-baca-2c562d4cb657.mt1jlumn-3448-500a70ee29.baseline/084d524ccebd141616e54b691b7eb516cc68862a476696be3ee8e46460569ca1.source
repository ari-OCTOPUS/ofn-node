#!/usr/bin/env python3
"""Content-free focused inventory derived from the real dark-capability scanner."""
from __future__ import annotations

from typing import Any, Iterable, Mapping

FOCUS_FLAGS = (
    "CORTEX_LOCAL_FIRST",
    "CORTEX_ROUTE_SCORER",
    "OCTOPUS_COLLAB_USE_MODEL",
    "OCTOPUS_WIRE_COLLAB",
    "OCTOPUS_WIRE_CONTEXT_FENCE",
    "OCTOPUS_WIRE_KILL_SEAM",
    "OCTOPUS_WIRE_OUTBOUND_HTTPS",
    "OCTOPUS_WIRE_ROUTE_SHADOW",
)


def focused_rows(result: Mapping[str, Any],
                 flags: Iterable[str] = FOCUS_FLAGS) -> list[dict[str, Any]]:
    """Return bounded structural evidence; never include any environment value."""
    by_flag = {str(row.get("flag")): dict(row)
               for row in result.get("rows", ()) if isinstance(row, Mapping)}
    live_source = str(result.get("live_source") or "absent")
    processes = list(result.get("processes") or ())
    rows: list[dict[str, Any]] = []
    for flag in flags:
        source = by_flag.get(str(flag))
        if source is None:
            rows.append({
                "flag": str(flag), "classification": "UNKNOWN",
                "tracked_or_profile_on": False, "live_source": live_source,
                "live_confidence": "NONE", "reader_count": 0, "readers": [],
                "reason": "not-found-by-static-scanner",
            })
            continue
        scanner_state = str(source.get("state") or "UNKNOWN")
        classification = scanner_state if scanner_state in {"DARK", "TUNING"} else "UNKNOWN"
        confidence = ("HIGH" if live_source == "live" and processes else
                      "STRUCTURAL_ONLY" if live_source in {"absent", "unreadable"} else "NONE")
        rows.append({
            "flag": str(flag),
            "classification": classification,
            "tracked_or_profile_on": bool(source.get("armed_in_file") or source.get("profile_on")),
            "live_source": live_source,
            "live_confidence": confidence,
            "reader_count": int(source.get("n_readers") or 0),
            "readers": list(source.get("readers") or ()),
            "reason": ("structurally-read-not-armed" if classification == "DARK" else
                       "defaulted-runtime-setting" if classification == "TUNING" else
                       "requires-live-snapshot-or-nonfocus-state"),
        })
    return rows


def inventory(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": "octopus.test-intelligence.dark-inventory.v1",
        "summary": {
            "n_flags": int(result.get("n_flags") or 0),
            "n_dark": int(result.get("n_dark") or 0),
            "n_partial": int(result.get("n_partial") or 0),
            "n_tuning": int(result.get("n_tuning") or 0),
            "live_source": str(result.get("live_source") or "absent"),
            "process_count": len(result.get("processes") or ()),
        },
        "focus": focused_rows(result),
        "interpretation": (
            "DARK is structural when live_source is absent; it is not evidence that a live "
            "process is currently off. No flag value is collected or emitted."
        ),
    }
