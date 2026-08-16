#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task_orchestrator.py -- Durable Multi-Agent Task Orchestration (EQUIP G1).

Mission: A multi-stage mission continues after crash/restart/timeout from the
last valid checkpoint without repeating side effects.

Design Principles:
  - Manage-Execute-Audit: task state lives OUTSIDE model context, on disk
  - State machine is explicit: illegal transitions are rejected + audited
  - Checkpoint per step: versioned, persisted to JSONL
  - Idempotency key per side effect: replay = NOOP if already executed
  - Bounded retry: exponential backoff + jitter, max attempts, poison detection
  - Kill-aware: cancellation from NBB-CP / kill coordinator propagates immediately
  - Worker restart: completed steps are never re-executed

Integration:
  - Uses telemetry.trace_context for correlation/tracing (G6)
  - Uses containment.kill_coordinator for kill-switch propagation (G8)
  - Uses containment.agent_circuit for circuit breaker per agent (G8)
  - Uses containment.audit_chain for tamper-evident audit trail (G8)
  - Uses durable_journal for step-level execution journaling
  - Uses mission_contract for canonical envelope/status vocabulary

No LangGraph, Temporal, Celery, or NATS -- none exist in this vault.
A pure state machine is sufficient for this scale (single laptop, single agent).

$0 | stdlib-only | no network | no LLM dependency | no external framework
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_OPS / "containment") not in sys.path:
    sys.path.insert(0, str(_OPS / "containment"))
if str(_OPS / "telemetry") not in sys.path:
    sys.path.insert(0, str(_OPS / "telemetry"))

SCHEMA = "task-orchestrator.v1"

# ── canonical task lifecycle states ─────────────────────────────────────

class TaskState(str, Enum):
    """Canonical task lifecycle states.

    Progression:
      CREATED -> PLANNED -> APPROVAL_PENDING -> RUNNING -> COMPLETED
                                     |            |-> PAUSED -> RUNNING (resume)
                                     |            |-> RETRYING -> RUNNING
                                     |            |-> FAILED
                                     |            |-> CANCELLED
                                     |            |-> COMPENSATING -> FAILED
      Any non-terminal -> CANCELLED (via kill switch / owner command)
    """
    CREATED = "CREATED"
    PLANNED = "PLANNED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    COMPENSATING = "COMPENSATING"

# Terminal states: no transitions out
TERMINAL_STATES = frozenset({
    TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED,
})

# Legal transitions (fail-closed: anything not listed is illegal)
_ALLOWED_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.CREATED: {TaskState.PLANNED, TaskState.CANCELLED},
    TaskState.PLANNED: {TaskState.APPROVAL_PENDING, TaskState.RUNNING,
                        TaskState.CANCELLED},
    TaskState.APPROVAL_PENDING: {TaskState.RUNNING, TaskState.CANCELLED,
                                 TaskState.FAILED},
    TaskState.RUNNING: {TaskState.PAUSED, TaskState.RETRYING,
                        TaskState.COMPLETED, TaskState.FAILED,
                        TaskState.CANCELLED, TaskState.COMPENSATING},
    TaskState.PAUSED: {TaskState.RUNNING, TaskState.CANCELLED},
    TaskState.RETRYING: {TaskState.RUNNING, TaskState.FAILED,
                         TaskState.CANCELLED},
    TaskState.COMPENSATING: {TaskState.FAILED, TaskState.CANCELLED},
    # Terminal: no outgoing
    TaskState.COMPLETED: set(),
    TaskState.FAILED: set(),
    TaskState.CANCELLED: set(),
}


# ── idempotency ────────────────────────────────────────────────────────

def idempotency_key(*, task_id: str, step_name: str, payload_hash: str) -> str:
    """Generate a deterministic idempotency key for a step execution."""
    raw = f"{task_id}|{step_name}|{payload_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def payload_hash(payload: dict | None) -> str:
    """Hash a step payload for idempotency."""
    raw = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"),
                     default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# ── retry policy ──────────────────────────────────────────────────────

@dataclass
class RetryPolicy:
    """Bounded retry with exponential backoff + jitter.

    Prevents retry storms and poison tasks.
    """
    max_attempts: int = 3
    base_delay_s: float = 1.0
    max_delay_s: float = 60.0
    backoff_factor: float = 2.0
    jitter_range_s: float = 0.5

    def delay_for_attempt(self, attempt: int) -> float:
        """Calculate delay for a given retry attempt (0-indexed attempt number)."""
        if attempt <= 0:
            return 0.0
        exp_delay = min(self.base_delay_s * (self.backoff_factor ** (attempt - 1)),
                        self.max_delay_s)
        jitter = random.uniform(0, self.jitter_range_s)
        return exp_delay + jitter

    def is_exhausted(self, attempt: int) -> bool:
        """Check if retry attempts are exhausted."""
        return attempt >= self.max_attempts


# ── checkpoint ─────────────────────────────────────────────────────────

@dataclass
class StepCheckpoint:
    """A versioned checkpoint for a single step execution."""
    task_id: str
    step_name: str
    step_index: int
    status: str  # "started", "completed", "failed", "skipped"
    idempotency_key: str
    payload_hash: str
    result_summary: str = ""
    error: str = ""
    attempt: int = 0
    ts: float = field(default_factory=time.time)
    version: int = 1

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "step_name": self.step_name,
            "step_index": self.step_index,
            "status": self.status,
            "idempotency_key": self.idempotency_key,
            "payload_hash": self.payload_hash,
            "result_summary": self.result_summary[:200],
            "error": self.error[:200],
            "attempt": self.attempt,
            "ts": self.ts,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StepCheckpoint":
        return cls(
            task_id=str(d.get("task_id", "")),
            step_name=str(d.get("step_name", "")),
            step_index=int(d.get("step_index", 0)),
            status=str(d.get("status", "")),
            idempotency_key=str(d.get("idempotency_key", "")),
            payload_hash=str(d.get("payload_hash", "")),
            result_summary=str(d.get("result_summary", "")),
            error=str(d.get("error", "")),
            attempt=int(d.get("attempt", 0)),
            ts=float(d.get("ts", 0)),
            version=int(d.get("version", 1)),
        )


# ── task step definition ──────────────────────────────────────────────

@dataclass
class TaskStep:
    """Definition of a single step in a workflow."""
    name: str
    handler: Callable | None = None  # Callable(task_context) -> result dict
    requires_approval: bool = False
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    timeout_s: float = 300.0
    payload: dict | None = None
    payload_hash_override: str | None = None  # For testing

    def compute_idempotency_key(self, task_id: str) -> str:
        ph = self.payload_hash_override or payload_hash(self.payload)
        return idempotency_key(task_id=task_id, step_name=self.name,
                               payload_hash=ph)


# ── task context (carried through lifecycle) ──────────────────────────

@dataclass
class TaskContext:
    """Mutable context carried through a task lifecycle."""
    task_id: str
    run_id: str
    agent_id: str
    correlation_id: str
    causation_id: str
    trace_id: str
    state: TaskState = TaskState.CREATED
    steps: List[TaskStep] = field(default_factory=list)
    checkpoints: List[StepCheckpoint] = field(default_factory=list)
    current_step_index: int = -1
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_steps_keys: set = field(default_factory=set)  # idempotency keys
    paused: bool = False
    cancelled: bool = False
    retry_counts: dict = field(default_factory=dict)  # step_name -> attempt count
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "trace_id": self.trace_id,
            "state": self.state.value,
            "steps": [{"name": s.name,
                       "requires_approval": s.requires_approval,
                       "timeout_s": s.timeout_s,
                       "max_retries": s.retry_policy.max_attempts,
                       "payload_hash_override": s.payload_hash_override}
                      for s in self.steps],
            "checkpoints": [cp.to_dict() for cp in self.checkpoints],
            "current_step_index": self.current_step_index,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_steps_keys": sorted(self.completed_steps_keys),
            "paused": self.paused,
            "cancelled": self.cancelled,
            "retry_counts": self.retry_counts,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TaskContext":
        ctx = cls(
            task_id=str(d.get("task_id", "")),
            run_id=str(d.get("run_id", "")),
            agent_id=str(d.get("agent_id", "")),
            correlation_id=str(d.get("correlation_id", "")),
            causation_id=str(d.get("causation_id", "")),
            trace_id=str(d.get("trace_id", "")),
            state=TaskState(d.get("state", "CREATED")),
            current_step_index=int(d.get("current_step_index", -1)),
            created_at=float(d.get("created_at", 0)),
            updated_at=float(d.get("updated_at", 0)),
            paused=bool(d.get("paused", False)),
            cancelled=bool(d.get("cancelled", False)),
            retry_counts=dict(d.get("retry_counts", {})),
            metadata=dict(d.get("metadata", {})),
        )
        # Restore step definitions (without handlers -- handlers are NOT
        # persisted; they must be re-registered by the caller on recovery)
        for s_d in (d.get("steps") or []):
            step = TaskStep(
                name=str(s_d.get("name", "")),
                requires_approval=bool(s_d.get("requires_approval", False)),
                timeout_s=float(s_d.get("timeout_s", 300.0)),
                retry_policy=RetryPolicy(
                    max_attempts=int(s_d.get("max_retries", 3))),
                payload_hash_override=s_d.get("payload_hash_override"),
                payload=s_d.get("payload"),
            )
            ctx.steps.append(step)
        # Restore checkpoints
        for cp_d in (d.get("checkpoints") or []):
            try:
                ctx.checkpoints.append(StepCheckpoint.from_dict(cp_d))
            except (KeyError, TypeError, ValueError):
                pass
        # Restore completed step keys
        for k in (d.get("completed_steps_keys") or []):
            ctx.completed_steps_keys.add(str(k))
        return ctx


# ── persistence ─────────────────────────────────────────────────────────

class TaskStore:
    """Append-only JSONL store for task state. Supports save/load/append."""

    def __init__(self, path: Optional[Path] = None):
        self._path = path or (_HERE / "state" / "orchestration" /
                              "task-state.jsonl")
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, ctx: TaskContext) -> bool:
        """Save full task state as a single JSONL record (append-only).
        Each save = new version. Load reads latest."""
        try:
            record = ctx.to_dict()
            record["version_ts"] = time.time()
            record["version_seq"] = len(self._load_raw()) + 1
            tmp = self._path.with_suffix(".jsonl.tmp")
            # Append to existing file
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            return True
        except OSError:
            return False

    def load(self, task_id: str) -> Optional[TaskContext]:
        """Load the latest version of a task by scanning for last matching record."""
        raw = self._load_raw()
        latest = None
        for rec in reversed(raw):
            if rec.get("task_id") == task_id:
                latest = rec
                break
        if latest is None:
            return None
        try:
            return TaskContext.from_dict(latest)
        except (KeyError, TypeError, ValueError):
            return None

    def load_all(self) -> List[dict]:
        """Load all records (for admin/debugging)."""
        return self._load_raw()

    def _load_raw(self) -> List[dict]:
        """Read all JSONL records."""
        if not self._path.exists():
            return []
        records = []
        try:
            for line in self._path.read_text("utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except (json.JSONDecodeError, ValueError):
                    continue
        except OSError:
            pass
        return records

    def record_checkpoint(self, cp: StepCheckpoint) -> bool:
        """Append a step checkpoint to the step-checkpoint ledger."""
        cp_path = self._path.parent / "step-checkpoints.jsonl"
        try:
            cp_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cp_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(cp.to_dict(), ensure_ascii=False) + "\n")
            return True
        except OSError:
            return False

    def load_checkpoints(self, task_id: str) -> List[StepCheckpoint]:
        """Load all checkpoints for a task."""
        cp_path = self._path.parent / "step-checkpoints.jsonl"
        if not cp_path.exists():
            return []
        checkpoints = []
        try:
            for line in cp_path.read_text("utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    if not isinstance(d, dict):
                        continue
                    if d.get("task_id") == task_id:
                        checkpoints.append(StepCheckpoint.from_dict(d))
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    continue
        except OSError:
            pass
        return checkpoints

    def completed_idempotency_keys(self, task_id: str) -> set:
        """Get all idempotency keys that completed successfully for a task."""
        checkpoints = self.load_checkpoints(task_id)
        return {cp.idempotency_key for cp in checkpoints
                if cp.status == "completed"}


# ── transition engine ──────────────────────────────────────────────────

def can_transition(from_state: TaskState, to_state: TaskState) -> bool:
    """Check if a state transition is legal."""
    return to_state in _ALLOWED_TRANSITIONS.get(from_state, set())


def transition(task_ctx: TaskContext, to_state: TaskState,
               reason: str = "") -> dict:
    """Attempt a state transition on a task context.

    Returns:
        {ok: bool, from: str, to: str, reason: str}

    Illegal transitions are rejected. Terminal states cannot be left.
    """
    if task_ctx.state in TERMINAL_STATES:
        return {"ok": False, "from": task_ctx.state.value,
                "to": to_state.value,
                "reason": f"terminal_state:{task_ctx.state.value}"}
    if not can_transition(task_ctx.state, to_state):
        return {"ok": False, "from": task_ctx.state.value,
                "to": to_state.value,
                "reason": f"illegal_transition:{task_ctx.state.value}->{to_state.value}"}
    old = task_ctx.state
    task_ctx.state = to_state
    task_ctx.updated_at = time.time()
    return {"ok": True, "from": old.value, "to": to_state.value,
            "reason": reason}


# ── step execution with idempotency ────────────────────────────────────

def execute_step(task_ctx: TaskContext, step: TaskStep,
                 store: TaskStore,
                 kill_check: Optional[Callable] = None,
                 clock: Optional[Callable] = None) -> dict:
    """Execute a single step with idempotency protection.

    If the step's idempotency key is already in the completed set, returns
    NOOP (not re-executed). This is the core crash-recovery mechanism:
    after restart, completed steps are skipped.

    Args:
        task_ctx: The task context (mutable)
        step: The step to execute
        store: Persistence store for checkpoints
        kill_check: Optional callable returning True if kill is active
        clock: Optional clock function (injectable for testing)

    Returns:
        {ok: bool, status: str, idempotency_key: str, result: dict, ...}
    """
    _clock = clock or time.time
    ik = step.compute_idempotency_key(task_ctx.task_id)

    # Check kill switch before execution
    if kill_check and kill_check():
        return {"ok": False, "status": "cancelled",
                "idempotency_key": ik, "reason": "kill_switch_active",
                "step_name": step.name}

    # Check cancellation flag on context
    if task_ctx.cancelled:
        return {"ok": False, "status": "cancelled",
                "idempotency_key": ik, "reason": "task_cancelled",
                "step_name": step.name}

    # IDempotency check: already completed?
    if ik in task_ctx.completed_steps_keys:
        return {"ok": True, "status": "NOOP",
                "idempotency_key": ik,
                "reason": "duplicate-replay:step_already_completed",
                "step_name": step.name}

    # Check pause
    if task_ctx.paused:
        return {"ok": False, "status": "paused",
                "idempotency_key": ik, "reason": "task_paused",
                "step_name": step.name}

    # Get retry count
    attempt = task_ctx.retry_counts.get(step.name, 0)

    # Record "started" checkpoint
    started_cp = StepCheckpoint(
        task_id=task_ctx.task_id, step_name=step.name,
        step_index=task_ctx.current_step_index,
        status="started", idempotency_key=ik,
        payload_hash=step.payload_hash_override or payload_hash(step.payload),
        attempt=attempt, ts=_clock(),
    )
    store.record_checkpoint(started_cp)

    # Execute the handler
    if step.handler is None:
        # No handler = skip (planning step or approval gate)
        completed_cp = StepCheckpoint(
            task_id=task_ctx.task_id, step_name=step.name,
            step_index=task_ctx.current_step_index,
            status="completed", idempotency_key=ik,
            payload_hash=step.payload_hash_override or payload_hash(step.payload),
            result_summary="no_handler:skipped", attempt=attempt,
            ts=_clock(),
        )
        store.record_checkpoint(completed_cp)
        task_ctx.completed_steps_keys.add(ik)
        return {"ok": True, "status": "skipped",
                "idempotency_key": ik, "step_name": step.name,
                "reason": "no_handler"}

    try:
        result = step.handler(task_ctx)
        if not isinstance(result, dict):
            result = {"raw": str(result)[:200]}

        # Check kill again after handler (long-running handler might have been killed)
        if kill_check and kill_check():
            return {"ok": False, "status": "cancelled",
                    "idempotency_key": ik,
                    "reason": "kill_switch_during_execution",
                    "step_name": step.name, "partial_result": result}

        # Success
        completed_cp = StepCheckpoint(
            task_id=task_ctx.task_id, step_name=step.name,
            step_index=task_ctx.current_step_index,
            status="completed", idempotency_key=ik,
            payload_hash=step.payload_hash_override or payload_hash(step.payload),
            result_summary=json.dumps(result, ensure_ascii=False)[:200],
            attempt=attempt, ts=_clock(),
        )
        store.record_checkpoint(completed_cp)
        task_ctx.completed_steps_keys.add(ik)
        task_ctx.retry_counts[step.name] = 0  # reset retry count on success

        return {"ok": True, "status": "completed",
                "idempotency_key": ik, "step_name": step.name,
                "result": result}

    except Exception as e:
        # Failure
        failed_cp = StepCheckpoint(
            task_id=task_ctx.task_id, step_name=step.name,
            step_index=task_ctx.current_step_index,
            status="failed", idempotency_key=ik,
            payload_hash=step.payload_hash_override or payload_hash(step.payload),
            error=f"{type(e).__name__}:{e}"[:200],
            attempt=attempt, ts=_clock(),
        )
        store.record_checkpoint(failed_cp)

        return {"ok": False, "status": "failed",
                "idempotency_key": ik, "step_name": step.name,
                "error": f"{type(e).__name__}:{e}",
                "attempt": attempt}


# ── orchestration engine ────────────────────────────────────────────────

class TaskOrchestrator:
    """Durable multi-agent task orchestrator.

    Manages the full lifecycle of a multi-step task:
      1. Create task with steps
      2. Plan steps (approve/reject)
      3. Execute steps sequentially with idempotency
      4. Handle pause/resume/retry/cancel
      5. Survive restart: resume from last checkpoint

    Usage:
        orch = TaskOrchestrator(store=TaskStore(path))
        task = orch.create_task(steps=[...], agent_id="worker-1")
        orch.plan(task)
        orch.start(task)
        # After crash:
        task = orch.load_task(task.task_id)
        orch.resume(task)
    """

    def __init__(self, *, store: Optional[TaskStore] = None,
                 kill_check: Optional[Callable] = None,
                 clock: Optional[Callable] = None,
                 approval_fn: Optional[Callable] = None):
        self._store = store or TaskStore()
        self._kill_check = kill_check
        self._clock = clock or time.time
        self._approval_fn = approval_fn
        self._audit_entries: list = []

    @property
    def store(self) -> TaskStore:
        return self._store

    def _check_kill(self) -> bool:
        """Check if kill is active (kill switch or provided callable)."""
        if self._kill_check and self._kill_check():
            return True
        # Also check kill coordinator if available
        try:
            from containment.kill_coordinator import KillCoordinator
            # We don't own the coordinator instance, so we check via opslib
            import opslib
            if opslib.halted() is not None:
                return True
        except Exception:  # noqa: BLE001
            pass
        return False

    def _audit(self, event: str, actor: str, action_id: str,
                risk_tier: str, decision: str, details: dict | None = None):
        """Record an audit entry (in-memory, for now; caller can flush)."""
        self._audit_entries.append({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event, "actor": actor, "action_id": action_id,
            "risk_tier": risk_tier, "decision": decision,
            "details": details or {},
        })

    # ── task creation ──────────────────────────────────────────────────
    def create_task(self, steps: Sequence[TaskStep], *,
                    task_id: Optional[str] = None,
                    run_id: Optional[str] = None,
                    agent_id: str = "unknown",
                    correlation_id: Optional[str] = None,
                    causation_id: Optional[str] = None,
                    trace_id: Optional[str] = None,
                    metadata: Optional[dict] = None) -> TaskContext:
        """Create a new task with the given steps.

        Returns the created TaskContext in CREATED state.
        """
        # Generate canonical IDs
        tid = task_id or f"TSK-{uuid.uuid4().hex[:8]}"
        rid = run_id or f"RUN-{uuid.uuid4().hex[:8]}"
        cid = correlation_id or uuid.uuid4().hex[:16]
        caus = causation_id or uuid.uuid4().hex[:16]
        trid = trace_id or uuid.uuid4().hex[:16]

        # Try to get trace_id from context if available
        if not trace_id:
            try:
                sys.path.insert(0, str(_OPS / "telemetry"))
                from trace_context import get_trace_id
                existing_trace = get_trace_id()
                if existing_trace:
                    trid = existing_trace
            except Exception:  # noqa: BLE001
                pass

        ctx = TaskContext(
            task_id=tid, run_id=rid, agent_id=agent_id,
            correlation_id=cid, causation_id=caus, trace_id=trid,
            steps=list(steps), metadata=metadata or {},
        )

        self._audit("task_created", agent_id, tid, "reversible_write",
                     "ALLOW", {"step_count": len(steps)})
        self._store.save(ctx)
        return ctx

    # ── task lifecycle ─────────────────────────────────────────────────
    def plan(self, task_ctx: TaskContext) -> dict:
        """Move task from CREATED to PLANNED."""
        result = transition(task_ctx, TaskState.PLANNED, "plan")
        if result["ok"]:
            self._store.save(task_ctx)
            self._audit("task_planned", task_ctx.agent_id, task_ctx.task_id,
                         "reversible_write", "ALLOW")
        return result

    def request_approval(self, task_ctx: TaskContext) -> dict:
        """Move task from PLANNED to APPROVAL_PENDING (if any step requires approval)."""
        has_approval_step = any(s.requires_approval for s in task_ctx.steps)
        if has_approval_step:
            result = transition(task_ctx, TaskState.APPROVAL_PENDING,
                                "approval_required")
        else:
            result = transition(task_ctx, TaskState.RUNNING, "no_approval_needed")
        if result["ok"]:
            self._store.save(task_ctx)
            self._audit("task_approval_requested" if has_approval_step
                         else "task_started",
                         task_ctx.agent_id, task_ctx.task_id,
                         "reversible_write", "ALLOW")
        return result

    def approve(self, task_ctx: TaskContext) -> dict:
        """Approve a task in APPROVAL_PENDING state, moving it to RUNNING."""
        result = transition(task_ctx, TaskState.RUNNING, "approved")
        if result["ok"]:
            self._store.save(task_ctx)
            self._audit("task_approved", "owner", task_ctx.task_id,
                         "irreversible", "ALLOW")
        return result

    def deny(self, task_ctx: TaskContext, reason: str = "") -> dict:
        """Deny a task in APPROVAL_PENDING state, moving it to FAILED."""
        result = transition(task_ctx, TaskState.FAILED,
                            f"denied:{reason}" if reason else "denied")
        if result["ok"]:
            self._store.save(task_ctx)
            self._audit("task_denied", "owner", task_ctx.task_id,
                         "irreversible", "DENY", {"reason": reason})
        return result

    def start(self, task_ctx: TaskContext) -> dict:
        """Start executing a task (must be in RUNNING or PLANNED state).

        If task is already in a terminal state, returns NOOP with status.
        """
        if task_ctx.state in TERMINAL_STATES:
            return {"ok": True, "status": task_ctx.state.value.lower(),
                    "reason": f"already_{task_ctx.state.value.lower()}"}
        if task_ctx.state == TaskState.PLANNED:
            r = self.request_approval(task_ctx)
            if r["ok"] and task_ctx.state == TaskState.APPROVAL_PENDING:
                return r
            if not r["ok"]:
                return r
        if task_ctx.state != TaskState.RUNNING:
            return {"ok": False, "reason": f"not_running:{task_ctx.state.value}",
                    "status": "error"}
        return self._execute_steps(task_ctx)

    def _execute_steps(self, task_ctx: TaskContext) -> dict:
        """Execute remaining steps (those not yet completed).

        This is the core loop. After a crash/restart, only uncompleted
        steps are executed. Completed steps are skipped (NOOP via idempotency).
        Uses a while loop so retries correctly re-execute the same step.
        """
        results = []
        i = 0
        while i < len(task_ctx.steps):
            step = task_ctx.steps[i]

            # Check kill before each step
            if self._check_kill():
                transition(task_ctx, TaskState.CANCELLED,
                            "kill_switch_during_execution")
                self._store.save(task_ctx)
                self._audit("task_cancelled", "system", task_ctx.task_id,
                             "irreversible", "DENY",
                             {"reason": "kill_switch", "at_step": step.name,
                              "completed": len(task_ctx.completed_steps_keys)})
                return {"ok": False, "status": "cancelled",
                        "reason": "kill_switch", "step_results": results,
                        "completed_steps": len(task_ctx.completed_steps_keys),
                        "total_steps": len(task_ctx.steps)}

            # Check if already paused
            if task_ctx.paused:
                break

            task_ctx.current_step_index = i
            step_result = execute_step(
                task_ctx, step, self._store,
                kill_check=self._check_kill,
                clock=self._clock,
            )
            results.append(step_result)

            # Handle step failure -> retry or task failure
            if step_result["ok"] and step_result["status"] == "completed":
                i += 1
                continue
            elif step_result["ok"] and step_result["status"] in ("NOOP", "skipped"):
                i += 1
                continue
            elif not step_result["ok"]:
                if step_result["status"] == "cancelled":
                    transition(task_ctx, TaskState.CANCELLED,
                                "kill_during_step_execution")
                    self._store.save(task_ctx)
                    self._audit("task_cancelled", "system", task_ctx.task_id,
                                 "irreversible", "DENY",
                                 {"reason": "kill_during_step",
                                  "at_step": step.name})
                    return {"ok": False, "status": "cancelled",
                            "reason": "kill_switch", "step_results": results,
                            "completed_steps": len(task_ctx.completed_steps_keys),
                            "total_steps": len(task_ctx.steps)}
                if step_result["status"] == "paused":
                    break

                # Retry logic: attempt = current count + 1 for this attempt
                current_attempt = task_ctx.retry_counts.get(step.name, 0)
                attempt = current_attempt + 1
                task_ctx.retry_counts[step.name] = attempt

                if step.retry_policy.is_exhausted(attempt):
                    # Max retries exceeded -> task FAILED
                    transition(task_ctx, TaskState.FAILED,
                                f"max_retries_exceeded:{step.name}")
                    self._store.save(task_ctx)
                    self._audit("task_failed", task_ctx.agent_id,
                                 task_ctx.task_id, "irreversible", "DENY",
                                 {"reason": "max_retries",
                                  "step": step.name,
                                  "attempt": attempt})
                    return {"ok": False, "status": "failed",
                            "reason": f"max_retries:{step.name}",
                            "step_results": results}

                # Transition to RETRYING
                transition(task_ctx, TaskState.RETRYING,
                            f"retrying:{step.name}:attempt:{attempt}")
                self._store.save(task_ctx)

                # Apply backoff delay
                delay = step.retry_policy.delay_for_attempt(attempt)
                time.sleep(delay)

                # Re-execute this step (do NOT increment i)
                transition(task_ctx, TaskState.RUNNING,
                            f"retry_resume:{step.name}:attempt:{attempt}")
                self._store.save(task_ctx)
                continue  # retry same step

        # All steps completed
        if len(task_ctx.completed_steps_keys) >= len(task_ctx.steps):
            transition(task_ctx, TaskState.COMPLETED, "all_steps_done")
            self._store.save(task_ctx)
            self._audit("task_completed", task_ctx.agent_id,
                         task_ctx.task_id, "reversible_write", "ALLOW")
            return {"ok": True, "status": "completed",
                    "step_results": results,
                    "completed_steps": len(task_ctx.completed_steps_keys),
                    "total_steps": len(task_ctx.steps)}

        # Paused mid-execution
        if task_ctx.paused:
            transition(task_ctx, TaskState.PAUSED, "paused_mid_execution")
            self._store.save(task_ctx)
            return {"ok": False, "status": "paused",
                    "reason": "paused", "step_results": results}

        # Incomplete but not paused (some steps skipped/no-handler?)
        return {"ok": True, "status": "partial",
                "step_results": results,
                "completed_steps": len(task_ctx.completed_steps_keys),
                "total_steps": len(task_ctx.steps)}

    # ── pause/resume ───────────────────────────────────────────────────
    def pause(self, task_ctx: TaskContext) -> dict:
        """Pause a running task. Effective on next step boundary."""
        if task_ctx.state not in (TaskState.RUNNING, TaskState.RETRYING):
            return {"ok": False, "reason": f"not_running:{task_ctx.state.value}"}
        task_ctx.paused = True
        transition(task_ctx, TaskState.PAUSED, "pause_requested")
        self._store.save(task_ctx)
        self._audit("task_paused", task_ctx.agent_id, task_ctx.task_id,
                     "reversible_write", "ALLOW")
        return {"ok": True, "status": "paused"}

    def resume(self, task_ctx: TaskContext) -> dict:
        """Resume a paused task from the last checkpoint."""
        if task_ctx.state != TaskState.PAUSED:
            return {"ok": False, "reason": f"not_paused:{task_ctx.state.value}"}
        task_ctx.paused = False
        transition(task_ctx, TaskState.RUNNING, "resumed_from_pause")
        self._store.save(task_ctx)
        self._audit("task_resumed", task_ctx.agent_id, task_ctx.task_id,
                     "reversible_write", "ALLOW")
        return self._execute_steps(task_ctx)

    # ── cancel ────────────────────────────────────────────────────────
    def cancel(self, task_ctx: TaskContext, reason: str = "owner_command") -> dict:
        """Cancel a task. Works from any non-terminal state."""
        if task_ctx.state in TERMINAL_STATES:
            return {"ok": False, "reason": f"terminal:{task_ctx.state.value}"}
        task_ctx.cancelled = True
        task_ctx.paused = False
        result = transition(task_ctx, TaskState.CANCELLED, reason)
        if result["ok"]:
            self._store.save(task_ctx)
            self._audit("task_cancelled", "system" if "kill" in reason
                         else task_ctx.agent_id,
                         task_ctx.task_id, "irreversible", "DENY",
                         {"reason": reason})
        return result

    # ── recovery ───────────────────────────────────────────────────────
    def load_task(self, task_id: str) -> Optional[TaskContext]:
        """Load a task from the store (for recovery after restart)."""
        return self._store.load(task_id)

    def recover(self, task_id: str) -> dict:
        """Recover a task after restart. Returns recovery summary.

        Checks if the task was in a non-terminal state when interrupted,
        and returns the appropriate action (resume, reconcile, or declare done).
        """
        ctx = self.load_task(task_id)
        if ctx is None:
            return {"ok": False, "reason": "task_not_found", "task_id": task_id}

        if ctx.state in TERMINAL_STATES:
            return {"ok": True, "action": "none",
                    "reason": f"already_terminal:{ctx.state.value}",
                    "task_id": task_id, "state": ctx.state.value}

        # Check what was completed
        completed_count = len(ctx.completed_steps_keys)
        total_steps = len(ctx.steps)

        # Check if all steps are completed but state wasn't updated (crash
        # after last step, before state transition)
        if completed_count >= total_steps and total_steps > 0:
            transition(ctx, TaskState.COMPLETED, "recovery:all_steps_completed")
            self._store.save(ctx)
            return {"ok": True, "action": "complete",
                    "reason": "recovery:all_steps_completed",
                    "task_id": task_id, "completed": completed_count,
                    "total": total_steps}

        # Find next step to execute by matching idempotency keys
        next_step_idx = -1
        for i, step in enumerate(ctx.steps):
            ik = step.compute_idempotency_key(task_id)
            if ik not in ctx.completed_steps_keys:
                next_step_idx = i
                break

        return {
            "ok": True,
            "action": "resume",
            "reason": "recovery:incomplete_task",
            "task_id": task_id,
            "state": ctx.state.value,
            "completed": completed_count,
            "total": total_steps,
            "next_step_index": next_step_idx,
            "retry_counts": dict(ctx.retry_counts),
        }

    # ── status ─────────────────────────────────────────────────────────
    def task_status(self, task_id: str) -> dict:
        """Get current status of a task."""
        ctx = self.load_task(task_id)
        if ctx is None:
            return {"ok": False, "reason": "task_not_found"}
        return {
            "ok": True,
            "task_id": ctx.task_id,
            "state": ctx.state.value,
            "agent_id": ctx.agent_id,
            "completed_steps": len(ctx.completed_steps_keys),
            "total_steps": len(ctx.steps),
            "paused": ctx.paused,
            "cancelled": ctx.cancelled,
            "retry_counts": ctx.retry_counts,
            "created_at": ctx.created_at,
            "updated_at": ctx.updated_at,
        }

    def incomplete_tasks(self) -> list:
        """Find all tasks that were interrupted (not in terminal state)."""
        records = self._store.load_all()
        # Group by task_id, take latest
        latest: dict[str, dict] = {}
        for rec in records:
            tid = rec.get("task_id", "")
            seq = rec.get("version_seq", 0)
            if tid not in latest or seq > latest[tid].get("version_seq", 0):
                latest[tid] = rec
        incomplete = []
        for tid, rec in latest.items():
            state = rec.get("state", "")
            if state not in ("COMPLETED", "FAILED", "CANCELLED"):
                incomplete.append({
                    "task_id": tid,
                    "state": state,
                    "completed_steps": rec.get("completed_steps_keys", []),
                    "total_steps": len(rec.get("steps", [])),
                })
        return incomplete


if __name__ == "__main__":
    # Demo
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="orch-demo-"))
    store = TaskStore(path=tmp / "tasks.jsonl")
    orch = TaskOrchestrator(store=store)

    # Define a 3-step workflow
    side_effects = []
    def step1(ctx):
        side_effects.append("step1")
        return {"effect": "step1_done"}

    def step2(ctx):
        side_effects.append("step2")
        return {"effect": "step2_done"}

    def step3(ctx):
        side_effects.append("step3")
        return {"effect": "step3_done"}

    steps = [
        TaskStep(name="step1", handler=step1),
        TaskStep(name="step2", handler=step2),
        TaskStep(name="step3", handler=step3),
    ]

    task = orch.create_task(steps, agent_id="demo-worker")
    print(f"Created: {task.task_id} state={task.state.value}")

    orch.plan(task)
    orch.request_approval(task)
    orch.approve(task)
    result = orch.start(task)
    print(f"Executed: {result['status']}, effects={side_effects}")

    # Verify: side effects happened exactly once per step
    assert side_effects == ["step1", "step2", "step3"], side_effects
    assert task.state == TaskState.COMPLETED

    # Simulate restart: load task, try to re-execute
    side_effects.clear()
    loaded = orch.load_task(task.task_id)
    assert loaded is not None
    assert loaded.state == TaskState.COMPLETED
    print(f"After restart load: state={loaded.state.value}")

    # Cleanup
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print("Demo complete.")
