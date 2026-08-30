"""تست‌های registry کنترل‌پلین — کامل‌بودن، TCB، و آینه‌ی SQLite."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests import _bootstrap  # noqa: F401

from control_plane.registry import load_registry, mirror_to_sqlite, read_mirror


class TestRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = load_registry()

    def test_loads_and_validates_clean(self):
        self.assertEqual(self.reg.version, 1)
        problems = self.reg.validate()
        self.assertEqual(problems, [], f"registry ناقص است: {problems}")

    def test_tcb_covers_sacred_modules(self):
        """TCB مالک باید در registry علامت خورده باشد."""
        tcb = set(self.reg.tcb_ids())
        for sacred in ("core", "config", "guardrails", "budget", "daemon",
                       "events", "self_code", "self_evolve", "automation",
                       "telegram", "llm_router"):
            self.assertIn(sacred, tcb, f"{sacred} باید TCB باشد")

    def test_disconnected_never_pass_status(self):
        """کانالِ غایب/نامعلوم نباید CONNECTED اعلام شود."""
        fin = self.reg.channel("financial_nervous")
        self.assertIsNotNone(fin)
        self.assertIn(fin["status"], ("MISSING", "UNKNOWN"))
        bus = self.reg.channel("events_bus")
        self.assertEqual(bus["status"], "CONNECTED")

    def test_honesty_disclaimer_present(self):
        """دکترین: بدونِ ادعای آگاهیِ پدیداری — باید صریح ثبت شده باشد."""
        goals = " ".join(self.reg.project.get("goals", []))
        self.assertTrue("بدون ادعای" in goals or "testbed" in goals)

    def test_mirror_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "cp.db"
            res = mirror_to_sqlite(self.reg, db)
            self.assertTrue(res["ok"])
            back = read_mirror(db)
            self.assertTrue(back["ok"])
            self.assertEqual(len(back["subsystems"]), len(self.reg.subsystems))
            self.assertEqual(len(back["channels"]), len(self.reg.channels))
            self.assertIn("mirrored_at", back["meta"])

    def test_mirror_never_targets_main_db(self):
        """آینه هرگز نباید DB اصلیِ پروژه باشد (آلوده‌نکردنِ storeی مشاهده‌شده)."""
        from control_plane import snapshot
        main_db = snapshot.DEFAULT_OUT / "4d_experiments.db"
        # قرارداد: مسیرِ آینه در ui/tab_control_plane زیر outputs/control_plane است
        from ui import tab_control_plane as tcp
        self.assertNotEqual(Path(tcp._MIRROR_DB), main_db)
        self.assertIn("control_plane", str(tcp._MIRROR_DB))


if __name__ == "__main__":
    unittest.main(verbosity=2)
