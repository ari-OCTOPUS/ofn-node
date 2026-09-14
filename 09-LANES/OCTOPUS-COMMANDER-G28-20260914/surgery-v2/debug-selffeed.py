import importlib.util
import json
import pathlib
import tempfile

spec = importlib.util.spec_from_file_location(
    "cw", "/home/ari/ofn/state/coding-worker/stage/"
    "W3G30-COMBINED-002/coding_worker.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
fx = pathlib.Path(tempfile.mkdtemp())
m.TASKS = fx / "tasks"
m.TASKS.mkdir()
m.BLOCKED = fx / "blocked"
m.BLOCKED.mkdir()
m.DONE = fx / "done"
m.DONE.mkdir()
m.FAILED = fx / "failed"
m.FAILED.mkdir()
m.LEARNING = fx / "learning.jsonl"
m.LEARNING.write_text(
    (json.dumps({"outcome": "PATCH_TESTS_FAILED"}) + "\n") * 4)
fn = m.FAILED / "SELF-RECUR-PATCH-TESTS-FAILED.json"
fn.write_text("{}")

# debug: print what the seen-set sees
seen = set()
for d in list(m.TASKS.glob("*.json")) + list(m.BLOCKED.glob("*.json")) \
        + list(m.DONE.glob("*.json")) + list(m.FAILED.glob("*.json")):
    seen.add(d.stem)
print("seen:", seen)
print("FAILED dir exists:", m.FAILED.exists())
print("FAILED contents:", list(m.FAILED.glob("*")))

n = m.self_feed()
print("self_feed result:", n)
print("tasks created:", list(m.TASKS.glob("*.json")))
