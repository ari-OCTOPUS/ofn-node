#!/usr/bin/env python3
"""
verdict_stream.py — Cognitive Kernel 0.1 verdict stream emitter.

Reads CLAIMS_LEDGER.csv, detects new rows via content hashing, and emits a
structured JSONL stream for body consumption. Persian user-facing text is included
in notification helpers.

Code comments in English. User-facing / notification text in Persian (Farsi).
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_MODULE_DIR = Path(__file__).resolve().parent
_KERNEL_ROOT = _MODULE_DIR.parent
CLAIMS_LEDGER = _KERNEL_ROOT / "CLAIMS_LEDGER.csv"
OUTPUT_DIR = _MODULE_DIR / "output"
STREAM_FILE = OUTPUT_DIR / "verdict_stream.jsonl"
CURSOR_FILE = OUTPUT_DIR / ".verdict_cursor"

# Verdicts that require owner attention (HIGH sensitivity)
_HIGH_SENSITIVITY_VERDICTS = {"REJECTED", "FAIL", "FAIL-by-design"}


def _row_hash(row: dict[str, str]) -> str:
    """Deterministic SHA256 hash of a CSV row dict (sorted keys)."""
    payload = json.dumps(row, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_ledger() -> list[dict[str, str]]:
    """Read CLAIMS_LEDGER.csv deterministically with DictReader."""
    if not CLAIMS_LEDGER.exists():
        logger.warning("CLAIMS_LEDGER not found: %s", CLAIMS_LEDGER)
        return []
    rows: list[dict[str, str]] = []
    try:
        with open(CLAIMS_LEDGER, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row is None:
                    continue
                rows.append(dict(row))
    except Exception as e:
        logger.error("Failed to read ledger: %s", e)
    return rows


def _load_cursor() -> set[str]:
    """Load the set of previously processed row hashes from the cursor file."""
    if not CURSOR_FILE.exists():
        return set()
    try:
        with open(CURSOR_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except Exception as e:
        logger.warning("Cursor load failed: %s", e)
        return set()


def _save_cursor(hashes: set[str]) -> None:
    """Persist the cursor set to disk."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(CURSOR_FILE, "w", encoding="utf-8") as f:
            for h in sorted(hashes):
                f.write(h + "\n")
    except Exception as e:
        logger.error("Cursor save failed: %s", e)


def _build_event(row: dict[str, str]) -> dict[str, Any]:
    """Convert a ledger row into a structured verdict event."""
    verdict = (row.get("verdict", "") or "").strip().upper()
    confidence_raw = (row.get("primary_value", "") or "").strip()
    try:
        confidence = float(confidence_raw) if confidence_raw else None
    except ValueError:
        confidence = None

    # evidence_tags: split on comma or semicolon
    evidence_tags = [t.strip() for t in (row.get("evidence_tag", "") or "").split(",") if t.strip()]

    # geometry_objects: derived from spec name (heuristic mapping)
    spec = (row.get("spec", "") or "").strip()
    geometry_objects = []
    if "geometry" in spec.lower():
        geometry_objects.append("geometry_abstraction")
    if "ontology" in spec.lower():
        geometry_objects.append("ontology_shift")
    if "multimetric" in spec.lower():
        geometry_objects.append("multimetric_memory")
    if "attractor" in spec.lower():
        geometry_objects.append("attractor_memory")

    # caveat_summary: from caveats column (truncated if very long)
    caveats = (row.get("caveats", "") or "").strip()
    caveat_summary = caveats[:500] if caveats else ""

    owner_action_required = verdict in _HIGH_SENSITIVITY_VERDICTS or "C4" in caveats.upper()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "claim_id": row.get("claim_id", ""),
        "experiment": row.get("experiment", ""),
        "verdict": verdict,
        "confidence": confidence,
        "evidence_tags": evidence_tags,
        "geometry_objects": geometry_objects,
        "caveat_summary": caveat_summary,
        "owner_action_required": owner_action_required,
    }


class VerdictStream:
    """Stateful verdict stream reader. Tracks processed rows via a cursor file."""

    def __init__(self, ledger_path: Path | None = None, cursor_path: Path | None = None, stream_path: Path | None = None) -> None:
        self.ledger_path = ledger_path or CLAIMS_LEDGER
        self.cursor_path = cursor_path or CURSOR_FILE
        self.stream_path = stream_path or STREAM_FILE

    def refresh(self) -> list[dict[str, Any]]:
        """
        Read the ledger, detect new rows, emit events to the JSONL stream,
        and update the cursor file. Returns the list of newly emitted events.
        """
        rows = _read_ledger()
        seen = _load_cursor()
        new_events: list[dict[str, Any]] = []
        new_hashes: set[str] = set()

        for row in rows:
            h = _row_hash(row)
            if h in seen:
                continue
            event = _build_event(row)
            new_events.append(event)
            new_hashes.add(h)

        if new_events:
            try:
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                with open(self.stream_path, "a", encoding="utf-8") as f:
                    for ev in new_events:
                        f.write(json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n")
                logger.info("Appended %d new verdict events to %s", len(new_events), self.stream_path)
            except Exception as e:
                logger.error("Failed to write verdict stream: %s", e)
                raise

        # Update cursor with all hashes from this ledger run (deterministic)
        all_hashes = {_row_hash(r) for r in rows}
        _save_cursor(all_hashes)
        return new_events

    def since_last(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return the most recent N events from the JSONL stream file."""
        if not self.stream_path.exists():
            return []
        try:
            with open(self.stream_path, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f if ln.strip()]
            events = []
            for ln in lines[-limit:]:
                try:
                    events.append(json.loads(ln))
                except Exception:
                    continue
            return events
        except Exception as e:
            logger.warning("Failed to read stream: %s", e)
            return []

    def high_priority_items(self) -> list[dict[str, Any]]:
        """Return events where owner_action_required is True."""
        all_events = self.since_last(limit=10000)
        return [ev for ev in all_events if ev.get("owner_action_required")]


def refresh() -> list[dict[str, Any]]:
    """Convenience standalone function to refresh the stream."""
    return VerdictStream().refresh()


def notify_digest() -> str:
    """
    Return a short Persian text summary of new verdicts for Telegram/notification.
    خلاصهٔ فارسی از verdictهای جدید برای ارسال به تلگرام/نوتیفیکیشن.
    """
    stream = VerdictStream()
    recent = stream.since_last(limit=20)
    if not recent:
        return "📭 هیچ verdict جدیدی در استریم نیست."

    high = stream.high_priority_items()
    lines = [f"📬 {len(recent)} verdict جدید در استریم:"]
    for ev in recent[-10:]:
        v = ev.get("verdict", "?")
        cid = ev.get("claim_id", "?")
        emoji = "🚨" if ev.get("owner_action_required") else "📝"
        lines.append(f"{emoji} {cid}: {v}")
    if high:
        lines.append(f"⚠️ {len(high)} مورد نیاز به اقدام مالک دارند.")
    return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    new = refresh()
    print(f"New verdicts: {len(new)}")
    print(notify_digest())
