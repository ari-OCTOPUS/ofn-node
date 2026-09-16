# 182-owned tests against isolated REAL worker copy. Not pc-worker 8.
# No production overwrite. No live inbox. No c3f085a8.
from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROD = HERE / "octopus_witness_worker.py.prodcopy"
PATCHED = HERE / "octopus_witness_worker.py"
PY = sys.executable


def load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def sandbox() -> Path:
    d = Path(tempfile.mkdtemp(prefix="once182_", dir=str(HERE / "_sand")))
    for sub in ("inbox", "processing", "processed", "state", "state/witness",
                "receipts", "outbox", "config", "bin"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    return d


def drop_msg(root: Path, name: str, mid: str):
    (root / "inbox" / name).write_text(
        json.dumps({"message_id": mid, "message_type": "verification_task",
                    "checksum": "x", "idempotency_key": mid}) + "\n",
        encoding="utf-8",
    )


class IsolatedRealWorkerOnce(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (HERE / "_sand").mkdir(exist_ok=True)
        sys.path.insert(0, str(HERE))

    def test_1_prod_ast_main_never_calls_cycle(self):
        tree = ast.parse(PROD.read_text(encoding="utf-8"))
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        names = []
        for c in ast.walk(main):
            if isinstance(c, ast.Call):
                if isinstance(c.func, ast.Attribute):
                    names.append(c.func.attr)
                elif isinstance(c.func, ast.Name):
                    names.append(c.func.id)
        self.assertNotIn("cycle", names)

    def test_2_prod_once_runtime_noop(self):
        root = sandbox()
        drop_msg(root, "a.json", "mid-a")
        calls = []
        prod_py = HERE / "_sand" / "worker_prod_import.py"
        prod_py.write_text(PROD.read_text(encoding="utf-8"), encoding="utf-8")
        mod = load_mod("worker_prod_once", prod_py)
        orig = mod.Worker.cycle

        def wrapped(self, *a, **k):
            calls.append(1)
            return orig(self, *a, **k)

        mod.Worker.cycle = wrapped
        argv = sys.argv
        try:
            sys.argv = ["prod", "--root", str(root), "--once"]
            rc = mod.main()
        finally:
            sys.argv = argv
            mod.Worker.cycle = orig
        self.assertTrue(rc in (0, None))
        self.assertEqual(calls, [])
        self.assertTrue((root / "inbox" / "a.json").exists())

    def test_3_patched_main_calls_cycle(self):
        tree = ast.parse(PATCHED.read_text(encoding="utf-8"))
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        names = []
        for c in ast.walk(main):
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute):
                names.append(c.func.attr)
        self.assertIn("cycle", names)

    def test_4_no_event_exit_0(self):
        root = sandbox()
        r = subprocess.run(
            [PY, str(PATCHED), "--root", str(root), "--once"],
            cwd=str(HERE), capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out.get("claimed"), 0)
        self.assertEqual(out.get("max_n"), 1)
        self.assertFalse(out.get("paused"))

    def test_5_three_inbox_claims_one(self):
        root = sandbox()
        drop_msg(root, "a.json", "mid-a")
        drop_msg(root, "b.json", "mid-b")
        drop_msg(root, "c.json", "mid-c")
        r = subprocess.run(
            [PY, str(PATCHED), "--root", str(root), "--once"],
            cwd=str(HERE), capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        out = json.loads(r.stdout)
        self.assertEqual(out.get("claimed"), 1)
        self.assertEqual(out.get("max_n"), 1)
        inbox = sorted(p.name for p in (root / "inbox").glob("*.json"))
        processed = sorted(p.name for p in (root / "processed").glob("*.json"))
        self.assertEqual(inbox, ["b.json", "c.json"])
        self.assertEqual(processed, ["mid-a.json"])
        skipped = [x for x in out.get("results", []) if x.get("action") == "skipped_cap"]
        self.assertEqual(len(skipped), 2)

    def test_6_prod_once_subprocess_leaves_inbox(self):
        prod_py = HERE / "_sand" / "worker_prod_run.py"
        prod_py.write_text(PROD.read_text(encoding="utf-8"), encoding="utf-8")
        root = sandbox()
        drop_msg(root, "z.json", "mid-z")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(HERE)
        r = subprocess.run(
            [PY, str(prod_py), "--root", str(root), "--once"],
            cwd=str(HERE), capture_output=True, text=True, timeout=20,
            env=env,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((root / "inbox" / "z.json").exists())
        self.assertEqual(list((root / "processed").glob("*.json")), [])


if __name__ == "__main__":
    r = unittest.main(verbosity=2, exit=False)
    sys.exit(0 if r.result.wasSuccessful() else 1)