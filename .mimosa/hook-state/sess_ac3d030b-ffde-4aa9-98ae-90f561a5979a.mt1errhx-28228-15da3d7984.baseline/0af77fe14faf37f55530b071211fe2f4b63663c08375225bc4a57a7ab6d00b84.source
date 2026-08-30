#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""common_v2.py — C6 evolution_v2: build baseline+patched modules from the LIVE c7 code.

Baseline = exact `_ops/memory/memory_store.py` from branch claude/c7-continuity
(SCHEMA_VERSION 2, admission_state owner-gate). Patched = same file with ONLY the
per-candidate N+1 hydration replaced by one batched IN(...) query that PRESERVES the
`admission_state='ADMITTED'` filter. Corpus deliberately mixes ADMITTED/PENDING/RETRACTED
so the governance invariant (PENDING/RETRACTED invisible to search) is actually exercised.
"""
from __future__ import annotations

import difflib
import io
import random
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
# real taxonomy must be importable by the exec'd modules
for _p in (str(WT / "_ops" / "outcomes"),):
    if _p not in sys.path:
        sys.path.insert(0, _p)

BASE_SRC = (HERE / "memory_store_c7_base.py").read_text("utf-8").replace("\r\n", "\n")

_OLD = (
    '            out = []\n'
    '            for mid, score in ids:\n'
    '                r = self._conn.execute("SELECT " + ",".join(_COLS) + " FROM memory WHERE memory_id=? "\n'
    '                                       "AND admission_state=\'ADMITTED\' "\n'
    '                                       "AND (valid_to IS NULL OR valid_to>?)",\n'
    '                                       (mid, _utc_now_iso())).fetchone()\n'
)
_NEW = (
    '            # batched hydration (C6 evolution_v2): ONE IN(...) query for all candidates\n'
    '            # instead of a per-candidate round-trip (N+1). Ranking/tie-break unchanged —\n'
    '            # candidate order is preserved, and the admission_state / validity /\n'
    '            # namespace / min_trust filters are byte-identical to the per-candidate form.\n'
    '            # (k*4 candidates stays far below SQLite\'s bound-parameter limit.)\n'
    '            now = _utc_now_iso()\n'
    '            row_by_id = {}\n'
    '            if ids:\n'
    '                mids = [mid for mid, _ in ids]\n'
    '                ph = ",".join("?" * len(mids))\n'
    '                for hr in self._conn.execute(\n'
    '                        "SELECT " + ",".join(_COLS) + " FROM memory WHERE memory_id IN (" + ph + ") "\n'
    '                        "AND admission_state=\'ADMITTED\' "\n'
    '                        "AND (valid_to IS NULL OR valid_to>?)", (*mids, now)).fetchall():\n'
    '                    row_by_id[hr[0]] = hr\n'
    '            out = []\n'
    '            for mid, score in ids:\n'
    '                r = row_by_id.get(mid)\n'
)

assert BASE_SRC.count(_OLD) == 1, f"anchor not unique in c7 source: {BASE_SRC.count(_OLD)}"
PATCHED_SRC = BASE_SRC.replace(_OLD, _NEW)


def write_artifacts():
    (HERE / "memory_store_c7_batched.py").write_text(PATCHED_SRC, "utf-8", newline="\n")
    diff = "".join(difflib.unified_diff(
        BASE_SRC.splitlines(keepends=True), PATCHED_SRC.splitlines(keepends=True),
        fromfile="a/_ops/memory/memory_store.py", tofile="b/_ops/memory/memory_store.py"))
    (HERE / "proposed_v2.patch").write_text(diff, "utf-8", newline="\n")
    return diff


def _load(src: str, name: str):
    mod = types.ModuleType(name)
    mod.__dict__["__file__"] = str(HERE / f"{name}.py")
    exec(compile(src, f"{name}.py", "exec"), mod.__dict__)
    return mod


BASE = _load(BASE_SRC, "ms_c7_base")
PATCHED = _load(PATCHED_SRC, "ms_c7_batched")

_TOPICS = ["painting", "lead", "sydney", "quote", "invoice", "crypto", "mining", "rig",
           "ziman", "gallery", "hypnosis", "budget", "telegram", "octopus", "memory",
           "recall", "latency", "receipt", "outcome", "governor", "heartbeat", "sandbox",
           "verifier", "hypothesis", "calibration", "throughput", "pipeline", "admission"]
_VERBS = ["improves", "reduces", "blocks", "raises", "measures", "cites", "scores",
          "routes", "gates", "verifies", "quarantines", "accepts", "rejects", "profiles"]
_NOUNS = ["decision", "acceptance", "cost", "risk", "signal", "candidate", "baseline",
          "corpus", "query", "index", "token", "spend", "margin", "session", "note"]
_NS = ["semantic", "episodic", "self_knowledge"]

DB_DIR = HERE / "dbs"
DB_DIR.mkdir(parents=True, exist_ok=True)


def fresh_db(tag: str) -> Path:
    p = DB_DIR / f"{tag}.db"
    for suf in ("", "-wal", "-shm"):
        try:
            Path(str(p) + suf).unlink()
        except OSError:
            pass
    return p


def make_corpus(db: Path, n: int, seed: int) -> dict:
    """Build a corpus with a deliberate mix of admission states.
    ~70% ADMITTED, ~15% PENDING, ~15% RETRACTED. Returns id sets per state."""
    rnd = random.Random(seed)
    store = BASE.MemoryStore(path=db)
    admitted, pending, retracted = set(), set(), set()
    try:
        for i in range(n):
            topic = rnd.choice(_TOPICS)
            content = (f"{topic} {rnd.choice(_VERBS)} {rnd.choice(_NOUNS)} "
                       f"{rnd.choice(_TOPICS)} {rnd.choice(_NOUNS)} n{i} s{seed}")
            roll = rnd.random()
            state = "ADMITTED" if roll < 0.70 else ("PENDING" if roll < 0.85 else "ADMITTED")
            rec = {"namespace": rnd.choice(_NS), "mkey": f"k-{seed}-{i}", "content": content,
                   "trust": "GRADED", "salience": round(rnd.random(), 3),
                   "confidence": round(rnd.random(), 3), "privacy": "scrubbed",
                   "admission_state": state,
                   "created_at": f"2026-07-{1 + (i % 22):02d}T00:{i % 60:02d}:00Z"}
            mid = store.insert(rec)
            if not mid:
                continue
            if state == "PENDING":
                pending.add(mid)
            elif roll >= 0.85:                      # retract a slice of the admitted ones
                if store.set_admission_state(mid, "RETRACTED"):
                    retracted.add(mid)
                else:
                    admitted.add(mid)
            else:
                admitted.add(mid)
    finally:
        store.close()
    return {"admitted": admitted, "pending": pending, "retracted": retracted}


def make_queries(seed: int, m: int) -> list:
    rnd = random.Random(seed * 7919 + 1)
    return [" ".join(rnd.choice(_TOPICS) for _ in range(rnd.randint(1, 3))) for _ in range(m)]


def timed_median(fn, iters=400, warmup=25) -> float:
    for _ in range(warmup):
        fn()
    xs = []
    for _ in range(iters):
        t = time.perf_counter()
        fn()
        xs.append(time.perf_counter() - t)
    return statistics.median(xs) * 1000.0
