"""تستِ رشدِ هدف‌محورِ خودآگاه (brain/self_growth) — دفترِ یادگیری + خودنگاره."""
from tests import _bootstrap  # noqa: F401

import tempfile
import unittest
from pathlib import Path

import config.settings as settings
from brain import self_growth as sg


class TestSelfGrowth(unittest.TestCase):
    def setUp(self):
        self._orig = settings.OUTPUT_DIR
        self._td = tempfile.TemporaryDirectory()
        settings.OUTPUT_DIR = Path(self._td.name)

    def tearDown(self):
        settings.OUTPUT_DIR = self._orig
        self._td.cleanup()

    def test_current_focus_shape(self):
        f = sg.current_focus(0)
        self.assertIn("goal", f)
        self.assertIn("target", f)
        self.assertTrue(f["target"].endswith(".py"))
        self.assertIn("motivation", f)

    def test_capability_ledger_roundtrip(self):
        self.assertEqual(sg.learned_capabilities(), [])
        sg.record_learned_capability({"id": "p1", "target": "data/x.py",
                                      "goal": "هدف", "rationale": "r"})
        sg.record_learned_capability({"id": "p2", "target": "ui/y.py",
                                      "goal": "هدف۲", "rationale": "r2"})
        caps = sg.learned_capabilities()
        self.assertEqual(len(caps), 2)
        self.assertEqual(caps[0]["target"], "ui/y.py")     # جدیدترین اول

    def test_self_portrait_renders(self):
        txt = sg.self_portrait()
        self.assertIn("خودنگاره", txt)
        self.assertIn("آگاهیِ پدیداری", txt)              # قابِ صادقانه
        ok, _ = sg.save_self_portrait()
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
