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
(m.FAILED / "SELF-RECUR-PATCH-TESTS-FAILED.json").write_text("{}")
n = m.self_feed()
print("with FAILED entry:", n, "(0=fixed)")
m.FAILED.glob("*.json").__next__().unlink()
n2 = m.self_feed()
print("after FAILED cleared:", n2, "(1=re-created ok)")
ok = n == 0 and n2 == 1
print("SELF-FEED FIX:", "VERIFIED" if ok else "FAIL")
