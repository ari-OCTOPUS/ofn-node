#!/usr/bin/env python3
"""durable_jobs — the fleet-job lifecycle state machine + reaper (fixture-first).

OPT2 contract (megaprompt §0):
  QUEUED -> LEASED(owner, lease_expiry) -> RUNNING(heartbeat<=30s)
    -> PERSISTED(result durable) -> ACKED -> CLOSED(terminal)
  exceptions:
    LEASED with expired lease & no heartbeat -> automatic reclaim -> QUEUED
    RUNNING finished without receipt         -> QUEUED or auditably FAILED
    PERSISTED without ACK                    -> replay w/ idempotency-key
    ACKED/PERSISTED stuck > closure_ttl      -> retry ONCE -> else FAILED CLOSE_UNCONFIRMED
    attempts >= max_receive                  -> DLQ (dead-letter), never a loop
  every transition carries a receipt in an append-only transitions ledger.

DISCIPLINE: default mode is DRY-RUN — computes transitions against a snapshot and
returns them; nothing touches the live bus. --apply writes ONLY to the
transitions ledger + a derived view (never rewrites bus history).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

TERMINAL = {"CLOSED", "FAILED", "DLQ", "REJECTED"}
ALLOWED = {
    "QUEUED":   {"LEASED"},
    "LEASED":   {"RUNNING", "QUEUED", "DLQ"},    # DLQ = receive-exhaustion
    "RUNNING":  {"PERSISTED", "QUEUED", "FAILED", "DLQ"},
    "PERSISTED": {"ACKED", "FAILED", "PERSISTED"},  # PERSISTED->PERSISTED = retry-once marker
    "ACKED":    {"CLOSED"},
    "FAILED":   set(),
    "CLOSED":   set(),
    "DLQ":      set(),
    "REJECTED": set(),
    "UNKNOWN":  {"QUEUED", "FAILED"},            # UNKNOWN must be dispositioned, never parked
}

HEARTBEAT_MAX_S = 30
CLOSURE_TTL_S = 24 * 3600
MAX_RECEIVE = 3


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _ts_of(row: dict) -> float:
    """Best-effort row timestamp (epoch float) from any of the known fields."""
    for k in ("ts", "at", "at_epoch", "updated_at", "lease_expiry"):
        v = row.get(k)
        if isinstance(v, (int, float)) and v > 1_500_000_000:
            return float(v)
    v = row.get("at_utc") or row.get("ts_utc") or ""
    if isinstance(v, str) and v:
        try:
            return time.mktime(time.strptime(v[:19], "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            pass
    return 0.0


def lease_expired(row: dict, now: float) -> bool:
    le = row.get("lease_expiry")
    if isinstance(le, (int, float)) and le > 1_500_000_000:
        return now > le
    # no machine-readable lease: fall back to wall age of the row
    age = now - _ts_of(row)
    return age > CLOSURE_TTL_S


def heartbeat_stale(row: dict, now: float) -> bool:
    hb = row.get("heartbeat_at") or row.get("last_heartbeat")
    if isinstance(hb, (int, float)) and hb > 1_500_000_000:
        return (now - hb) > HEARTBEAT_MAX_S
    return True  # no heartbeat ever observed = stale by contract


def owner_alive(row: dict) -> bool:
    """Read-only proc check for the declared owner pid/host (fixture-injectable)."""
    pid = row.get("owner_pid")
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def evaluate(row: dict, now: float | None = None) -> dict | None:
    """Pure function: which contract transition does this row demand right now?

    Returns a transition dict (with receipt fields) or None if healthy/terminal.
    """
    now = time.time() if now is None else now
    state = row.get("state")
    if state in TERMINAL:
        return None
    attempt = int(row.get("attempt") or 0) + 1

    if state in ("LEASED", "RUNNING"):
        if lease_expired(row, now) or heartbeat_stale(row, now):
            if not owner_alive(row):
                if attempt >= MAX_RECEIVE:
                    return _t(row, "DLQ", "leases expired + no heartbeat + max receives",
                              attempt=attempt)
                return _t(row, "QUEUED", "LEASE_EXPIRED_RECLAIMED", attempt=attempt)
        # owner alive but lease stale -> renew (observed, not enforced here)
        return None

    if state in ("PERSISTED", "ACK_RESULT", "ACKED"):
        stuck_s = now - _ts_of(row)
        if stuck_s > CLOSURE_TTL_S:
            retried = bool(row.get("closure_retry_at"))
            if retried:
                return _t(row, "FAILED", "CLOSE_UNCONFIRMED", attempt=attempt)
            return _t(row, state, "CLOSURE_RETRY_ONCE", attempt=attempt,
                      closure_retry_at=now, replay_key=row.get("idempotency_key"))
        return None

    if state == "UNKNOWN":
        return _t(row, "FAILED", "UNKNOWN_DISPOSITION_REQUIRED", attempt=attempt)

    return None


def _t(row: dict, new_state: str, why: str, **extra) -> dict:
    return {
        "at_utc": now_utc(),
        "job_id": row.get("job_id"),
        "from": row.get("state"),
        "to": new_state,
        "why": why,
        "idempotency_key": row.get("idempotency_key"),
        **extra,
    }


class TransitionsLedger:
    """Append-only, fsynced. Write failure aborts the reaper (no silent loss)."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, t: dict) -> None:
        line = (json.dumps(t, ensure_ascii=False) + "\n").encode("utf-8")
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o640)
        try:
            os.write(fd, line)
            os.fsync(fd)
        finally:
            os.close(fd)


class IdempotencyRegistry:
    """Replay guard: idempotency_key -> final outcome. Exactly-once final effect."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seen: dict[str, str] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                try:
                    d = json.loads(line)
                    self._seen[d["key"]] = d["outcome"]
                except (json.JSONDecodeError, KeyError):
                    continue

    def register(self, key: str, outcome: str) -> bool:
        """Returns True if NEWLY registered; False if replay (already seen)."""
        if key in self._seen:
            return False
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"key": key, "outcome": outcome,
                                "at_utc": now_utc()}) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self._seen[key] = outcome
        return True

    def outcome_of(self, key: str) -> str | None:
        return self._seen.get(key)


def apply_transitions(rows: list[dict], transitions: list[dict]) -> list[dict]:
    """Reconcile a dry-run's transitions into a derived row view (bus untouched).

    This is what the next evaluation round runs against — the reaper never
    re-emits a transition for state it already advanced.
    """
    by_job: dict[str, dict] = {}
    for t in transitions:
        by_job[t["job_id"]] = t
    out = []
    for r in rows:
        t = by_job.get(r.get("job_id"))
        if not t or r.get("state") in TERMINAL:
            out.append(r)
            continue
        r2 = dict(r)
        r2["state"] = t["to"]
        if "attempt" in t:
            r2["attempt"] = t["attempt"]
        for k in ("closure_retry_at",):
            if k in t:
                r2[k] = t[k]
        out.append(r2)
    return out


def latest_rows(bus_rows: list[dict]) -> list[dict]:
    """The bus is append-history: collapse to the newest row per job_id.

    Newest = last occurrence in file order (append-only guarantee).
    """
    by_job: dict[str, dict] = {}
    for r in bus_rows:
        jid = r.get("job_id") or r.get("id")
        if jid:
            by_job[jid] = r
    return list(by_job.values())


def reap(bus_rows: list[dict], ledger: TransitionsLedger | None = None,
         now: float | None = None, apply: bool = False) -> list[dict]:
    """Evaluate every non-terminal job (latest row per job_id); dry-run by default."""
    transitions = []
    for row in latest_rows(bus_rows):
        t = evaluate(row, now)
        if t is None:
            continue
        transitions.append(t)
        if apply and ledger is not None:
            ledger.append(t)
    return transitions


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--bus", default="/home/ari/ofn/state/fleet-jobs/fleet_jobs.jsonl")
    ap.add_argument("--ledger", default="/home/ari/ofn/state/fleet-jobs/transitions.jsonl")
    ap.add_argument("--apply", action="store_true", help="write transitions ledger (never touches bus)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    rows = [json.loads(l) for l in open(args.bus, encoding="utf-8") if l.strip()]
    ts = reap(rows, ledger=TransitionsLedger(args.ledger), apply=args.apply)
    if args.json:
        print(json.dumps({"transitions": ts, "n": len(ts)}, ensure_ascii=False, indent=1))
    else:
        for t in ts:
            print(f"{t['job_id']} {t['from']}->{t['to']} {t['why']}")
        print(f"-- {len(ts)} transition(s), apply={args.apply}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
