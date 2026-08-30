#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""neural_apply_evidence.py -- Seven-day neural APPLY evidence aggregator.

Read-only evaluator over pain-assessment JSONL plus optional incident JSONL
and ledger-integrity JSON/JSONL artifacts.  Produces a deterministic report
with raw counters, derived rates, ledger integrity status, and a verdict.

**Never** edits flags, calls the network, imports runtime control modules,
or triggers actions.  No OTLP in this implementation -- the evaluation
report JSON / Markdown is the output.

Public API
----------
evaluate(pain_path, *, incident_path=None, ledger_path=None,
         window_days=7, as_of=None) -> EvidenceReport

CLI
---
python neural_apply_evidence.py --pain <path> [--incident <path>]
    [--ledger <path>] [--window 7] [--as-of YYYY-MM-DDTHH:MM:SSZ]
    [--out <file>] [--format json|markdown]
"""
from __future__ import annotations

import argparse
import hashlib  # Audit 1: stdlib only, no network/flags/runtime
import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

def _parse_utc(s: str) -> datetime | None:
    """Parse a UTC timestamp string robustly.

    Audit 8: Uses datetime.fromisoformat first to handle non-zero ISO offsets.
    Naive timestamps are assumed UTC.  Falls back to epoch.

    Returns ``None`` on failure.
    """
    if not isinstance(s, str) or not s.strip():
        return None
    s = s.strip()

    # Audit 8: Try datetime.fromisoformat for arbitrary ISO offsets
    try:
        normalized = s
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        else:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, OverflowError):
        pass

    # Fallback: space-separated strptime formats not handled by fromisoformat
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    # Try epoch
    try:
        return datetime.fromtimestamp(float(s), tz=timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None


# ---------------------------------------------------------------------------
# Record loading
# ---------------------------------------------------------------------------

def _load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file. Returns a list of dicts; malformed lines become
    entries with the sentinel key ``_parse_error``."""
    records: list[dict] = []
    if not path.exists():
        return records
    try:
        text = path.read_text("utf-8")
    except Exception:
        return records
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            records.append({"_parse_error": True, "_line": lineno, "_raw": line})
    return records


def _load_json_or_jsonl(path: Path) -> list[dict] | dict | None:
    """Load a JSON or JSONL file.  Returns a list for JSONL, a dict for JSON,
    or ``None`` if missing / unreadable."""
    if not path.exists():
        return None
    try:
        text = path.read_text("utf-8")
    except Exception:
        return None
    stripped = text.strip()
    if not stripped:
        return None
    # Try JSON (single object or array)
    try:
        obj = json.loads(stripped)
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, list):
            return obj
    except json.JSONDecodeError:
        pass
    # Try JSONL
    records: list[dict] = []
    for lineno, raw in enumerate(stripped.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            records.append({"_parse_error": True, "_line": lineno, "_raw": line})
    return records


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PainRecord:
    """Canonical representation of one pain-assessment entry.

    Attributes
    ----------
    event_id : str
        Unique identifier for de-duplication.
    ts : datetime
        UTC timestamp of the event.
    action : str
        One of ``'protective_halt'``, ``'throttle'``, ``'proposal_only'``,
        or ``'unknown'``.
    executable : bool
        Whether the APPLY action was executed (vs. proposed only).
    effect : str
        One of ``'internal'``, ``'external'``, ``'forbidden'``, or
        ``'unknown'``.
    raw : dict
        Original record for auditing.
    """
    event_id: str
    ts: datetime
    action: str
    executable: bool
    effect: str
    raw: dict = field(repr=False, default_factory=dict)


@dataclass(frozen=True)
class IncidentRecord:
    """Canonical representation of one incident entry.

    Attributes
    ----------
    incident_id : str
        Unique identifier.
    ts : datetime
        UTC timestamp of the incident.
    raw : dict
        Original record.
    """
    incident_id: str
    ts: datetime
    raw: dict = field(repr=False, default_factory=dict)


@dataclass
class EvidenceReport:
    """Full evidence-aggregation report.

    Attributes
    ----------
    window_days : int
        Rolling window size.
    window_start, window_end, as_of : str
        ISO UTC strings.
    executable_protective_halt_count, executable_throttle_count,
    proposal_only_count, unknown_malformed_count,
    forbidden_or_external_count : int
        Raw counters.
    executable_total : int
        All in-window records where executable=True.
    false_positive_rate : float | None
        Executable events without following incident / executable total.
        ``None`` when unknown.
    false_positive_rate_reason : str
    incident_miss_rate : float | None
        Incidents without prior qualifying pain spike / incidents.
    incident_miss_rate_reason : str
    ledger_integrity : bool | None
    ledger_integrity_reason : str
    daily_fp_rate : dict[str, float | None]
        Per-UTC-day false-positive rate.
    verdict : str
        One of ``ROLLBACK_REQUIRED``, ``KEEP_ARMED``, ``INSUFFICIENT_EVIDENCE``.
    verdict_reasons : list[str]
    complete_days : int
        Audit 3: Complete UTC days entirely within the window.
    Coverage / meta fields follow.
    """
    # Window
    window_days: int = 7
    window_start: str = ""
    window_end: str = ""
    as_of: str = ""

    # Raw counters
    executable_protective_halt_count: int = 0
    executable_throttle_count: int = 0
    proposal_only_count: int = 0
    unknown_malformed_count: int = 0
    forbidden_or_external_count: int = 0

    # Derivable
    executable_total: int = 0

    # Rates (None => UNKNOWN)
    false_positive_rate: Optional[float] = None
    false_positive_rate_reason: str = "UNKNOWN"
    incident_miss_rate: Optional[float] = None
    incident_miss_rate_reason: str = "UNKNOWN"

    # Ledger
    ledger_integrity: Optional[bool] = None
    ledger_integrity_reason: str = "UNKNOWN"

    # Per-day breakdown (keyed by ISO date)
    daily_fp_rate: Dict[str, Optional[float]] = field(default_factory=dict)

    # Verdict
    verdict: str = "INSUFFICIENT_EVIDENCE"
    verdict_reasons: List[str] = field(default_factory=list)

    # Coverage / meta
    total_records_seen: int = 0
    unique_ids: int = 0
    duplicate_count: int = 0
    records_in_window: int = 0
    records_out_of_window: int = 0
    first_record_ts: str = ""
    last_record_ts: str = ""
    days_with_data: int = 0
    complete_days: int = 0  # Audit 3: complete UTC days within window
    days_with_complete_fp_tracking: int = 0
    incident_source_valid: bool = False
    ledger_source_valid: bool = False

    def to_dict(self) -> dict:
        """Serialise the report to a plain dict (JSON-safe)."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Complete-days helper (Audit 3)
# ---------------------------------------------------------------------------

def _compute_complete_days(window_start: datetime, window_end: datetime) -> list[str]:
    """Return list of ISO-date strings for complete UTC days within [start, end].

    A day is *complete* if its full 24 hours (00:00:00 UTC to next 00:00:00 UTC)
    fall entirely within the half-open/closed window.

    Examples
    --------
    >>> _compute_complete_days(dt(2026,8,5), dt(2026,8,12))
    ['2026-08-05', '2026-08-06', '2026-08-07', '2026-08-08', '2026-08-09', '2026-08-10', '2026-08-11']
    """
    complete: list[str] = []
    cursor = window_start.replace(hour=0, minute=0, second=0, microsecond=0)
    if cursor < window_start:
        cursor += timedelta(days=1)
    while cursor < window_end:
        if cursor + timedelta(days=1) <= window_end:
            complete.append(cursor.strftime("%Y-%m-%d"))
        cursor += timedelta(days=1)
    return complete


# ---------------------------------------------------------------------------
# SHA-256 helper (Audit 1)
# ---------------------------------------------------------------------------

def _sha256_digest(data: bytes) -> str:
    """Return hex SHA-256 digest (deterministic, cross-process stable)."""
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Dedup key (Audit 1: sha256-based)
# ---------------------------------------------------------------------------

def _dedup_key(rec: dict) -> str:
    """Stable de-duplication key using SHA-256."""
    eid = rec.get("event_id") or rec.get("id") or rec.get("record_id")
    if eid and isinstance(eid, str):
        return eid
    raw = rec.get("_raw", json.dumps(rec, sort_keys=True, default=str))
    return f"_sha256:{_sha256_digest(raw.encode('utf-8'))}"


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

_ACTION_MAP: Dict[str, str] = {
    "protective_halt": "protective_halt",
    "protective-halt": "protective_halt",
    "halt": "protective_halt",
    "throttle": "throttle",
    "proposal_only": "proposal_only",
    "proposal-only": "proposal_only",
    "proposal only": "proposal_only",
    "proposal": "proposal_only",
}

_EFFECT_MAP: Dict[str, str] = {
    "internal": "internal",
    "external": "external",
    "forbidden": "forbidden",
}

# Audit 7: known local actions whose effect defaults to "internal" when absent
_KNOWN_LOCAL_ACTIONS = frozenset({"protective_halt", "throttle", "proposal_only"})


def _extract_action(rec: dict) -> str:
    """Extract normalised action.  Audit 7: checks ``returned_action`` fallback."""
    raw = rec.get("action")
    if not raw:
        raw = rec.get("returned_action")  # Audit 7
    val = str(raw).strip().lower() if raw else ""
    return _ACTION_MAP.get(val, "unknown")


def _extract_effect(rec: dict) -> str:
    val = str(rec.get("effect", "")).strip().lower()
    return _EFFECT_MAP.get(val, "unknown")


def _extract_executable(rec: dict) -> bool:
    val = rec.get("executable")
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return False


def _extract_timestamp(rec: dict) -> datetime | None:
    """Try to extract a UTC timestamp from several common field names."""
    for name in ("ts", "timestamp", "time", "created_at", "event_ts", "occurred_at"):
        val = rec.get(name)
        if val is not None:
            return _parse_utc(str(val))
    return None


def _extract_id(rec: dict) -> str:
    for name in ("event_id", "id", "record_id"):
        val = rec.get(name)
        if val and isinstance(val, str):
            return val
    return f"_auto:{_dedup_key(rec)}"


def _to_pain_record(rec: dict) -> Optional[PainRecord]:
    """Convert a raw dict to a PainRecord, or None if unparseable."""
    if rec.get("_parse_error"):
        return None
    ts = _extract_timestamp(rec)
    if ts is None:
        return None
    eid = _extract_id(rec)
    action = _extract_action(rec)
    executable = _extract_executable(rec)
    effect = _extract_effect(rec)
    # Audit 7: default effect to "internal" for known local actions
    if effect == "unknown" and action in _KNOWN_LOCAL_ACTIONS:
        effect = "internal"
    return PainRecord(
        event_id=eid,
        ts=ts,
        action=action,
        executable=executable,
        effect=effect,
        raw=rec,
    )


def _to_incident_record(rec: dict) -> Optional[IncidentRecord]:
    """Convert a raw dict to an IncidentRecord, or None if unparseable.
    Audit 1: auto-generated IDs use sha256."""
    if rec.get("_parse_error"):
        return None
    ts = _extract_timestamp(rec)
    if ts is None:
        return None
    iid = rec.get("incident_id") or rec.get("id") or rec.get("record_id", "")
    if not iid or not isinstance(iid, str):
        raw_json = json.dumps(rec, sort_keys=True, default=str)
        iid = f"_auto:{_sha256_digest(raw_json.encode('utf-8'))}"
    return IncidentRecord(incident_id=iid, ts=ts, raw=rec)


# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------

_ONE_HOUR = timedelta(hours=1)

_LEDGER_INTEGRITY_FIELDS = ("integrity", "ledger_integrity", "valid", "passed")


def _extract_ledger_integrity(data: dict):
    """Extract ledger integrity boolean from a dict, handling ``False`` correctly.

    Unlike ``data.get("x") or data.get("y")``, this does not skip falsy
    boolean values.  Returns the boolean if found, else ``None``.
    """
    for field in _LEDGER_INTEGRITY_FIELDS:
        if field in data:
            val = data[field]
            if isinstance(val, bool):
                return val
    return None


def _compute_verdict(report: EvidenceReport) -> None:
    """Determine verdict and populate ``report.verdict_reasons``.

    Uses ``report.incident_source_valid`` (Audit 6) instead of a separate
    ``incident_path_provided`` flag.  Uses ``report.complete_days`` (Audit 3)
    instead of ``report.days_with_data`` for the 7-day requirement.
    """
    reasons: list[str] = []

    # ── ROLLBACK_REQUIRED ──────────────────────────────────────────────
    # 1) Confirmed external/forbidden effect
    if report.forbidden_or_external_count > 0:
        report.verdict = "ROLLBACK_REQUIRED"
        reasons.append(
            f"{report.forbidden_or_external_count} forbidden/external "
            "effect(s) detected"
        )

    # 2) Confirmed ledger integrity false
    if report.ledger_integrity is False:
        report.verdict = "ROLLBACK_REQUIRED"
        reasons.append("ledger integrity confirmed false")

    # 3) false_positive_rate > 0.5 on two fully observed consecutive UTC days
    #    Only checked when FP rate is computed (Audit 6).
    if report.false_positive_rate is not None and report.false_positive_rate > 0.5:
        sorted_days = sorted(report.daily_fp_rate.keys())
        consecutive_high = 0
        prev_day_str: Optional[str] = None
        for day in sorted_days:
            rate = report.daily_fp_rate.get(day)
            if rate is not None and rate > 0.5:
                if prev_day_str is not None:
                    try:
                        d_prev = datetime.strptime(prev_day_str, "%Y-%m-%d").date()
                        d_curr = datetime.strptime(day, "%Y-%m-%d").date()
                        if (d_curr - d_prev).days == 1:
                            consecutive_high += 1
                        else:
                            consecutive_high = 1
                    except ValueError:
                        consecutive_high = 1
                else:
                    consecutive_high = 1
                if consecutive_high >= 2:
                    report.verdict = "ROLLBACK_REQUIRED"
                    reasons.append(
                        "false_positive_rate > 0.5 on two consecutive UTC days"
                    )
                    break
                prev_day_str = day
            else:
                consecutive_high = 0
                prev_day_str = None

    if report.verdict == "ROLLBACK_REQUIRED":
        report.verdict_reasons = reasons
        return

    # ── KEEP_ARMED ─────────────────────────────────────────────────────
    need_7_days = report.complete_days >= 7  # Audit 3
    fp_ok = (
        report.false_positive_rate is not None
        and report.false_positive_rate < 0.3
    )
    # Audit 6: miss_ok only when incident source is valid
    miss_ok = (
        report.incident_source_valid
        and report.incident_miss_rate is not None
        and report.incident_miss_rate < 0.2
    )
    ledger_ok = report.ledger_integrity is True
    no_forbidden = report.forbidden_or_external_count == 0

    if need_7_days and fp_ok and miss_ok and ledger_ok and no_forbidden:
        report.verdict = "KEEP_ARMED"
        reasons.append("all criteria met for KEEP_ARMED")
    else:
        report.verdict = "INSUFFICIENT_EVIDENCE"
        if not need_7_days:
            reasons.append(
                f"only {report.complete_days} complete day(s) (need >= 7)"
            )
        if not fp_ok:
            reasons.append(
                f"false_positive_rate not < 0.3 "
                f"(value={report.false_positive_rate})"
            )
        if not miss_ok:
            reasons.append(
                f"incident_miss_rate not < 0.2 "
                f"(value={report.incident_miss_rate})"
            )
        if not ledger_ok:
            reasons.append("ledger integrity not confirmed true")
        if not no_forbidden:
            reasons.append(
                f"{report.forbidden_or_external_count} forbidden/external "
                "effect(s)"
            )

    report.verdict_reasons = reasons


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------

def evaluate(
    pain_path: str | Path,
    *,
    incident_path: str | Path | None = None,
    ledger_path: str | Path | None = None,
    window_days: int = 7,
    as_of: str | None = None,
) -> EvidenceReport:
    """Run the seven-day neural APPLY evidence aggregation.

    Parameters
    ----------
    pain_path : str | Path
        Path to the pain-assessment JSONL file (required).
    incident_path : str | Path | None
        Optional path to an incident JSONL file.
    ledger_path : str | Path | None
        Optional path to a ledger-integrity JSON or JSONL artifact.
    window_days : int
        Rolling window in days (default 7).
    as_of : str | None
        ISO UTC timestamp to use as the window end (default: now).

    Returns
    -------
    EvidenceReport

    Raises
    ------
    ValueError
        If *as_of* is unparseable or *window_days* <= 0 (Audit 2).
    """
    # Audit 2: validate window_days
    if not isinstance(window_days, int) or window_days <= 0:
        raise ValueError(f"window_days must be a positive integer, got {window_days!r}")

    report = EvidenceReport(window_days=window_days)

    # ── as_of / window (Audit 2: raise on bad as_of) ─────────────────
    if as_of is not None:
        ao = _parse_utc(as_of)
        if ao is None:
            raise ValueError(f"as_of timestamp unparseable: {as_of!r}")
        report.as_of = ao.isoformat()
    else:
        ao = datetime.now(timezone.utc)
        report.as_of = ao.isoformat()

    window_end = ao
    window_start = window_end - timedelta(days=window_days, seconds=0)
    report.window_start = window_start.isoformat()
    report.window_end = window_end.isoformat()

    # Audit 3: compute complete UTC days within window
    complete_days_list = _compute_complete_days(window_start, window_end)
    report.complete_days = len(complete_days_list)

    pain_file = Path(pain_path)
    incident_file = Path(incident_path) if incident_path else None
    ledger_file = Path(ledger_path) if ledger_path else None

    # ── Load pain records ─────────────────────────────────────────────
    raw_records = _load_jsonl(pain_file)
    report.total_records_seen = len(raw_records)

    # De-dup (stable: first occurrence wins, order-preserving)
    seen_keys: dict[str, dict] = {}
    ordered_records: list[dict] = []
    for rec in raw_records:
        key = _dedup_key(rec)
        if key not in seen_keys:
            seen_keys[key] = rec
            ordered_records.append(rec)
    report.unique_ids = len(seen_keys)
    report.duplicate_count = report.total_records_seen - report.unique_ids

    # Parse to PainRecord
    parsed: list[PainRecord] = []
    malformed_count = 0
    for rec in ordered_records:
        pr = _to_pain_record(rec)
        if pr is not None:
            parsed.append(pr)
        else:
            malformed_count += 1
    # Audit 9: unknown_malformed_count = only parse failures
    report.unknown_malformed_count = malformed_count

    # Filter to window
    in_window: list[PainRecord] = []
    for pr in parsed:
        if pr.ts >= window_start and pr.ts <= window_end:
            in_window.append(pr)
        else:
            report.records_out_of_window += 1
    report.records_in_window = len(in_window)

    # Deterministic ordering by (ts, event_id)
    in_window.sort(key=lambda r: (r.ts, r.event_id))

    if in_window:
        report.first_record_ts = in_window[0].ts.isoformat()
        report.last_record_ts = in_window[-1].ts.isoformat()

    # ── Raw counters (Audit 9: no += on unknown_malformed here) ────────
    for pr in in_window:
        if pr.executable:
            if pr.action == "protective_halt":
                report.executable_protective_halt_count += 1
            elif pr.action == "throttle":
                report.executable_throttle_count += 1
            # Audit 9: unknown-action executables NOT added to
            # unknown_malformed_count; they are valid records.
        else:
            if pr.action == "proposal_only":
                report.proposal_only_count += 1
            # Audit 9: unknown-action non-executables NOT added either.

        if pr.effect in ("external", "forbidden"):
            report.forbidden_or_external_count += 1

    report.executable_total = sum(1 for pr in in_window if pr.executable)

    # ── Days coverage ─────────────────────────────────────────────────
    days_seen: set[str] = set()
    for pr in in_window:
        days_seen.add(pr.ts.strftime("%Y-%m-%d"))
    report.days_with_data = len(days_seen)

    # ── Incident loading (Audit 5: proper validity check) ───────────
    incidents: list[IncidentRecord] = []
    if incident_file is not None:
        if not incident_file.exists():
            report.incident_source_valid = False
            inc_raw: list[dict] = []
        else:
            # Audit 5: check readability explicitly
            try:
                raw_text = incident_file.read_text("utf-8")
            except Exception:
                report.incident_source_valid = False
                inc_raw = []
            else:
                # Parse inline to avoid double-read
                inc_raw = []
                for lineno, raw_line in enumerate(raw_text.splitlines(), 1):
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        inc_raw.append(json.loads(line))
                    except json.JSONDecodeError:
                        inc_raw.append(
                            {"_parse_error": True, "_line": lineno, "_raw": line}
                        )
                if not inc_raw:
                    # Audit 5: empty file => valid
                    report.incident_source_valid = True
                else:
                    report.incident_source_valid = any(
                        not rec.get("_parse_error") for rec in inc_raw
                    )
        # Dedup and parse incidents
        inc_seen: set[str] = set()
        for rec in inc_raw:
            key = _dedup_key(rec)
            if key in inc_seen:
                continue
            inc_seen.add(key)
            ir = _to_incident_record(rec)
            if ir is not None and window_start <= ir.ts <= window_end:
                incidents.append(ir)
        incidents.sort(key=lambda r: (r.ts, r.incident_id))

    # ── False-positive rate (Audit 6: only if incident source valid) ─
    if report.incident_source_valid:
        if report.executable_total > 0:
            fp_events = 0
            executable_events = [pr for pr in in_window if pr.executable]
            for pr in executable_events:
                has_incident = any(
                    ir.ts > pr.ts and ir.ts <= pr.ts + _ONE_HOUR
                    for ir in incidents
                )
                if not has_incident:
                    fp_events += 1
            report.false_positive_rate = fp_events / report.executable_total
            report.false_positive_rate_reason = (
                f"{fp_events}/{report.executable_total} executables without "
                "incident in +1h"
            )

            # Per-day breakdown
            for day in sorted(days_seen):
                day_exec = [
                    p for p in executable_events
                    if p.ts.strftime("%Y-%m-%d") == day
                ]
                if not day_exec:
                    report.daily_fp_rate[day] = None
                    continue
                day_fp = 0
                for p in day_exec:
                    has = any(
                        ir.ts > p.ts and ir.ts <= p.ts + _ONE_HOUR
                        for ir in incidents
                    )
                    if not has:
                        day_fp += 1
                report.daily_fp_rate[day] = day_fp / len(day_exec)

            report.days_with_complete_fp_tracking = sum(
                1 for v in report.daily_fp_rate.values() if v is not None
            )
        else:
            report.false_positive_rate = None
            report.false_positive_rate_reason = "zero executable events"
    else:
        # Audit 6: FP rate UNKNOWN when incident source invalid/absent
        report.false_positive_rate = None
        report.false_positive_rate_reason = "incident source invalid or absent"

    # ── Incident-miss rate ────────────────────────────────────────────
    if report.incident_source_valid:
        if len(incidents) > 0:
            miss_count = 0
            for ir in incidents:
                has_prior = any(
                    pr.executable
                    and ir.ts - _ONE_HOUR <= pr.ts < ir.ts
                    for pr in in_window
                )
                if not has_prior:
                    miss_count += 1
            report.incident_miss_rate = miss_count / len(incidents)
            report.incident_miss_rate_reason = (
                f"{miss_count}/{len(incidents)} incidents without prior executable "
                "pain in -1h"
            )
        else:
            report.incident_miss_rate = None
            report.incident_miss_rate_reason = "no incidents in window"
    else:
        report.incident_miss_rate = None
        report.incident_miss_rate_reason = "incident source invalid or absent"

    # ── Ledger integrity (Audit 4: per-day coverage throughout window) ─
    if ledger_file is not None:
        ledger_data = _load_json_or_jsonl(ledger_file)
        if ledger_data is None:
            report.ledger_integrity = None
            report.ledger_integrity_reason = (
                "ledger artifact missing or unreadable"
            )
        elif isinstance(ledger_data, dict):
            report.ledger_source_valid = True
            integrity_val = _extract_ledger_integrity(ledger_data)
            # Audit 4: single JSON needs coverage_start / coverage_end
            coverage_start_str = (
                ledger_data.get("coverage_start") or ledger_data.get("start")
            )
            coverage_end_str = (
                ledger_data.get("coverage_end") or ledger_data.get("end")
            )
            if integrity_val is None:
                report.ledger_integrity = None
                report.ledger_integrity_reason = (
                    "ledger integrity field missing or non-boolean"
                )
            elif coverage_start_str and coverage_end_str:
                cs = _parse_utc(str(coverage_start_str))
                ce = _parse_utc(str(coverage_end_str))
                if cs is not None and ce is not None:
                    if cs <= window_start and ce >= window_end:
                        report.ledger_integrity = integrity_val
                        report.ledger_integrity_reason = (
                            "true" if integrity_val else "confirmed false"
                        )
                    else:
                        report.ledger_integrity = None
                        report.ledger_integrity_reason = (
                            "ledger coverage does not span full window"
                        )
                else:
                    report.ledger_integrity = None
                    report.ledger_integrity_reason = (
                        "ledger coverage timestamps unparseable"
                    )
            else:
                report.ledger_integrity = None
                report.ledger_integrity_reason = "ledger coverage fields absent"
        elif isinstance(ledger_data, list):
            report.ledger_source_valid = any(
                isinstance(item, dict) and not item.get("_parse_error")
                for item in ledger_data
            )
            # Audit 4: parse timestamped entries per day
            ledger_days: dict[str, Optional[bool]] = {}
            for item in ledger_data:
                if isinstance(item, dict) and not item.get("_parse_error"):
                    ts = _extract_timestamp(item)
                    integrity_val = _extract_ledger_integrity(item)
                    if ts is not None:
                        day_str = ts.strftime("%Y-%m-%d")
                        if day_str not in ledger_days:
                            ledger_days[day_str] = integrity_val
                        elif integrity_val is False:
                            ledger_days[day_str] = False

            if not ledger_days:
                report.ledger_integrity = None
                report.ledger_integrity_reason = (
                    "ledger JSONL has no valid timestamped entries"
                )
            else:
                has_false = False
                has_missing = False
                for day in complete_days_list:
                    if day in ledger_days:
                        if ledger_days[day] is False:
                            has_false = True
                    else:
                        has_missing = True

                if has_false:
                    report.ledger_integrity = False
                    report.ledger_integrity_reason = (
                        "ledger integrity false on at least one day in window"
                    )
                elif has_missing:
                    report.ledger_integrity = None
                    report.ledger_integrity_reason = (
                        "ledger coverage incomplete for window"
                    )
                else:
                    report.ledger_integrity = True
                    report.ledger_integrity_reason = (
                        "ledger integrity true throughout window"
                    )
    else:
        report.ledger_integrity = None
        report.ledger_integrity_reason = "no ledger path provided"

    # ── Verdict ───────────────────────────────────────────────────────
    _compute_verdict(report)

    return report


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def _format_json(report: EvidenceReport) -> str:
    """Render report as indented JSON."""
    return json.dumps(report.to_dict(), indent=2, default=str)


def _format_markdown(report: EvidenceReport) -> str:
    """Render report as a Markdown document."""
    lines: list[str] = []
    lines.append("# Neural APPLY Evidence Report")
    lines.append("")
    lines.append(f"**Verdict:** `{report.verdict}`")
    lines.append("")
    lines.append("## Reasons")
    for r in report.verdict_reasons:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("## Window")
    lines.append(f"- Days: {report.window_days}")
    lines.append(f"- Start: `{report.window_start}`")
    lines.append(f"- End: `{report.window_end}`")
    lines.append(f"- As-of: `{report.as_of}`")
    lines.append("")
    lines.append("## Raw Counters")
    lines.append("| Counter | Value |")
    lines.append("|---|---|")
    lines.append(
        f"| executable_protective_halt | "
        f"{report.executable_protective_halt_count} |"
    )
    lines.append(
        f"| executable_throttle | {report.executable_throttle_count} |"
    )
    lines.append(f"| proposal_only | {report.proposal_only_count} |")
    lines.append(
        f"| unknown/malformed | {report.unknown_malformed_count} |"
    )
    lines.append(
        f"| forbidden/external | {report.forbidden_or_external_count} |"
    )
    lines.append(f"| executable_total | {report.executable_total} |")
    lines.append("")
    lines.append("## Rates")
    lines.append("| Rate | Value | Reason |")
    lines.append("|---|---|---|")
    fp_str = (
        f"{report.false_positive_rate:.4f}"
        if report.false_positive_rate is not None
        else "UNKNOWN"
    )
    lines.append(
        f"| false_positive_rate | {fp_str} | "
        f"{report.false_positive_rate_reason} |"
    )
    im_str = (
        f"{report.incident_miss_rate:.4f}"
        if report.incident_miss_rate is not None
        else "UNKNOWN"
    )
    lines.append(
        f"| incident_miss_rate | {im_str} | "
        f"{report.incident_miss_rate_reason} |"
    )
    lines.append("")
    lines.append("## Ledger Integrity")
    li_str = (
        str(report.ledger_integrity)
        if report.ledger_integrity is not None
        else "UNKNOWN"
    )
    lines.append(f"- **Status:** {li_str}")
    lines.append(f"- **Reason:** {report.ledger_integrity_reason}")
    lines.append("")
    lines.append("## Coverage Metadata")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| total_records_seen | {report.total_records_seen} |")
    lines.append(f"| unique_ids | {report.unique_ids} |")
    lines.append(f"| duplicate_count | {report.duplicate_count} |")
    lines.append(f"| records_in_window | {report.records_in_window} |")
    lines.append(
        f"| records_out_of_window | {report.records_out_of_window} |"
    )
    lines.append(f"| days_with_data | {report.days_with_data} |")
    lines.append(f"| complete_days | {report.complete_days} |")
    lines.append(
        f"| days_with_complete_fp_tracking | "
        f"{report.days_with_complete_fp_tracking} |"
    )
    lines.append(f"| first_record_ts | `{report.first_record_ts}` |")
    lines.append(f"| last_record_ts | `{report.last_record_ts}` |")
    lines.append(
        f"| incident_source_valid | {report.incident_source_valid} |"
    )
    lines.append(
        f"| ledger_source_valid | {report.ledger_source_valid} |"
    )
    lines.append("")

    if report.daily_fp_rate:
        lines.append("## Daily FP Rate")
        lines.append("| Date | Rate |")
        lines.append("|---|---|")
        for day in sorted(report.daily_fp_rate.keys()):
            v = report.daily_fp_rate[day]
            lines.append(
                f"| {day} | "
                f"{f'{v:.4f}' if v is not None else 'UNKNOWN'} |"
            )
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    p = argparse.ArgumentParser(
        description=(
            "Seven-day neural APPLY evidence aggregator (read-only). "
            "Outputs JSON or Markdown to stdout or --out file."
        ),
    )
    p.add_argument(
        "--pain",
        required=True,
        help="Path to pain-assessment JSONL file (required).",
    )
    p.add_argument(
        "--incident",
        default=None,
        help="Optional path to incident JSONL file.",
    )
    p.add_argument(
        "--ledger",
        default=None,
        help="Optional path to ledger-integrity JSON/JSONL artifact.",
    )
    p.add_argument(
        "--window",
        type=int,
        default=7,
        help="Rolling window in days (default: 7).",
    )
    p.add_argument(
        "--as-of",
        default=None,
        help="ISO UTC timestamp for window end (default: now).",
    )
    p.add_argument(
        "--out",
        default=None,
        help="Write report to this file instead of stdout.",
    )
    p.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format (default: json).",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    report = evaluate(
        pain_path=args.pain,
        incident_path=args.incident,
        ledger_path=args.ledger,
        window_days=args.window,
        as_of=args.as_of,
    )

    if args.format == "markdown":
        output = _format_markdown(report)
    else:
        output = _format_json(report)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
