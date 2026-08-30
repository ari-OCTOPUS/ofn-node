#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_v3.py — Cycle-2 Phase-1 DIAGNOSE: where does the memory subsystem hurt NOW?

Post-cycle-1 state: search() hydration is batched. Remaining suspects:
  (a) get(namespace, mkey)      — WHERE on unindexed columns -> full scan? O(n)?
  (b) insert() dedupe check     — WHERE namespace+content_sha256 -> full scan? O(n)?
  (c) search() FTS candidate qry — dominant remaining cost of search, but WAL/bm25-bound.

Evidence gathered:
  1. EXPLAIN QUERY PLAN for each statement (SCAN vs SEARCH — mechanism, exact).
  2. Latency of get()/insert()/search() at n=1k/5k/20k (scaling law — does it grow?).
All sandboxed (own DBs), $0, offline, live tree untouched.
"""
from __future__ import annotations

import io
import random
import statistics
import sys
import time
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
import memory_store as ms  # noqa: E402  (== live code, verified 0-diff vs master 34535ec)

DB = HERE / "dbs"
DB.mkdir(parents=True, exist_ok=True)

_TOPICS = ["painting", "lead", "sydney", "quote", "invoice", "crypto", "mining", "memory",
           "recall", "receipt", "governor", "heartbeat", "verifier", "calibration"]
_NS = ["semantic", "episodic", "self_knowledge"]


def build(n, seed):
    p = DB / f"p3-{seed}-{n}.db"
    for s in ("", "-wal", "-shm"):
        try:
            Path(str(p) + s).unlink()
        except OSError:
            pass
    st = ms.MemoryStore(path=p)
    rnd = random.Random(seed)
    for i in range(n):
        st.insert({"namespace": rnd.choice(_NS), "mkey": f"k-{seed}-{i}",
                   "content": f"{rnd.choice(_TOPICS)} {rnd.choice(_TOPICS)} note n{i} s{seed}",
                   "trust": "GRADED", "salience": round(rnd.random(), 3),
                   "privacy": "scrubbed"})
    return st


def med(fn, iters=300, warmup=20):
    for _ in range(warmup):
        fn()
    xs = []
    for _ in range(iters):
        t = time.perf_counter()
        fn()
        xs.append(time.perf_counter() - t)
    return statistics.median(xs) * 1000.0


def qplan(st):
    print("  -- EXPLAIN QUERY PLAN (mechanism) --")
    plans = {
        "get(ns,mkey)": ("SELECT memory_id FROM memory WHERE namespace=? AND mkey=? "
                         "AND admission_state='ADMITTED' AND (valid_to IS NULL OR valid_to>?) "
                         "ORDER BY created_at DESC, memory_id DESC", ("semantic", "k-1-1", "z")),
        "insert-dedupe": ("SELECT memory_id FROM memory WHERE namespace=? AND content_sha256=? "
                          "AND (mkey IS ? OR mkey=?) AND admission_state IN ('PENDING','ADMITTED') "
                          "AND (valid_to IS NULL OR valid_to>?)", ("semantic", "x", None, None, "z")),
        "search-hydrate(IN)": ("SELECT memory_id FROM memory WHERE memory_id IN (?,?,?) "
                               "AND admission_state='ADMITTED' AND (valid_to IS NULL OR valid_to>?)",
                               ("a", "b", "c", "z")),
    }
    for name, (sql, args) in plans.items():
        rows = st._conn.execute("EXPLAIN QUERY PLAN " + sql, args).fetchall()
        detail = " | ".join(r[3] for r in rows)
        print(f"    {name:<20} -> {detail}")


if __name__ == "__main__":
    print("=" * 74)
    print("Cycle-2 Phase-1 — memory subsystem profile (against LIVE code 34535ec)")
    print("=" * 74)
    first = True
    for n in (1000, 5000, 20000):
        seed = n
        st = build(n, seed)
        if first:
            qplan(st)
            first = False
        rnd = random.Random(99)
        keys = [f"k-{seed}-{rnd.randrange(n)}" for _ in range(64)]
        ki = [0]

        def _k():
            ki[0] = (ki[0] + 1) % len(keys)
            return keys[ki[0]]

        g = med(lambda: st.get("semantic", _k()))
        s = med(lambda: st.search("painting lead", k=5), iters=200)
        ins_i = [0]

        def _ins():
            ins_i[0] += 1
            st.insert({"namespace": "episodic", "mkey": f"ins-{seed}-{ins_i[0]}",
                       "content": f"probe insert {seed} {ins_i[0]}", "trust": "GRADED",
                       "privacy": "scrubbed"})
        ins = med(_ins, iters=150, warmup=10)
        print(f"\n  n={n:<6} get()={g:8.4f}ms   insert()={ins:8.4f}ms   search(k=5)={s:8.4f}ms")
        st.close()
