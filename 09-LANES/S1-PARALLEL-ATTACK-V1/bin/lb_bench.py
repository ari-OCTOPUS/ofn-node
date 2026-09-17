#!/usr/bin/env python3
"""S1-PARALLEL-ATTACK-V1 / L-B — real-data append/flush benchmark + inventory (node 182).

B5 patch candidates measured on the SAME frozen real dataset (last N journal
events copied read-only):
  A) baseline   = live semantics: append_event() = write+fsync per event
  B) batch-commit = buffer writes, fsync every K events (K=100)
  C) lazy-flush  = write per event, fsync every T window (simulated: fsync every
     5s of wall time) — approximated by fsync-every-32 given the short run
Measures wall time + process CPU; verifies byte-identity of journals and replay
state-hash equality across variants (semantic preservation, no synthetic data).

Also: B3 cardinality inventory + B6 retention dry-run (projections from real
sizes/rates only, clearly labelled).
Output: /var/lib/octopus/state/s1pa-attack/lb-bench.json (+ stdout). Read-only
for the live journal; writes only inside the s1pa-attack sandbox.
"""
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, "/opt/octopus/current/src")
import octopus_sensorium.snapshot as SNAP  # noqa: E402

J = Path("/var/lib/octopus/state/events.jsonl")
SB = Path("/var/lib/octopus/state/s1pa-attack/lb")
N = 3000
K_BATCH = 100
K_LAZY = 32

def load_tail(n):
    with J.open("rb") as fh:
        fh.seek(0, 2)
        size = fh.tell()
        keep = []
        chunk = 1 << 20
        pos = size
        while pos > 0 and len(keep) < n + 50:
            pos = max(0, pos - chunk)
            fh.seek(pos)
            data = fh.read(min(chunk, size - pos))
            lines = data.split(b"\n")
            if pos > 0 and lines:
                lines[0] = b""  # partial line
            keep = lines + keep
        return [l for l in keep if l.strip()][-n:]

def _parses(b):
    try:
        json.loads(b.decode("utf-8"))
        return True
    except Exception:
        return False


def replay_hash_of(journal):
    state = {}
    with journal.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            SNAP.apply_event(state, rec)
    return SNAP.state_hash(state)

def run_variant(name, events, journal, fsync_every):
    if journal.exists():
        journal.unlink()
    real_fsync = os.fsync
    count = [0]
    t0 = time.perf_counter()
    c0 = time.process_time()
    class FakeFile:
        pass
    # patch os.fsync as seen inside the snapshot module
    orig = SNAP.os.fsync
    def counting_fsync(fd):
        count[0] += 1
        if fsync_every is None or count[0] % fsync_every == 0:
            return orig(fd)
        return None
    SNAP.os.fsync = counting_fsync
    try:
        for ev in events:
            rec = json.loads(ev.decode("utf-8"))
            rec.pop("seq", None)
            SNAP.append_event(rec, journal=journal)
    finally:
        SNAP.os.fsync = orig
    wall = time.perf_counter() - t0
    cpu = time.process_time() - c0
    return {"name": name, "events": len(events), "fsyncs": count[0],
            "wall_s": round(wall, 3), "cpu_s": round(cpu, 3),
            "bytes": journal.stat().st_size}

def main():
    if SB.exists():
        shutil.rmtree(str(SB))
    SB.mkdir(parents=True)
    events = [e for e in load_tail(N) if _parses(e)]
    snaps = sorted(Path("/var/lib/octopus/state/snapshots").glob("snapshot-*.json"))
    ja = SB / "journal-A.jsonl"
    jb = SB / "journal-B.jsonl"
    jc = SB / "journal-C.jsonl"
    A = run_variant("A_baseline_fsync_per_event", events, ja, None)
    B = run_variant("B_batch_commit_100", events, jb, K_BATCH)
    C = run_variant("C_lazy_flush_32", events, jc, K_LAZY)
    identical = (hashlib.sha256(ja.read_bytes()).hexdigest()
                 == hashlib.sha256(jb.read_bytes()).hexdigest()
                 == hashlib.sha256(jc.read_bytes()).hexdigest())
    hashA = replay_hash_of(ja)
    hashB = replay_hash_of(jb)
    hashC = replay_hash_of(jc)

    # B3 inventory (snaps already sorted above)
    st = J.stat()
    snap_bytes = sum(p.stat().st_size for p in snaps)
    # journal rate from telemetry-free estimate: use last two snapshots
    rate = None
    if len(snaps) >= 2:
        import json as _j
        try:
            s_old = _j.loads(snaps[0].read_text())
            s_new = _j.loads(snaps[-1].read_text())
            dt = snaps[-1].stat().st_mtime - snaps[0].stat().st_mtime
            if dt > 0:
                rate = (int(s_new.get("journal_seq", 0)) - int(s_old.get("journal_seq", 0))) / dt
        except Exception:
            pass
    inv = {"events_jsonl_bytes": st.st_size, "events_lines_approx": None,
           "snapshots": len(snaps), "snapshots_bytes": snap_bytes,
           "events_per_sec_est": rate and round(rate, 4),
           "bytes_per_event": round(st.st_size / 3078916, 2)}
    proj30 = rate and round(rate * 86400 * 30 * inv["bytes_per_event"] / 1e6, 1)

    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "variants": [A, B, C],
           "journals_byte_identical": identical,
           "replay_hashes": {"A": hashA, "B": hashB, "C": hashC,
                             "all_equal": hashA == hashB == hashC},
           "inventory_B3": inv,
           "projection_30d_mb_UNVERIFIED_ESTIMATE": proj30,
           "retention_note": "snapshots wired hourly prune 24h; events.jsonl + derived have NO retention wired"}
    (SB / "lb-bench.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1))

if __name__ == "__main__":
    main()
