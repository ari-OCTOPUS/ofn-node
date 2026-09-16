#!/usr/bin/env python3
"""patch_v14_freedom.py — GOV-FREEDOM-V2 on the coding worker (non-TCB).

Adds: free-form octopus.patch.v1 patches (multi-line, multi-file, non-TCB only),
second-model critique hook, up to 3 tasks per tick. Enum path is kept as the
local-model fallback. Pre-image backup + compile gate + anchor checks included.
"""
import hashlib
import pathlib
import py_compile
import shutil
import sys

T = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py")
B = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py.pre-freedom-v2-20260913")
src = T.read_text(encoding="utf-8")
print("pre_image_sha256:", hashlib.sha256(src.encode()).hexdigest()[:24])

if "octopus.patch.v1" in src:
    print("already patched")
    sys.exit(0)

NEW = '''
# ------------------------------------------- GOV-FREEDOM-V2 (owner, 2026-09-13)
# Free-form non-TCB patches: the model proposes a structured document; THIS
# worker owns deterministic validation (paths, anchors, AST, tests) and keeps a
# rollback. The enum path above stays as the weak-local-model fallback. Node 182
# still gates the actual deploy (canary), per section 5 of the directive.
PATCH_KIND = "octopus.patch.v1"
PATCH_ALLOW_ROOTS = (OPS, ROOT, Path("/home/ari/ofn/eti"))
PATCH_DENY_MARKERS = ("/autonomy/", "/.config/", "secret", "SECRETS", "witness-pins",
                      "tcb-manifest", "/api-budget/", "/etc/", ".ssh", "id_rsa",
                      "STOP-", "kill", "HALT")
MAX_PATCH_FILES = 4
MAX_PATCH_LINES_PER_FILE = 120
MAX_TEST_FILES = 3
MAX_TASKS_PER_TICK = 3   # GOV-FREEDOM-V2 section 9


def _first_json(text: str) -> dict | None:
    """First parseable JSON object in a model reply (bounded scan)."""
    depth, start = 0, -1
    for i, ch in enumerate(text[:60000]):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    obj = json.loads(text[start:i + 1])
                    if isinstance(obj, dict):
                        return obj
                except json.JSONDecodeError:
                    pass
                start = -1
    return None


def patch_doc_errors(doc) -> list:
    """Deterministic validation of an octopus.patch.v1 document."""
    errs = []
    if not isinstance(doc, dict) or doc.get("kind") != PATCH_KIND:
        return ["BAD_KIND"]
    files = doc.get("files") or []
    tests = doc.get("tests") or []
    run = doc.get("run_tests") or []
    if not (1 <= len(files) <= MAX_PATCH_FILES):
        errs.append("FILE_COUNT")
    if len(tests) > MAX_TEST_FILES:
        errs.append("TEST_COUNT")
    if not isinstance(doc.get("summary"), str) or not (8 <= len(doc["summary"]) <= 400):
        errs.append("SUMMARY")
    scope = doc.get("diff_scope")
    if not isinstance(scope, list) or not scope or len(scope) > MAX_PATCH_FILES:
        errs.append("DIFF_SCOPE")
    for f in files:
        p = str(f.get("path", ""))
        if not p or ".." in p or p.startswith("/"):
            errs.append("PATH_SHAPE"); continue
        rp = (Path("/home/ari/ofn") / p).resolve()
        if not any(str(rp).startswith(str(r.resolve()) + os.sep) for r in PATCH_ALLOW_ROOTS):
            errs.append("PATH_NOT_NON_TCB:" + p[:40]); continue
        if any(m in p for m in PATCH_DENY_MARKERS):
            errs.append("PATH_DENY:" + p[:40]); continue
        if f.get("op") != "replace_anchor":
            errs.append("OP:" + str(f.get("op"))[:20]); continue
        a, r = f.get("anchor", ""), f.get("replacement", "")
        if not isinstance(a, str) or not a or not isinstance(r, str) or not r:
            errs.append("ANCHOR_SHAPE"); continue
        if len(r.splitlines()) > MAX_PATCH_LINES_PER_FILE:
            errs.append("REPLACEMENT_TOO_LARGE")
    for t in tests:
        tp = str(t.get("path", ""))
        if not tp.endswith(".py") or "/" in tp or ".." in tp:
            errs.append("TEST_PATH:" + tp[:40])
    allowed = ("python3 -m pytest", "python -m pytest", "pytest -q")
    for c in run:
        if not any(str(c).startswith(pfx) for pfx in allowed) or \\
                any(b in str(c) for b in (";", "&&", "|", "`", "$(")):
            errs.append("RUN_CMD:" + str(c)[:40])
    return errs


def process_patch_task(task: dict) -> str:
    """GOV-FREEDOM-V2 section 3: free-form multi-file non-TCB patch cycle.

    paid-capable model -> JSON doc -> deterministic validation -> stage ->
    AST + tests -> per-file canary proposals (witness still gates deploys).
    """
    tid = task["task_id"]
    import api_budget
    prompt = (json.dumps(task.get("context", {}))[:6000])
    r = api_budget.paid_call(tid, task.get("purpose", "free-form-patch"), prompt,
                             est_in_tok=2500, max_out_tok=700, first_call_cap=0.25)
    if not r.get("ok"):
        resp = cognition_request(task)          # local fallback stays available
        if resp is None:
            learn(task, {"outcome": "PATCH_COGNITION_FAILED", "repeat": False})
            return "cognition-failed"
        r = {"text": resp.get("text", ""), "provider": "local-llamacpp-180"}
    doc = _first_json(r.get("text") or "")
    if doc is None:
        receipt("PATCH_REJECTED", reason="NO_JSON_DOC", provider=r.get("provider"))
        learn(task, {"outcome": "PATCH_NO_JSON", "repeat": False})
        return "rejected"
    errs = patch_doc_errors(doc)
    if errs:
        receipt("PATCH_REJECTED", reason=";".join(errs)[:120], provider=r.get("provider"))
        learn(task, {"outcome": "PATCH_INVALID", "detail": errs[:3], "repeat": False})
        return "rejected"
    if len(doc.get("files") or []) > 1:          # section 6: second-model critique
        try:
            c = api_budget.critique(json.dumps(doc)[:4000], exclude=r.get("provider"),
                                    task_id=tid + "-critique")
            receipt("PATCH_CRITIQUE", verdict=str(c.get("verdict"))[:40],
                    provider=c.get("provider"))
            if c.get("verdict") == "REJECT":
                learn(task, {"outcome": "PATCH_CRITIQUE_REJECT", "repeat": False})
                return "rejected"
        except Exception as exc:                  # critique must never block progress
            receipt("PATCH_CRITIQUE_UNAVAILABLE", err=type(exc).__name__)
    stage = STAGE_ROOT / tid
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    try:
        for f in doc["files"]:
            rel = f["path"]
            srcf = Path("/home/ari/ofn") / rel
            (stage / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(srcf, stage / rel)
            text = (stage / rel).read_text(encoding="utf-8")
            if text.count(f["anchor"]) != 1:
                raise ValueError("ANCHOR_DRIFT:" + rel[:40])
            new_text = text.replace(f["anchor"], f["replacement"], 1)
            if rel.endswith(".py"):
                ast.parse(new_text)              # patched module must still parse
            (stage / rel).write_text(new_text, encoding="utf-8")
        for t in doc.get("tests") or []:
            (stage / t["path"]).write_text(str(t.get("content", "")), encoding="utf-8")
    except (ValueError, SyntaxError, OSError) as exc:
        receipt("PATCH_REJECTED", reason=str(exc)[:100])
        learn(task, {"outcome": "PATCH_STAGE_ERROR", "repeat": False})
        return "patch-drift"
    ok_all = True
    for cmd in doc.get("run_tests") or []:
        p = subprocess.run(str(cmd).split(), cwd=stage, capture_output=True,
                           text=True, timeout=300)
        tail = (p.stdout or "").strip().splitlines()[-1:] or [""]
        receipt("PATCH_STAGE_TEST", cmd=str(cmd)[:60], ok=p.returncode == 0,
                tail=tail[0][:120])
        ok_all = ok_all and p.returncode == 0
    if not ok_all:
        learn(task, {"outcome": "PATCH_TESTS_FAILED", "repeat": False})
        return "tests-failed"
    # sequential per-file canary proposals; each carries its own rollback backup
    spooled = 0
    for f in doc["files"]:
        rel = f["path"]
        target = Path("/home/ari/ofn") / rel
        backup = stage / (rel.replace(os.sep, "__") + ".bak")
        shutil.copyfile(target, backup)
        patched = stage / rel
        patched_sha, backup_sha = sha_file(patched), sha_file(backup)
        CANARY_SPOOL.mkdir(parents=True, exist_ok=True)
        pf = CANARY_SPOOL / ("freedom-%s-%d.json" % (tid, spooled))
        pf.write_text(json.dumps(
            {"patched": str(patched), "backup": str(backup), "target": str(target),
             "target_sha256": patched_sha, "component": task.get("component", "coding-worker"),
             "requested_by": VERSION, "task_id": tid, "patch_kind": PATCH_KIND,
             "summary": doc.get("summary", "")[:200],
             "diff_scope": doc.get("diff_scope", [])[:MAX_PATCH_FILES]},
            sort_keys=True) + "\\n", encoding="utf-8")
        receipt("FREEDOM_CANARY_PROPOSAL_SUBMITTED", proposal=str(pf),
                target=rel, patched_sha256=patched_sha, backup_sha256=backup_sha)
        spooled += 1
    learn(task, {"outcome": "FREEDOM_CANARY_SUBMITTED", "files": spooled,
                 "summary": doc.get("summary", "")[:120]})
    return "canary-submitted"


'''

anchor = "def process_task(task: dict) -> str:"
if anchor not in src:
    print("ANCHOR_MISSING: process_task")
    sys.exit(3)
src = src.replace(anchor, NEW + anchor, 1)

branch_anchor = '''    receipt("TASK_STARTED", task=tid, purpose=task["purpose"])'''
branch_new = '''    receipt("TASK_STARTED", task=tid, purpose=task["purpose"])
    if task.get("patch_mode") == "free":        # GOV-FREEDOM-V2 section 3
        return process_patch_task(task)'''
if branch_anchor not in src:
    print("ANCHOR_MISSING: TASK_STARTED")
    sys.exit(3)
src = src.replace(branch_anchor, branch_new, 1)

loop_old = '''        result = process_task(task)
        dest = DONE if result in ("canary-submitted",) else FAILED
        if result in ("canary-submitted", "rejected", "tests-failed", "patch-drift",
                      "cognition-failed"):
            dest.mkdir(parents=True, exist_ok=True)
            os.replace(TASKS / name, dest / name)
        receipt("TICK_COMPLETE", processed=task["task_id"], result=result)
        print(json.dumps({"processed": task["task_id"], "result": result}))
        return 0
    receipt("TICK_COMPLETE", idle=True, note="NATIVE_CODING_IDLE_HEALTHY")
    print(json.dumps({"idle": True, "note": "NATIVE_CODING_IDLE_HEALTHY"}))
    return 0'''
loop_new = '''        result = process_task(task)
        processed_n += 1
        processed_ids.append({"task": task["task_id"], "result": result})
        dest = DONE if result in ("canary-submitted",) else FAILED
        if result in ("canary-submitted", "rejected", "tests-failed", "patch-drift",
                      "cognition-failed"):
            dest.mkdir(parents=True, exist_ok=True)
            os.replace(TASKS / name, dest / name)
    if processed_ids:                            # GOV-FREEDOM-V2 section 9
        receipt("TICK_COMPLETE", processed=processed_ids)
        print(json.dumps({"processed": processed_ids}))
    else:
        receipt("TICK_COMPLETE", idle=True, note="NATIVE_CODING_IDLE_HEALTHY")
        print(json.dumps({"idle": True, "note": "NATIVE_CODING_IDLE_HEALTHY"}))
    return 0'''
if loop_old not in src:
    print("ANCHOR_MISSING: tick loop tail")
    sys.exit(3)
src = src.replace(loop_old, loop_new, 1)

loop_head_old = '''    check_awaited_canaries()
    TASKS.mkdir(parents=True, exist_ok=True)
    for name in sorted(os.listdir(TASKS)):'''
loop_head_new = '''    check_awaited_canaries()
    TASKS.mkdir(parents=True, exist_ok=True)
    processed_n, processed_ids = 0, []           # GOV-FREEDOM-V2 section 9
    for name in sorted(os.listdir(TASKS)):
        if processed_n >= MAX_TASKS_PER_TICK:
            break'''
if loop_head_old not in src:
    print("ANCHOR_MISSING: tick loop head")
    sys.exit(3)
src = src.replace(loop_head_old, loop_head_new, 1)

src = src.replace('VERSION = "octopus-coding-worker/1.0.0"',
                  'VERSION = "octopus-coding-worker/1.4.0-freedom-v2"', 1)

if not B.exists():
    shutil.copy2(T, B)
    print("backup written:", B.name)
T.write_text(src, encoding="utf-8")
try:
    py_compile.compile(str(T), doraise=True)
except py_compile.PyCompileError as exc:
    print("PY_COMPILE_FAILED:", exc)
    shutil.copy2(B, T)
    sys.exit(4)
print("post_image_sha256:", hashlib.sha256(T.read_bytes()).hexdigest()[:24])
print("PATCH_V14_OK")
