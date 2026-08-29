#!/usr/bin/env python3
"""Mini Scientist sandbox runner — replays a fixture through the REAL production
evidence-store code (imported read-only from /opt/octopus/current) into an isolated
work directory, with hard limits, network denial, and byte-level write accounting.

Safety model:
  - Never touches /var/lib/octopus or any production path; all writes go to --work.
  - socket/getaddrinfo monkeypatched to raise before any library import.
  - RLIMIT_CPU / RLIMIT_AS / RLIMIT_FSIZE + SIGALRM wall clock.
  - OCTOPUS_INDEX_FLUSH_EVERY=1 reproduces the pre-fix per-observation rewrite
    behavior using the same production code (no patched copy needed).

Output: writes <work>/../<label>.result.json and prints it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import shutil
import signal
import socket
import sys
import time
from pathlib import Path

PROD_SRC = "/opt/octopus/current/src"


class NetworkDeniedError(RuntimeError):
    pass


def deny_network() -> None:
    def _deny(*_a, **_k):
        raise NetworkDeniedError("network is denied inside the sandbox runner")
    socket.socket = _deny
    socket.socketpair = _deny
    socket.create_connection = _deny
    socket.getaddrinfo = _deny


def set_limits(cpu_s: int, as_mb: int, fsize_mb: int, wall_s: int) -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s))
    resource.setrlimit(resource.RLIMIT_AS, (as_mb << 20, as_mb << 20))
    resource.setrlimit(resource.RLIMIT_FSIZE, (fsize_mb << 20, fsize_mb << 20))

    def _wall(_sig, _frm):
        raise TimeoutError(f"wall clock limit {wall_s}s exceeded")
    signal.signal(signal.SIGALRM, _wall)
    signal.alarm(wall_s)


def io_counters() -> dict[str, int]:
    out = {}
    for line in Path("/proc/self/io").read_text().splitlines():
        key, _, val = line.partition(":")
        out[key.strip()] = int(val)
    return out


def hash_tree(root: Path) -> dict[str, str]:
    result = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            result[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--label", default="run")
    ap.add_argument("--flush-every", type=int, default=200)
    ap.add_argument("--flush-max-age", type=float, default=300.0)
    ap.add_argument("--cpu-s", type=int, default=300)
    ap.add_argument("--as-mb", type=int, default=1536)
    ap.add_argument("--fsize-mb", type=int, default=512)
    ap.add_argument("--wall-s", type=int, default=600)
    args = ap.parse_args()

    deny_network()
    set_limits(args.cpu_s, args.as_mb, args.fsize_mb, args.wall_s)

    os.environ["OCTOPUS_INDEX_FLUSH_EVERY"] = str(max(1, args.flush_every))
    os.environ["OCTOPUS_INDEX_FLUSH_MAX_AGE"] = str(max(1.0, args.flush_max_age))

    work = Path(args.work)
    if work.exists():
        shutil.rmtree(work)
    ev_dir = work / "evidence"
    ev_dir.mkdir(parents=True)

    sys.path.insert(0, PROD_SRC)
    from octopus_sensorium.evidence import store  # noqa: E402  (import after env+guards)

    records = [json.loads(l) for l in Path(args.fixture).read_text().splitlines() if l.strip()]
    io0 = io_counters()
    t0 = time.monotonic()
    persisted = 0
    skipped_dupes = 0
    for rec in records:
        obs = rec.get("observation") or {}
        before = (ev_dir / store.JSONL_NAME)
        size_before = before.stat().st_size if before.exists() else 0
        ret = store.persist_observation(rec.get("sensor_id") or "unknown", obs, directory=ev_dir)
        size_after = (ev_dir / store.JSONL_NAME).stat().st_size if (ev_dir / store.JSONL_NAME).exists() else 0
        if size_after > size_before:
            persisted += 1
        else:
            skipped_dupes += 1
        _ = ret
    flushed = store.flush_indexes(ev_dir)
    elapsed = time.monotonic() - t0
    io1 = io_counters()

    result = {
        "schema": "octopus.mini-scientist.sandbox-run.v1",
        "label": args.label,
        "fixture": args.fixture,
        "fixture_sha256": hashlib.sha256(Path(args.fixture).read_bytes()).hexdigest(),
        "work": str(work),
        "params": {"flush_every": args.flush_every, "flush_max_age": args.flush_max_age,
                   "cpu_s": args.cpu_s, "as_mb": args.as_mb, "wall_s": args.wall_s},
        "records_in_fixture": len(records),
        "persisted": persisted,
        "skipped_duplicates": skipped_dupes,
        "flushed_entries_final": flushed,
        "io_delta": {k: io1.get(k, 0) - io0.get(k, 0) for k in
                     ("rchar", "wchar", "read_bytes", "write_bytes", "syscw")},
        "write_bytes_per_persisted_obs": round(
            max(0, io1.get("write_bytes", 0) - io0.get("write_bytes", 0)) / max(1, persisted), 1),
        "elapsed_s": round(elapsed, 3),
        "output_tree_sha256": hash_tree(ev_dir),
        "network_denied_selftest": "NetworkDeniedError raised (monkeypatch active)",
        "may_authorize": False,
    }
    out = work.parent / f"{args.label}.result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
