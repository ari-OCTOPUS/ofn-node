# -*- coding: utf-8 -*-
"""Wave 1 read-only memory path.

Does not write MemoryStore / memory.db. Does not infer task_id.
Production lock stays false until an independent verifier passes.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import receipt_v2, task_context

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent
LOCK_PATH = _OPS / "state" / "wave1" / "lock.json"
STOP_WAVE1 = _OPS / "STOP-WAVE1-READ"
STOP_ORGANISM = _OPS / "STOP-ORGANISM"
CAPABILITY = "memory.read"
MAX_READS_PER_CYCLE = 3
MAX_HITS = 8
TIMEOUT_MS = 250


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def freeze_lock_closed(path: Path | None = None) -> dict[str, Any]:
    """Ensure the production lock exists and is closed. Never opens Wave 1."""
    dest = Path(path or LOCK_PATH)
    dest.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "schema": "wave1-lock/1",
        "wave1_unlocked": False,
        "verifier_pass": False,
        "updated": _utc(),
        "note": "Closed by default. Only wave1_closeout may open after verifier PASS.",
    }
    if dest.exists():
        try:
            cur = json.loads(dest.read_text(encoding="utf-8"))
        except ValueError:
            cur = {}
        if cur.get("wave1_unlocked") is True:
            # Do not silently close an already-open lock here; caller decides.
            return cur
    dest.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    return rec


def read_lock(path: Path | None = None) -> dict[str, Any]:
    p = Path(path or LOCK_PATH)
    if not p.exists():
        return {"wave1_unlocked": False, "verifier_pass": False, "missing": True}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return {"wave1_unlocked": False, "verifier_pass": False, "corrupt": True}
    data["wave1_unlocked"] = bool(data.get("wave1_unlocked") is True)
    return data


def kill_engaged(*, overlay_root: Path | None = None, shadow: bool = False) -> dict[str, Any]:
    if overlay_root is not None:
        hit = next((overlay_root / name for name in (
            "STOP-WAVE1-READ", "STOP-ORGANISM", "HALT-ALL")
                    if (overlay_root / name).exists()), None)
        return {"engaged": hit is not None, "path": str(hit) if hit else None}
    if shadow:
        return {"engaged": False, "path": None}
    hit = next((p for p in (STOP_WAVE1, STOP_ORGANISM, _OPS / "HALT-ALL") if p.exists()), None)
    return {"engaged": hit is not None, "path": str(hit) if hit else None}


class WriteGuard:
    """Rejects any memory-store mutation during the read-only wave."""

    def __init__(self):
        self.attempts: list[dict[str, Any]] = []

    def deny(self, op: str, **detail) -> dict[str, Any]:
        rec = {"op": op, "denied": True, "ts": _utc(), **detail}
        self.attempts.append(rec)
        return rec

    @property
    def mutations(self) -> int:
        return len(self.attempts)


class FixtureStore:
    """TEST_ONLY in-memory store. Writes are counted and refused."""

    def __init__(self, rows: list[dict], guard: WriteGuard | None = None):
        self._rows = [dict(r) for r in rows]
        self.guard = guard or WriteGuard()
        self._fingerprint = _sha256_bytes(
            json.dumps(self._rows, sort_keys=True, ensure_ascii=False).encode("utf-8"))

    def all_records(self) -> list[dict]:
        return [dict(r) for r in self._rows]

    def fingerprint(self) -> str:
        return _sha256_bytes(
            json.dumps(self._rows, sort_keys=True, ensure_ascii=False).encode("utf-8"))

    def write(self, *args, **kwargs):
        self.guard.deny("write", args=str(args)[:80])
        raise RuntimeError("WAVE1_READ_ONLY: memory write forbidden")

    def delete(self, *args, **kwargs):
        self.guard.deny("delete")
        raise RuntimeError("WAVE1_READ_ONLY: memory delete forbidden")

    def compact(self, *args, **kwargs):
        self.guard.deny("compact")
        raise RuntimeError("WAVE1_READ_ONLY: memory compact forbidden")

    def mutate_unchanged(self) -> bool:
        return self.fingerprint() == self._fingerprint


def _eligible(row: dict, decision_time: datetime) -> bool:
    occ = row.get("occurred_at")
    rec = row.get("recorded_at")
    if not occ or not rec:
        return False
    try:
        def _p(v):
            dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        return _p(occ) <= decision_time and _p(rec) <= decision_time
    except ValueError:
        return False


def _visible_to_task(row: dict, task_id: str) -> bool:
    if row.get("shared") is True:
        return True
    owner = str(row.get("task_id") or "").strip()
    return bool(owner) and owner == task_id


def retrieve(
    store: FixtureStore,
    *,
    caller_task: str | None,
    run_id: str | None,
    kind: str,
    needle: str = "",
    decision_time: datetime | None = None,
    shadow: bool = False,
    overlay_root: Path | None = None,
    lock_path: Path | None = None,
    max_hits: int = MAX_HITS,
) -> dict[str, Any]:
    """Task-isolated read. Never fabricates task_id. Never writes the store."""
    dt = decision_time or datetime.now(timezone.utc)
    resolved = task_context.resolve(caller_task=caller_task, run_id=run_id, environ={})
    kill = kill_engaged(overlay_root=overlay_root, shadow=shadow)
    lock = read_lock(lock_path)
    allowed = bool(shadow) or (lock.get("wave1_unlocked") is True)
    status = "ok"
    rows: list[dict] = []
    if kill["engaged"]:
        status = "killed"
    elif not allowed:
        status = "locked"
    elif resolved["attribution_status"] != "resolved":
        status = "unresolved"
    else:
        task = str(resolved["task_id"])
        needle_l = needle.lower()
        for row in store.all_records():
            if not _eligible(row, dt):
                continue
            if not _visible_to_task(row, task):
                continue
            if kind == "query_experiments" and row.get("kind") != "experiment":
                continue
            if kind == "get_pending_hypotheses" and (
                    row.get("kind") != "hypothesis" or row.get("resolved")):
                continue
            if kind == "search_vault":
                text = str(row.get("text") or row.get("payload") or "")
                if needle_l not in text.lower():
                    continue
            if kind == "by_id":
                if str(row.get("id") or row.get("memory_id") or "") != needle:
                    continue
            rows.append(row)
            if len(rows) >= max_hits:
                break

    tid = resolved["task_id"] if status == "ok" else None
    evidence_ids = [str(r.get("id") or r.get("memory_id") or "") for r in rows]
    env = receipt_v2.envelope(
        task_id=tid,
        run_id=resolved.get("run_id"),
        agent_id="wave1-readonly",
        capability_id=CAPABILITY,
        outcome="ok" if status == "ok" else "skipped" if status in ("killed", "locked") else "unattributed",
        evidence_ref=",".join(evidence_ids) or f"wave1:{status}",
    )
    if status != "ok":
        env["task_id"] = tid or ""
        if status == "unresolved":
            env["task_id"] = ""
            env["outcome"] = "unattributed"
    env["task_id_source"] = resolved["task_id_source"]
    env["attribution_status"] = (
        "resolved" if status == "ok" and tid else "unresolved")
    if status == "ok" and not tid:
        env["attribution_status"] = "unresolved"
        env["outcome"] = "unattributed"
    env["wave1_status"] = status
    env["kind"] = kind
    env["hits"] = evidence_ids
    env["kill"] = kill
    env["shadow"] = bool(shadow)
    env["store_fingerprint"] = store.fingerprint()
    env["write_attempts"] = store.guard.mutations
    return {
        "status": status,
        "rows": rows,
        "ids": evidence_ids,
        "receipt": env,
        "resolved": resolved,
        "kill": kill,
        "mutations": store.guard.mutations,
        "fingerprint": store.fingerprint(),
    }


def default_fixture() -> list[dict]:
    """Deterministic TEST_ONLY records. Not production memory."""
    t0 = "2026-08-20T10:00:00+00:00"
    t1 = "2026-08-20T10:01:00+00:00"
    future = "2026-08-21T10:00:00+00:00"
    rows = []
    for i in range(1, 9):
        rows.append({
            "id": f"mem_a_{i:02d}",
            "kind": "experiment" if i % 2 else "hypothesis",
            "task_id": "tsk_wave1_a",
            "shared": False,
            "resolved": False,
            "occurred_at": t0,
            "recorded_at": t1,
            "text": f"alpha fixture {i} spine",
        })
    rows.append({
        "id": "mem_b_01", "kind": "experiment", "task_id": "tsk_wave1_b",
        "shared": False, "resolved": False, "occurred_at": t0, "recorded_at": t1,
        "text": "bravo private secret-context",
    })
    rows.append({
        "id": "mem_b_02", "kind": "hypothesis", "task_id": "tsk_wave1_b",
        "shared": False, "resolved": False, "occurred_at": t0, "recorded_at": t1,
        "text": "bravo private hypothesis",
    })
    rows.append({
        "id": "mem_shared_01", "kind": "experiment", "task_id": "tsk_wave1_shared",
        "shared": True, "resolved": False, "occurred_at": t0, "recorded_at": t1,
        "text": "shared contract spine",
    })
    rows.append({
        "id": "mem_future_01", "kind": "experiment", "task_id": "tsk_wave1_a",
        "shared": False, "resolved": False, "occurred_at": future, "recorded_at": future,
        "text": "future must not leak",
    })
    return rows


def run_shadow_sample(*, overlay_root: Path | None = None) -> dict[str, Any]:
    """≥10 attributed reads on the fixture. Zero store mutations."""
    guard = WriteGuard()
    store = FixtureStore(default_fixture(), guard)
    fp0 = store.fingerprint()
    dt = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    receipts: list[dict] = []
    leaks: list[str] = []
    readback_fail = 0

    kinds = (
        ["query_experiments"] * 4
        + ["get_pending_hypotheses"] * 3
        + ["search_vault"] * 3
    )
    for i, kind in enumerate(kinds, start=1):
        needle = "spine" if kind == "search_vault" else ""
        out = retrieve(
            store, caller_task="tsk_wave1_a", run_id="run_wave1_a",
            kind=kind, needle=needle, decision_time=dt, shadow=True,
            overlay_root=overlay_root)
        receipts.append(out["receipt"])
        if "mem_b_01" in out["ids"] or "mem_b_02" in out["ids"]:
            leaks.append(f"A_saw_B_on_{kind}_{i}")
        if out["status"] != "ok":
            readback_fail += 1

    # Isolation probe: B must not see A's private records.
    b = retrieve(
        store, caller_task="tsk_wave1_b", run_id="run_wave1_b",
        kind="search_vault", needle="alpha", decision_time=dt, shadow=True,
        overlay_root=overlay_root)
    receipts.append(b["receipt"])
    if any(i.startswith("mem_a_") for i in b["ids"]):
        leaks.append("B_saw_A_private")

    # Unresolved must stay null — never infer from PID/time.
    u = retrieve(
        store, caller_task="", run_id="", kind="query_experiments",
        decision_time=dt, shadow=True, overlay_root=overlay_root)
    receipts.append(u["receipt"])
    fabricated = 0
    for r in receipts:
        src = r.get("task_id_source")
        tid = r.get("task_id")
        if src == "legacy_missing" and tid not in (None, ""):
            fabricated += 1

    # Kill switch: overlay STOP file stops retrieval.
    kill_root = Path(overlay_root) if overlay_root is not None else (
        _ROOT / "06-EVIDENCE" / "WAVE1-ENTRY-PREFLIGHT-2026-08-20" / "_shadow_overlay")
    kill_root.mkdir(parents=True, exist_ok=True)
    stop = kill_root / "STOP-WAVE1-READ"
    stop.write_text("preflight-kill\n", encoding="utf-8")
    k = retrieve(
        store, caller_task="tsk_wave1_a", run_id="run_wave1_a",
        kind="query_experiments", decision_time=dt, shadow=True,
        overlay_root=kill_root)
    stop.unlink(missing_ok=True)
    receipts.append(k["receipt"])
    kill_ok = k["status"] == "killed" and k["ids"] == []

    # Write guard: attempted write must not change fingerprint.
    write_blocked = False
    try:
        store.write({"id": "should_not_land"})
    except RuntimeError:
        write_blocked = True
    fp1 = store.fingerprint()

    # Readback of a known id for task A.
    rb = retrieve(
        store, caller_task="tsk_wave1_a", run_id="run_wave1_a",
        kind="by_id", needle="mem_a_01", decision_time=dt, shadow=True,
        overlay_root=overlay_root)
    receipts.append(rb["receipt"])
    if rb["ids"] != ["mem_a_01"]:
        readback_fail += 1

    attributed_ok = [r for r in receipts if r.get("wave1_status") == "ok"]
    attributed = sum(1 for r in attributed_ok
                     if r.get("attribution_status") == "resolved" and r.get("task_id"))
    n = len(attributed_ok)
    ratio = round(attributed / n, 4) if n else 0.0
    return {
        "schema": "wave1-shadow-sample/1",
        "n": n,
        "n_including_negative_probes": len(receipts),
        "attributed": attributed,
        "ratio": ratio,
        "fabricated_task_ids": fabricated,
        "cross_task_leaks": leaks,
        "readback_failures": readback_fail,
        "memory_mutations": 0 if fp0 == fp1 and store.mutate_unchanged() else 1,
        "fingerprint_before": fp0,
        "fingerprint_after": fp1,
        "write_blocked": write_blocked,
        "write_attempts": store.guard.mutations,
        "kill_switch_ok": kill_ok,
        "kill_probe_status": k["status"],
        "receipts": receipts,
        "wave1_unlocked": False,
        "paid_calls": 0,
    }
