"""تست‌های Channel Doctor — UNKNOWN هرگز PASS نمی‌شود؛ گزارش فقط در مسیرِ خودش."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests import _bootstrap  # noqa: F401

from control_plane.channel_doctor import run_doctor


_FAKE_REGISTRY = """\
version: 1
project: {id: fake, name: fake, root: ".", owner: Armin}
subsystems:
  - {id: s1, name: n, path: "mod.py", owner: Armin, tcb: false,
     risk_tier: low, live: passive, authority: observe-only}
channels:
  - id: good
    name: "کانالِ سالم"
    source: "mod.py"
    sink: "state.json"
    state_files: ["state.json"]
    replay: "deterministic"
    risk_tier: low
    authority: observe-only
    status: CONNECTED
  - id: broken
    name: "sourceش نیست"
    source: "ghost/missing.py"
    sink: "x"
    replay: "deterministic"
    risk_tier: low
    authority: observe-only
    status: CONNECTED
  - id: mystery
    name: "declared UNKNOWN"
    source: "mod.py"
    sink: "x"
    replay: "deterministic"
    risk_tier: low
    authority: observe-only
    status: UNKNOWN
"""


class TestChannelDoctor(unittest.TestCase):
    def _setup(self, td: str) -> tuple[Path, Path, Path]:
        root = Path(td)
        (root / "mod.py").write_text("# ok", encoding="utf-8")
        (root / "state.json").write_text("{}", encoding="utf-8")
        regp = root / "registry.yaml"
        regp.write_text(_FAKE_REGISTRY, encoding="utf-8")
        report_dir = root / "_reports"
        return root, regp, report_dir

    def test_verdicts_and_unknown_never_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root, regp, rd = self._setup(td)
            rep = run_doctor(registry_path=regp, root=root,
                             db=root / "no.db", report_dir=rd)
            v = {r["id"]: r["verdict"] for r in rep["channels"]}
            self.assertEqual(v["good"], "PASS")
            self.assertEqual(v["broken"], "FAIL")
            # قاعده‌ی طلایی: کانالِ declared-UNKNOWN هرگز PASS نمی‌شود
            self.assertEqual(v["mystery"], "UNKNOWN")
            self.assertEqual(rep["summary"],
                             {"PASS": 1, "WARN": 0, "FAIL": 1, "UNKNOWN": 1})

    def test_reports_written_only_in_report_dir(self):
        with tempfile.TemporaryDirectory() as td:
            root, regp, rd = self._setup(td)
            before = {str(p) for p in root.rglob("*")}
            rep = run_doctor(registry_path=regp, root=root,
                             db=root / "no.db", report_dir=rd)
            after = {str(p) for p in root.rglob("*")}
            new = after - before
            self.assertTrue(new, "گزارش باید نوشته شود")
            for p in new:
                self.assertIn("_reports", p, f"نوشتنِ خارج از مسیرِ گزارش: {p}")
            data = json.loads((rd / "channel_doctor.json").read_text(encoding="utf-8"))
            self.assertIn("summary", data)
            self.assertTrue((rd / "channel_doctor.md").exists())

    def test_no_write_mode(self):
        with tempfile.TemporaryDirectory() as td:
            root, regp, rd = self._setup(td)
            before = {str(p) for p in root.rglob("*")}
            run_doctor(registry_path=regp, root=root, db=root / "no.db",
                       report_dir=rd, write_reports=False)
            self.assertEqual({str(p) for p in root.rglob("*")}, before)

    def test_real_registry_runs_without_reports(self):
        """دکتر روی registry واقعی هم باید بدونِ exception و بدونِ نوشتن اجرا شود."""
        rep = run_doctor(write_reports=False)
        self.assertGreaterEqual(len(rep["channels"]), 15)
        self.assertEqual(rep["registry_problems"], [])
        # کانالِ MISSING (financial_nervous) نباید PASS شده باشد
        v = {r["id"]: r["verdict"] for r in rep["channels"]}
        self.assertNotEqual(v.get("financial_nervous"), "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
