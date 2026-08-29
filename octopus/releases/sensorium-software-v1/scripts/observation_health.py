"""Live observation/bus health helpers for doctor (read-only).

Detects misleading "healthy" snapshots when Sensorium is active but:
- bus_state == ISOLATED, or
- observations_published is frozen across recent snapshots.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

SNAPSHOT_DIR = Path("/var/lib/octopus/state/snapshots")


def _load(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def recent_snapshots(limit: int = 8) -> list[tuple[Path, dict[str, Any]]]:
    if not SNAPSHOT_DIR.is_dir():
        return []
    paths = sorted(SNAPSHOT_DIR.glob("snapshot-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[tuple[Path, dict[str, Any]]] = []
    for p in paths[:limit]:
        out.append((p, _load(p)))
    return out


def assess_bus(sensorium_active: bool, snapshots: list[tuple[Path, dict[str, Any]]] | None = None) -> dict[str, Any]:
    snaps = snapshots if snapshots is not None else recent_snapshots(3)
    if not snaps:
        return {
            "ok": not sensorium_active,
            "reason": "no_snapshots",
            "bus_state": None,
            "evidence": None,
        }
    path, doc = snaps[0]
    bus = str(doc.get("bus_state") or "UNKNOWN")
    if sensorium_active and bus == "ISOLATED":
        return {
            "ok": False,
            "reason": "isolated_while_active",
            "bus_state": bus,
            "evidence": str(path),
            "observations_published": doc.get("observations_published"),
        }
    if sensorium_active and bus not in {"CONNECTED", "ISOLATED"}:
        return {
            "ok": False,
            "reason": f"unexpected_bus:{bus}",
            "bus_state": bus,
            "evidence": str(path),
        }
    return {
        "ok": True if (not sensorium_active or bus == "CONNECTED") else False,
        "reason": "ok" if bus == "CONNECTED" else f"bus={bus}",
        "bus_state": bus,
        "evidence": str(path),
        "observations_published": doc.get("observations_published"),
    }


def assess_frozen(
    sensorium_active: bool,
    snapshots: list[tuple[Path, dict[str, Any]]] | None = None,
    *,
    min_span_sec: float = 8.0,
    max_age_sec: float = 120.0,
) -> dict[str, Any]:
    snaps = snapshots if snapshots is not None else recent_snapshots(8)
    if not sensorium_active:
        return {"ok": True, "reason": "inactive_skip", "delta": None, "evidence": []}
    if len(snaps) < 2:
        return {"ok": False, "reason": "insufficient_snapshots", "delta": None, "evidence": [str(p) for p, _ in snaps]}

    # Prefer two snapshots spanning at least min_span_sec
    newest_path, newest = snaps[0]
    older_path, older = snaps[0], snaps[0]
    for path, doc in snaps[1:]:
        span = newest_path.stat().st_mtime - path.stat().st_mtime
        older_path, older = path, doc
        if span >= min_span_sec:
            break
    span = newest_path.stat().st_mtime - older_path.stat().st_mtime
    age = time.time() - newest_path.stat().st_mtime
    try:
        n0 = int(older.get("observations_published") or 0)
        n1 = int(newest.get("observations_published") or 0)
    except (TypeError, ValueError):
        return {"ok": False, "reason": "obs_count_unreadable", "delta": None, "evidence": [str(older_path), str(newest_path)]}

    delta = n1 - n0
    evidence = [str(older_path), str(newest_path)]
    if age > max_age_sec:
        return {
            "ok": False,
            "reason": "snapshot_stale_while_active",
            "delta": delta,
            "age_sec": age,
            "span_sec": span,
            "obs": [n0, n1],
            "evidence": evidence,
        }
    if span >= min_span_sec and delta <= 0:
        return {
            "ok": False,
            "reason": "frozen_obs_while_active",
            "delta": delta,
            "age_sec": age,
            "span_sec": span,
            "obs": [n0, n1],
            "evidence": evidence,
            "bus_state": newest.get("bus_state"),
        }
    return {
        "ok": True,
        "reason": "advancing" if delta > 0 else "span_too_short",
        "delta": delta,
        "age_sec": age,
        "span_sec": span,
        "obs": [n0, n1],
        "evidence": evidence,
        "bus_state": newest.get("bus_state"),
    }
