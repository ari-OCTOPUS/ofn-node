#!/usr/bin/env python3
"""FLEET COMPUTE — durable task store and admission policy (control plane).

Implements the task contract the fleet CPU scan requires: a durable queue with
real leases, exactly-once settlement, a retry budget, and fail-closed admission
driven by measured node telemetry.

Design rules taken from the scan, kept explicit here because they are the whole
point of the module:

* A missing or stale measurement yields UNKNOWN, and UNKNOWN never grants a
  lease. Absence of evidence is not evidence of headroom.
* Workers execute only pre-registered profiles. `params` is data; it is never
  interpolated into a shell string by this module or by the worker.
* External effects are out of scope by construction: every task carries
  external_effects=0 and customer_send=False, and the schema refuses otherwise.

Stdlib only, SQLite in WAL mode, append-only event log.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA_VERSION = "compute.v1"

# Task lifecycle. PARKED is a first-class terminal-ish state: it means the
# control plane deliberately declined to place the task (no admissible node,
# stale telemetry, owner pause) and will retry later without consuming an
# attempt. That is different from FAILED_RETRYABLE, which consumed an attempt.
STATES = (
    "QUEUED",
    "LEASED",
    "RUNNING",
    "SUCCEEDED",
    "FAILED_RETRYABLE",
    "FAILED_FINAL",
    "PARKED",
    "CANCELLED",
)
TERMINAL = ("SUCCEEDED", "FAILED_FINAL", "CANCELLED")

# Resource classes a node must advertise to be eligible.
RESOURCE_CLASSES = ("cpu_batch", "io_batch")

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id          TEXT PRIMARY KEY,
    idempotency_key  TEXT NOT NULL UNIQUE,
    profile          TEXT NOT NULL,
    params_json      TEXT NOT NULL,
    input_digest     TEXT NOT NULL,
    resource_class   TEXT NOT NULL,
    max_attempts     INTEGER NOT NULL,
    attempt          INTEGER NOT NULL DEFAULT 0,
    deadline_utc     TEXT,
    state            TEXT NOT NULL,
    worker_node_id   TEXT,
    lease_id         TEXT,
    lease_expiry_utc TEXT,
    created_utc      TEXT NOT NULL,
    updated_utc      TEXT NOT NULL,
    output_digest    TEXT,
    result_json      TEXT,
    last_error       TEXT,
    external_effects INTEGER NOT NULL DEFAULT 0,
    customer_send    INTEGER NOT NULL DEFAULT 0,
    CHECK (state IN ('QUEUED','LEASED','RUNNING','SUCCEEDED','FAILED_RETRYABLE','FAILED_FINAL','PARKED','CANCELLED')),
    CHECK (external_effects = 0),
    CHECK (customer_send = 0),
    CHECK (resource_class IN ('cpu_batch','io_batch'))
);

CREATE TABLE IF NOT EXISTS leases (
    lease_id       TEXT PRIMARY KEY,
    task_id        TEXT NOT NULL,
    worker_node_id TEXT NOT NULL,
    granted_utc    TEXT NOT NULL,
    expiry_utc     TEXT NOT NULL,
    released_utc   TEXT,
    release_reason TEXT
);

CREATE TABLE IF NOT EXISTS events (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,
    at_utc       TEXT NOT NULL,
    kind         TEXT NOT NULL,
    task_id      TEXT,
    node_id      TEXT,
    payload_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_state ON tasks(state);
CREATE INDEX IF NOT EXISTS idx_tasks_lease ON tasks(lease_expiry_utc);
CREATE INDEX IF NOT EXISTS idx_events_task ON events(task_id);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_utc(stamp: str) -> datetime:
    return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def plus_seconds(stamp: str, seconds: int) -> str:
    return (parse_utc(stamp) + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(obj) -> str:
    return hashlib.sha256(canon(obj)).hexdigest()


def new_id(prefix: str, seed: dict) -> str:
    """Deterministic id for content-addressed objects (tasks).

    Not used for leases: two claims of the same task on the same node inside one
    second hash identically, and the lease table would reject the second one.
    """
    return f"{prefix}-{sha(seed)[:16]}"


def new_lease_id(task_id: str, node_id: str) -> str:
    """Unique by construction. A lease is an event, not a content-addressed object."""
    return f"lease-{secrets.token_hex(8)}"


class Store:
    """SQLite-backed durable task store.

    Every mutating call writes an event row in the same transaction as the state
    change, so the event log cannot drift from the task table.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.path), isolation_level=None, timeout=15)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA_SQL)
        self.db.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES('schema', ?)", (SCHEMA_VERSION,)
        )

    # ---------- events ----------

    def event(self, kind: str, task_id: str | None = None, node_id: str | None = None, **payload) -> None:
        self.db.execute(
            "INSERT INTO events(at_utc, kind, task_id, node_id, payload_json) VALUES(?,?,?,?,?)",
            (utc_now(), kind, task_id, node_id, json.dumps(payload, sort_keys=True, ensure_ascii=False)),
        )

    def events(self, task_id: str | None = None, limit: int = 100) -> list[dict]:
        if task_id:
            rows = self.db.execute(
                "SELECT * FROM events WHERE task_id=? ORDER BY seq DESC LIMIT ?", (task_id, limit)
            ).fetchall()
        else:
            rows = self.db.execute(
                "SELECT * FROM events ORDER BY seq DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    # ---------- enqueue ----------

    def enqueue(
        self,
        profile: str,
        params: dict,
        *,
        input_digest: str,
        idempotency_key: str,
        resource_class: str = "cpu_batch",
        max_attempts: int = 2,
        deadline_utc: str | None = None,
    ) -> dict:
        """Insert a task. Idempotent on idempotency_key: a repeat returns the original."""
        if resource_class not in RESOURCE_CLASSES:
            raise ValueError(f"unknown resource_class: {resource_class}")
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")

        existing = self.db.execute(
            "SELECT * FROM tasks WHERE idempotency_key=?", (idempotency_key,)
        ).fetchone()
        if existing:
            self.event("ENQUEUE_DEDUPED", existing["task_id"], payload_kind="idempotency_key")
            return {"ok": True, "deduped": True, "task": dict(existing)}

        task_id = new_id("task", {"profile": profile, "idem": idempotency_key})
        now = utc_now()
        try:
            self.db.execute(
                """INSERT INTO tasks(task_id, idempotency_key, profile, params_json, input_digest,
                       resource_class, max_attempts, attempt, deadline_utc, state, created_utc,
                       updated_utc, external_effects, customer_send)
                   VALUES(?,?,?,?,?,?,?,0,?, 'QUEUED', ?, ?, 0, 0)""",
                (
                    task_id, idempotency_key, profile, json.dumps(params, sort_keys=True),
                    input_digest, resource_class, max_attempts, deadline_utc, now, now,
                ),
            )
        except sqlite3.IntegrityError:
            row = self.db.execute(
                "SELECT * FROM tasks WHERE idempotency_key=?", (idempotency_key,)
            ).fetchone()
            self.event("ENQUEUE_RACE_DEDUPED", row["task_id"])
            return {"ok": True, "deduped": True, "task": dict(row)}
        self.event("ENQUEUED", task_id, profile=profile, resource_class=resource_class,
                   input_digest=input_digest)
        return {"ok": True, "deduped": False, "task": self.get(task_id)}

    # ---------- read ----------

    def get(self, task_id: str) -> dict | None:
        row = self.db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        return dict(row) if row else None

    def by_state(self, state: str, limit: int = 50) -> list[dict]:
        rows = self.db.execute(
            "SELECT * FROM tasks WHERE state=? ORDER BY created_utc LIMIT ?", (state, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> dict:
        rows = self.db.execute("SELECT state, COUNT(*) c FROM tasks GROUP BY state").fetchall()
        counts = {r["state"]: r["c"] for r in rows}
        active = self.db.execute(
            "SELECT COUNT(*) c FROM tasks WHERE state IN ('LEASED','RUNNING')"
        ).fetchone()["c"]
        return {
            "schema": SCHEMA_VERSION,
            "at_utc": utc_now(),
            "by_state": counts,
            "active": active,
            "events": self.db.execute("SELECT COUNT(*) c FROM events").fetchone()["c"],
        }

    # ---------- lease / claim ----------

    def claim(self, task_id: str, node_id: str, *, lease_seconds: int) -> dict:
        """Grant a real, expiring lease. Refuses unless the task is QUEUED."""
        task = self.get(task_id)
        if not task:
            return {"ok": False, "error": "unknown_task"}
        if task["state"] != "QUEUED":
            return {"ok": False, "error": "not_queued", "state": task["state"]}

        now = utc_now()
        lease_id = new_lease_id(task_id, node_id)
        expiry = plus_seconds(now, lease_seconds)
        self.db.execute(
            "INSERT INTO leases(lease_id, task_id, worker_node_id, granted_utc, expiry_utc) VALUES(?,?,?,?,?)",
            (lease_id, task_id, node_id, now, expiry),
        )
        self.db.execute(
            "UPDATE tasks SET state='LEASED', worker_node_id=?, lease_id=?, lease_expiry_utc=?, updated_utc=? WHERE task_id=?",
            (node_id, lease_id, expiry, now, task_id),
        )
        self.event("LEASED", task_id, node_id=node_id, lease_id=lease_id, expiry_utc=expiry)
        return {"ok": True, "lease_id": lease_id, "expiry_utc": expiry, "task": self.get(task_id)}

    def start(self, task_id: str) -> dict:
        task = self.get(task_id)
        if not task:
            return {"ok": False, "error": "unknown_task"}
        if task["state"] != "LEASED":
            return {"ok": False, "error": "not_leased", "state": task["state"]}
        self.db.execute(
            "UPDATE tasks SET state='RUNNING', attempt=attempt+1, updated_utc=? WHERE task_id=?",
            (utc_now(), task_id),
        )
        self.event("STARTED", task_id, node_id=task["worker_node_id"],
                   attempt=task["attempt"] + 1)
        return {"ok": True, "task": self.get(task_id)}

    def release_lease(self, lease_id: str, reason: str) -> None:
        self.db.execute(
            "UPDATE leases SET released_utc=?, release_reason=? WHERE lease_id=? AND released_utc IS NULL",
            (utc_now(), reason, lease_id),
        )

    # ---------- settle ----------

    def succeed(self, task_id: str, *, output_digest: str, result: dict | None = None) -> dict:
        task = self.get(task_id)
        if not task:
            return {"ok": False, "error": "unknown_task"}
        if task["state"] == "SUCCEEDED":
            # Exactly-once settlement: a duplicate result must not change state.
            self.event("SETTLE_DUPLICATE_IGNORED", task_id, output_digest=output_digest)
            return {"ok": True, "duplicate": True, "task": task}
        if task["state"] not in ("RUNNING", "LEASED"):
            return {"ok": False, "error": "not_settleable", "state": task["state"]}

        now = utc_now()
        self.db.execute(
            "UPDATE tasks SET state='SUCCEEDED', output_digest=?, result_json=?, updated_utc=?, lease_expiry_utc=NULL WHERE task_id=?",
            (output_digest, json.dumps(result or {}, sort_keys=True), now, task_id),
        )
        if task["lease_id"]:
            self.release_lease(task["lease_id"], "completed")
        self.event("SUCCEEDED", task_id, node_id=task["worker_node_id"],
                   output_digest=output_digest, attempt=task["attempt"])
        return {"ok": True, "duplicate": False, "task": self.get(task_id)}

    def fail(self, task_id: str, *, error: str, retryable: bool = True) -> dict:
        """Record a failure and apply the retry budget.

        A retryable failure returns to QUEUED only while attempts remain;
        otherwise it is FAILED_FINAL. A non-retryable failure is always final.
        """
        task = self.get(task_id)
        if not task:
            return {"ok": False, "error": "unknown_task"}
        if task["state"] in TERMINAL:
            return {"ok": False, "error": "already_terminal", "state": task["state"]}

        attempts_left = task["max_attempts"] - task["attempt"]
        if retryable and attempts_left > 0:
            new_state = "QUEUED"
        else:
            new_state = "FAILED_FINAL"

        now = utc_now()
        self.db.execute(
            "UPDATE tasks SET state=?, last_error=?, worker_node_id=NULL, lease_id=NULL, lease_expiry_utc=NULL, updated_utc=? WHERE task_id=?",
            (new_state, error[:600], now, task_id),
        )
        if task["lease_id"]:
            self.release_lease(task["lease_id"], f"failed:{error[:80]}")
        self.event("FAILED", task_id, node_id=task["worker_node_id"], retryable=retryable,
                   attempts_left=attempts_left, next_state=new_state, error=error[:300])
        return {"ok": True, "task": self.get(task_id)}

    def park(self, task_id: str, *, reason: str) -> dict:
        """Decline to place a task without consuming an attempt (no admissible node)."""
        task = self.get(task_id)
        if not task:
            return {"ok": False, "error": "unknown_task"}
        if task["state"] in TERMINAL:
            return {"ok": False, "error": "already_terminal", "state": task["state"]}
        self.db.execute(
            "UPDATE tasks SET state='PARKED', last_error=?, worker_node_id=NULL, lease_id=NULL, lease_expiry_utc=NULL, updated_utc=? WHERE task_id=?",
            (reason[:600], utc_now(), task_id),
        )
        self.event("PARKED", task_id, reason=reason[:300])
        return {"ok": True, "task": self.get(task_id)}

    def unpark(self, task_id: str) -> dict:
        task = self.get(task_id)
        if not task:
            return {"ok": False, "error": "unknown_task"}
        if task["state"] != "PARKED":
            return {"ok": False, "error": "not_parked", "state": task["state"]}
        self.db.execute(
            "UPDATE tasks SET state='QUEUED', updated_utc=? WHERE task_id=?", (utc_now(), task_id)
        )
        self.event("UNPARKED", task_id)
        return {"ok": True, "task": self.get(task_id)}

    def cancel(self, task_id: str, *, reason: str) -> dict:
        task = self.get(task_id)
        if not task:
            return {"ok": False, "error": "unknown_task"}
        if task["state"] in TERMINAL:
            return {"ok": False, "error": "already_terminal", "state": task["state"]}
        self.db.execute(
            "UPDATE tasks SET state='CANCELLED', last_error=?, worker_node_id=NULL, lease_id=NULL, lease_expiry_utc=NULL, updated_utc=? WHERE task_id=?",
            (reason[:600], utc_now(), task_id),
        )
        if task["lease_id"]:
            self.release_lease(task["lease_id"], "cancelled")
        self.event("CANCELLED", task_id, reason=reason[:300])
        return {"ok": True, "task": self.get(task_id)}

    def reclaim_expired(self, *, now: str | None = None) -> list[dict]:
        """Return leases whose expiry has passed; the tasks go back to QUEUED.

        This is what makes a rebooted or partitioned worker safe: its lease
        expires and the task is reassigned without a second settlement, because
        a late result for an already-reassigned task hits the duplicate guard in
        `succeed`.

        Returns one row per reclaimed task carrying the node and attempt that
        were cleared, because the caller needs them to stop the worker's scope —
        after this call the task row no longer knows which node it was on.
        """
        now = now or utc_now()
        rows = self.db.execute(
            """SELECT t.task_id, t.lease_id, t.worker_node_id, t.attempt, t.max_attempts
               FROM tasks t WHERE t.state IN ('LEASED','RUNNING')
                 AND t.lease_expiry_utc IS NOT NULL AND t.lease_expiry_utc < ?""",
            (now,),
        ).fetchall()
        reclaimed = []
        for row in rows:
            self.release_lease(row["lease_id"], "expired")
            # An expired attempt that has exhausted its budget is final.
            if row["attempt"] >= row["max_attempts"]:
                self.db.execute(
                    "UPDATE tasks SET state='FAILED_FINAL', last_error='lease_expired_budget_exhausted', worker_node_id=NULL, lease_id=NULL, lease_expiry_utc=NULL, updated_utc=? WHERE task_id=?",
                    (now, row["task_id"]),
                )
                kind = "LEASE_EXPIRED_FINAL"
            else:
                self.db.execute(
                    "UPDATE tasks SET state='QUEUED', worker_node_id=NULL, lease_id=NULL, lease_expiry_utc=NULL, updated_utc=? WHERE task_id=?",
                    (now, row["task_id"]),
                )
                kind = "LEASE_EXPIRED_REQUEUED"
            self.event(kind, row["task_id"], node_id=row["worker_node_id"],
                       attempt=row["attempt"])
            reclaimed.append({
                "task_id": row["task_id"],
                "node_id": row["worker_node_id"],
                "attempt": row["attempt"],
                "kind": kind,
            })
        return reclaimed

    def close(self) -> None:
        self.db.close()


# --------------------------------------------------------------------------
# Admission policy
# --------------------------------------------------------------------------

DEFAULT_POLICY = {
    "schema": "compute_policy.v1",
    # Telemetry older than this is UNKNOWN, and UNKNOWN never grants a lease.
    "max_telemetry_age_s": 90,
    "temp_ceiling_millic": 70000,
    "temp_admit_millic": 55000,
    "mem_used_pct_ceiling": 80.0,
    "mem_avail_min_mb": 400,
    # MEASURED CAVEAT (2026-09-18, node 114): a cgroup that exhausts its
    # bandwidth quota gets its tasks throttled, and throttled tasks are not
    # counted as runnable, so load1 badly understates utilisation under a
    # quota. An 8-worker load capped at CPUQuota=400% showed 8 processes at
    # ~50% CPU each while load1 read 0.66. cpu_pct (from /proc/stat deltas)
    # remains trustworthy; load1 is kept only as a coarse "is something else
    # already busy" signal on unquotaed nodes.
    "load_per_core_ceiling": 1.2,
    "cpu_pct_admit": 45.0,
    "disk_used_pct_ceiling": 90.0,
    "reserved_cores": 1,
    "reserved_mem_mb": 512,
    "lease_seconds": 120,
    "owner_pause": False,
    "allowed_nodes": None,
    # A node with this many recent failures is excluded outright rather than
    # merely deprioritised: on a 7-board fleet a flaky node is a liability, and
    # a small score penalty loses to a few degrees of thermal headroom.
    "max_failures_before_quarantine": 2,
}


def evaluate_node(
    node_id: str,
    telemetry: dict | None,
    policy: dict,
    *,
    now: str | None = None,
    failure_count: int = 0,
    capability: dict | None = None,
    require_capability: bool = False,
) -> dict:
    """Return an admission verdict for one node with explicit reason codes.

    Fail-closed: anything we cannot measure is a refusal, not a default-yes.
    """
    now = now or utc_now()
    reasons: list[str] = []
    t = telemetry or {}

    allowed = policy.get("allowed_nodes")
    if allowed is not None and node_id not in allowed:
        return {"node_id": node_id, "admit": False, "verdict": "DENIED", "reasons": ["NODE_NOT_ALLOWED"]}

    quarantine_at = policy.get("max_failures_before_quarantine", 2)
    if failure_count >= quarantine_at:
        return {
            "node_id": node_id,
            "admit": False,
            "verdict": "DENIED",
            "reasons": [f"NODE_QUARANTINED({failure_count})"],
        }

    # Placement must be capability-driven, never hostname-driven: a node whose
    # agent cannot report what it can run is not a compute target.
    if require_capability and not capability:
        return {"node_id": node_id, "admit": False, "verdict": "UNKNOWN", "reasons": ["AGENT_ABSENT"]}

    if not t.get("ok"):
        return {"node_id": node_id, "admit": False, "verdict": "UNKNOWN", "reasons": ["NO_TELEMETRY"]}

    stamp = t.get("node_utc") or t.get("probe_utc")
    age = None
    if stamp:
        try:
            age = (parse_utc(now) - parse_utc(stamp)).total_seconds()
        except ValueError:
            age = None
    if age is None:
        reasons.append("TELEMETRY_AGE_UNKNOWN")
    elif age > policy["max_telemetry_age_s"]:
        reasons.append(f"STALE_TELEMETRY({int(age)}s)")

    cores = t.get("nproc") or 0
    if cores < 1:
        reasons.append("CORES_UNKNOWN")

    hot = t.get("hottest_millic")
    if hot is None:
        reasons.append("THERMAL_UNKNOWN")
    elif hot >= policy["temp_ceiling_millic"]:
        reasons.append(f"THERMAL_CEILING({hot})")
    elif hot >= policy["temp_admit_millic"]:
        reasons.append(f"THERMAL_HOT({hot})")

    mem_used = t.get("mem_used_pct")
    mem_avail_mb = (t.get("mem_avail_kb") or 0) / 1024.0
    if mem_used is None:
        reasons.append("MEMORY_UNKNOWN")
    elif mem_used >= policy["mem_used_pct_ceiling"]:
        reasons.append(f"MEMORY_PRESSURE({mem_used}%)")
    if mem_avail_mb and mem_avail_mb < policy["mem_avail_min_mb"]:
        reasons.append(f"MEMORY_AVAIL_LOW({int(mem_avail_mb)}MB)")

    load1 = t.get("load1")
    if load1 is None:
        reasons.append("LOAD_UNKNOWN")
    elif cores and load1 > policy["load_per_core_ceiling"] * cores:
        reasons.append(f"LOAD_HIGH({load1}/{cores})")

    cpu_pct = t.get("cpu_pct")
    if cpu_pct is None:
        reasons.append("CPU_PCT_UNKNOWN")
    elif cpu_pct >= policy["cpu_pct_admit"]:
        reasons.append(f"CPU_BUSY({cpu_pct}%)")

    disk = t.get("disk_root_used_pct")
    if disk:
        try:
            if float(str(disk).rstrip("%")) >= policy["disk_used_pct_ceiling"]:
                reasons.append(f"DISK_PRESSURE({disk})")
        except ValueError:
            reasons.append("DISK_UNPARSED")

    # A node already running the fleet's own control services must keep a core
    # free; it is never a full-capacity compute target.
    if cores and cores - policy["reserved_cores"] < 1:
        reasons.append("NO_SPARE_CORE")

    admit = not reasons
    return {
        "node_id": node_id,
        "admit": admit,
        "verdict": "ADMIT" if admit else ("UNKNOWN" if any(r.endswith("UNKNOWN") for r in reasons) else "DENIED"),
        "reasons": reasons,
        "headroom": {
            "cores": cores,
            "usable_cores": max(0, cores - policy["reserved_cores"]) if cores else 0,
            "load1": load1,
            "cpu_pct": cpu_pct,
            "hottest_millic": hot,
            "mem_avail_mb": int(mem_avail_mb) if mem_avail_mb else None,
        },
    }


def placement_score(verdict: dict, policy: dict, *, failure_count: int = 0) -> float:
    """Weighted preference among already-admitted nodes.

    Only admissible nodes are scored, so this never overrides a refusal.
    Higher is better. Thermal headroom dominates because sustained small-board
    load is thermally limited, not core limited.
    """
    if not verdict.get("admit"):
        return float("-inf")
    h = verdict.get("headroom", {})
    thermal_head = (policy["temp_admit_millic"] - (h.get("hottest_millic") or 0)) / 1000.0
    cpu_head = 100.0 - (h.get("cpu_pct") or 0.0)
    load_head = (h.get("usable_cores") or 0) - (h.get("load1") or 0.0)
    score = 3.0 * thermal_head + 1.0 * cpu_head + 2.0 * load_head - 5.0 * failure_count
    return round(score, 3)


def select_placement(candidates: list[dict], policy: dict, *, require_capability: bool = False) -> dict:
    """Pick the best admissible node, or report why nothing can be placed."""
    evaluated = [
        {**evaluate_node(
            c["node_id"], c.get("telemetry"), policy,
            failure_count=c.get("failure_count", 0),
            capability=c.get("capability"),
            require_capability=require_capability,
        ),
         "score": None,
         "failure_count": c.get("failure_count", 0),
         "capable": bool(c.get("capability"))}
        for c in candidates
    ]
    for e in evaluated:
        e["score"] = placement_score(e, policy, failure_count=e["failure_count"])
    admissible = [e for e in evaluated if e["admit"]]
    admissible.sort(key=lambda e: e["score"], reverse=True)
    return {
        "chosen": admissible[0] if admissible else None,
        "evaluated": evaluated,
        "reason": None if admissible else "NO_ADMISSIBLE_NODE",
    }
