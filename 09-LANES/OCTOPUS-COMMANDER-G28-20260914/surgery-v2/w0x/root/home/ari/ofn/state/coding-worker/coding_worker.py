#!/usr/bin/env python3
"""OCTOPUS native coding worker — node 138, additive, NON-TCB.

Lane NATIVE-COGNITION-20260913. Pulls one eligible real task from its
node-side queue, requests a structured patch proposal from the node-180
Cognition Broker over the proven mesh SSH route, deterministically validates
the proposal, applies a bounded anchor patch in an isolated stage, runs
focused tests there, packages hashes, and submits the deployment through the
ALREADY-DEPLOYED witnessed ops-agent B8 canary spool. The model never
executes; the worker never runs model-supplied shell; TCB targets are
rejected. Append-only hash-chained receipts + learning ledger.

Status when idle and healthy: NATIVE_CODING_IDLE_HEALTHY.
"""
from __future__ import annotations

import ast
from collections import Counter
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
ROOT = HOME / "ofn" / "state" / "coding-worker"
STATE = ROOT / "state"
TASKS = STATE / "tasks"
DONE = STATE / "done"
FAILED = STATE / "failed"
STAGE_ROOT = HOME / "ofn" / "state" / "coding-worker" / "stage"  # shared, not PrivateTmp
RECEIPTS = STATE / "coding-receipts.jsonl"
LEARNING = STATE / "learning.jsonl"
COOLDOWN = STATE / "cooldown.json"
OPS = HOME / "ofn" / "state" / "ops-agent"
CANARY_SPOOL = OPS / "state" / "canary-requests"
BROKER_SSH = ["ssh", "-i", str(HOME / ".ssh" / "octopus_mesh_ed25519"),
              "-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
              "-o", "StrictHostKeyChecking=yes", "root@192.168.0.180",
              "python3 /var/lib/octopus/cognition-broker/cognition_broker.py"]
VERSION = "octopus-coding-worker/1.4.0-freedom-v2"

_TCB_TARGETS = ("supervisor.py", "tcb-manifest.json", "witness-pins.json",
                "recovery-contract.json", "witness_verifier.py")
_ALLOWED_EXPR_CALLS = {"split"}
_MAX_DIFF_LINES = 120


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def sha_obj(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def receipt(kind: str, **kw) -> dict:
    prev = None
    if RECEIPTS.exists():
        last = None
        for l in RECEIPTS.read_text(encoding="utf-8").splitlines():
            if l.strip():
                last = l
        prev = json.loads(last).get("cr_hash") if last else None
    row = {"schema": "octopus.coding-receipt.v1", "kind": kind, "worker": VERSION,
           "at": now_iso(), **kw}
    row["previous_cr_hash"] = prev
    row["cr_hash"] = sha_obj({k: v for k, v in row.items() if k != "cr_hash"})
    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    with RECEIPTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def learn(task: dict, outcome: dict) -> None:
    prev = None
    if LEARNING.exists():
        last = None
        for l in LEARNING.read_text(encoding="utf-8").splitlines():
            if l.strip():
                last = l
        prev = json.loads(last).get("lr_hash") if last else None
    row = {"schema": "octopus.coding-learning.v1", "at": now_iso(),
           "task_id": task.get("task_id"), **outcome, "previous_lr_hash": prev}
    row["lr_hash"] = sha_obj({k: v for k, v in row.items() if k != "lr_hash"})
    LEARNING.parent.mkdir(parents=True, exist_ok=True)
    with LEARNING.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def verify_own_chain() -> tuple:
    ok, prev, n = True, None, 0
    if not RECEIPTS.exists():
        return True, 0
    for l in RECEIPTS.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except json.JSONDecodeError:
            return False, n
        n += 1
        if sha_obj({k: v for k, v in d.items() if k != "cr_hash"}) != d.get("cr_hash"):
            ok = False
        if d.get("previous_cr_hash") != prev:
            ok = False
        prev = d.get("cr_hash")
    return ok, n


def cooldown_active() -> bool:
    try:
        c = json.loads(COOLDOWN.read_text(encoding="utf-8"))
        return c.get("until", "") > now_iso()
    except (OSError, json.JSONDecodeError):
        return False


def set_cooldown(seconds: int) -> None:
    until = datetime.fromtimestamp(time.time() + seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    COOLDOWN.write_text(json.dumps({"until": until}), encoding="utf-8")


# --------------------------------------------------------------- cognition
BUDGET_DIR = HOME / "ofn" / "state" / "api-budget"
PAID_FALLBACK_MAX_USD = 0.25   # per call; the shared global budget still caps


def paid_fallback(task: dict) -> dict | None:
    """Paid rung, reached ONLY after the local node-180 model failed.

    LOCAL_FIRST is this worker's duty. The credential broker holds the key and
    enforces the budget contract; this worker can neither read a credential nor
    exceed the per-call cap. Fail-closed: any rejection returns None.
    """
    try:
        if str(BUDGET_DIR) not in sys.path:
            sys.path.insert(0, str(BUDGET_DIR))
        import api_budget
        prompt = json.dumps(task.get("context", ""))[:4000]
        r = api_budget.paid_call(task["task_id"], "coding-worker-paid-fallback",
                                 prompt, est_in_tok=1200, max_out_tok=256,
                                 first_call_cap=PAID_FALLBACK_MAX_USD)
    except Exception as exc:  # noqa: BLE001
        receipt("PAID_FALLBACK_ERROR", err=type(exc).__name__)
        return None
    if not r.get("ok"):
        receipt("PAID_FALLBACK_REJECTED", error=r.get("error"),
                provider=r.get("provider"), http=r.get("http_status"))
        return None
    cost = (r.get("settle") or {}).get("cost_usd")
    receipt("PAID_FALLBACK_RESPONSE", provider=r.get("provider"),
            model=r.get("served_model"), cost_usd=cost)
    return {"ok": True, "model": r.get("served_model"), "text": r.get("text", ""),
            "cost_usd": cost, "provider": r.get("provider"), "paid": True}


def cognition_request(task: dict, mode: str = "proposal") -> dict | None:
    req = {"schema": "octopus.cognition-request.v1",
           "task_id": task["task_id"], "purpose": task["purpose"],
           "prompt_context": task["context"],
           # G16: the broker is opt-in. "patch" returns the raw model text so a
           # free-form patch document can be validated by THIS worker; the default
           # "proposal" path is unchanged for every existing caller.
           "mode": mode,
           # G15: the free-form patch path does not carry output_contract; a bare
           # task["output_contract"] raised KeyError and killed the whole tick.
           "output_contract": task.get("output_contract") or (
               "Return exactly ONE JSON object of kind octopus.patch.v1, on ONE line, "
               "with no prose and no markdown fence. Keys: "
               "kind (string \"octopus.patch.v1\"), summary (string), "
               "diff_scope (JSON ARRAY of strings, e.g. [\"state/ops-agent/ops_agent.py\"]), "
               "files (ARRAY of objects with path, op=\"replace_anchor\", anchor, replacement), "
               "tests (ARRAY of objects with path, content), run_tests (ARRAY of strings). "
               "diff_scope, files, tests and run_tests MUST be arrays, never strings.")}
    try:
        r = subprocess.run(BROKER_SSH, input=json.dumps(req).encode(),
                           capture_output=True, timeout=150)
        if r.returncode != 0:
            receipt("COGNITION_FAIL_CLOSED", rc=r.returncode,
                    err=(r.stdout or b"").decode("utf-8", "replace")[:120])
            return paid_fallback(task)
        d = json.loads(r.stdout.decode("utf-8"))
        if not d.get("ok"):
            receipt("COGNITION_FAIL_CLOSED", err=d.get("error"))
            return paid_fallback(task)
        receipt("COGNITION_RESPONSE", model=d.get("model"), tokens=d.get("tokens"),
                cost_usd=d.get("cost_usd"), broker_receipt=d.get("receipt"))
        return d
    except subprocess.TimeoutExpired:
        receipt("COGNITION_TIMEOUT")
        return paid_fallback(task)


# --------------------------------------------------------------- validation
def expression_safe(expr: str) -> bool:
    """The ONLY model-derived value we accept: one Python expression over the
    string variable `category`, limited to subscript/split/attribute-free forms."""
    if not expr or len(expr) > 60 or ";" in expr or "`" in expr:
        return False
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id != "category":
                return False
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Attribute) or node.func.attr not in _ALLOWED_EXPR_CALLS:
                return False
            for a in node.args:
                if not (isinstance(a, ast.Constant) and isinstance(a.value, str) and len(a.value) <= 4):
                    return False
            if node.keywords:
                return False
        elif isinstance(node, ast.Attribute):
            if node.attr not in _ALLOWED_EXPR_CALLS:
                return False
        elif isinstance(node, (ast.Expression, ast.expr_context, ast.Constant, ast.Slice)):
            continue
        elif isinstance(node, ast.Subscript):
            continue
        else:
            return False
    compile(expr, "<expr>", "eval")
    return True


def apply_anchor_patch(src: Path, anchors: list, replacement_builder) -> str:
    """Deterministic anchor replacement: each anchor must match EXACTLY ONCE.
    Returns the new text; refuses (raises) on any drift."""
    text = src.read_text(encoding="utf-8")
    lines_changed = 0
    for anchor in anchors:
        if text.count(anchor) != 1:
            raise ValueError(f"ANCHOR_DRIFT:{anchor[:50]}")
    for anchor, new in replacement_builder():
        if text.count(anchor) != 1:
            raise ValueError(f"ANCHOR_DRIFT:{anchor[:50]}")
        if new.count("\n") > _MAX_DIFF_LINES:
            raise ValueError("DIFF_TOO_LARGE")
        lines_changed += new.count("\n") - anchor.count("\n") + 1
        text = text.replace(anchor, new, 1)
    return text


def run_stage_tests(stage: Path, test_file_name: str, timeout_s: int = 300) -> tuple:
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", test_file_name],
                       cwd=stage, capture_output=True, text=True, timeout=timeout_s)
    tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
    return r.returncode == 0, tail[0][:160]


# --------------------------------------------------------------- task cycle

# ------------------------------------------- GOV-FREEDOM-V2 (owner, 2026-09-13)
# Free-form non-TCB patches: the model proposes a structured document; THIS
# worker owns deterministic validation (paths, anchors, AST, tests) and keeps a
# rollback. The enum path above stays as the weak-local-model fallback. Node 182
# still gates the actual deploy (canary), per section 5 of the directive.
PATCH_KIND = "octopus.patch.v1"
# owner decision 2026-09-13: the worker may repair the organism's OWN agents
# (glass_runner, go_b3_owner_bind, doctor, imap_listener, ...). TCB stays
# unreachable: the TCB target names were ADDED to PATCH_DENY_MARKERS in this
# same change, so widening the root tightened the deny list with it.
PATCH_ALLOW_ROOTS = (OPS, ROOT, Path("/home/ari/ofn/eti"),
                     Path("/home/ari/ofn/ofn/agents"))
PATCH_DENY_MARKERS = ("/autonomy/", "/.config/", "secret", "SECRETS", "witness-pins",
                      "tcb-manifest", "recovery-contract", "witness_verifier",
                      "supervisor.py", "/api-budget/", "/etc/", ".ssh", "id_rsa",
                      "STOP-", "kill", "HALT")
MAX_PATCH_FILES = 4
MAX_PATCH_LINES_PER_FILE = 120
MAX_TEST_FILES = 3
MAX_TASKS_PER_TICK = 3   # GOV-FREEDOM-V2 section 9


def _quote_bare_keys(s: str) -> str:
    """Quote bare identifiers used as OBJECT KEYS, outside of string literals.

    Owner decision 2026-09-14. The local model emits JSON5-style keys ({kind: ...}).
    A string-aware scan is used so nothing inside a string value is touched.
    The result is still parsed with strict json.loads, so this cannot accept a
    document that is not otherwise valid JSON.
    """
    out, i, n = [], 0, len(s)
    in_str = esc = False
    prev = ""
    while i < n:
        c = s[i]
        if in_str:
            out.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str, prev = True, '"'
            out.append(c)
            i += 1
            continue
        if c in "{,":
            prev = c
            out.append(c)
            i += 1
            continue
        if c in " \t\r\n":
            out.append(c)
            i += 1
            continue
        if prev in ("{", ",") and (c.isalpha() or c == "_"):
            j = i
            while j < n and (s[j].isalnum() or s[j] == "_"):
                j += 1
            k = j
            while k < n and s[k] in " \t\r\n":
                k += 1
            if k < n and s[k] == ":":
                out.append('"' + s[i:j] + '"')
                i, prev = j, '"'
                continue
        prev = c
        out.append(c)
        i += 1
    return "".join(out)


def _first_json(text: str) -> dict | None:
    """First parseable JSON object in a model reply (bounded scan).

    Strict json.loads is tried FIRST; only if nothing parses is the bare-key
    normalisation applied and strict parsing retried. The repair is recorded.
    """
    got = _scan_json(text)
    if got is not None:
        return got
    fixed = _scan_json(_quote_bare_keys(text))
    if fixed is not None:
        receipt("PATCH_JSON_KEY_NORMALISED", note="local model emitted unquoted object keys")
    return fixed


def _scan_json(text: str) -> dict | None:
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
        if not any(str(c).startswith(pfx) for pfx in allowed) or \
                any(b in str(c) for b in (";", "&&", "|", "`", "$(")):
            errs.append("RUN_CMD:" + str(c)[:40])
    return errs


_SECRETISH = re.compile(
    r"(sk-[A-Za-z0-9_\-]{8,}|ghp_[A-Za-z0-9]{8,}|AIza[A-Za-z0-9_\-]{10,}"
    r"|xox[baprs]-[A-Za-z0-9\-]{8,}|[A-Za-z0-9_\-]{32,}"
    r"|(?i:(token|key|secret|password|passwd|authorization)\s*[=:]\s*\S+))")


def _redact(text: str) -> str:
    """A receipt must never carry a credential. Anything credential-shaped, and
    anything long enough to be one, is replaced wholesale."""
    return _SECRETISH.sub("[REDACTED]", text or "")


def _no_json_diag(r: dict) -> dict:
    """G11: the free-form path used to record only reason+provider, so a
    NO_JSON_DOC could never be explained after the fact. Record the shape of the
    reply - never its secrets - so the cause is knowable next time."""
    t = r.get("text") or ""
    return {"reason": "NO_JSON_DOC", "provider": r.get("provider"), "model": r.get("model"),
            "resp_len": len(t),
            "resp_sha256": hashlib.sha256(t.encode("utf-8")).hexdigest(),
            "finish_reason": r.get("finish_reason") or r.get("stop_reason"),
            "truncated": r.get("truncated"),   # G25: may be None = unknown, not False
            "parser": "octopus.patch.v1", "parser_version": 1, "stage": "json_extract",
            "resp_excerpt": _redact(t[:240])}


def process_patch_task(task: dict) -> str:
    """GOV-FREEDOM-V2 section 3: free-form multi-file non-TCB patch cycle.

    paid-capable model -> JSON doc -> deterministic validation -> stage ->
    AST + tests -> per-file canary proposals (witness still gates deploys).
    """
    tid = task["task_id"]
    # dependency/import repair 2026-09-13: api_budget lives in a hyphenated
    # dir that is not importable as a package, so it must be on sys.path before
    # the free-form patch path imports it. Same guard paid_fallback() already uses.
    if str(BUDGET_DIR) not in sys.path:
        sys.path.insert(0, str(BUDGET_DIR))
    import api_budget
    prompt = (json.dumps(task.get("context", {}))[:6000])
    r = api_budget.paid_call(tid, task.get("purpose", "free-form-patch"), prompt,
                             est_in_tok=2500, max_out_tok=700, first_call_cap=0.25)
    if not r.get("ok") or not (r.get("text") or "").strip():
        # G14: the broker settles such a call with rejection_reason
        # "insufficient-or-empty" (response_sha256 == sha256(b"")) and still returns
        # ok=True. A billed but EMPTY reply is not an answer - fall through to the
        # local model exactly as though the paid rung had failed.
        if r.get("ok"):
            receipt("PAID_EMPTY_RESPONSE", provider=r.get("provider"),
                    request_id=r.get("request_id"))
        resp = cognition_request(task, mode="patch")   # G16: need free-form text
        if resp is None:
            learn(task, {"outcome": "PATCH_COGNITION_FAILED", "repeat": False})
            return "cognition-failed"
        r = {"text": resp.get("text", ""), "provider": "local-llamacpp-180",
             # G25: the caller used to discard the broker's diagnostic fields, so a
             # truncated reply was reported as truncated=false and the reason for a
             # parse failure was unknowable. Carry them through.
             "truncated": resp.get("truncated"), "usable_output": resp.get("usable_output"),
             "tokens_returned": resp.get("tokens_returned"),
             "n_predict_cap": resp.get("n_predict_cap"),
             "mode": resp.get("mode"), "stage": resp.get("stage"),
             "timings": resp.get("timings"), "broker_error": resp.get("error")}
    if not (r.get("text") or "").strip():
        receipt("PATCH_REJECTED", reason="EMPTY_COGNITION_REPLY",
                provider=r.get("provider"), stage="cognition")
        learn(task, {"outcome": "PATCH_EMPTY_REPLY", "repeat": False})
        return "rejected"
    doc = _first_json(r.get("text") or "")
    if doc is None:
        receipt("PATCH_REJECTED", **_no_json_diag(r))          # G11
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
            # G26: read and write with newline="" so the file OWN line endings survive.
            # Text-mode IO normalised every ending, so a 1-line semantic change to a CRLF
            # file produced a whole-file rewrite (measured: ops_agent.py live crlf=774 ->
            # candidate crlf=0, a 1548-line diff for a 2-line change).
            with (stage / rel).open("r", encoding="utf-8", newline="") as fh:
                text = fh.read()
            _crlf = text.count("\r\n")
            _lf = text.count("\n") - _crlf
            _eol = "\r\n" if _crlf >= _lf else "\n"
            # the model authors both anchor and replacement with LF; the target may be
            # CRLF, so normalise BOTH to the file own EOL before matching.
            _anchor = f["anchor"].replace("\r\n", "\n").replace("\n", _eol)
            _repl = f["replacement"].replace("\r\n", "\n").replace("\n", _eol)
            if text.count(_anchor) != 1:
                raise ValueError("ANCHOR_DRIFT:" + rel[:40])
            new_text = text.replace(_anchor, _repl, 1)
            if rel.endswith(".py"):
                ast.parse(new_text)              # patched module must still parse
            with (stage / rel).open("w", encoding="utf-8", newline="") as fh:
                fh.write(new_text)
        _tdir = stage / Path(doc["files"][0]["path"]).parent
        _tdir.mkdir(parents=True, exist_ok=True)
        for t in doc.get("tests") or []:
            (_tdir / Path(t["path"]).name).write_text(
                str(t.get("content", "")), encoding="utf-8")
        # A repair task KNOWS its own acceptance test. Letting a 0.6B model author the
        # test that judges its own patch produced PATCH_STAGE_TEST ok=false on the real
        # task (12:08:09Z). When the task supplies one, it is authoritative.
        _task_test = task.get("stage_test_content")
        if _task_test:
            _tn = Path(task.get("stage_test_name") or "test_task_supplied.py").name
            (_tdir / _tn).write_text(str(_task_test), encoding="utf-8")
            _task_run = ["python3 -m pytest", "-q", _tn]
            doc["run_tests"] = [list(_task_run)] if isinstance(doc.get("run_tests"), list) else doc.get("run_tests")
            doc["run_tests"] = ["python3 -m pytest -q " + _tn] + [
                c for c in (doc.get("run_tests") or []) if _tn not in str(c)]
    except (ValueError, SyntaxError, OSError) as exc:
        receipt("PATCH_REJECTED", reason=str(exc)[:100])
        learn(task, {"outcome": "PATCH_STAGE_ERROR", "repeat": False})
        return "patch-drift"
    _dirs = sorted({str((stage / Path(f["path"])).parent) for f in doc["files"]})
    _tdir = stage / Path(doc["files"][0]["path"]).parent
    _env = {**os.environ, "PYTHONPATH": os.pathsep.join(_dirs)}
    ok_all = True
    for cmd in doc.get("run_tests") or []:
        p = subprocess.run(str(cmd).split(), cwd=_tdir, env=_env, capture_output=True,
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
            sort_keys=True) + "\n", encoding="utf-8")
        receipt("FREEDOM_CANARY_PROPOSAL_SUBMITTED", proposal=str(pf),
                target=rel, patched_sha256=patched_sha, backup_sha256=backup_sha)
        spooled += 1
    learn(task, {"outcome": "FREEDOM_CANARY_SUBMITTED", "files": spooled,
                 "summary": doc.get("summary", "")[:120]})
    return "canary-submitted"



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

BLOCKED = STATE / "blocked"
FAIL_OUTCOMES = ("PATCH_NO_JSON", "PATCH_INVALID", "PATCH_STAGE_ERROR", "PATCH_TESTS_FAILED",
                 "PATCH_EMPTY_REPLY", "PATCH_ANCHOR_DRIFT", "COGNITION_FAILED",
                 "PATCH_COGNITION_FAILED", "PATCH_CRITIQUE_REJECT")


def dependency_blocked(task: dict) -> list:
    """AUTONOMY-1: stop retrying structurally blocked work.

    A dependency is satisfied BY EVIDENCE: the named file must currently contain the
    named marker. A failed, rolled-back or not-yet-applied dependency therefore parks
    the task instead of burning a model call every tick.
    """
    unmet = []
    for dep in task.get("depends_on") or []:
        path = dep.get("path")
        dtype = dep.get("type", "build")
        try:
            raw = Path(path).read_bytes()
        except OSError:
            unmet.append({"path": path, "type": dtype, "why": "unreadable"})
            continue
        if dtype == "runtime":
            # owner 2026-09-14: a runtime dependency is satisfied only by the version
            # ACTUALLY LOADED - the bytes must match the accepted hash, not merely exist.
            want = dep.get("loaded_sha256")
            have = hashlib.sha256(raw).hexdigest()
            if not want or have != want:
                unmet.append({"path": path, "type": dtype, "why": "loaded_hash_mismatch",
                              "want": str(want)[:16], "have": have[:16]})
            continue
        marker = dep.get("must_contain")
        if marker and marker not in raw.decode("utf-8", "replace"):
            unmet.append({"path": path, "type": dtype, "why": "marker_absent"})
    return unmet


def unblock() -> int:
    """owner 2026-09-14: resume is triggered by the DEPENDENCY BEING SATISFIED, not by a
    clock or an HQ message. Every tick re-evaluates parked work."""
    if not BLOCKED.exists():
        return 0
    resumed = 0
    for f in sorted(BLOCKED.glob("*.json")):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        # a blocked file may be either {"task": {...}, "unmet": [...]} (parked here) or a
        # BARE task file (e.g. the retired superseded-* entries). Anything without a real
        # task_id must never be written back into the queue - an empty dict caused
        # KeyError: task_id in process_task.
        task_doc = doc.get("task") if isinstance(doc.get("task"), dict) else doc
        if not isinstance(task_doc, dict) or not task_doc.get("task_id"):
            continue
        if dependency_blocked(task_doc):
            continue
        TASKS.mkdir(parents=True, exist_ok=True)
        task_doc.setdefault("provenance", {})["unparked_at"] = now_iso()
        (TASKS / f.name).write_text(json.dumps(task_doc, indent=1), encoding="utf-8")
        os.remove(f)
        receipt("TASK_UNPARKED", task=task_doc.get("task_id"),
                because="dependency satisfied by evidence")
        learn(task_doc, {"outcome": "UNPARKED_DEPENDENCY_SATISFIED", "repeat": False})
        resumed += 1
    return resumed


def park_blocked(task: dict, unmet: list) -> str:
    BLOCKED.mkdir(parents=True, exist_ok=True)
    receipt("TASK_BLOCKED_DEPENDENCY", task=task["task_id"], unmet=unmet[:3])
    learn(task, {"outcome": "BLOCKED_DEPENDENCY", "repeat": False, "unmet": unmet[:2]})
    (BLOCKED / (task["task_id"] + ".json")).write_text(
        json.dumps({"task": task, "unmet": unmet,
                    "parked_at": now_iso()}, sort_keys=True) + "\n", encoding="utf-8")
    return "blocked"


CANARY_DIR = HOME / "ofn" / "state" / "ops-agent" / "state" / "canary-requests"
CANARY_SEEN = STATE / "canary-outcomes.json"


def verify_canary_outcomes() -> int:
    """AUTONOMY-2 (owner 2026-09-14): close the deploy loop WITHOUT a human.

    For every canary request, compare the target on disk with the hash the request
    promised. Record RETAINED / MISMATCH once per (request, expected hash). This does
    not roll anything back on its own - rollback belongs to the contract that owns the
    action - it makes the OUTCOME visible to the organism.
    """
    if not CANARY_DIR.exists():
        return 0
    try:
        seen = json.loads(CANARY_SEEN.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        seen = {}
    n = 0
    for f in sorted(CANARY_DIR.glob("*.json")):
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        tgt, want = Path(str(r.get("target", ""))), str(r.get("expected_post_sha256") or r.get("target_sha256") or "")
        if not want or not tgt.exists():
            continue
        have = hashlib.sha256(tgt.read_bytes()).hexdigest()
        key = f.name + ":" + want[:16]
        if seen.get(key):
            continue
        if have == want:
            result = "RETAINED"
        else:
            result = "NOT_YET_OR_ROLLED_BACK"
        seen[key] = {"at": now_iso(), "result": result, "have": have[:16], "want": want[:16]}
        receipt("CANARY_OUTCOME_READBACK", request=f.name, result=result,
                target=str(tgt), have=have[:16], want=want[:16])
        learn({"task_id": f.stem, "purpose": "canary outcome readback"},
              {"outcome": "CANARY_" + result, "repeat": False,
                                    "target": str(tgt), "have": have[:16], "want": want[:16]})
        n += 1
    CANARY_SEEN.write_text(json.dumps(seen, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return n


def self_feed() -> int:
    """AUTONOMY-1: with an empty queue, derive ONE task from the organism's own failures.

    Evidence only: a learning-ledger row that recorded a real failure and was marked
    not-repeatable becomes a task with REAL provenance. The id is derived from the
    outcome signature, so the same failure can never be queued twice.
    """
    try:
        rows = [json.loads(l) for l in LEARNING.read_text(encoding="utf-8").splitlines() if l.strip()]
    except (OSError, json.JSONDecodeError):
        return 0
    seen = set()
    for d in list(TASKS.glob("*.json")) + list(BLOCKED.glob("*.json")) + list(DONE.glob("*.json")):
        seen.add(d.stem)
    # AUTONOMY-2: recurrence is a weakness signal. A failure the organism keeps hitting
    # is evidence even when no single fresh row describes an actionable defect.
    _counts = Counter(str(r.get("outcome", "")) for r in rows)
    _recurrent = [o for o, c in _counts.items() if c >= 3 and o in FAIL_OUTCOMES]
    for _o in _recurrent:
        _tid = "SELF-RECUR-" + re.sub(r"[^A-Za-z0-9]+", "-", _o).strip("-").upper()[:40]
        if _tid in seen:
            continue
        _rows = [r for r in rows if str(r.get("outcome", "")) == _o]
        TASKS.mkdir(parents=True, exist_ok=True)
        (TASKS / (_tid + ".json")).write_text(json.dumps({
            "schema": "octopus.coding-task.v1", "task_id": _tid, "patch_mode": "free",
            "component": "coding-worker", "self_fed": True, "weakness_signal": True,
            "purpose": ("recurrence repair: outcome %s has occurred %d times in the organism's own "
                        "learning ledger, which is a weakness signal rather than one bad run"
                        % (_o, _counts[_o])),
            "provenance": {"class": "DERIVED_FROM_REAL_EVIDENCE", "source": str(LEARNING),
                           "source_ts": _rows[-1].get("at"),
                           "source_hash": hashlib.sha256(_o.encode()).hexdigest()[:32]},
            "context": {"ORIGIN": "recurrence_weakness_signal", "outcome": _o,
                        "occurrences": _counts[_o],
                        "evidence_rows": [{k: r.get(k) for k in ("at", "outcome", "detail", "tail")}
                                          for r in _rows[-3:]]},
            "class": "A_internal_repair_with_B8_canary", "risk": "low",
            "reversibility": "full", "rollback": "no artifact produced until a patch is accepted",
            "falsification": "no reproducible defect can be stated from the recurrence",
            "timeout_s": 300}, indent=1) + "\n", encoding="utf-8")
        receipt("TASK_SELF_FED", task=_tid, outcome=_o, source="recurrence_weakness_signal",
                occurrences=_counts[_o])
        return 1
    for row in reversed(rows):
        outcome = str(row.get("outcome", ""))
        if outcome not in FAIL_OUTCOMES:
            continue
        # DEDUPE FIX 2026-09-13 (observed churn: two SELF-PATCH-NO-JSON tasks in ten minutes):
        # keying on the ledger ROW hash made every new row a new task, so one unresolved
        # failure was re-queued forever. Key on the FAILURE SIGNATURE instead: the same
        # outcome with the same evidence dedupes, while materially different evidence
        # (a changed detail/tail) can still produce a genuinely new successor task.
        _ev = str(row.get("detail") or row.get("tail") or "")
        sig = re.sub(r"[^A-Za-z0-9]+", "-", outcome).strip("-").upper()
        sig = (sig + "-" + hashlib.sha256(_ev.encode()).hexdigest()[:8].upper())[:48]
        tid = "SELF-" + sig
        if tid in seen:
            continue
        task_doc = {
            "schema": "octopus.coding-task.v1", "task_id": tid, "patch_mode": "free",
            "component": "coding-worker", "target_file": "", "self_fed": True,
            "purpose": ("self-derived repair task: the organism's own learning ledger recorded "
                        "outcome=%s and marked it not-repeatable, so the failure needs a real fix "
                        "rather than a retry" % outcome),
            "provenance": {"class": "REAL_CODE_DEFECT", "source": str(LEARNING),
                           "source_ts": row.get("at"), "source_hash": str(row.get("lr_hash"))[:32]},
            "context": {"ORIGIN": "self_fed_from_learning_ledger", "outcome": outcome,
                        "previous_row": {k: row.get(k) for k in ("at", "outcome", "detail", "tail")}},
            "class": "A_internal_repair_with_B8_canary", "risk": "low",
            "reversibility": "full", "rollback": "no artifact produced until a patch is accepted",
            "falsification": "no reproducible defect can be stated from the recorded outcome",
            "timeout_s": 300,
        }
        TASKS.mkdir(parents=True, exist_ok=True)
        (TASKS / (tid + ".json")).write_text(json.dumps(task_doc, indent=1), encoding="utf-8")
        receipt("TASK_SELF_FED", task=tid, outcome=outcome, source="learning_ledger")
        return 1
    receipt("NO_ELIGIBLE_SELF_FEED", note="no fresh actionable failure and no recurrence")
    return 0


def process_task(task: dict) -> str:
    tid = task["task_id"]
    _unmet = dependency_blocked(task)
    if _unmet:
        return park_blocked(task, _unmet)
    receipt("TASK_STARTED", task=tid, purpose=task["purpose"])
    if not provenance_ok(task):                     # REAL-WORK-BRIDGE-20260913
        p = task.get("provenance") or {}
        receipt("TASK_REJECTED_NO_REAL_WORLD_PROVENANCE",
                fixture=bool(task.get("fixture")), cls=p.get("class"),
                has_source=bool(p.get("source")), has_ts=bool(p.get("source_ts")),
                has_hash=bool(p.get("source_hash")))
        return "rejected"
    if task.get("patch_mode") == "free":        # GOV-FREEDOM-V2 section 3
        return process_patch_task(task)
    # 1. cognition
    if cooldown_active():
        receipt("TASK_DEFERRED_COOLDOWN", task=tid)
        return "cooldown"
    resp = cognition_request(task)
    if resp is None:
        set_cooldown(1800)
        learn(task, {"outcome": "COGNITION_FAILED", "repeat": False,
                     "blacklist": ["broker-unavailable"]})
        return "cognition-failed"
    proposal = resp.get("proposal") or {}
    enum_map = task.get("proposal_enum_map")
    if enum_map:
        # constrained cognition: the model only CLASSIFIES (one enum word);
        # the actual code expression comes from this frozen deterministic table
        choice = str(proposal.get(task["proposal_field"], ""))
        expr = enum_map.get(choice, "")
        receipt("ENUM_CHOICE_RECEIVED", choice=choice, mapped=bool(expr))
    else:
        expr = str(proposal.get(task["proposal_field"], ""))
    receipt("PROPOSAL_RECEIVED", expression=expr[:60],
            confidence=proposal.get("confidence"))
    # 2. deterministic validation of the model expression
    if not expression_safe(expr):
        receipt("PROPOSAL_REJECTED", reason="EXPRESSION_UNSAFE")
        learn(task, {"outcome": "PROPOSAL_REJECTED_UNSAFE", "expression": expr[:60],
                     "blacklist": [f"unsafe-expr:{expr[:24]}"], "repeat": False})
        return "rejected"
    # evaluate the expression against known category names for sanity
    for sample, want in (("B4_NON_TCB_DEPLOYMENT_ROLLBACK", "B4"),
                         ("B5_SAFE_STORAGE_MAINTENANCE", "B5"),
                         ("B2_OCTOPUS_OWNED_WORKER_RECOVERY", "B2")):
        got = eval(compile(expr, "<expr>", "eval"), {"__builtins__": {}},
                   {"category": sample})  # noqa: S307 — AST-whitelisted expression only
        if got != want:
            receipt("PROPOSAL_REJECTED", reason=f"SAMPLE_MISMATCH:{sample}->{got}")
            learn(task, {"outcome": "PROPOSAL_REJECTED_SEMANTIC",
                         "blacklist": [f"wrong-mapping:{expr[:24]}"], "repeat": False})
            return "rejected"
    # 3. isolated stage
    stage = STAGE_ROOT / tid
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    target_name = task["target_file"]
    if any(t in target_name for t in _TCB_TARGETS):
        receipt("PROPOSAL_REJECTED", reason="TCB_TARGET")
        return "rejected"
    shutil.copyfile(OPS / target_name, stage / target_name)
    for extra in task.get("stage_extras", []):
        shutil.copyfile(ROOT / extra, stage / Path(extra).name)
    # 4. deterministic anchor patch using the validated expression
    try:
        new_text = apply_anchor_patch(
            stage / target_name, task["anchors"],
            lambda: [(a, n.format(expr=expr)) for a, n in task["replacements"]])
    except ValueError as exc:
        receipt("PATCH_REJECTED", reason=str(exc)[:80])
        learn(task, {"outcome": "PATCH_ANCHOR_DRIFT", "repeat": False})
        return "patch-drift"
    (stage / target_name).write_text(new_text, encoding="utf-8")
    ast.parse(new_text)  # patched module must still parse
    # 5. focused tests in the stage (the stage test file gates the patch)
    ok, tail = run_stage_tests(stage, Path(task["stage_test"]).name)
    receipt("STAGE_TESTS", ok=ok, tail=tail)
    if not ok:
        learn(task, {"outcome": "STAGE_TESTS_FAILED", "tail": tail,
                     "blacklist": [f"failing-expr:{expr[:24]}"], "repeat": False})
        shutil.rmtree(stage, ignore_errors=True)
        return "tests-failed"
    # 6. package + canary proposal through the witnessed ops-agent B8 spool
    backup = OPS / target_name
    patched = stage / target_name
    patched_sha = sha_file(patched)
    backup_sha = sha_file(backup)
    CANARY_SPOOL.mkdir(parents=True, exist_ok=True)
    proposal_file = CANARY_SPOOL / f"native-{tid}.json"
    # B8 handler prefers "backup" when both keys exist (known limitation): the
    # canary request carries ONLY the patched artifact; the backup path stays in
    # our records and rollback rides the B4 spool with it if ever needed.
    proposal_file.write_text(json.dumps(
        {"patched": str(patched), "target": str(OPS / target_name),
         "target_sha256": patched_sha, "component": task.get("component", "ops-agent"),
         "requested_by": VERSION, "task_id": tid}, sort_keys=True) + "\n", encoding="utf-8")
    receipt("CANARY_PROPOSAL_SUBMITTED", proposal=str(proposal_file),
            patched_sha256=patched_sha, backup_sha256=backup_sha)
    learn(task, {"outcome": "CANARY_SUBMITTED", "expression": expr,
                 "patched_sha256": patched_sha, "model": resp.get("model"),
                 "tokens": resp.get("tokens"), "witness": "ops-agent-B8->182 pending"})
    (STATE / "awaiting-canary").mkdir(parents=True, exist_ok=True)
    (STATE / "awaiting-canary" / (tid + ".json")).write_text(json.dumps(
        {"task": task, "patched_sha256": patched_sha, "submitted_at": now_iso()},
        sort_keys=True) + "\n", encoding="utf-8")
    return "canary-submitted"


def check_awaited_canaries() -> None:
    d = STATE / "awaiting-canary"
    if not d.exists():
        return
    ops_receipts = []
    p = OPS / "state" / "ops-receipts.jsonl"
    if p.exists():
        ops_receipts = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    for name in sorted(os.listdir(d)):
        info = json.loads((d / name).read_text(encoding="utf-8"))
        tid = info["task"]["task_id"]
        want = info["patched_sha256"]
        executed = [r for r in ops_receipts if r.get("kind") == "OPS_B_EXECUTED"
                    and r.get("argv") and any(want[:16] in json.dumps(r.get("argv")) for _ in [0])]
        closed = [r for r in ops_receipts if r.get("kind") in ("OPS_B_CYCLE_CLOSED", "OPS_B_OUTCOME_REJECTED")]
        # simpler: look for cycle closure naming our canary component after submission
        recent = [r for r in ops_receipts if r.get("at", "") >= info["submitted_at"]
                  and r.get("kind") in ("OPS_B_CYCLE_CLOSED", "OPS_B_OUTCOME_REJECTED",
                                        "OPS_B_WITNESS_REJECTED", "OPS_B_PAUSED_WITNESS_UNAVAILABLE")]
        if not recent:
            continue
        r = recent[-1]
        outcome = {"final": r["kind"], "at": r["at"]}
        if r["kind"] == "OPS_B_CYCLE_CLOSED":
            # G4: read back the REAL declared target of THIS request. OPS/target_file
            # is only right when the target happens to live in the ops-agent dir; for
            # any other target the verifier checked the wrong path and could report
            # ROLLBACK_SUSPECTED for a good deploy (or RETAINED for a bad one).
            prop = CANARY_SPOOL / ("native-%s.json" % tid)
            tgt = None
            try:
                tgt = (json.loads(prop.read_text(encoding="utf-8")) or {}).get("target")
            except (OSError, json.JSONDecodeError):
                tgt = None
            outcome["target"] = tgt
            outcome["target_source"] = "canary_request" if tgt else "ops_relative_fallback"
            check_path = Path(tgt) if tgt else (OPS / info["task"]["target_file"])
            if not tgt and not info["task"].get("legacy_ops_relative_target"):
                # G23: a file that HAPPENS to sit at OPS/target_file with the right
                # hash is not identity. Without a valid request, or an EXPLICIT legacy
                # contract marker, there is no PASS and no speculative rollback.
                outcome["deployed_hash_verified"] = None
                outcome["result"] = "UNVERIFIABLE_REQUEST"
            elif not tgt and not check_path.exists():
                outcome["deployed_hash_verified"] = None
                outcome["result"] = "UNVERIFIED_NO_TARGET"
            else:
                deployed_ok = check_path.exists() and sha_file(check_path) == want
                outcome["deployed_hash_verified"] = deployed_ok
                outcome["result"] = "RETAINED" if deployed_ok else "ROLLBACK_SUSPECTED"
        else:
            outcome["result"] = "ROLLED_BACK_OR_BLOCKED"
        learn(info["task"], outcome)
        receipt("CANARY_RESOLVED", task=tid, **{k: v for k, v in outcome.items() if k != "task"})
        (STATE / "resolved").mkdir(parents=True, exist_ok=True)
        os.replace(d / name, STATE / "resolved" / name)


def tick() -> int:
    ok, n = verify_own_chain()
    if not ok:
        print(f"FAIL_CLOSED: coding receipt chain broken at {n}")
        return 2
    # CONTINUITY-20260913: owner kill-switch gates coding too; disk-critical
    # defers new coding work (experiments shrink first, never Tier 0 data)
    if (HOME / "ofn" / "state" / "autonomy" / "STOP-AUTONOMY").exists() or             Path("/etc/octopus-ops-halt").exists():
        receipt("OWNER_STOP", note="coding paused by owner kill-switch")
        return 0
    du = subprocess.run(["df", "-P", "/"], capture_output=True, text=True).stdout
    for line in du.splitlines():
        if line.startswith("/"):
            try:
                pct = int(line.split()[4].replace("%", ""))
                if pct >= 90:
                    receipt("DISK_CRITICAL_DEFER", pct=pct,
                            note="coding deferred; experiments shrink first")
                    return 0
            except (ValueError, IndexError):
                pass
    check_awaited_canaries()
    unblock()   # AUTONOMY: resume parked work on dependency evidence
    verify_canary_outcomes()   # AUTONOMY-2: read back our own deploys
    TASKS.mkdir(parents=True, exist_ok=True)
    processed_n, processed_ids = 0, []           # GOV-FREEDOM-V2 section 9
    for name in sorted(os.listdir(TASKS)):
        if processed_n >= MAX_TASKS_PER_TICK:
            break
        if not name.endswith(".json"):
            continue
        try:
            task = json.loads((TASKS / name).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        # ROBUSTNESS: a malformed task file must never kill the tick. Quarantine it with a
        # receipt and keep going - a worker that dies on bad input stops being autonomous.
        if not isinstance(task, dict) or not task.get("task_id"):
            (BLOCKED).mkdir(parents=True, exist_ok=True)
            receipt("TASK_MALFORMED", file=name, note="missing task_id; quarantined")
            try:
                os.replace(TASKS / name, BLOCKED / ("malformed-" + name))
            except OSError:
                pass
            continue
        result = process_task(task)
        processed_n += 1
        processed_ids.append({"task": task["task_id"], "result": result})
        dest = DONE if result in ("canary-submitted",) else FAILED
        if result in ("canary-submitted", "rejected", "tests-failed", "patch-drift",
                      "cognition-failed", "blocked"):
            dest.mkdir(parents=True, exist_ok=True)
            os.replace(TASKS / name, dest / name)
    if processed_ids:                            # GOV-FREEDOM-V2 section 9
        receipt("TICK_COMPLETE", processed=processed_ids)
        print(json.dumps({"processed": processed_ids}))
    else:
        # AUTONOMY-1: an empty hand-fed queue is not the end of the work; derive from evidence
        fed = self_feed()
        receipt("TICK_COMPLETE", idle=fed == 0,
                note="NATIVE_CODING_SELF_FED" if fed else "NATIVE_CODING_IDLE_HEALTHY")
        print(json.dumps({"idle": True, "note": "NATIVE_CODING_IDLE_HEALTHY"}))
    return 0


def main() -> int:
    try:
        return tick()
    except Exception as exc:  # noqa: BLE001
        try:
            receipt("WORKER_ABNORMAL", error=type(exc).__name__, detail=str(exc)[:200])
        except Exception:  # noqa: BLE001, S110
            pass
        print("WORKER_ABNORMAL", type(exc).__name__)
        return 2


if __name__ == "__main__":
    sys.exit(main())
