#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""trace_replay.py -- Unified trace replay for Octopus observability.

Given a trace_id, collects all related events/spans/records from the
subsystems that exist in the vault:
  1. brain/events.py -- dashboard_events table in 4d_experiments.db
  2. otel_setup.py   -- _ops/state/otel/traces.jsonl
  3. semantic_trace  -- _ops/state/cortex/semantic-trace.jsonl
  4. cognitive/event_stream -- _ops/state/cognitive/runs/*.jsonl

This is a READ-ONLY module. It never modifies any data.
Used for:
  - Acceptance scenario: verify a single trace_id spans all handoffs
  - Debugging: visualize the full lifecycle of a decision
  - Evaluation: compute coverage metrics (which span types are present)

Output: a unified TraceReplay object with events grouped by source and
ordered chronologically.
"""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Source paths
_OPS = Path(__file__).resolve().parent.parent
_STATE = _OPS / "state"
_SEMANTIC_TRACE = _STATE / "cortex" / "semantic-trace.jsonl"
_OTEL_TRACES = _STATE / "otel" / "traces.jsonl"
_COGNITIVE_RUNS = _STATE / "cognitive" / "runs"

# Try to find the 4d experiments DB
def _find_experiments_db() -> Path | None:
    """Find the 4d_experiments.db used by brain/events.py."""
    candidates = []
    # Check common locations
    try:
        from config.settings import OUTPUT_DIR
        candidates.append(OUTPUT_DIR / "4d_experiments.db")
    except ImportError:
        pass
    candidates.extend([
        Path(os.environ.get("OCTOPUS_STATE_DIR", "")) / "4d_experiments.db",
        _OPS.parent / "4d_system" / "experiments" / "4d_experiments.db",
        Path("4d_experiments.db"),
    ])
    for c in candidates:
        if c.exists():
            return c
    return None


@dataclass
class TraceEvent:
    """A single event from any source, normalized for unified replay."""
    source: str          # "brain_events" | "otel_traces" | "semantic_trace" | "cognitive_stream"
    ts: str              # timestamp
    event_type: str      # original event type/name
    trace_id: str        # the trace_id (may be shortened/normalized)
    agent_id: str        # agent/producer that emitted
    status: str          # ok/error/info/etc
    duration_ms: int     # duration if available
    summary: str         # human-readable summary
    raw: dict            # original raw record


@dataclass
class TraceReplay:
    """Unified trace replay result."""
    trace_id: str
    events: list[TraceEvent] = field(default_factory=list)
    sources_queried: list[str] = field(default_factory=list)
    span_types_present: set[str] = field(default_factory=set)
    has_intent: bool = False
    has_policy: bool = False
    has_memory: bool = False
    has_model: bool = False
    has_tool: bool = False
    has_approval: bool = False
    has_outcome: bool = False
    total_duration_ms: int = 0

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def coverage_ratio(self) -> float:
        """Fraction of span categories present."""
        categories = [
            self.has_intent, self.has_policy, self.has_memory,
            self.has_model, self.has_tool, self.has_approval, self.has_outcome,
        ]
        return sum(categories) / len(categories) if categories else 0.0

    def to_digest(self) -> dict:
        """Produce a digest dict suitable for health digest."""
        return {
            "trace_id": self.trace_id,
            "event_count": self.event_count,
            "sources_queried": self.sources_queried,
            "span_types_present": sorted(self.span_types_present),
            "coverage_ratio": round(self.coverage_ratio, 3),
            "has_intent": self.has_intent,
            "has_policy": self.has_policy,
            "has_memory": self.has_memory,
            "has_model": self.has_model,
            "has_tool": self.has_tool,
            "has_approval": self.has_approval,
            "has_outcome": self.has_outcome,
            "total_duration_ms": self.total_duration_ms,
        }


def replay_trace(trace_id: str, *,
                 include_brain_events: bool = True,
                 include_otel_traces: bool = True,
                 include_semantic_trace: bool = True,
                 include_cognitive: bool = True,
                 ) -> TraceReplay:
    """Replay all events for a given trace_id across all subsystems.

    Args:
        trace_id: The trace ID to replay (supports partial matching for short IDs).
        include_*: Flags to include/exclude each source (useful for targeted replay).

    Returns:
        TraceReplay object with all collected events.
    """
    result = TraceReplay(trace_id=trace_id[:16])

    # Normalize the trace_id for matching
    tid_normalized = trace_id[:16].lower()

    if include_brain_events:
        _replay_brain_events(result, tid_normalized)

    if include_otel_traces:
        _replay_otel_traces(result, tid_normalized)

    if include_semantic_trace:
        _replay_semantic_trace(result, tid_normalized)

    if include_cognitive:
        _replay_cognitive(result, tid_normalized)

    # Sort by timestamp
    result.events.sort(key=lambda e: e.ts)

    # Compute total duration
    if result.events:
        ts_list = [e.ts for e in result.events if e.ts]
        if len(ts_list) >= 2:
            try:
                # Simple duration from first to last event timestamp
                from datetime import datetime
                first = datetime.fromisoformat(ts_list[0].replace("Z", "+00:00"))
                last = datetime.fromisoformat(ts_list[-1].replace("Z", "+00:00"))
                result.total_duration_ms = int(
                    (last - first).total_seconds() * 1000
                )
            except (ValueError, TypeError):
                pass

    return result


def _replay_brain_events(result: TraceReplay, tid: str) -> None:
    """Query brain/events.py dashboard_events table."""
    result.sources_queried.append("brain_events")
    db_path = _find_experiments_db()
    if db_path is None:
        return
    try:
        conn = sqlite3.connect(str(db_path), timeout=5, uri=True)
        conn.row_factory = sqlite3.Row
        # Match trace_id as prefix (supports 8-char short IDs from brain/events.py)
        rows = conn.execute(
            "SELECT * FROM dashboard_events WHERE trace_id LIKE ? ORDER BY id ASC",
            (tid + "%",),
        ).fetchall()
        conn.close()
        for r in rows:
            ev_type = r["event_name"] or ""
            summary = (r["summary"] or "")[:200]
            te = TraceEvent(
                source="brain_events",
                ts=r["timestamp"],
                event_type=ev_type,
                trace_id=r["trace_id"] or "",
                agent_id=r["agent_id"] or "",
                status=r["status"] or "info",
                duration_ms=int(r["duration_ms"] or 0),
                summary=summary,
                raw=dict(r),
            )
            result.events.append(te)
            result.span_types_present.add(ev_type)
            _classify_event(ev_type, result)
    except Exception:
        pass  # read-only, never crash


def _replay_otel_traces(result: TraceReplay, tid: str) -> None:
    """Read otel_setup.py traces.jsonl."""
    result.sources_queried.append("otel_traces")
    if not _OTEL_TRACES.exists():
        return
    try:
        lines = _OTEL_TRACES.read_text("utf-8", errors="replace").splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            rec_tid = str(rec.get("trace_id", ""))
            if not rec_tid.startswith(tid) and not tid.startswith(rec_tid[:len(tid)] if len(rec_tid) >= len(tid) else ""):
                continue
            te = TraceEvent(
                source="otel_traces",
                ts="",
                event_type=rec.get("name", ""),
                trace_id=rec_tid,
                agent_id="",
                status=rec.get("status", "unset"),
                duration_ms=int(rec.get("duration_ms", 0)),
                summary=f"otel span: {rec.get('name', '')}",
                raw=rec,
            )
            # Reconstruct timestamp from start_ms
            if rec.get("start_ms"):
                import time
                te.ts = time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ",
                    time.gmtime(rec["start_ms"] / 1000),
                )
            result.events.append(te)
            result.span_types_present.add(rec.get("name", ""))
    except OSError:
        pass


def _replay_semantic_trace(result: TraceReplay, tid: str) -> None:
    """Read semantic_trace.py semantic-trace.jsonl."""
    result.sources_queried.append("semantic_trace")
    if not _SEMANTIC_TRACE.exists():
        return
    try:
        lines = _SEMANTIC_TRACE.read_text("utf-8", errors="replace").splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            rec_tid = str(rec.get("trace_id", ""))
            if not rec_tid.startswith(tid[:8]) and not tid[:8].startswith(rec_tid):
                continue
            te = TraceEvent(
                source="semantic_trace",
                ts=rec.get("ts", ""),
                event_type="semantic_trace",
                trace_id=rec_tid,
                agent_id="cortex",
                status="ok",
                duration_ms=0,
                summary=f"cycle={rec.get('cycle')} read_ok={rec.get('semantic_memory_read_ok')}",
                raw=rec,
            )
            result.events.append(te)
            result.span_types_present.add("semantic_trace")
            result.has_memory = True
    except OSError:
        pass


def _replay_cognitive(result: TraceReplay, tid: str) -> None:
    """Read cognitive/event_stream.py JSONL files."""
    result.sources_queried.append("cognitive_stream")
    if not _COGNITIVE_RUNS.exists():
        return
    try:
        for run_file in _COGNITIVE_RUNS.glob("*.jsonl"):
            lines = run_file.read_text("utf-8", errors="replace").splitlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                rec_tid = str(rec.get("trace_id", ""))
                if not rec_tid or not (rec_tid.startswith(tid[:12]) or tid[:12].startswith(rec_tid.replace("trace_", ""))):
                    continue
                te = TraceEvent(
                    source="cognitive_stream",
                    ts=rec.get("occurred_at", ""),
                    event_type=rec.get("event_type", ""),
                    trace_id=rec_tid,
                    agent_id=rec.get("producer", ""),
                    status=rec.get("status", "info"),
                    duration_ms=0,
                    summary=f"{rec.get('event_type', '')} seq={rec.get('sequence', '?')}",
                    raw=rec,
                )
                result.events.append(te)
                result.span_types_present.add(rec.get("event_type", ""))
                _classify_event(rec.get("event_type", ""), result)
    except OSError:
        pass


def _classify_event(event_type: str, result: TraceReplay) -> None:
    """Classify an event into span categories for coverage analysis."""
    et = event_type.lower()
    if "intent" in et or "user_message" in et:
        result.has_intent = True
    if "policy" in et or "approval" in et:
        result.has_policy = True
    if "memory" in et or "retriev" in et:
        result.has_memory = True
    if "model" in et or "token" in et:
        result.has_model = True
    if "tool" in et:
        result.has_tool = True
    if "approval" in et:
        result.has_approval = True
    if "outcome" in et or "completed" in et or "failed" in et:
        result.has_outcome = True
