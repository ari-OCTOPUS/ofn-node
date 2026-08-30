#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Force the valid_to timing race: target memory is the LAST-hydrated candidate,
its valid_to sits in (patched_now, orig_last_candidate_now]."""
from __future__ import annotations
import sys, types
from pathlib import Path
_HERE = Path(__file__).resolve().parent
_WT = _HERE.parent.parent
sys.path.insert(0, str(_HERE)); sys.path.insert(0, str(_WT/"_ops"/"memory")); sys.path.insert(0, str(_WT/"_ops"/"outcomes"))
import bench_common as bc, memory_store as ms
_SRC = (_WT/"_ops"/"memory"/"memory_store.py").read_text("utf-8")

def build(src, name):
    m = types.ModuleType(name); m.__dict__["__file__"]=str(_WT/"_ops"/"memory"/"memory_store.py")
    exec(compile(src, name+".py","exec"), m.__dict__); return m
# original N+1 search spliced
ORIG='''    def search(self, query, namespace=None, k=5, min_trust=None):
        q=str(query or "").strip()
        import re as _re
        terms=[t for t in _re.findall(r"[^\\W_]{3,}", q,_re.UNICODE)][:12]
        fts_q=" OR ".join(terms) if terms else ""
        with _LOCK:
            ids=[]
            if self._fts and fts_q:
                try:
                    frows=self._conn.execute("SELECT memory_id, bm25(memory_fts) AS score FROM memory_fts WHERE memory_fts MATCH ? ORDER BY score LIMIT ?",(fts_q,max(k*4,20))).fetchall()
                    ids=[(r[0],r[1]) for r in frows]
                except sqlite3.OperationalError: ids=[]
            if not ids:
                like=f"%{q}%"
                lrows=self._conn.execute("SELECT memory_id, 0.0 FROM memory WHERE content LIKE ? OR mkey LIKE ? LIMIT ?",(like,like,max(k*4,20))).fetchall()
                ids=[(r[0],0.0) for r in lrows]
            out=[]
            for mid,score in ids:
                r=self._conn.execute("SELECT "+",".join(_COLS)+" FROM memory WHERE memory_id=? AND (valid_to IS NULL OR valid_to>?)",(mid,_utc_now_iso())).fetchone()
                if not r: continue
                d=dict(zip(_COLS,r))
                if namespace and d["namespace"]!=namespace: continue
                if min_trust and not tax.trust_at_least(d["trust"],min_trust): continue
                sal=d.get("salience") or 0.0
                d["_rank"]=float(score)-float(sal); out.append(d)
        out.sort(key=lambda x:x["_rank"]); return out[:k]
'''
st=_SRC.index("    def search(self, query"); en=_SRC.index("    def as_memories_used(self",st)
omod=build(_SRC[:st]+ORIG+"\n"+_SRC[en:],"mo"); Orig=omod.MemoryStore
pmod=build(_SRC,"mp"); Patched=pmod.MemoryStore   # current file = batched

def sig(rows): return [(r["memory_id"], round(float(r.get("_rank",0.0)),9)) for r in rows]

DB=bc.DB_DIR/"race2.db"
for suf in ("","-wal","-shm"):
    try: Path(str(DB)+suf).unlink()
    except OSError: pass
s=Orig(path=DB)
# strong match (many repeats of terms) -> best bm25 -> hydrated FIRST
s.insert({"namespace":"semantic","mkey":"strong","content":"alpha alpha alpha beta beta beta gamma gamma gamma","trust":"GRADED","salience":0.9,"created_at":"2026-01-01T00:00:00Z"})
# weak match (few terms) -> worse bm25 -> hydrated LAST; expires in the race window
s.insert({"namespace":"semantic","mkey":"weak","content":"alpha beta gamma tail","trust":"GRADED","salience":0.5,"valid_to":"2026-07-24T12:00:00.000005+00:00","created_at":"2026-01-01T00:00:00Z"})
s.close()

class Clk:
    def __init__(s,seq): s.seq=seq; s.i=0
    def __call__(s):
        v=s.seq[min(s.i,len(s.seq)-1)]; s.i+=1; return v
# patched: single call -> uses seq[0] (before boundary). orig: cand1 seq[0] (before), cand2 seq[1] (after boundary)
seq=["2026-07-24T12:00:00.000004+00:00","2026-07-24T12:00:00.000006+00:00","2026-07-24T12:00:00.000006+00:00"]

omod.__dict__["_utc_now_iso"]=Clk(list(seq))
b1=Orig(path=DB); a=sig(b1.search("alpha beta gamma",k=5)); b1.close()
pmod.__dict__["_utc_now_iso"]=Clk(list(seq))
p1=Patched(path=DB); b=sig(p1.search("alpha beta gamma",k=5)); p1.close()
print("orig (per-candidate clock, weak hydrated after boundary):", a)
print("pat  (single snapshot before boundary):                  ", b)
print("FORCED timing-race divergence:", a!=b)
