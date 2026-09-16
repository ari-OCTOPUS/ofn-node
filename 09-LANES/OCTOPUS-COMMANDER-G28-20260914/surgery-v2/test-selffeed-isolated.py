"""Isolated self-feed test: redirects ALL state paths including RECEIPTS,
uses non-zero exit on FAIL. Simulates the 4-step lifecycle the reviewer
tested: create → fail → move to FAILED → self_feed again."""
import importlib.util
import json
import pathlib
import sys
import tempfile

ART = ("/home/ari/ofn/state/coding-worker/stage/"
       "W3G30-COMBINED-003/coding_worker.py")
BASE = ("/home/ari/ofn/state/coding-worker/stage/"
        "W3G30-COMBINED-001/coding_worker.py")  # 72fed2e2 without fix


def load(artifact, fx):
    spec = importlib.util.spec_from_file_location(
        "cw_%d" % id(fx), artifact)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    # redirect ALL state paths (including RECEIPTS)
    m.HOME = fx
    m.STATE = fx / "cw-state"
    m.TASKS = m.STATE / "tasks"
    m.BLOCKED = m.STATE / "blocked"
    m.DONE = m.STATE / "done"
    m.FAILED = m.STATE / "failed"
    m.STAGE_ROOT = m.STATE / "stage"
    m.LEARNING = m.STATE / "learning.jsonl"
    m.RECEIPTS = m.STATE / "coding-receipts.jsonl"
    m.CANARY_DIR = fx / "ops-agent/state/canary-requests"
    m.CANARY_SPOOL = m.CANARY_DIR
    for d in (m.TASKS, m.BLOCKED, m.DONE, m.FAILED, m.STAGE_ROOT):
        d.mkdir(parents=True, exist_ok=True)
    m.CANARY_DIR.mkdir(parents=True, exist_ok=True)
    return m


def lifecycle_test(artifact, label):
    fx = pathlib.Path(tempfile.mkdtemp(prefix="sf-"))
    m = load(artifact, fx)
    # 4 learning rows for same outcome (triggers >=3 recurrence)
    for _ in range(4):
        m.LEARNING.open("a").write(json.dumps(
            {"outcome": "PATCH_TESTS_FAILED", "at": "2026-09-14T10:00:00Z",
             "task": "some-task", "provenance": {"source_hash": "abc123"}}
        ) + "\n")
    results = []
    for step in range(4):
        n = m.self_feed()
        results.append(n)
        # simulate: any created task fails and moves to FAILED
        for f in list(m.TASKS.glob("SELF-*.json")):
            m.FAILED.mkdir(parents=True, exist_ok=True)
            f.rename(m.FAILED / f.name)
    return results


r_base = lifecycle_test(BASE, "base")
r_fixed = lifecycle_test(ART, "fixed")
print("base  72fed2e2:", r_base, "(infinite loop if all 1s)")
print("fixed    v003:", r_fixed, "(should have at most one 1 then 0s)")
ok = r_base == [1, 1, 1, 1] and r_fixed[0] <= 1 and all(n == 0 for n in r_fixed[1:])
print("VERDICT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
