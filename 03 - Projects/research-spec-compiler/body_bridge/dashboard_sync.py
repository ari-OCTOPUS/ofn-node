#!/usr/bin/env python3
"""
dashboard_sync.py — Sync upstream kernel feeds into a single dashboard JSON.

Reads manifest.json, adr_feed.json, verdict_stream.jsonl, GEOMETRY.md, and
CLAIMS_LEDGER.csv to produce kernel_dashboard.json for body consumption.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

KERNEL_ROOT = Path(__file__).resolve().parent.parent
BODY_OUTPUT = KERNEL_ROOT / "body_bridge" / "output"
DASHBOARD_PATH = BODY_OUTPUT / "kernel_dashboard.json"
LEDGER_PATH = KERNEL_ROOT / "CLAIMS_LEDGER.csv"

# Regex for geometry status lines like [RUN] ontology_shift
_RE_GEOMETRY_STATUS = re.compile(r"^\[(RUN|MAP|SPEC)\]\s*(.+)$", re.MULTILINE)


def _read_json(path: Path) -> dict[str, Any]:
    """Safely read a JSON file, returning empty dict on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to read JSON %s: %s", path, e)
        return {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Safely read a JSONL file, returning empty list on failure."""
    events: list[dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except (FileNotFoundError, OSError) as e:
        logger.warning("Failed to read JSONL %s: %s", path, e)
    return events


def _read_text(path: Path) -> str:
    """Safely read a text file, returning empty string on failure."""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as e:
        logger.warning("Failed to read text %s: %s", path, e)
        return ""


def _count_ledger_rows(path: Path) -> int:
    """Count data rows in CLAIMS_LEDGER.csv (excluding header)."""
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            lines = f.readlines()
        if not lines:
            return 0
        # First line is header; count remaining non-empty lines
        return sum(1 for line in lines[1:] if line.strip())
    except (FileNotFoundError, OSError) as e:
        logger.warning("Failed to read ledger %s: %s", path, e)
        return 0


def _parse_geometry_status(text: str) -> dict[str, str]:
    """Parse GEOMETRY.md for [RUN]/[MAP]/[SPEC] lines."""
    status: dict[str, str] = {}
    for match in _RE_GEOMETRY_STATUS.finditer(text):
        tag = match.group(1)
        name = match.group(2).strip()
        if name:
            status[name] = tag
    return status


def _compute_tally(adrs: list[dict[str, Any]]) -> dict[str, int]:
    """Count verdicts from ADR list."""
    tally: dict[str, int] = {
        "INTEGRATE": 0,
        "OPTIMIZE": 0,
        "REJECTED": 0,
        "FAIL": 0,
        "UNKNOWN": 0,
        "ACCEPTED": 0,
    }
    for adr in adrs:
        v = adr.get("verdict", "UNKNOWN")
        if v in tally:
            tally[v] += 1
        else:
            tally["UNKNOWN"] += 1
    return tally


def _extract_high_priority_adrs(adrs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return ADRs that are REJECTED, borderline, or have C4 caveats."""
    high: list[dict[str, Any]] = []
    for adr in adrs:
        verdict = adr.get("verdict", "")
        caveats = adr.get("caveats", "")
        if not isinstance(caveats, str):
            caveats = str(caveats) if caveats is not None else ""
        is_high = False
        reason = ""
        if verdict == "REJECTED":
            is_high = True
            reason = "machine_rejected"
        elif "borderline" in verdict.lower():
            is_high = True
            reason = "borderline"
        elif "C4" in caveats.upper():
            is_high = True
            reason = "c4_caveat"
        if is_high:
            high.append({
                "adr_number": adr.get("adr_number"),
                "title": adr.get("title", ""),
                "verdict": verdict,
                "reason": reason,
            })
    return high


def _count_organism_events() -> int:
    """Count events in organism_events.json if it exists."""
    events_path = KERNEL_ROOT / "experiments" / "data" / "organism_events.json"
    try:
        data = _read_json(events_path)
        # Try n_events field first, then len(events list)
        if "n_events" in data:
            return int(data["n_events"])
        events = data.get("events", [])
        return len(events)
    except Exception:
        return 0


def _build_persian_report(adr_count: int, experiment_count: int, tally: dict[str, int]) -> str:
    """Build a short Persian summary string."""
    total = tally.get("INTEGRATE", 0) + tally.get("OPTIMIZE", 0) + tally.get("REJECTED", 0) + tally.get("FAIL", 0)
    return (
        f"کرنل {adr_count} ADR و {experiment_count} آزمایش دارد. "
        f"تصمیم‌ها: INTEGRATE={tally.get('INTEGRATE', 0)}، OPTIMIZE={tally.get('OPTIMIZE', 0)}، "
        f"REJECTED={tally.get('REJECTED', 0)}."
    )


def sync() -> dict[str, Any]:
    """
    Read upstream feeds and write kernel_dashboard.json.
    Returns the dashboard dict.
    """
    manifest = _read_json(BODY_OUTPUT / "manifest.json")
    adr_feed = _read_json(BODY_OUTPUT / "adr_feed.json")

    adrs = adr_feed.get("adrs", [])
    tally = _compute_tally(adrs)
    experiment_count = len(manifest.get("experiments", []))
    adr_count = adr_feed.get("total", len(adrs))
    ledger_rows = _count_ledger_rows(LEDGER_PATH)

    # last_experiment from last ADR entry
    last_adr = adrs[-1] if adrs else {}
    last_experiment = {}
    if last_adr:
        last_experiment = {
            "name": last_adr.get("title", ""),
            "date": last_adr.get("date", ""),
            "verdict": last_adr.get("verdict", ""),
        }

    high_priority_adr = _extract_high_priority_adrs(adrs)

    geometry_text = _read_text(KERNEL_ROOT / "GEOMETRY.md")
    geometry_status = _parse_geometry_status(geometry_text)

    snapshot_events = _count_organism_events()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    fresh_events_available = snapshot_events > 0

    persian_report = _build_persian_report(adr_count, experiment_count, tally)

    dashboard: dict[str, Any] = {
        "tally": tally,
        "experiment_count": experiment_count,
        "adr_count": adr_count,
        "ledger_rows": ledger_rows,
        "last_experiment": last_experiment,
        "high_priority_adr": high_priority_adr,
        "geometry_status": geometry_status,
        "identity_anchor": 0.135073,
        "body_bridge_status": {
            "snapshot_events": snapshot_events,
            "last_sync": now,
            "fresh_events_available": fresh_events_available,
        },
        "sensitivity_summary": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
        "persian_report": persian_report,
        "last_updated": now,
    }

    try:
        BODY_OUTPUT.mkdir(parents=True, exist_ok=True)
        with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False, sort_keys=True)
        logger.info("Dashboard synced to %s", DASHBOARD_PATH)
    except OSError as e:
        logger.error("Failed to write dashboard: %s", e)

    return dashboard


def get_metric(key: str) -> Any:
    """
    Read the dashboard JSON and return a value by dot-path key.
    E.g. 'adr_count', 'tally.INTEGRATE', 'identity_anchor'.
    Returns None if key not found or file missing.
    """
    try:
        with open(DASHBOARD_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None

    parts = key.split(".")
    for part in parts:
        if isinstance(data, dict) and part in data:
            data = data[part]
        else:
            return None
    return data


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    dash = sync()
    print(f"Dashboard synced: {dash['adr_count']} ADRs, {dash['experiment_count']} experiments")


if __name__ == "__main__":
    main()
