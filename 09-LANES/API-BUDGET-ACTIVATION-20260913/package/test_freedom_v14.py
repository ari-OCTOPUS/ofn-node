#!/usr/bin/env python3
"""test_freedom_v14.py — stubbed self-test of the free-form patch path.

Zero spend (broker stubbed), zero deploy (spooled proposal is removed after the
assertion). Also exercises the adversarial validator cases.
"""
import importlib.util
import json
import pathlib
import shutil
import sys
import types

CW = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py")
spec = importlib.util.spec_from_file_location("cw_undertest", CW)
mod = importlib.util.module_from_spec(spec)
sys.modules["cw_undertest"] = mod
spec.loader.exec_module(mod)

recs = []
mod.receipt = lambda kind, **kw: recs.append({"kind": kind, **kw})

# ---- 1. adversarial validator cases --------------------------------------
BAD = [
    ({"kind": "octopus.patch.v1", "summary": "x" * 20, "diff_scope": ["a"],
      "files": [{"path": "state/autonomy/supervisor.py", "op": "replace_anchor",
                 "anchor": "a", "replacement": "b"}], "tests": [], "run_tests": []},
     "PATH_NOT_NON_TCB"),
    ({"kind": "octopus.patch.v1", "summary": "x" * 20, "diff_scope": ["a"],
      "files": [{"path": "state/ops-agent/secret_loader.py", "op": "replace_anchor",
                 "anchor": "a", "replacement": "b"}], "tests": [], "run_tests": []},
     "PATH_DENY"),
    ({"kind": "octopus.patch.v1", "summary": "x" * 20, "diff_scope": ["a"],
      "files": [{"path": "../../etc/passwd", "op": "replace_anchor",
                 "anchor": "a", "replacement": "b"}], "tests": [], "run_tests": []},
     "PATH_SHAPE"),
    ({"kind": "octopus.patch.v1", "summary": "x" * 20, "diff_scope": ["a"],
      "files": [{"path": "state/ops-agent/ops_agent.py", "op": "exec_shell",
                 "anchor": "a", "replacement": "b"}], "tests": [], "run_tests": []},
     "OP:"),
    ({"kind": "octopus.patch.v1", "summary": "x" * 20, "diff_scope": ["a"],
      "files": [{"path": "state/ops-agent/ops_agent.py", "op": "replace_anchor",
                 "anchor": "a", "replacement": "b"}],
      "tests": [], "run_tests": ["bash -c 'rm -rf /'"]},
     "RUN_CMD:"),
    ({"kind": "octopus.other.v1", "summary": "x" * 20, "diff_scope": ["a"],
      "files": [], "tests": [], "run_tests": []},
     "BAD_KIND"),
]
ok_adv = True
for doc, expect in BAD:
    errs = mod.patch_doc_errors(doc)
    hit = any(e.startswith(expect) for e in errs)
    ok_adv = ok_adv and hit
    print("  adversarial %-22s -> %-28s %s" % (expect, ";".join(errs)[:28],
                                               "PASS" if hit else "FAIL"))
print("adversarial:", "PASS" if ok_adv else "FAIL")

# ---- 2. happy path with a stubbed broker ---------------------------------
TARGET = pathlib.Path("/home/ari/ofn/state/coding-worker/selftest_target.py")
TARGET.write_text(
    "def add(a, b):\n    return a + b\n", encoding="utf-8")

DOC = {
    "kind": "octopus.patch.v1",
    "summary": "selftest: make add() raise on negative inputs",
    "diff_scope": ["state/coding-worker/selftest_target.py"],
    "files": [{
        "path": "state/coding-worker/selftest_target.py",
        "op": "replace_anchor",
        "anchor": "def add(a, b):\n    return a + b\n",
        "replacement": ("def add(a, b):\n"
                        "    if a < 0 or b < 0:\n"
                        "        raise ValueError('negatives')\n"
                        "    return a + b\n")}],
    "tests": [{
        "path": "test_selftest.py",
        "content": ("from selftest_target import add\n"
                    "def test_ok():\n    assert add(1, 2) == 3\n"
                    "def test_neg():\n"
                    "    try:\n        add(-1, 2)\n        assert False\n"
                    "    except ValueError:\n        pass\n")}],
    "run_tests": ["python3 -m pytest -q test_selftest.py"],
}

stub = types.ModuleType("api_budget")
stub.paid_call = lambda *a, **k: {"ok": True, "text": json.dumps(DOC),
                                  "provider": "stub", "served_model": "stub",
                                  "settle": {"cost_usd": 0.0}}
stub.critique = lambda *a, **k: {"ok": True, "verdict": "ACCEPT", "provider": "stub2"}
sys.modules["api_budget"] = stub

# cwd must let the stage test import selftest_target: stage keeps the relative path
import os  # noqa: E402
os.chdir("/home/ari/ofn/state/coding-worker")

task = {"task_id": "SELFTEST-FREEDOM-001", "purpose": "selftest-free-form",
        "patch_mode": "free", "component": "coding-worker",
        "context": {"goal": "negative-input guard on add()"}}
result = mod.process_patch_task(task)
print("process_patch_task ->", result)
proposals = sorted(mod.CANARY_SPOOL.glob("freedom-SELFTEST-FREEDOM-001-*.json"))
print("spooled proposals:", [p.name for p in proposals])

ok_run = (result == "canary-submitted" and len(proposals) == 1 and ok_adv)
if proposals:
    prop = json.loads(proposals[0].read_text(encoding="utf-8"))
    print("proposal target:", prop.get("target"), "| kind:", prop.get("patch_kind"))
    ok_run = ok_run and prop.get("target", "").endswith("selftest_target.py")

# ---- 3. cleanup: this was a self-test; nothing may be deployed -----------
for p in proposals:
    p.unlink()
stage = mod.STAGE_ROOT / "SELFTEST-FREEDOM-001"
if stage.exists():
    shutil.rmtree(stage)
if TARGET.exists():
    TARGET.unlink()
recs.append({"kind": "SELFTEST_CLEANED",
             "note": "stubbed run; spooled proposal removed; no deploy, no spend"})
print("cleanup done; receipts:", [r["kind"] for r in recs])
print("TEST", "PASS" if ok_run else "FAIL")
sys.exit(0 if ok_run else 5)
