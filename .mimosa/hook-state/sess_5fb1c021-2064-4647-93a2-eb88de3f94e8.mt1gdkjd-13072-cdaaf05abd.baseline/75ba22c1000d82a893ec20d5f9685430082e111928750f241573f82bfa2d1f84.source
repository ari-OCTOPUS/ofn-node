#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""experiment_v3.py — Cycle-2 Phase-2: secondary indexes for get()/insert-dedupe.

Patch: two additive, idempotent CREATE INDEX IF NOT EXISTS in __init__
  idx_memory_ns_mkey (namespace, mkey, created_at DESC)  -> serves get()'s WHERE+ORDER BY
  idx_memory_ns_sha  (namespace, content_sha256)         -> serves insert()'s dedupe check
Access-path only: explicit ORDER BY already fixes result order, so outputs must be
byte-identical. Existing live DBs gain the indexes on next open (one-time build, measured).

Gates:
  A. byte-identical: get()/search() results and insert() return values identical across a
     mixed ADMITTED/PENDING/RETRACTED corpus (incl. supersede + dedupe paths).
  B. governance: PENDING/RETRACTED never visible from get()/search() in either version.
  C. mechanism: EXPLAIN QUERY PLAN flips SCAN->SEARCH for get + dedupe.
  D. latency: symmetric paired (same op both variants, lead alternated, GC off).
  E. migration cost: one-time CREATE INDEX on a pre-existing 20k-row DB, measured.
"""
from __future__ import annotations

import difflib
import gc
import io
import json
import random
import shutil
import statistics
import sys
import time
import types
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

HERE = Path(__file__).resolve().parent
WT = HERE.parent.parent
for _p in (str(WT / "_ops" / "memory"), str(WT / "_ops" / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import os
os.environ["OCTOPUS_STATE_DIR"] = str(HERE / "state")

SRC = (WT / "_ops" / "memory" / "memory_store.py").read_text("utf-8").replace("\r\n", "\n")

_ANCHOR = (
    '                self._conn.execute(\n'
    '                    "ALTER TABLE memory ADD COLUMN admission_state TEXT NOT NULL DEFAULT \'ADMITTED\'")\n'
    '            try:\n'
)
_REPL = (
    '                self._conn.execute(\n'
    '                    "ALTER TABLE memory ADD COLUMN admission_state TEXT NOT NULL DEFAULT \'ADMITTED\'")\n'
    '            # C6 evolution_v3: secondary indexes — get() and the insert() dedupe check were\n'
    '            # full-table SCANs (O(n); ~6.7ms/7.5ms at 20k rows). Additive + idempotent,\n'
    '            # access-path only: explicit ORDER BY already fixes result order, so outputs are\n'
    '            # byte-identical. Existing DBs gain the indexes on next open (one-time build).\n'
    '            self._conn.execute(\n'
    '                "CREATE INDEX IF NOT EXISTS idx_memory_ns_mkey "\n'
    '                "ON memory(namespace, mkey, created_at DESC)")\n'
    '            self._conn.execute(\n'
    '                "CREATE INDEX IF NOT EXISTS idx_memory_ns_sha "\n'
    '                "ON memory(namespace, content_sha256)")\n'
    '            try:\n'
)
assert SRC.count(_ANCHOR) == 1, f"anchor count={SRC.count(_ANCHOR)}"
PATCHED_SRC = SRC.replace(_ANCHOR, _REPL)


def _load(src, name):
    mod = types.ModuleType(name)
    mod.__dict__["__file__"] = str(HERE / f"{name}.py")
    exec(compile(src, f"{name}.py", "exec"), mod.__dict__)
    return mod


BASE = _load(SRC, "ms_v3_base")
PATCHED = _load(PATCHED_SRC, "ms_v3_indexed")

DBD = HERE / "dbs"
DBD.mkdir(parents=True, exist_ok=True)
_TOPICS = ["painting", "lead", "sydney", "quote", "invoice", "crypto", "mining", "memory",
           "recall", "receipt", "governor", "heartbeat", "verifier", "calibration", "admission"]
_NS = ["semantic", "episodic", "self_knowledge"]


def fresh(tag):
    p = DBD / f"{tag}.db"
    for s in ("", "-wal", "-shm"):
        try:
            Path(str(p) + s).unlink()
        except OSError:
            pass
    return p


def seed_corpus(store, n, seed):
    """Mixed-state corpus incl. dedupe-duplicates and supersede chains. Returns log of
    (op, args, ret) so both variants can be replay-compared."""
    rnd = random.Random(seed)
    log = []
    for i in range(n):
        rec = {"namespace": rnd.choice(_NS), "mkey": f"k-{seed}-{i}",
               "content": f"{rnd.choice(_TOPICS)} {rnd.choice(_TOPICS)} note n{i} s{seed}",
               "trust": "GRADED", "salience": round(rnd.random(), 3), "privacy": "scrubbed",
               "created_at": f"2026-07-{1 + (i % 22):02d}T00:{i % 60:02d}:00Z"}
        roll = rnd.random()
        if roll < 0.12:
            rec["admission_state"] = "PENDING"
        mid = store.insert(dict(rec))
        log.append(("insert", rec["mkey"], mid is not None))
        if mid and roll >= 0.88:
            ok = store.set_admission_state(mid, "RETRACTED")
            log.append(("retract", rec["mkey"], ok))
        if mid and 0.5 < roll < 0.55:   # exact-duplicate insert -> dedupe must skip
            dup = store.insert(dict(rec))
            log.append(("dup-insert", rec["mkey"], dup is None))
        if mid and 0.55 <= roll < 0.60:  # supersede chain
            rec2 = dict(rec)
            rec2["content"] = rec["content"] + " v2"
            rec2["supersedes"] = mid
            m2 = store.insert(rec2)
            log.append(("supersede", rec["mkey"], m2 is not None))
    return log


def _gsig(d):
    return None if d is None else (d["memory_id"], d["content"], d["trust"], d["admission_state"])


def _ssig(rows):
    return [(r["memory_id"], round(float(r["_rank"]), 9)) for r in rows]


def correctness(n=4000, seed=777):
    db_b, db_p = fresh(f"corr-b-{seed}"), fresh(f"corr-p-{seed}")
    sb = BASE.MemoryStore(path=db_b)
    sp = PATCHED.MemoryStore(path=db_p)
    log_b = seed_corpus(sb, n, seed)
    log_p = seed_corpus(sp, n, seed)
    ops_equal = log_b == log_p
    rnd = random.Random(3)
    checks = mism = 0
    leak = 0
    queries = [" ".join(rnd.choice(_TOPICS) for _ in range(rnd.randint(1, 2))) for _ in range(30)]
    keys = [f"k-{seed}-{rnd.randrange(n)}" for _ in range(200)] + ["nope", None and "x" or "k-0-0"]
    for kkey in keys:
        for ns in _NS + [None and "x" or "semantic"]:
            for mt in (None, "GRADED", "OWNER_CONFIRMED"):
                checks += 1
                a = _gsig(sb.get(ns, kkey, min_trust=mt))
                b = _gsig(sp.get(ns, kkey, min_trust=mt))
                if a != b:
                    mism += 1
                if a and a[3] != "ADMITTED":
                    leak += 1
                if b and b[3] != "ADMITTED":
                    leak += 1
    for q in queries:
        for k in (1, 5, 20):
            for ns in (None, "semantic"):
                checks += 1
                ra = sb.search(q, namespace=ns, k=k)
                rb = sp.search(q, namespace=ns, k=k)
                if _ssig(ra) != _ssig(rb):
                    mism += 1
                for r in ra + rb:
                    if r["admission_state"] != "ADMITTED":
                        leak += 1
    mb, mp = sb.metrics(), sp.metrics()
    sb.close(); sp.close()
    return {"replay_ops_equal": ops_equal, "checks": checks, "mismatches": mism,
            "admission_leaks": leak, "metrics_equal": mb == mp, "metrics": mb}


def mechanism():
    db = fresh("mech")
    sp = PATCHED.MemoryStore(path=db)
    seed_corpus(sp, 500, 5)
    out = {}
    for name, sql, args in [
        ("get", "SELECT memory_id FROM memory WHERE namespace=? AND mkey=? "
                "AND admission_state='ADMITTED' AND (valid_to IS NULL OR valid_to>?) "
                "ORDER BY created_at DESC, memory_id DESC", ("semantic", "k", "z")),
        ("dedupe", "SELECT memory_id FROM memory WHERE namespace=? AND content_sha256=? "
                   "AND (mkey IS ? OR mkey=?) AND admission_state IN ('PENDING','ADMITTED') "
                   "AND (valid_to IS NULL OR valid_to>?)", ("semantic", "x", None, None, "z"))]:
        rows = sp._conn.execute("EXPLAIN QUERY PLAN " + sql, args).fetchall()
        out[name] = " | ".join(r[3] for r in rows)
    sp.close()
    return out


def paired_latency(n, seed, iters=800):
    db_b, db_p = fresh(f"lat-b-{seed}-{n}"), fresh(f"lat-p-{seed}-{n}")
    sb = BASE.MemoryStore(path=db_b)
    sp = PATCHED.MemoryStore(path=db_p)
    seed_corpus(sb, n, seed); seed_corpus(sp, n, seed)
    rnd = random.Random(9)
    keys = [f"k-{seed}-{rnd.randrange(n)}" for _ in range(64)]
    ki = [0]

    def _k():
        ki[0] = (ki[0] + 1) % len(keys)
        return keys[ki[0]]
    for _ in range(50):
        sb.get("semantic", _k()); sp.get("semantic", _k())
    bs, ps = [], []
    ii = [0]

    def ins(st, tag):
        ii[0] += 1
        st.insert({"namespace": "episodic", "mkey": f"L{tag}-{ii[0]}",
                   "content": f"latprobe {tag} {ii[0]}", "trust": "GRADED", "privacy": "scrubbed"})
    ib, ip = [], []
    lead = True
    gc.collect(); gc.disable()
    try:
        for _ in range(iters):
            kk = _k()
            if lead:
                t = time.perf_counter(); sb.get("semantic", kk); bs.append(time.perf_counter() - t)
                t = time.perf_counter(); sp.get("semantic", kk); ps.append(time.perf_counter() - t)
                t = time.perf_counter(); ins(sb, "b"); ib.append(time.perf_counter() - t)
                t = time.perf_counter(); ins(sp, "p"); ip.append(time.perf_counter() - t)
            else:
                t = time.perf_counter(); sp.get("semantic", kk); ps.append(time.perf_counter() - t)
                t = time.perf_counter(); sb.get("semantic", kk); bs.append(time.perf_counter() - t)
                t = time.perf_counter(); ins(sp, "p"); ip.append(time.perf_counter() - t)
                t = time.perf_counter(); ins(sb, "b"); ib.append(time.perf_counter() - t)
            lead = not lead
    finally:
        gc.enable()
    sb.close(); sp.close()

    def m(x):
        return statistics.median(x) * 1000.0
    return {"n": n, "get_base_ms": round(m(bs), 4), "get_idx_ms": round(m(ps), 4),
            "get_speedup": round(m(bs) / m(ps), 1),
            "ins_base_ms": round(m(ib), 4), "ins_idx_ms": round(m(ip), 4),
            "ins_speedup": round(m(ib) / m(ip), 1)}


def migration_cost():
    """One-time cost of opening an EXISTING 20k-row baseline DB with the patched class."""
    db = fresh("mig-20k")
    sb = BASE.MemoryStore(path=db)
    seed_corpus(sb, 20000, 11)
    sb.close()
    t = time.perf_counter()
    sp = PATCHED.MemoryStore(path=db)          # builds both indexes here
    build_ms = (time.perf_counter() - t) * 1000.0
    idx = [r[0] for r in sp._conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_memory%'").fetchall()]
    t = time.perf_counter()
    sp2 = PATCHED.MemoryStore(path=db)         # idempotent reopen
    reopen_ms = (time.perf_counter() - t) * 1000.0
    sp.close(); sp2.close()
    return {"first_open_build_ms": round(build_ms, 1), "reopen_ms": round(reopen_ms, 1),
            "indexes": idx}


if __name__ == "__main__":
    (HERE / "memory_store_v3_indexed.py").write_text(PATCHED_SRC, "utf-8", newline="\n")
    diff = "".join(difflib.unified_diff(
        SRC.splitlines(keepends=True), PATCHED_SRC.splitlines(keepends=True),
        fromfile="a/_ops/memory/memory_store.py", tofile="b/_ops/memory/memory_store.py"))
    (HERE / "proposed_v3.patch").write_text(diff, "utf-8", newline="\n")
    add = sum(1 for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    rem = sum(1 for l in diff.splitlines() if l.startswith("-") and not l.startswith("---"))
    print(f"patch: +{add}/-{rem} lines, __init__ only\n")

    print("[C] mechanism (patched query plans):")
    for k, v in mechanism().items():
        print(f"    {k:<8} -> {v}")

    print("\n[A/B] correctness + governance (mixed-state corpus, replayed on both):")
    c = correctness()
    print(f"    replay_ops_equal={c['replay_ops_equal']}  checks={c['checks']}  "
          f"mismatches={c['mismatches']}  admission_leaks={c['admission_leaks']}  "
          f"metrics_equal={c['metrics_equal']}")

    print("\n[D] latency (symmetric paired, GC off):")
    lat = [paired_latency(n, s) for n, s in [(1000, 1), (5000, 2), (20000, 3)]]
    for r in lat:
        print(f"    n={r['n']:<6} get {r['get_base_ms']:8.4f} -> {r['get_idx_ms']:8.4f} ms "
              f"({r['get_speedup']}x)   insert {r['ins_base_ms']:8.4f} -> {r['ins_idx_ms']:8.4f} ms "
              f"({r['ins_speedup']}x)")

    print("\n[E] migration cost (existing 20k DB):")
    mig = migration_cost()
    print(f"    first open (index build): {mig['first_open_build_ms']}ms   "
          f"reopen: {mig['reopen_ms']}ms   indexes={mig['indexes']}")

    res = {"schema": "c6-evolution-v3-result", "patch": {"added": add, "removed": rem},
           "mechanism": mechanism(), "correctness": c, "latency": lat, "migration": mig}
    (HERE / "result_v3.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
    print("\nwrote result_v3.json")
