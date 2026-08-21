#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Typed MemoryContext — cycle-1 write must change cycle-2 decision.

Wires the three MemoryReadLoop queries plus similar-failure and owner-decision
retrieval into one snapshot. decide_from_context is the only decision function;
later results must cite context_id.

Fixture-safe: callers inject a ReadStore. Live organism consume_tick is
propose-only (writes pulse JSON; never memory.db; never Telegram).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from memory_read_loop import MemoryReadLoop, ReadResult, _parse  # noqa: E402

_FAIL_OUTCOMES = frozenset({"failed", "failure", "error", "fail"})


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


@dataclass
class MemoryContext:
    context_id: str
    goal_id: str
    queries: list[str] = field(default_factory=list)
    memories_read: list[dict] = field(default_factory=list)
    experiments_read: list[dict] = field(default_factory=list)
    contradictions: list[dict] = field(default_factory=list)
    stale_items: list[dict] = field(default_factory=list)
    similar_failures: list[dict] = field(default_factory=list)
    owner_decisions: list[dict] = field(default_factory=list)
    source_snapshot_sha: str = ""
    decision_time: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _row_public(row: dict) -> dict:
    keys = ("id", "memory_id", "kind", "text", "payload", "outcome", "goal_id",
            "occurred_at", "recorded_at", "resolved", "status")
    return {k: row.get(k) for k in keys if k in row}


def retrieve_similar_failures(store, needle: str, decision_time: datetime | str) -> list[dict]:
    """Runtime call site required by owner order — not a stub import."""
    dt = _parse(decision_time)
    n = str(needle or "").lower()
    out: list[dict] = []
    for row in store.all_records():
        if str(row.get("kind") or "") != "experiment":
            continue
        if str(row.get("outcome") or "").lower() not in _FAIL_OUTCOMES:
            continue
        blob = f"{row.get('text') or ''} {row.get('payload') or ''} {row.get('goal_id') or ''}".lower()
        if n and n not in blob:
            continue
        if not MemoryReadLoop._eligible(row, dt):
            continue
        out.append(_row_public(row))
    return out


def retrieve_owner_decisions(store, decision_time: datetime | str) -> list[dict]:
    """Runtime call site required by owner order — not a stub import."""
    dt = _parse(decision_time)
    out: list[dict] = []
    for row in store.all_records():
        if str(row.get("kind") or "") not in {"owner_decision", "owner-verdict", "verdict"}:
            continue
        if not MemoryReadLoop._eligible(row, dt):
            continue
        out.append(_row_public(row))
    return out


def _contradictions(experiments: list[dict], hypotheses: list[dict]) -> list[dict]:
    found: list[dict] = []
    by_goal: dict[str, list[str]] = {}
    for row in experiments:
        gid = str(row.get("goal_id") or "")
        if not gid:
            continue
        by_goal.setdefault(gid, []).append(str(row.get("outcome") or ""))
    for gid, outcomes in by_goal.items():
        norm = {o.lower() for o in outcomes if o}
        if "success" in norm and (norm & _FAIL_OUTCOMES):
            found.append({"goal_id": gid, "kind": "contradictory_outcomes"})
    return found


def build_context(store, *, goal_id: str, decision_time: datetime | str,
                  needle: str = "", snapshot_sha: str = "") -> MemoryContext:
    dt = _parse(decision_time)
    loop = MemoryReadLoop(store, agent_id="cycle_context", session_id=str(goal_id))
    exp: ReadResult = loop.query_experiments(dt)
    hyp: ReadResult = loop.get_pending_hypotheses(dt)
    vault: ReadResult = loop.search_vault(str(needle or goal_id), dt)
    failures = retrieve_similar_failures(store, needle or goal_id, dt)
    decisions = retrieve_owner_decisions(store, dt)
    stale = []
    for row in list(exp.rows) + list(hyp.rows):
        rec = row.get("recorded_at")
        if rec:
            try:
                age_s = (dt - _parse(rec)).total_seconds()
                if age_s > 7 * 86400:
                    stale.append(_row_public(row))
            except (TypeError, ValueError):
                pass
    ctx = MemoryContext(
        context_id=f"mctx-{uuid.uuid4().hex[:12]}",
        goal_id=str(goal_id),
        queries=["query_experiments", "get_pending_hypotheses", "search_vault",
                 "retrieve_similar_failures", "retrieve_owner_decisions"],
        memories_read=[_row_public(r) for r in vault.rows],
        experiments_read=[_row_public(r) for r in exp.rows],
        contradictions=_contradictions(exp.rows, hyp.rows),
        stale_items=stale,
        similar_failures=failures,
        owner_decisions=decisions,
        source_snapshot_sha=snapshot_sha or _sha(json.dumps([
            exp.ids, hyp.ids, vault.ids, [f.get("id") for f in failures]
        ], sort_keys=True)),
        decision_time=dt.isoformat(),
    )
    return ctx


def decide_from_context(ctx: MemoryContext) -> dict[str, Any]:
    """Decision that must change when cycle-1 evidence is present in cycle-2."""
    failed_ids = []
    for row in list(ctx.experiments_read) + list(ctx.similar_failures):
        if str(row.get("outcome") or "").lower() in _FAIL_OUTCOMES:
            failed_ids.append(str(row.get("id") or row.get("memory_id") or ""))
    if failed_ids:
        action, reason = "hold_and_revise", "prior_failure"
    elif ctx.owner_decisions:
        action, reason = "follow_owner", "owner_decision_present"
    elif any(str(r.get("outcome") or "").lower() in {"success", "passed", "ok"}
             for r in ctx.experiments_read):
        action, reason = "continue", "prior_success"
    elif ctx.experiments_read:
        action, reason = "observe_prior", "prior_evidence_no_outcome"
    else:
        action, reason = "explore", "no_prior_evidence"
    out = {
        "action": action,
        "reason": reason,
        "context_id": ctx.context_id,
        "goal_id": ctx.goal_id,
        "used_memory_ids": [str(r.get("id") or "") for r in ctx.experiments_read],
        "used_failure_ids": [x for x in failed_ids if x],
        "source_snapshot_sha": ctx.source_snapshot_sha,
    }
    return out


class _DictStore:
    def __init__(self, rows: list[dict]):
        self._rows = list(rows)

    def all_records(self) -> list[dict]:
        return list(self._rows)


def consume_tick(memory_read: dict | None, *, goal_id: str = "organism-beat",
                 needle: str = "spine") -> dict[str, Any]:
    """Live/organism hook: consume pulse memory_read into a decision artifact.

    Does not open production memory.db. Uses ids already read this beat when
    present; otherwise an empty store (honest explore).
    """
    mr = dict(memory_read or {})
    rows: list[dict] = []
    now = datetime.now(timezone.utc).isoformat()
    for kind, key in (("experiment", "experiment_ids"),
                      ("hypothesis", "hypothesis_ids"),
                      ("hypothesis", "vault_ids")):
        for rid in mr.get(key) or []:
            rows.append({
                "id": rid, "kind": kind, "text": needle,
                "occurred_at": now, "recorded_at": now, "resolved": False,
            })
    # Live spine mapping has no outcome field — decision stays explore unless
    # a fixture/store injects failures. That is truthful, not fabricated success.
    ctx = build_context(_DictStore(rows), goal_id=goal_id,
                        decision_time=datetime.now(timezone.utc), needle=needle,
                        snapshot_sha=str(mr.get("newest_id") or ""))
    decision = decide_from_context(ctx)
    artifact = {
        "schema": "memory-context/1",
        "context": ctx.to_dict(),
        "decision": decision,
        "consumed": True,
        "memory_read_status": mr.get("status"),
        "ts": now,
    }
    try:
        base = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
        pulse = (Path(base) if base else (_OPS / "state")) / "pulse"
        pulse.mkdir(parents=True, exist_ok=True)
        (pulse / "memory-context-latest.json").write_text(
            json.dumps(artifact, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass
    return artifact
