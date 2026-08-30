#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_search.py — C6 Phase-1 DIAGNOSE: where does MemoryStore.search() spend time?

Decomposes one search into: (A) FTS5 candidate query, (B) the N+1 per-candidate
hydration loop as written in memory_store.search, (C) a single batched IN(...) hydration
over the SAME candidates. Proves empirically whether the N+1 loop is the bottleneck.
Read-only w.r.t. the live organism; all DBs are in the sandbox.
"""
from __future__ import annotations

import io
import re
import sqlite3
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):   # Windows cp1252 console → force UTF-8
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_common as bc  # noqa: E402
import memory_store as ms  # noqa: E402

_COLS = ms._COLS
_NOW = ms._utc_now_iso


def _candidates(conn, query, k=5):
    """Replicate memory_store.search's candidate step (FTS5 path)."""
    terms = [t for t in re.findall(r"[^\W_]{3,}", query, re.UNICODE)][:12]
    fts_q = " OR ".join(terms) if terms else ""
    if not fts_q:
        return []
    rows = conn.execute(
        "SELECT memory_id, bm25(memory_fts) AS score FROM memory_fts "
        "WHERE memory_fts MATCH ? ORDER BY score LIMIT ?", (fts_q, max(k * 4, 20))).fetchall()
    return [(r[0], r[1]) for r in rows]


def _hydrate_n1(conn, ids):
    """Exactly memory_store.search's per-candidate loop (N+1)."""
    now = _NOW()
    out = []
    for mid, score in ids:
        r = conn.execute("SELECT " + ",".join(_COLS) + " FROM memory WHERE memory_id=? "
                         "AND (valid_to IS NULL OR valid_to>?)", (mid, now)).fetchone()
        if r:
            out.append(r)
    return out


def _hydrate_batched(conn, ids):
    """Single batched hydration over the same candidate ids (the proposed fix)."""
    now = _NOW()
    if not ids:
        return []
    mids = [m for m, _ in ids]
    ph = ",".join("?" * len(mids))
    rows = conn.execute(
        "SELECT " + ",".join(_COLS) + " FROM memory WHERE memory_id IN (" + ph + ") "
        "AND (valid_to IS NULL OR valid_to>?)", (*mids, now)).fetchall()
    return rows


def run(sizes=(1000, 5000), iters=400):
    print("=" * 70)
    print("C6 Phase-1 PROFILE — MemoryStore.search() cost decomposition")
    print("iters/measure:", iters)
    print("=" * 70)
    for n in sizes:
        store = bc.fresh_store(f"profile-{n}")
        got = bc.make_corpus(store, n, seed=n)
        conn = store._conn
        m = store.metrics()
        queries = bc.make_queries(seed=n, m=64)
        # candidate count per query (the N+1 multiplier)
        cand_counts = [len(_candidates(conn, q)) for q in queries]
        avg_cand = sum(cand_counts) / max(1, len(cand_counts))
        qi = {"i": 0}

        def _q():
            qi["i"] = (qi["i"] + 1) % len(queries)
            return queries[qi["i"]]

        full = bc.timed(lambda: store.search(_q(), k=5), iters=iters)
        cand_only = bc.timed(lambda: _candidates(conn, _q()), iters=iters)

        # hydrate steps operate on a fixed representative candidate set
        rep = _candidates(conn, queries[0])
        hyd_n1 = bc.timed(lambda: _hydrate_n1(conn, rep), iters=iters)
        hyd_bat = bc.timed(lambda: _hydrate_batched(conn, rep), iters=iters)

        print(f"\ncorpus n={n}  active={m['active']}  fts={m['fts']}  "
              f"avg_candidates/query={avg_cand:.1f}")
        print(f"  full search()          median={full['median_ms']:.4f}ms  p95={full['p95_ms']:.4f}ms")
        print(f"  (A) FTS candidate qry  median={cand_only['median_ms']:.4f}ms")
        print(f"  (B) N+1 hydration loop median={hyd_n1['median_ms']:.4f}ms  "
              f"(over {len(rep)} candidates)")
        print(f"  (C) batched hydration  median={hyd_bat['median_ms']:.4f}ms  "
              f"(same {len(rep)} candidates)")
        if hyd_bat["median_ms"] > 0:
            print(f"  hydration speedup (B/C)= {hyd_n1['median_ms']/hyd_bat['median_ms']:.2f}x")
        share = 100.0 * hyd_n1["median_ms"] / full["median_ms"] if full["median_ms"] else 0
        print(f"  N+1 hydration share of full search ≈ {share:.0f}%")
        store.close()


if __name__ == "__main__":
    run()
