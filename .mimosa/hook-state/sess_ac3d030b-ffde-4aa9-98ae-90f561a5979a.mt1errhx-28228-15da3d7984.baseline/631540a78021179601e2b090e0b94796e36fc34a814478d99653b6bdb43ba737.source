"""R18 — تست‌های دلتا-نه-سطح در consolidation 4d (رأی مالک 2026-08-16).

طرح: watermark منبع (sidecar r18-marks) — منبعِ تغییریافته گزارش می‌شود؛
دلتای صفر = پیامِ صادقانهٔ واحد؛ گم‌شدن marks = یک‌بار degraded + بازسازی.
"""
from tests import _bootstrap  # noqa: F401

import tempfile
import unittest
from pathlib import Path

from brain import consolidation as cc

SRC = {"frontier": {"cells": 27},
       "experiments": [{"verdict": "ok"}, {"verdict": "invalid"}],
       "reflections": [{"score": 3}, {"score": 4}]}


def _verify_ok(name, data):
    # همان گیتِ واقعی ماژول را بازاستفاده کن تا تست با تولید یکی باشد
    return cc._verify_source(name, data)


class TestR18Delta(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.path = Path(self.td.name) / "consolidation.json"
        self.cyc = cc.ConsolidationCycle(data_path=self.path)

    def tearDown(self):
        self.td.cleanup()

    def _run(self, sources):
        return self.cyc.run(sources)

    def test_first_run_is_degraded_and_rebuilds_marks(self):
        r = self._run(SRC)
        self.assertTrue(any("r18-degraded" in i for i in r.insights), r.insights)
        self.assertTrue(self.path.with_suffix(".r18-marks.json").exists())

    def test_unchanged_sources_yield_delta_zero(self):
        self._run(SRC)                       # degraded + marks
        r2 = self._run(dict(SRC))            # همان داده‌ها
        self.assertEqual(len(r2.insights), 1, r2.insights)
        self.assertIn("delta-zero", r2.insights[0])
        self.assertNotIn("r18-degraded", r2.insights[0])

    def test_changed_source_is_reported_others_silent(self):
        self._run(SRC)
        changed = dict(SRC)
        changed["frontier"] = {"cells": 31}
        r2 = self._run(changed)
        self.assertEqual(len(r2.insights), 1, r2.insights)
        self.assertIn("31", r2.insights[0])
        self.assertIn("frontier", r2.insights[0])
        self.assertNotIn("delta-zero", r2.insights[0])

    def test_marks_persist_across_instances(self):
        self._run(SRC)
        cyc2 = cc.ConsolidationCycle(data_path=self.path)
        r2 = cyc2.run(dict(SRC))
        self.assertIn("delta-zero", r2.insights[0])   # نه degraded — marks زنده

    def test_all_invalid_sources_still_recorded(self):
        r = self._run({"bogus": {"no": "gate"}})
        self.assertEqual(r.verified_sources, [])
        self.assertEqual(r.discarded_sources, ["bogus"])


if __name__ == "__main__":
    unittest.main()
