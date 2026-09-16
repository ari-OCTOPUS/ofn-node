#!/usr/bin/env python3
"""patch_realwork_bridge.py — REAL-WORK-BRIDGE-20260913 admission gates.

A) coding_worker: no task without REAL provenance may run (both enum and
   free-form paths). REJECT_NO_REAL_WORLD_PROVENANCE.
B) api_budget: paid-gate — forbidden purposes rejected, duplicate prompts
   (task+context-hash+provider) rejected. No LLM decides evidence existence.
"""
import hashlib
import pathlib
import py_compile
import shutil
import sys

CW = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py")
API = pathlib.Path("/home/ari/ofn/state/api-budget/api_budget.py")

# ---------- A. worker provenance gate ---------------------------------------
s = CW.read_text(encoding="utf-8")
print("worker pre:", hashlib.sha256(s.encode()).hexdigest()[:24])
if "TASK_REJECTED_NO_REAL_WORLD_PROVENANCE" not in s:
    GATE = '''
# ------------------------- REAL-WORK-BRIDGE-20260913 (owner directive)
# No synthetic / demonstration / duplicate / stale / unknown task may enter the
# live operational queue. Provenance is checked deterministically — never by a
# model. Fixtures live only inside isolated tests.
REAL_PROVENANCE_CLASSES = frozenset((
    "REAL_RUNTIME_INCIDENT", "REAL_CODE_DEFECT", "REAL_SECURITY_FINDING",
    "REAL_RESOURCE_PRESSURE", "REAL_PREDICTION_DUE", "REAL_GITHUB_WORK",
    "REAL_OWNER_GOAL", "REAL_BUSINESS_WORK", "DERIVED_FROM_REAL_EVIDENCE"))


def provenance_ok(task: dict) -> bool:
    p = task.get("provenance") or {}
    return (not task.get("fixture")
            and p.get("class") in REAL_PROVENANCE_CLASSES
            and bool(p.get("source"))
            and bool(p.get("source_ts"))
            and bool(p.get("source_hash")))

'''
    anchor = "def process_task(task: dict) -> str:"
    if anchor not in s:
        print("ANCHOR_MISSING worker gate"); sys.exit(3)
    s = s.replace(anchor, GATE + anchor, 1)
    mark = '''    receipt("TASK_STARTED", task=tid, purpose=task["purpose"])'''
    gate_call = '''    receipt("TASK_STARTED", task=tid, purpose=task["purpose"])
    if not provenance_ok(task):                     # REAL-WORK-BRIDGE-20260913
        p = task.get("provenance") or {}
        receipt("TASK_REJECTED_NO_REAL_WORLD_PROVENANCE",
                fixture=bool(task.get("fixture")), cls=p.get("class"),
                has_source=bool(p.get("source")), has_ts=bool(p.get("source_ts")),
                has_hash=bool(p.get("source_hash")))
        return "rejected"'''
    if mark not in s:
        print("ANCHOR_MISSING worker gate call"); sys.exit(3)
    s = s.replace(mark, gate_call, 1)
    B = CW.with_suffix(".py.pre-realwork-20260913")
    if not B.exists():
        shutil.copy2(CW, B)
    CW.write_text(s, encoding="utf-8")
    py_compile.compile(str(CW), doraise=True)
    print("worker gate installed")

# ---------- B. broker paid gate ---------------------------------------------
a = API.read_text(encoding="utf-8")
print("broker pre:", hashlib.sha256(a.encode()).hexdigest()[:24])
if "PAID_COGNITION_NOT_JUSTIFIED" not in a:
    anchor = 'def paid_call(task_id: str, purpose: str, prompt: str, est_in_tok: int = 1500,'
    if anchor not in a:
        print("ANCHOR_MISSING broker"); sys.exit(3)
    i = a.index(anchor)
    j = a.index('"""', a.index('"""', i) + 3) + 3  # end of docstring
    GATE_B = '''
    # ------------------- REAL-WORK-BRIDGE-20260913: paid admission gate -----
    import hashlib as _h
    _purpose = (purpose or "").lower()
    _forbidden = ("heartbeat", "status-report", "formatting", "translation",
                  "fixture", "demo", "demonstration", "polling", "waiting",
                  "already-solved", "activity")
    if any(t in _purpose for t in _forbidden):
        return {"ok": False, "error": "PAID_COGNITION_NOT_JUSTIFIED",
                "reason": "purpose:" + _purpose[:40]}
    _ctx = _h.sha256(prompt.encode()).hexdigest()
    for _r in _rows():
        if (_r.get("kind") == "reserve" and _r.get("task_id") == task_id
                and _r.get("context_sha256") == _ctx
                and _r.get("provider") == (provider or "auto")):
            return {"ok": False, "error": "PAID_DUPLICATE_PROMPT",
                    "reason": "same task+context+provider already reserved"}
    _kw = {"ctx_hash": _ctx}
'''
    a = a[:j] + GATE_B + a[j:]
    # thread ctx through reserve call
    old_call = 'r = reserve(task_id, purpose, est_in_tok, max_out_tok, "local-insufficient",\n                provider=provider, model=mdl)'
    new_call = ('r = reserve(task_id, purpose, est_in_tok, max_out_tok, "local-insufficient",\n'
                '                provider=provider, model=mdl, ctx_hash=_ctx)')
    if old_call not in a:
        print("ANCHOR_MISSING reserve call"); sys.exit(3)
    a = a.replace(old_call, new_call, 1)
    BA = API.with_suffix(".py.pre-realwork-20260913")
    if not BA.exists():
        shutil.copy2(API, BA)
    API.write_text(a, encoding="utf-8")
    py_compile.compile(str(API), doraise=True)
    print("broker gate installed")
    del _kw  # noqa: F821 (kept for symmetry; not used)
print("post: worker=%s broker=%s" % (
    hashlib.sha256(CW.read_bytes()).hexdigest()[:24],
    hashlib.sha256(API.read_bytes()).hexdigest()[:24]))
print("REALWORK_GATE_OK")
