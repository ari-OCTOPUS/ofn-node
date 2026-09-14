"""Full-path acceptance for the G30 stage-guard wiring (owner mission هـ).

Drives the PATCHED worker's process_patch_task over its REAL staging path with
the model boundary stubbed to a fixed patch document: (A) a replacement whose
JSON form carried "\b" (decoded to a literal backspace) must be rejected at
staging before any proposal; (B) the correct backslash+b text must stage
cleanly, pass the byte guard, and reach the canary phase. All state roots are
fixture-isolated; no network, no production write."""
import importlib.util
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, "/home/ari/ofn/ofn/budget")
sys.path.insert(0, "/home/ari/ofn/state/api-budget")
sys.path.insert(0, "/home/ari/ofn/ofn")
sys.path.insert(0, "/home/ari/ofn")
sys.path.insert(0, "/home/ari/ofn/ofn/agents")

ART = ("/home/ari/ofn/state/coding-worker/stage/G30-STAGE-GUARD-WIRING-001/"
       "coding_worker.py")
spec = importlib.util.spec_from_file_location("cw_g30", ART)
cw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cw)

fx = pathlib.Path(tempfile.mkdtemp(prefix="g30path-"))
(fx / "stage").mkdir(parents=True, exist_ok=True)
(fx / "canary").mkdir(parents=True, exist_ok=True)
cw.STAGE_ROOT = fx / "stage"
cw.CANARY_SPOOL = fx / "canary"
receipts = []
cw.receipt = lambda kind, **kw: receipts.append((kind, kw)) or {}
cw.learn = lambda *a, **k: None

import api_budget  # noqa: E402  (same module object the worker imports)

SRC_REL = ("state/coding-worker/stage/G30-STAGE-GUARD-WIRING-001/"
           "test-src/mod.py")
srcf = pathlib.Path("/home/ari/ofn") / SRC_REL
srcf.parent.mkdir(parents=True, exist_ok=True)
srcf.write_text('PAT = re.compile(r"(old)")\nprint(PAT)\n', encoding="utf-8")


def make_doc(replacement):
    return {"kind": getattr(cw, "PATCH_KIND", "octopus.patch.v1"),
            "files": [{"path": SRC_REL, "op": "replace_anchor",
                       "anchor": 'PAT = re.compile(r"(old)")',
                       "replacement": replacement}],
            "tests": [], "run_tests": [],
            "summary": "g30 wiring path test",
            "diff_scope": [SRC_REL]}


def run(replacement):
    receipts.clear()
    doc = make_doc(replacement)
    api_budget.paid_call = lambda *a, **k: {
        "ok": True, "text": json.dumps(doc), "provider": "fixture"}
    r = cw.process_patch_task({"task_id": "G30-PATH-TEST",
                               "context": {}, "purpose": "free-form-patch"})
    return r, [(k, rec.get("reason", "")) for k, rec in receipts]


g30_repl = 'PAT = re.compile("' + chr(8) + '(old)' + chr(8) + '")'
ok_repl = 'PAT = re.compile(r"\\b(old)\\b")'

rA, recA = run(g30_repl)
canary_after_A = len(list((fx / "canary").glob("*.json")))
rB, recB = run(ok_repl)
staged = fx / "stage/G30-PATH-TEST" / SRC_REL
staged_txt = staged.read_text(encoding="utf-8") if staged.exists() else ""

print("A(backspace):", rA, recA[:3])
print("B(correct)  :", rB, recB[:3])
print("B staged bytes contain literal backslash+b:", "\\b(old)\\b" in staged_txt)

a_ok = (rA == "patch-drift"
        and any(k == "PATCH_REJECTED" and "STAGE_BYTES_DIRTY" in str(reason)
                for k, reason in recA)
        and canary_after_A == 0)
b_ok = (rB == "canary-submitted"
        and not any("STAGE_BYTES_DIRTY" in str(k) + str(reason)
                    for k, reason in recB)
        and len(list((fx / "canary").glob("*.json"))) == 1
        and "\\b(old)\\b" in staged_txt)
print()
print("A_rejected_at_staging_before_proposal:", a_ok)
print("B_clean_through_guard_to_canary      :", b_ok)
sys.exit(0 if (a_ok and b_ok) else 1)
