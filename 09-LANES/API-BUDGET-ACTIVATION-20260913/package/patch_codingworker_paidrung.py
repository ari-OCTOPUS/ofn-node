#!/usr/bin/env python3
"""patch3 — wire the multi-provider paid rung into the coding worker.

Local (node-180) stays FIRST. The paid rung is reached only after the local
model fails. The worker never sees a credential and never records one: the
broker owns the key, the budget contract and the provider route.
"""
import hashlib
import pathlib
import py_compile
import shutil
import sys

T = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py")
B = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py.pre-paidrung-20260913")
src = T.read_text(encoding="utf-8")
print("pre_image_sha256:", hashlib.sha256(src.encode()).hexdigest()[:24])

if "import sys" not in src.split("def ")[0]:
    print("NOTE: no top-level 'import sys' — adding")
    src = src.replace("import subprocess", "import subprocess\nimport sys", 1)

FUNC = '''BUDGET_DIR = HOME / "ofn" / "state" / "api-budget"
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


'''
if "def paid_fallback(" in src:
    print("already wired; nothing to do")
    sys.exit(0)

anchor = "def cognition_request(task: dict) -> dict | None:"
if anchor not in src:
    print("ANCHOR_MISSING: cognition_request")
    sys.exit(3)
src = src.replace(anchor, FUNC + anchor, 1)
print("patched: paid_fallback added")

PATCHES = [
    ('            receipt("COGNITION_FAIL_CLOSED", rc=r.returncode,\n'
     '                    err=(r.stdout or b"").decode("utf-8", "replace")[:120])\n'
     '            return None',
     '            receipt("COGNITION_FAIL_CLOSED", rc=r.returncode,\n'
     '                    err=(r.stdout or b"").decode("utf-8", "replace")[:120])\n'
     '            return paid_fallback(task)'),
    ('        if not d.get("ok"):\n'
     '            receipt("COGNITION_FAIL_CLOSED", err=d.get("error"))\n'
     '            return None',
     '        if not d.get("ok"):\n'
     '            receipt("COGNITION_FAIL_CLOSED", err=d.get("error"))\n'
     '            return paid_fallback(task)'),
    ('    except subprocess.TimeoutExpired:\n'
     '        receipt("COGNITION_TIMEOUT")\n'
     '        return None',
     '    except subprocess.TimeoutExpired:\n'
     '        receipt("COGNITION_TIMEOUT")\n'
     '        return paid_fallback(task)'),
]
for old, new in PATCHES:
    if old not in src:
        print("ANCHOR_MISSING:", old.strip().splitlines()[0][:60])
        sys.exit(3)
    src = src.replace(old, new, 1)
print("patched: 3 fallback sites")

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
print("PATCH3_OK")
