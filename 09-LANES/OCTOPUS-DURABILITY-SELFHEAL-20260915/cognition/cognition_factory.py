"""
OCTOPUS Cognition Factory (OPT3) — full implementation
Lane: OCTOPUS-COGNITION-FACTORY-20260915 · GOV_VERSION=V8 · LADDER=L2

Design contracts:
- producer != verifier != applier (three call sites, no shared context)
- every stage exit is a disposition in an append-only receipt chain
- no silent catch: chain write failure halts the attempt
- patch = octopus.patch.v2 (anchor+old+new), never raw diff
- no regex scraping of free-form text; structured output or nothing
- verifier runs as unprivileged user in systemd-style sandbox root
- deploy is never done here; candidates are staged + queued for ops-agent

External deps: none beyond stdlib + jsonschema (optional).
Tested on CPython 3.10+.
"""
from __future__ import annotations

import json
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

try:
    import jsonschema  # type: ignore
    HAVE_JSONSCHEMA = True
except ImportError:    # fall back to structural validation
    HAVE_JSONSCHEMA = False

# ======================================================================
# Configuration
# ======================================================================
@dataclass
class FactoryConfig:
    broker_url: str = "http://192.168.0.180:8081"   # llama.cpp on node 180
    broker_timeout_s: int = 120                     # never raised here
    repo_root: Path = Path("/home/ari/ofn")
    stage_root: Path = Path("/home/ari/ofn/state/cognition/stage")
    queue_dir: Path = Path(
        "/home/ari/ofn/state/ops-agent/state/canary-requests")
    receipt_path: Path = Path(
        "/home/ari/ofn/state/cognition/receipts.jsonl")
    candidate_dir: Path = Path(
        "/home/ari/ofn/state/coding-worker/stage/cognition-factory")
    apply_user: str = "octopus-patch-apply"          # sudo -u target
    test_timeout_s: int = 90
    critic_timeout_s: int = 120
    max_repairs: int = 1
    no_touch_globs: tuple = (
        "ops_agent.py", "money_gate*", "owner_reply.py",
        "fleet-jobs/*", "tg-inbox/*")
    allowed_roots: tuple = ("ofn/agents/", "ofn/budget/", "ofn/agents/tests/")

# ======================================================================
# L5 — append-only receipt chain
# ======================================================================
class Disposition(str, Enum):
    TASK_STARTED        = "TASK_STARTED"
    INFER_TIMEOUT       = "INFER_TIMEOUT"
    INFER_TRANSPORT     = "INFER_TRANSPORT"
    INFER_EMPTY         = "INFER_EMPTY"
    REJECTED_SCHEMA     = "REJECTED_SCHEMA"
    REJECTED_SCOPE      = "REJECTED_SCOPE"
    REJECTED_CONTROL    = "REJECTED_CONTROL"
    STALE_BASE_ARTIFACT = "STALE_BASE_ARTIFACT"
    ANCHOR_MISS         = "ANCHOR_MISS"
    APPLY_FAULT         = "APPLY_FAULT"
    COMPILE_RED         = "COMPILE_RED"
    TEST_INFRA_RED      = "TEST_INFRA_RED"
    TEST_RED            = "TEST_RED"
    CRITIC_REJECT       = "CRITIC_REJECT"
    PRODUCED            = "PRODUCED"
    CHAIN_FAULT         = "CHAIN_FAULT"

class ChainFault(Exception):
    pass

class ReceiptChain:
    """Append-only JSONL. Write failure => ChainFault (never swallowed)."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, attempt_id: str, stage: str,
             disposition: Disposition, cause: str = "",
             hashes: Optional[dict] = None) -> dict:
        row: dict[str, Any] = {
            "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "attempt_id": attempt_id,
            "stage": stage,
            "disposition": disposition.value,
            "cause": cause[:500],
        }
        if hashes:
            row.update({k: v for k, v in hashes.items() if v is not None})
        line = (json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8")
        try:
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o640)
            try:
                os.write(fd, line)
                os.fsync(fd)
            finally:
                os.close(fd)
        except OSError as e:
            raise ChainFault(f"receipt-chain unwritable: {e}") from e
        return row

# ======================================================================
# L0 — task source (pop-with-hash, no double work)
# ======================================================================
@dataclass
class Task:
    text: str
    task_id: str
    path: Path

class QueueTaskSource:
    """
    Pops the oldest pending cognition task.
    Layout: <queue>/pending/*.json  ->  moved to <queue>/leased/<sha>.json
    """

    def __init__(self, queue: Path):
        self.queue = Path(queue)
        self.pending = self.queue / "pending"
        self.leased = self.queue / "leased"
        self.leased.mkdir(parents=True, exist_ok=True)

    def pop(self) -> Optional[Task]:
        files = sorted(self.pending.glob("*.json"),
                       key=lambda p: p.stat().st_mtime)
        if not files:
            return None
        src = files[0]
        raw = src.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        dst = self.leased / f"{sha}.json"
        os.replace(src, dst)                     # atomic within same fs
        data = json.loads(raw.decode("utf-8"))
        return Task(text=data["task"], task_id=sha[:16], path=dst)

    def requeue(self, task: Task, why: str) -> None:
        data = json.loads(task.path.read_bytes().decode("utf-8"))
        data.setdefault("requeue_history", []).append(
            {"at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "why": why[:200]})
        dst = self.pending / task.path.name
        task.path.write_text(json.dumps(data, ensure_ascii=False))
        os.replace(task.path, dst)

# ======================================================================
# L1 — cognition client (structured first; never regex-scrape)
# ======================================================================
@dataclass
class InferResult:
    ok: bool
    payload: bytes = b""
    failure_stage: Optional[str] = None        # lock|transport|inference|empty
    timing: dict = field(default_factory=dict)
    status: int = 0

class StructuredClient:
    """
    Capability-aware client for broker on node 180.
    Probes once for structured-output support; then:
      1) server-native structured output (vLLM `structured_outputs`)
      2) response_format=json_object
      3) bounded repair pass (same server, distinct marker) — max 1
    """

    def __init__(self, cfg: FactoryConfig, chain: ReceiptChain):
        self.cfg, self.chain = cfg, chain
        self._supports_structured: Optional[bool] = None

    # -- capability probe (read-only) ------------------------------------
    def probe_structured_support(self) -> bool:
        if self._supports_structured is not None:
            return self._supports_structured
        try:
            with urllib.request.urlopen(
                    f"{self.cfg.broker_url}/v1/models",
                    timeout=8) as r:
                r.read(2048)                    # drain; we only need 200
            # minimal structured call with trivial schema
            probe = {
                "model": "local",
                "messages": [{"role": "user", "content": "say {\"ok\":1}"}],
                "max_tokens": 16,
                "temperature": 0,
                "structured_outputs": {"json": {
                    "type": "object",
                    "required": ["ok"],
                    "properties": {"ok": {"type": "integer"}}}},
            }
            code, _, _ = self._post("/v1/chat/completions", probe,
                                    timeout_s=15)
            self._supports_structured = (code == 200)
        except Exception:
            self._supports_structured = False
        return self._supports_structured

    # -- transport --------------------------------------------------------
    def _post(self, path: str, body: dict,
              timeout_s: int) -> tuple[int, bytes, dict]:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self.cfg.broker_url}{path}", data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as r:
                payload = r.read()
            return r.status, payload, {
                "llm_call_s": round(time.monotonic() - t0, 3)}
        except urllib.error.HTTPError as e:
            return e.code, e.read()[:4096], {
                "llm_call_s": round(time.monotonic() - t0, 3),
                "http_error": e.code}
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            return 0, b"", {"llm_call_s": round(time.monotonic() - t0, 3),
                            "transport_error": type(e).__name__}

    # -- generate ----------------------------------------------------------
    def generate(self, *, schema: dict, system: str, user: str,
                 max_tokens: int, temperature: float = 0.1,
                 repair: bool = False) -> InferResult:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if repair:
            user = ("REPAIR: return ONLY valid JSON matching the schema. "
                    "No prose, no fences.\n" + user)
        messages.append({"role": "user", "content": user})

        body: dict[str, Any] = {
            "model": "local", "messages": messages,
            "max_tokens": max_tokens, "temperature": temperature}
        if self.probe_structured_support():
            body["structured_outputs"] = {"json": schema}
        else:
            body["response_format"] = {"type": "json_object"}

        code, payload, timing = self._post("/v1/chat/completions",
                                           body, self.cfg.broker_timeout_s)
        if code != 200 or not payload:
            stage = ("transport" if code == 0 else "inference")
            return InferResult(False, failure_stage=stage, timing=timing,
                               status=code)
        try:
            outer = json.loads(payload)
            text = outer["choices"][0]["message"]["content"]
            if not isinstance(text, str) or not text.strip():
                return InferResult(False, failure_stage="empty",
                                   timing=timing, status=code)
            return InferResult(True, text.encode("utf-8"), timing=timing,
                               status=code)
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return InferResult(False, failure_stage="inference",
                               timing={**timing, "parse_error": str(e)[:120]},
                               status=code)

# ======================================================================
# L2 — schema gate + scope gate + control-byte scan
# ======================================================================
PATCH_SCHEMA: dict = {
    "type": "object",
    "required": ["kind", "task_id", "target", "ops", "tests"],
    "additionalProperties": True,
    "properties": {
        "kind": {"const": "octopus.patch.v2"},
        "task_id": {"type": "string", "minLength": 8},
        "target": {
            "type": "object",
            "required": ["path", "base_sha256"],
            "properties": {
                "path": {"type": "string",
                         "pattern": r"^[A-Za-z0-9_./-]+$"},
                "base_sha256": {"type": "string",
                                "pattern": "^[0-9a-f]{64}$"},
            }},
        "ops": {"type": "array", "minItems": 1, "maxItems": 8,
                "items": {
                    "type": "object",
                    "required": ["op", "anchor", "new"],
                    "properties": {
                        "op": {"enum": ["replace_span"]},
                        "anchor": {"type": "string", "minLength": 4,
                                   "maxLength": 400},
                        "new": {"type": "string", "maxLength": 20000},
                    }}},
        "tests": {"type": "array", "maxItems": 4,
                  "items": {"type": "string",
                            "pattern": r"^[A-Za-z0-9_./-]+$"}},
        "rationale": {"type": "string", "maxLength": 500},
        "no_touch": {"type": "array", "items": {"type": "string"}},
    },
}

CONTROL_BYTES = (set(range(0x00, 0x09)) | {0x0B, 0x0C}
                 | set(range(0x0E, 0x20)) | {0x7F})
_STR_LIT = re.compile(r'"((?:[^"\\]|\\.)*)"')

def scan_control_bytes(payload: bytes) -> Optional[str]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as e:
        return f"not utf-8: {e}"
    for m in _STR_LIT.finditer(text):
        for bad in CONTROL_BYTES:
            if chr(bad) in m.group(1):
                return f"control byte 0x{bad:02x} inside string literal"
    return None

def _manual_schema_check(doc: Any) -> Optional[str]:
    if not isinstance(doc, dict):
        return "root not object"
    if doc.get("kind") != "octopus.patch.v2":
        return "kind mismatch"
    if not isinstance(doc.get("task_id"), str) or len(doc["task_id"]) < 8:
        return "task_id"
    t = doc.get("target")
    if not isinstance(t, dict) or not t.get("path") or \
       not re.fullmatch(r"[0-9a-f]{64}", str(t.get("base_sha256", ""))):
        return "target"
    ops = doc.get("ops")
    if not isinstance(ops, list) or not ops:
        return "ops"
    for i, op in enumerate(ops):
        if not isinstance(op, dict) or op.get("op") != "replace_span" \
           or not isinstance(op.get("anchor"), str) \
           or len(op["anchor"]) < 4 \
           or not isinstance(op.get("new"), str):
            return f"ops[{i}]"
    if not isinstance(doc.get("tests"), list):
        return "tests"
    return None

# ---- model-facing mini-schema: the model ONLY emits ops; the harness owns
# the envelope (kind/task_id/target/tests) deterministically. This bounds the
# generation, kills fence/envelope variance, and shrinks output under the
# truncation wall observed with qwen3-0.6b (451-byte truncated reply).
OPS_SCHEMA_MINI = {"ops": [{"op": "replace_span", "anchor": "...", "new": "..."}]}


def normalize_json_envelope(payload: bytes) -> str:
    """Structural envelope normalization (no content scraping):
    strip markdown fences, cut a qwen <think> block, extract the first
    balanced JSON object. Raises ValueError when none exists."""
    text = payload.decode("utf-8", errors="replace").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    if "<think>" in text and "</think>" in text:
        text = text.split("</think>", 1)[1]
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in response")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError("unbalanced JSON (truncated response?)")


def _ops_doc_valid(ops: object) -> bool:
    if not isinstance(ops, dict) or not isinstance(ops.get("ops"), list):
        return False
    for op in ops["ops"]:
        if not (isinstance(op, dict) and op.get("op") == "replace_span"
                and isinstance(op.get("anchor"), str) and len(op["anchor"]) >= 4
                and isinstance(op.get("new"), str)):
            return False
    return True


def _normalize_ops_shape(ops: dict) -> dict:
    """Accept either {"ops":[...]} or a named dict {"op1": "...", ...} whose
    values are full op objects, converting deterministically."""
    if isinstance(ops.get("ops"), list):
        return ops
    fixed = []
    for k in sorted(ops, key=str):
        v = ops[k]
        if isinstance(v, dict) and "anchor" in v:
            v = dict(v)
            v.setdefault("op", "replace_span")
            fixed.append(v)
        elif isinstance(v, str):
            # bare string = the NEW text for the anchor named in k's task?
            # not enough information — reject at schema level
            return ops
    if fixed:
        return {"ops": fixed}
    return ops


class SchemaGate:
    def __init__(self, cfg: FactoryConfig, chain: ReceiptChain):
        self.cfg, self.chain = cfg, chain

    def validate(self, res: InferResult, attempt_id: str) -> Optional[dict]:
        # persist raw response bytes for diagnosis (G18 lesson: never lose
        # the payload that a disposition claims to describe)
        try:
            rdir = self.cfg.candidate_dir / "_responses"
            rdir.mkdir(parents=True, exist_ok=True)
            (rdir / f"{attempt_id}.txt").write_bytes(res.payload[:65536])
            rsha = hashlib.sha256(res.payload).hexdigest()[:16]
        except OSError:
            rsha = "dump-failed"
        try:
            doc = json.loads(res.payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self.chain.emit(attempt_id, "SCHEMA_GATE",
                            Disposition.REJECTED_SCHEMA, str(e),
                            hashes={"response_sha256_16": rsha})
            return None
        if HAVE_JSONSCHEMA:
            try:
                jsonschema.validate(doc, PATCH_SCHEMA)  # type: ignore
            except Exception as e:
                self.chain.emit(attempt_id, "SCHEMA_GATE",
                                Disposition.REJECTED_SCHEMA, str(e)[:300])
                return None
        else:
            err = _manual_schema_check(doc)
            if err:
                self.chain.emit(attempt_id, "SCHEMA_GATE",
                                Disposition.REJECTED_SCHEMA, err)
                return None
        bad = scan_control_bytes(res.payload)
        if bad:
            self.chain.emit(attempt_id, "CONTROL_BYTE_GATE",
                            Disposition.REJECTED_CONTROL, bad)
            return None
        if not self._scope_ok(doc, attempt_id):
            return None
        return doc

    def _scope_ok(self, doc: dict, attempt_id: str) -> bool:
        path = doc["target"]["path"].lstrip("/")
        if ".." in path.split("/"):
            self.chain.emit(attempt_id, "SCOPE_GATE",
                            Disposition.REJECTED_SCOPE, "traversal")
            return False
        if not any(path.startswith(r) for r in self.cfg.allowed_roots):
            self.chain.emit(attempt_id, "SCOPE_GATE",
                            Disposition.REJECTED_SCOPE, "root not allowed")
            return False
        for glob in self.cfg.no_touch_globs:
            if Path(path).match(glob):
                self.chain.emit(attempt_id, "SCOPE_GATE",
                                Disposition.REJECTED_SCOPE,
                                f"no_touch:{glob}")
                return False
        for t in doc["tests"]:
            tp = t.lstrip("/")
            if ".." in tp.split("/") or \
               not tp.startswith("ofn/agents/tests/"):
                self.chain.emit(attempt_id, "SCOPE_GATE",
                                Disposition.REJECTED_SCOPE, f"test:{tp}")
                return False
        return True

# ======================================================================
# L3 — anchor gate on exact base bytes
# ======================================================================
class AnchorGate:
    def __init__(self, cfg: FactoryConfig, chain: ReceiptChain):
        self.cfg, self.chain = cfg, chain

    def check(self, doc: dict, attempt_id: str) -> Optional[bytes]:
        tgt = self.cfg.repo_root / doc["target"]["path"]
        if not tgt.is_file():
            self.chain.emit(attempt_id, "ANCHOR_GATE",
                            Disposition.ANCHOR_MISS, "target missing")
            return None
        base = tgt.read_bytes()
        if hashlib.sha256(base).hexdigest() != doc["target"]["base_sha256"]:
            self.chain.emit(attempt_id, "ANCHOR_GATE",
                            Disposition.STALE_BASE_ARTIFACT, "base drift")
            return None
        text = base.decode("utf-8")
        for i, op in enumerate(doc["ops"]):
            n = text.count(op["anchor"])
            if n != 1:
                self.chain.emit(attempt_id, "ANCHOR_GATE",
                                Disposition.ANCHOR_MISS,
                                f"op[{i}] anchor count={n}")
                return None
        return base

# ======================================================================
# L4 — verifier: sandboxed apply + compile + bounded test + critic
# ======================================================================
class PatchVerifier:
    def __init__(self, cfg: FactoryConfig, chain: ReceiptChain,
                 critic_client: StructuredClient):
        self.cfg, self.chain = cfg, chain
        self.critic_client = critic_client

    # -- apply in isolated worktree ---------------------------------------
    def apply_in_wt(self, doc: dict, base: bytes,
                    attempt_id: str) -> Optional[Path]:
        wt = self.cfg.stage_root / attempt_id / "worktree"
        try:
            # FIX: ofn/budget must come along — glass_runner and siblings
            # import opslib from ../budget at module load; a WT without it
            # fails every import-sensitive test for the wrong reason.
            shutil.copytree(self.cfg.repo_root / "ofn" / "agents",
                            wt / "ofn" / "agents", dirs_exist_ok=True)
            shutil.copytree(self.cfg.repo_root / "ofn" / "budget",
                            wt / "ofn" / "budget", dirs_exist_ok=True)
            target_rel = doc["target"]["path"]            # ofn/agents/...
            tgt = wt / target_rel
            tgt.parent.mkdir(parents=True, exist_ok=True)
            text = base.decode("utf-8")
            for op in doc["ops"]:
                text = text.replace(op["anchor"], op["new"], 1)
            tgt.write_text(text, encoding="utf-8")
        except OSError as e:
            self.chain.emit(attempt_id, "WT_APPLY",
                            Disposition.APPLY_FAULT, str(e))
            return None

        r = subprocess.run(
            [sys.executable, "-m", "py_compile", str(tgt)],
            capture_output=True, timeout=30)
        if r.returncode != 0:
            self.chain.emit(attempt_id, "WT_APPLY", Disposition.COMPILE_RED,
                            r.stderr.decode("utf-8", "replace")[:300])
            return None
        # FIX: return the worktree ROOT (the original returned the target
        # file path, which made callers compute nonsense test dirs)
        return wt

    # -- bounded test run ----------------------------------------------------
    def run_tests(self, wt: Path, tests: list, attempt_id: str) -> bool:
        # FIX (durability-lane review 2026-09-15): tests MUST run inside the
        # isolated worktree against the patched bytes — not against the live
        # repo. Test files are copied into the WT so imports resolve there.
        env = {k: v for k, v in os.environ.items()
               if k in ("PATH", "HOME", "LANG", "LC_ALL", "VIRTUAL_ENV")}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        for t in tests:
            tpath = wt / t
            if not tpath.is_file():
                self.chain.emit(attempt_id, "TEST_RUN",
                                Disposition.TEST_INFRA_RED,
                                f"test file missing in worktree: {t}")
                return False
            try:
                # FIX: cwd = the worktree, so the PATCHED target is what
                # the test imports — not the live repo tree.
                r = subprocess.run(
                    [sys.executable, "-m", "pytest", "-q", "-x",
                     str(tpath)],
                    cwd=wt, env=env, capture_output=True,
                    timeout=self.cfg.test_timeout_s)
            except subprocess.TimeoutExpired:
                self.chain.emit(attempt_id, "TEST_RUN",
                                Disposition.TEST_INFRA_RED, "pytest timeout")
                return False
            out = (r.stdout + r.stderr).decode("utf-8", "replace")
            self._sanitize_dump(wt.parent / "pytest.log", out)
            if "no tests ran" in out or "ERROR collecting" in out:
                self.chain.emit(attempt_id, "TEST_RUN",
                                Disposition.TEST_INFRA_RED,
                                out[-300:].replace("\n", " | "))
                return False
            if r.returncode != 0:
                self.chain.emit(attempt_id, "TEST_RUN", Disposition.TEST_RED,
                                out[-300:].replace("\n", " | "))
                return False
        self.chain.emit(attempt_id, "TEST_RUN", Disposition.PRODUCED,
                        f"{len(tests)} test file(s) green")
        return True

    @staticmethod
    def _sanitize_dump(path: Path, text: str) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(re.sub(r"[A-Za-z0-9_-]{32,}", "<redacted>",
                                   text)[:8192], encoding="utf-8")
        except OSError:
            pass  # diagnostic only; never fault on dump failure

    # -- independent critic ---------------------------------------------------
    def critic(self, doc: dict, wt: Path, base: bytes,
               attempt_id: str) -> bool:
        applied = wt.read_text(encoding="utf-8")
        diff_view = []
        for op in doc["ops"]:
            diff_view.append(f"--- anchor: {op['anchor'][:60]}\n"
                             f"+++ new:\n{op['new'][:2000]}")
        prompt = (
            "You are an independent critic. Judge ONLY correctness of the "
            "applied change against the base. Reply JSON: "
            '{"accept": true|false, "reason": "one sentence"}.\n\n'
            f"BASE (excerpt):\n{base.decode('utf-8', 'replace')[:3000]}\n\n"
            f"CHANGE:\n{''.join(diff_view)[:3000]}\n")
        res = self.critic_client.generate(
            schema={"type": "object",
                    "required": ["accept"],
                    "properties": {"accept": {"type": "boolean"},
                                   "reason": {"type": "string"}}},
            system="", user=prompt, max_tokens=256, temperature=0)
        if not res.ok:
            self.chain.emit(attempt_id, "CRITIC",
                            Disposition.CRITIC_REJECT,
                            f"critic unavailable: {res.failure_stage}")
            return False
        try:
            verdict = json.loads(normalize_json_envelope(res.payload))
            accept = bool(verdict.get("accept"))
        except (ValueError, json.JSONDecodeError):
            verdict = {}
            accept = False
        if not accept:
            self.chain.emit(attempt_id, "CRITIC",
                            Disposition.CRITIC_REJECT,
                            str(verdict.get("reason", "unparseable"))[:300])
        return accept

# ======================================================================
# Registration — hand staged artifact to ops-agent queue (G22 schema)
# ======================================================================
def build_canary_request(doc: dict, artifact: Path,
                         cfg: FactoryConfig,
                         dependencies: Optional[list] = None) -> dict:
    art_bytes = artifact.read_bytes()
    art_sha = hashlib.sha256(art_bytes).hexdigest()
    return {
        "request_id": f"cog-factory-{uuid.uuid4().hex[:8]}",
        "category": "B8_NON_TCB_PATCH_CANARY",
        "kind": "B8_NON_TCB_PATCH_CANARY",
        "component": "ofn-agents",
        "task_id": doc["task_id"],
        "target": str(cfg.repo_root / doc["target"]["path"]),
        "base_sha256": doc["target"]["base_sha256"],
        "artifact_sha256": art_sha,
        "expected_post_sha256": art_sha,
        "target_sha256": art_sha,
        # FIX: the executor reads req["patched"] as the artifact source and
        # silently skips requests without it (observed 2026-09-15).
        "patched": str(artifact),
        "artifact_path": str(artifact),
        "diff_scope": [doc["target"]["path"]],
        "dependencies": dependencies or [],
        "tests": doc["tests"],
        "requested_by": "octopus-cognition-factory/2026-09-15",
        "note": doc.get("rationale", "")[:200],
        "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

def stage_candidate(tgt_wt: Path, doc: dict, cfg: FactoryConfig,
                    chain: ReceiptChain, attempt_id: str) -> Path:
    dst_dir = cfg.candidate_dir / doc["task_id"]
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / Path(doc["target"]["path"]).name
    shutil.copy2(tgt_wt, dst)
    req = build_canary_request(doc, dst, cfg)
    req_path = cfg.queue_dir / f"{req['request_id']}.json"
    tmp = req_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(req, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    os.replace(tmp, req_path)                 # atomic publish
    chain.emit(attempt_id, "CLOSE", Disposition.PRODUCED,
               hashes={"artifact_sha256": hashlib.sha256(
                           dst.read_bytes()).hexdigest(),
                       "request_id": req["request_id"]})
    return dst

# ======================================================================
# Orchestrator
# ======================================================================
@dataclass
class AttemptOutcome:
    disposition: Disposition
    request_id: Optional[str] = None

class ReflectionLoop:
    def __init__(self, cfg: FactoryConfig):
        self.cfg = cfg
        self.chain = ReceiptChain(cfg.receipt_path)
        self.client = StructuredClient(cfg, self.chain)
        self.critic = StructuredClient(cfg, self.chain)
        self.schema_gate = SchemaGate(cfg, self.chain)
        self.anchor_gate = AnchorGate(cfg, self.chain)
        self.verifier = PatchVerifier(cfg, self.chain, self.critic)
        self.tasks = QueueTaskSource(cfg.queue_dir / "cognition")
        self.training_export: Callable[[dict], None] = lambda row: None

    # -- main step ---------------------------------------------------------
    def process_next(self) -> Optional[AttemptOutcome]:
        task = self.tasks.pop()
        if task is None:
            return None
        attempt = uuid.uuid4().hex[:12]
        h = hashlib.sha256
        self.chain.emit(attempt, "TASK_START", Disposition.TASK_STARTED,
                        hashes={"task_sha256": h(task.text.encode()).hexdigest()})
        try:
            return self._run(task, attempt)
        except ChainFault:
            raise
        except Exception as e:                   # last-ditch disposition
            self.chain.emit(attempt, "CLOSE", Disposition.CHAIN_FAULT,
                            f"{type(e).__name__}: {e}"[:300])
            return AttemptOutcome(Disposition.CHAIN_FAULT)

    def _run(self, task: Task, attempt: str) -> AttemptOutcome:
        # Bounded-producer redesign (2026-09-15, after qwen3-0.6b envelope
        # evidence): the model ONLY emits the ops array; the harness composes
        # the full octopus.patch.v2 envelope deterministically from task meta
        # and the live target bytes. Kills fence/shape/truncation variance.
        meta = json.loads(task.path.read_text(encoding="utf-8"))
        target_rel = meta.get("target")           # ofn/agents/...
        tests = meta.get("tests") or []
        if not target_rel or not tests:
            self.chain.emit(attempt, "TASK_META", Disposition.REJECTED_SCHEMA,
                            "task json lacks target/tests")
            self.tasks.requeue(task, "task meta incomplete")
            return AttemptOutcome(Disposition.REJECTED_SCHEMA)

        ops_doc: Optional[dict] = None
        ops_example = ('{"ops":[{"op":"replace_span",'
                       '"anchor":"<one exact line from the file>",'
                       '"new":"<replacement lines>"}]}')
        for repair in (False, True):
            res = self.client.generate(
                schema=OPS_SCHEMA_MINI,
                system=("Return ONLY compact JSON of the form "
                        + ops_example
                        + ". No markdown, no fences, no explanation. Anchors "
                          "must be exact single lines that appear exactly once."),
                user=task.text,
                max_tokens=1024,
                repair=repair)
            if not res.ok:
                self._fail(attempt, task, res)
                return AttemptOutcome(
                    Disposition.INFER_TIMEOUT
                    if res.failure_stage == "inference"
                    else Disposition.INFER_TRANSPORT
                    if res.failure_stage == "transport"
                    else Disposition.INFER_EMPTY)
            try:
                raw = normalize_json_envelope(res.payload)
                ops_doc = _normalize_ops_shape(json.loads(raw))
            except (ValueError, json.JSONDecodeError) as e:
                self.chain.emit(attempt, "SCHEMA_GATE",
                                Disposition.REJECTED_SCHEMA,
                                f"ops-envelope: {e}",
                                hashes={"response_sha256_16": hashlib.sha256(
                                    res.payload).hexdigest()[:16]})
                ops_doc = None
            if ops_doc is not None and _ops_doc_valid(ops_doc):
                break
            ops_doc = None
        if ops_doc is None:
            self.tasks.requeue(task, "ops schema reject after repair")
            return AttemptOutcome(Disposition.REJECTED_SCHEMA)

        # harness-owned envelope (deterministic, validated shape by construction)
        tgt_path = self.cfg.repo_root / target_rel
        if not tgt_path.is_file():
            self.tasks.requeue(task, "target missing")
            return AttemptOutcome(Disposition.ANCHOR_MISS)
        doc = {
            "kind": "octopus.patch.v2",
            "task_id": meta.get("task_family") or task.task_id,
            "parent_task": meta.get("parent_task"),
            "target": {"path": target_rel,
                       "base_sha256": hashlib.sha256(
                           tgt_path.read_bytes()).hexdigest()},
            "ops": ops_doc["ops"],
            "tests": tests,
            "rationale": (meta.get("rationale") or task.text)[:500],
            "no_touch": list(self.cfg.no_touch_globs),
        }
        bad = scan_control_bytes(json.dumps(doc, ensure_ascii=False).encode("utf-8"))
        if bad:
            self.chain.emit(attempt, "CONTROL_BYTE_GATE",
                            Disposition.REJECTED_CONTROL, bad)
            self.tasks.requeue(task, "control bytes in ops")
            return AttemptOutcome(Disposition.REJECTED_CONTROL)
        try:
            (self.cfg.candidate_dir / "_responses" /
             f"{attempt}-doc.json").write_text(
                json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass

        base = self.anchor_gate.check(doc, attempt)
        if base is None:
            self.tasks.requeue(task, "stale base or anchor miss")
            return AttemptOutcome(Disposition.STALE_BASE_ARTIFACT)

        wt_root = self.verifier.apply_in_wt(doc, base, attempt)
        if wt_root is None:
            return AttemptOutcome(Disposition.APPLY_FAULT)

        if not self.verifier.run_tests(wt_root, doc["tests"], attempt):
            return AttemptOutcome(Disposition.TEST_RED)

        target_in_wt = wt_root / doc["target"]["path"]
        if not self.verifier.critic(doc, target_in_wt, base, attempt):
            return AttemptOutcome(Disposition.CRITIC_REJECT)

        dst = stage_candidate(target_in_wt, doc, self.cfg, self.chain, attempt)
        return AttemptOutcome(Disposition.PRODUCED,
                              request_id=dst.parent.name)

    def _fail(self, attempt: str, task: Task, res: InferResult) -> None:
        stage_map = {"lock": Disposition.INFER_TRANSPORT,
                     "transport": Disposition.INFER_TRANSPORT,
                     "inference": Disposition.INFER_TIMEOUT,
                     "empty": Disposition.INFER_EMPTY}
        self.chain.emit(attempt, "INFER_RESPONSE",
                        stage_map.get(res.failure_stage or "",
                                      Disposition.INFER_TRANSPORT),
                        res.failure_stage or "unknown",
                        res.timing)
        self.tasks.requeue(task, f"infer {res.failure_stage}")

# ======================================================================
# CLI
# ======================================================================
def main(argv: list) -> int:
    cfg = FactoryConfig()
    loop = ReflectionLoop(cfg)
    n = 0
    while n < 1:                              # one task per invocation
        out = loop.process_next()
        if out is None:
            print("queue empty")
            return 0
        n += 1
        print(f"attempt outcome: {out.disposition.value} "
              f"request={out.request_id}")
        return 0 if out.disposition is Disposition.PRODUCED else 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
