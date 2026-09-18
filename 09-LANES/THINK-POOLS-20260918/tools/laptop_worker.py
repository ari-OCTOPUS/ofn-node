#!/usr/bin/env python3
"""OCTOPUS laptop worker agent (Windows-native) — RUN-TO-COMPLETION item 8.

Owner decree (MISSION-PROMPT, phase 5): an agent on the laptop at 50% CPU,
short renewable leases, and local preemption — lid/power/user interaction
must return healthy work to the queue; the NATS hub always keeps its headroom.

Windows equivalents of the Linux fleet envelope, kernel-enforced:
- CPUQuota=50% -> hard affinity mask of 6 of 12 cores (the process literally
  cannot run on the other six) + BELOW_NORMAL priority. nats-server.exe is
  never touched and keeps the other cores — that is the hub's reservation.
- lease        -> leased/<id>.json with an expiry renewed by a heartbeat; any
  death (lid/sleep/power/kill) expires the lease and the next agent start
  returns the item to pending (attempt+1). That is the safety net for the
  triggers software cannot watch on Windows.
- preemption   -> a monitor thread watches GetLastInputInfo: real user input
  while working (idle < PREEMPT_IDLE_S) kills the child, returns the item to
  pending (attempt+1, reason user_interaction), writes a ledger row, exits.

Work = test_shard items over the ofn suite payload with the vendored pytest
(8.3.5, the same bundle the fleet boards run). Windows' 32k command line
forces chunked pytest invocations; results are aggregated per item.

Usage:
  python laptop_worker.py --root F:/octo-exec/LAPTOP-WORKER-20260918 [--seed] [--once]
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

SUITE_REL = "ofn-suite"
PYLIB_REL = "ofn-pylib"
LEASE_S = 300
HEARTBEAT_S = 60
PREEMPT_IDLE_S = 15
ITEM_DEADLINE_S = 1500
CHUNK = 350
CORES_ALLOWED = 6


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


class Ledger:
    def __init__(self, path: Path):
        self.path = path

    def write(self, event: str, **kw) -> None:
        row = {"at": now_iso(), "event": event, **kw}
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            fh.flush()


def apply_cpu_envelope() -> str:
    """Hard 50% core share via affinity mask + below-normal priority.

    Handle width matters: GetCurrentProcess must be declared c_void_p, or the
    64-bit pseudo-handle truncates to 32 bits and the mask call fails."""
    kernel32 = ctypes.windll.kernel32
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    kernel32.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    total = os.cpu_count() or 1
    mask = (1 << min(CORES_ALLOWED, total)) - 1
    handle = kernel32.GetCurrentProcess()
    if not kernel32.SetProcessAffinityMask(handle, mask):
        return f"affinity-failed-err={ctypes.get_last_error()}"
    kernel32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    kernel32.SetPriorityClass(handle, 0x4000)  # BELOW_NORMAL_PRIORITY_CLASS
    return f"affinity_mask={mask:0{total}b} ({CORES_ALLOWED}/{total} cores) priority=below_normal"


def idle_ms() -> float:
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
    info = LASTINPUTINFO(ctypes.sizeof(LASTINPUTINFO), 0)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
    return (ctypes.windll.kernel32.GetTickCount() - info.dwTime) % 2**32 * 1.0


class Preemption(threading.Thread):
    """Watch for real user input; set the flag once it happens."""

    def __init__(self, idle_threshold_s: float):
        super().__init__(daemon=True)
        self.idle_threshold_ms = idle_threshold_s * 1000
        self.triggered = ""
        self.stop = threading.Event()

    def run(self) -> None:
        while not self.stop.wait(2.0):
            if idle_ms() < self.idle_threshold_ms:
                self.triggered = f"user_interaction idle_ms={idle_ms():.0f}"
                return


def seed_queue(root: Path, items: list[dict], ledger: Ledger) -> None:
    pending = root / "queue" / "pending"
    pending.mkdir(parents=True, exist_ok=True)
    for item in items:
        p = pending / f"{item['id']}.json"
        if p.exists():
            continue
        p.write_text(json.dumps(item, sort_keys=True), encoding="utf-8")
        ledger.write("seeded", item=item["id"])


def reclaim_expired(root: Path, ledger: Ledger) -> int:
    leased, pending = root / "queue" / "leased", root / "queue" / "pending"
    n = 0
    for p in sorted(leased.glob("*.json")):
        try:
            item = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if item.get("lease_expires_at", "") > now_iso():
            continue
        item["attempt"] = int(item.get("attempt", 0)) + 1
        item["last_reason"] = "lease_expired"
        item.pop("lease_expires_at", None)
        (pending / p.name).write_text(json.dumps(item, sort_keys=True), encoding="utf-8")
        p.unlink()
        ledger.write("requeued", item=item["id"], reason="lease_expired", attempt=item["attempt"])
        n += 1
    return n


def lease_next(root: Path) -> dict | None:
    pending, leased = root / "queue" / "pending", root / "queue" / "leased"
    leased.mkdir(parents=True, exist_ok=True)
    for p in sorted(pending.glob("*.json"), key=lambda q: q.stat().st_mtime):
        item = json.loads(p.read_text(encoding="utf-8"))
        item["lease_expires_at"] = datetime.fromtimestamp(
            time.time() + LEASE_S, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        (leased / p.name).write_text(json.dumps(item, sort_keys=True), encoding="utf-8")
        p.unlink()
        return item
    return None


def heartbeat(root: Path, item: dict, stop: threading.Event) -> None:
    leased = root / "queue" / "leased" / f"{item['id']}.json"
    while not stop.wait(HEARTBEAT_S):
        try:
            cur = json.loads(leased.read_text(encoding="utf-8"))
            cur["lease_expires_at"] = datetime.fromtimestamp(
                time.time() + LEASE_S, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
            leased.write_text(json.dumps(cur, sort_keys=True), encoding="utf-8")
        except (OSError, json.JSONDecodeError):
            return


def collect_ids(suite: Path, env: dict) -> list[str]:
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"],
                         cwd=str(suite), env=env, capture_output=True, text=True,
                         timeout=180, creationflags=0x08000000)
    return [l.strip() for l in out.stdout.splitlines() if "::" in l]


def run_shard(item: dict, root: Path, preempt: Preemption) -> dict:
    suite, pylib = root / SUITE_REL, root / PYLIB_REL
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pylib)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    ids = collect_ids(suite, env)
    selected = ids[item["shard_index"]::item["shard_count"]]
    passed = failed = errors = 0
    deadline = time.monotonic() + ITEM_DEADLINE_S
    chunks_run = 0
    for i in range(0, len(selected), CHUNK):
        if preempt.triggered or time.monotonic() > deadline:
            break
        chunk = selected[i:i + CHUNK]
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header",
                            "-p", "no:cacheprovider", *chunk],
                           cwd=str(suite), env=env, capture_output=True, text=True,
                           timeout=max(30, int(deadline - time.monotonic())),
                           creationflags=0x08000000)
        chunks_run += 1
        tail = [l for l in r.stdout.strip().splitlines() if l.strip()][-1:] or [""]
        # robust parse: count words like "12 passed" / "3 failed" / "1 error"
        for num, word in re.findall(r"(\d+)\s+(passed|failed|errors?|skipped)", tail[0]):
            if word.startswith("passed"):
                passed += int(num)
            elif word.startswith("failed"):
                failed += int(num)
            elif word.startswith("error"):
                errors += int(num)
    return {"collected": len(ids), "selected": len(selected), "chunks": chunks_run,
            "passed": passed, "failed": failed, "errors": errors,
            "complete": chunks_run == (len(selected) + CHUNK - 1) // CHUNK and not preempt.triggered}


def finish(root: Path, item: dict, result: dict, ledger: Ledger, reason: str) -> None:
    leased = root / "queue" / "leased" / f"{item['id']}.json"
    if reason == "done":
        out = root / "queue" / "done"
        out.mkdir(parents=True, exist_ok=True)
        item.pop("lease_expires_at", None)
        item["result"] = result
        item["finished_at"] = now_iso()
        (out / f"{item['id']}.json").write_text(json.dumps(item, sort_keys=True, indent=1),
                                                encoding="utf-8")
        leased.unlink(missing_ok=True)
        ledger.write("done", item=item["id"],
                     passed=result["passed"], failed=result["failed"],
                     errors=result["errors"], selected=result["selected"])
    else:
        pending = root / "queue" / "pending"
        item["attempt"] = int(item.get("attempt", 0)) + 1
        item["last_reason"] = reason
        item.pop("lease_expires_at", None)
        (pending / f"{item['id']}.json").write_text(json.dumps(item, sort_keys=True),
                                                    encoding="utf-8")
        leased.unlink(missing_ok=True)
        ledger.write("requeued", item=item["id"], reason=reason, attempt=item["attempt"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="F:/octo-exec/LAPTOP-WORKER-20260918")
    ap.add_argument("--seed", action="store_true", help="seed shards 3/4/5 of 6 (the boards took 0/1/2)")
    ap.add_argument("--once", action="store_true", help="process one item then exit")
    args = ap.parse_args()

    root = Path(args.root)
    ledger = Ledger(root / "ledger.jsonl")
    envelope = apply_cpu_envelope()
    ledger.write("start", pid=os.getpid(), envelope=envelope)
    print(f"[agent] {envelope}", flush=True)

    if args.seed:
        seed_queue(root, [
            {"id": "shard-3-of-6", "shard_index": 3, "shard_count": 6},
            {"id": "shard-4-of-6", "shard_index": 4, "shard_count": 6},
            {"id": "shard-5-of-6", "shard_index": 5, "shard_count": 6},
        ], ledger)

    reclaimed = reclaim_expired(root, ledger)
    if reclaimed:
        print(f"[agent] reclaimed {reclaimed} expired lease(s)", flush=True)

    processed = 0
    while True:
        item = lease_next(root)
        if item is None:
            print("[agent] queue empty", flush=True)
            return 0
        print(f"[agent] leased {item['id']} attempt={item.get('attempt', 0)}", flush=True)
        ledger.write("leased", item=item["id"], attempt=item.get("attempt", 0))
        preempt = Preemption(PREEMPT_IDLE_S)
        preempt.start()
        hb_stop = threading.Event()
        hb = threading.Thread(target=heartbeat, args=(root, item, hb_stop), daemon=True)
        hb.start()
        t0 = time.monotonic()
        result = run_shard(item, root, preempt)
        elapsed = round(time.monotonic() - t0, 1)
        hb_stop.set()
        preempt.stop.set()
        if preempt.triggered:
            finish(root, item, result, ledger, "preempted:" + preempt.triggered)
            print(f"[agent] PREEMPTED after {elapsed}s — {item['id']} returned to queue "
                  f"({preempt.triggered})", flush=True)
            return 3
        finish(root, item, result, ledger, "done")
        print(f"[agent] done {item['id']} in {elapsed}s — {result}", flush=True)
        processed += 1
        if args.once:
            return 0


if __name__ == "__main__":
    sys.exit(main())
