#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""adversarial correctness probe (verifier, lens=correctness-completeness).
Constructs inputs the battery corpus never creates: valid_to values, expiry,
duplicate FTS ids, and large candidate sets (IN() param count)."""
from __future__ import annotations
import io, sys, types
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8")
    except Exception: pass

_HERE = Path(__file__).resolve().parent
_WT = _HERE.parent.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_WT / "_ops" / "memory"))
sys.path.insert(0, str(_WT / "_ops" / "outcomes"))
import bench_common as bc
import memory_store as ms

_SRC = (_WT / "_ops" / "memory" / "memory_store.py").read_text("utf-8")
# build patched module the same way verify_edges does (splice current file, which
# already IS the patched in-file version — so patched == current file here)
mod = types.ModuleType("mp")
mod.__dict__["__file__"] = str(_WT / "_ops" / "memory" / "memory_store.py")
exec(compile(_SRC, "mp.py", "exec"), mod.__dict__)
Patched = mod.MemoryStore   # current file already contains batched search
Orig = ms.MemoryStore       # same file... need the ORIGINAL N+1 version

# reconstruct the ORIGINAL search from git-less source: the opt file is the batched;
# we synthesize the original N+1 body and splice it in for a true A/B.
_ORIG_SEARCH = '''    def search(self, query, namespace=None, k=5, min_trust=None):
        q = str(query or "").strip()
        import re as _re
        terms = [t for t in _re.findall(r"[^\\W_]{3,}", q, _re.UNICODE)][:12]
        fts_q = " OR ".join(terms) if terms else ""
        with _LOCK:
            ids = []
            if self._fts and fts_q:
                try:
                    frows = self._conn.execute(
                        "SELECT memory_id, bm25(memory_fts) AS score FROM memory_fts "
                        "WHERE memory_fts MATCH ? ORDER BY score LIMIT ?", (fts_q, max(k*4,20))).fetchall()
                    ids = [(r[0], r[1]) for r in frows]
                except sqlite3.OperationalError:
                    ids = []
            if not ids:
                like = f"%{q}%"
                lrows = self._conn.execute(
                    "SELECT memory_id, 0.0 FROM memory WHERE content LIKE ? OR mkey LIKE ? LIMIT ?",
                    (like, like, max(k*4,20))).fetchall()
                ids = [(r[0], 0.0) for r in lrows]
            out = []
            for mid, score in ids:
                r = self._conn.execute("SELECT " + ",".join(_COLS) + " FROM memory WHERE memory_id=? "
                                       "AND (valid_to IS NULL OR valid_to>?)",
                                       (mid, _utc_now_iso())).fetchone()
                if not r:
                    continue
                d = dict(zip(_COLS, r))
                if namespace and d["namespace"] != namespace:
                    continue
                if min_trust and not tax.trust_at_least(d["trust"], min_trust):
                    continue
                sal = d.get("salience") or 0.0
                d["_rank"] = float(score) - float(sal)
                out.append(d)
        out.sort(key=lambda x: x["_rank"])
        return out[:k]
'''
start = _SRC.index("    def search(self, query")
end = _SRC.index("    def as_memories_used(self", start)
orig_src = _SRC[:start] + _ORIG_SEARCH + "\n" + _SRC[end:]
omod = types.ModuleType("mo")
omod.__dict__["__file__"] = str(_WT / "_ops" / "memory" / "memory_store.py")
exec(compile(orig_src, "mo.py", "exec"), omod.__dict__)
Orig = omod.MemoryStore

def _sig(rows):
    return [(r["memory_id"], round(float(r.get("_rank", 0.0)), 9)) for r in rows]

DB = bc.DB_DIR / "adv.db"
for suf in ("", "-wal", "-shm"):
    try: Path(str(DB)+suf).unlink()
    except OSError: pass

# ---- craft a corpus WITH valid_to values + a superseded-reinsert duplicate ----
s = Orig(path=DB)
# active memory
s.insert({"namespace":"semantic","mkey":"a","content":"painting quote sydney alpha",
          "trust":"GRADED","salience":0.5,"created_at":"2026-01-01T00:00:00Z"})
# memory that will be superseded (goes expired) then re-inserted identical -> dup fts id
s.insert({"namespace":"semantic","mkey":"b","content":"painting quote sydney bravo",
          "trust":"GRADED","salience":0.5,"created_at":"2026-01-01T00:00:00Z"})
# supersede b's memory
mid_b = s.get("semantic","b")["memory_id"]
s.insert({"namespace":"semantic","mkey":"b","content":"painting quote sydney bravo v2",
          "trust":"GRADED","salience":0.5,"supersedes":mid_b,"created_at":"2026-01-02T00:00:00Z"})
# re-insert identical bravo (b now expired) -> same mid, INSERT OR IGNORE, but 2nd fts row
s.insert({"namespace":"semantic","mkey":"b","content":"painting quote sydney bravo",
          "trust":"GRADED","salience":0.5,"created_at":"2026-01-01T00:00:00Z"})
# a memory with a FUTURE valid_to just barely ahead (expiry boundary test)
s.insert({"namespace":"semantic","mkey":"c","content":"painting quote sydney charlie",
          "trust":"GRADED","salience":0.5,"valid_from":"2026-01-01T00:00:00Z",
          "valid_to":"2099-01-01T00:00:00Z","created_at":"2026-01-01T00:00:00Z"})
# a memory ALREADY expired
s.insert({"namespace":"semantic","mkey":"d","content":"painting quote sydney delta",
          "trust":"GRADED","salience":0.5,"valid_from":"2020-01-01T00:00:00Z",
          "valid_to":"2021-01-01T00:00:00Z","created_at":"2020-01-01T00:00:00Z"})
s.close()

# check FTS for duplicate memory_id rows
import sqlite3
c = sqlite3.connect(str(DB))
duprows = c.execute("SELECT memory_id, COUNT(*) FROM memory_fts GROUP BY memory_id HAVING COUNT(*)>1").fetchall()
print("duplicate FTS memory_id rows:", duprows)
c.close()

print("\n=== A/B on crafted valid_to/dup corpus ===")
base = Orig(path=DB); pat = Patched(path=DB)
mism = 0
for q in ["painting quote sydney", "bravo", "charlie", "delta", "sydney"]:
    for k in (1,5,20):
        for f in ({}, {"namespace":"semantic"}, {"min_trust":"GRADED"}):
            a = _sig(base.search(q,k=k,**f)); b = _sig(pat.search(q,k=k,**f))
            if a != b:
                mism += 1
                print(f"MISMATCH q={q!r} k={k} f={f}\n  orig={a}\n  pat ={b}")
base.close(); pat.close()
print("crafted-corpus mismatches:", mism)

# ---- valid_to TIMING RACE: monkeypatch clock so original's per-candidate now drifts
print("\n=== valid_to timing-race probe (controlled clock) ===")
# corpus: 3 matching memories; one expires at a boundary timestamp.
DB2 = bc.DB_DIR / "adv_race.db"
for suf in ("", "-wal", "-shm"):
    try: Path(str(DB2)+suf).unlink()
    except OSError: pass
s2 = Orig(path=DB2)
s2.insert({"namespace":"semantic","mkey":"x1","content":"zeta match one","trust":"GRADED","salience":0.9,"created_at":"2026-01-01T00:00:00Z"})
# this one expires exactly at boundary T
s2.insert({"namespace":"semantic","mkey":"x2","content":"zeta match two","trust":"GRADED","salience":0.5,"valid_to":"2026-07-23T12:00:00.000005+00:00","created_at":"2026-01-01T00:00:00Z"})
s2.insert({"namespace":"semantic","mkey":"x3","content":"zeta match three","trust":"GRADED","salience":0.1,"created_at":"2026-01-01T00:00:00Z"})
s2.close()

import memory_store as _ms_orig
# a clock that advances by 1us each call, starting just before the boundary
class Clk:
    def __init__(self, seq): self.seq=seq; self.i=0
    def __call__(self):
        v = self.seq[min(self.i, len(self.seq)-1)]; self.i+=1; return v
# boundary is ...12:00:00.000005 ; give patched a 'now' BEFORE it, original later calls cross it
seq = ["2026-07-23T12:00:00.000003+00:00",  # 1st call (patched single call OR orig cand1)
       "2026-07-23T12:00:00.000004+00:00",
       "2026-07-23T12:00:00.000006+00:00",  # crosses boundary -> x2 now expired for later candidates
       "2026-07-23T12:00:00.000007+00:00",
       "2026-07-23T12:00:00.000008+00:00"]

# run ORIGINAL with drifting clock
omod.__dict__["_utc_now_iso"] = Clk(list(seq))
base2 = Orig(path=DB2)
a = _sig(base2.search("zeta match", k=5))
base2.close()
# run PATCHED with a clock whose FIRST value matches original's first call
mod.__dict__["_utc_now_iso"] = Clk(list(seq))
pat2 = Patched(path=DB2)
b = _sig(pat2.search("zeta match", k=5))
pat2.close()
# restore
omod.__dict__["_utc_now_iso"] = _ms_orig._utc_now_iso
mod.__dict__["_utc_now_iso"] = _ms_orig._utc_now_iso
print("orig (drifting per-candidate clock):", a)
print("pat  (single-snapshot clock):       ", b)
print("timing-race divergence:", a != b)
