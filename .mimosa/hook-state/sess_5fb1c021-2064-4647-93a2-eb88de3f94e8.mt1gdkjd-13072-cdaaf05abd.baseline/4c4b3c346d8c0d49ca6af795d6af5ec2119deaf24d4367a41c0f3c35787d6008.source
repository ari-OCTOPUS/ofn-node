#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_common.py — C6 evolution_v1 sandbox: deterministic corpus + timing helpers.

Isolation: imports the REAL MemoryStore from the worktree under test, but every DB
lives under this sandbox dir. Zero external effect, zero network, $0, offline.
Deterministic: fixed RNG seed → same corpus every run (reproducible evidence).
"""
from __future__ import annotations

import os
import random
import statistics
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_WT = _HERE.parent.parent                      # <worktree>
for _p in (str(_WT / "_ops" / "memory"), str(_WT / "_ops" / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# sandbox all state under this dir — NEVER the live organism state
os.environ["OCTOPUS_STATE_DIR"] = str(_HERE / "state")

import memory_store as ms  # noqa: E402  (real code under test)

SANDBOX = _HERE
DB_DIR = _HERE / "dbs"
DB_DIR.mkdir(parents=True, exist_ok=True)

# a small controlled vocabulary so FTS5 has real terms to match on
_TOPICS = ["painting", "lead", "sydney", "quote", "invoice", "crypto", "mining", "rig",
           "ziman", "gallery", "onlyfans", "hypnosis", "budget", "telegram", "octopus",
           "memory", "recall", "latency", "receipt", "outcome", "governor", "heartbeat",
           "sandbox", "verifier", "hypothesis", "calibration", "throughput", "pipeline"]
_VERBS = ["improves", "reduces", "blocks", "raises", "measures", "cites", "scores",
          "routes", "gates", "verifies", "quarantines", "accepts", "rejects", "profiles"]
_NOUNS = ["decision", "acceptance", "cost", "risk", "signal", "candidate", "baseline",
          "corpus", "query", "index", "token", "spend", "margin", "session", "note"]
_NS = ["semantic", "episodic", "self_knowledge"]   # namespaces the gate auto/advisory-commits


def make_corpus(store: "ms.MemoryStore", n: int, seed: int) -> int:
    """Insert n deterministic memories directly via store.insert (bypasses the write
    gate on purpose — we are benchmarking the READ path, not admission). Returns count
    actually inserted (dedupe may drop exact-duplicate content)."""
    rnd = random.Random(seed)
    inserted = 0
    for i in range(n):
        topic = rnd.choice(_TOPICS)
        content = (f"{topic} {rnd.choice(_VERBS)} {rnd.choice(_NOUNS)} "
                   f"{rnd.choice(_TOPICS)} {rnd.choice(_NOUNS)} n{i} s{seed}")
        rec = {
            "namespace": rnd.choice(_NS),
            "mkey": f"k-{seed}-{i}",
            "content": content,
            "trust": "GRADED",
            "salience": round(rnd.random(), 3),
            "confidence": round(rnd.random(), 3),
            "privacy": "scrubbed",
            "created_at": f"2026-07-{1 + (i % 22):02d}T00:{i % 60:02d}:00Z",
        }
        try:
            if store.insert(rec):
                inserted += 1
        except Exception:  # noqa: BLE001
            pass
    return inserted


def make_queries(seed: int, m: int) -> list:
    """Deterministic query battery drawn from the same vocabulary (guaranteed hits)."""
    rnd = random.Random(seed * 7919 + 1)
    qs = []
    for _ in range(m):
        parts = [rnd.choice(_TOPICS) for _ in range(rnd.randint(1, 3))]
        qs.append(" ".join(parts))
    return qs


def fresh_store(tag: str) -> "ms.MemoryStore":
    p = DB_DIR / f"{tag}.db"
    for suf in ("", "-wal", "-shm"):
        try:
            (Path(str(p) + suf)).unlink()
        except OSError:
            pass
    return ms.MemoryStore(path=p)


def timed(fn, *, iters: int, warmup: int = 20) -> dict:
    """Run fn() iters times (after warmup), return latency stats in milliseconds."""
    for _ in range(warmup):
        fn()
    samples = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    return {
        "n": len(samples),
        "median_ms": round(statistics.median(samples), 4),
        "mean_ms": round(statistics.fmean(samples), 4),
        "p95_ms": round(samples[min(len(samples) - 1, int(len(samples) * 0.95))], 4),
        "min_ms": round(samples[0], 4),
    }
