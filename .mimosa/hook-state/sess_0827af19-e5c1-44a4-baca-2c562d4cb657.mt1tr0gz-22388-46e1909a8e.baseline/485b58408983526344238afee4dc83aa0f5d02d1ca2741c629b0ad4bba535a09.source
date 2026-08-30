#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_studio_pf_leg.py — گاردهای پای Project-F در خودآگاهیِ ارگانیسم.

چرا این تست وجود دارد: تا ۲۰۲۶-۰۸-۰۳ این پا در `ORGANISM-STATE.business_legs`
**غایب** بود، پس ۱۲ مصرف‌کنندهٔ آن فهرست (doctor/self_knowledge/weekly_review/…)
نه زنده می‌دیدندش نه مرده. حالا که ثبت شده، چهار چیز باید قفل بماند:

  ۱) **content-free** — هیچ متنِ درفت/کپشن/بدنهٔ DM از مرزِ پوشهٔ پروژه بیرون
     نرود (قاعدهٔ قفل‌شدهٔ #۷). با فیکسچرِ عمداً متن‌دار سنجیده می‌شود.
  ۲) **سه‌حالتیِ صادق** — فایلِ غایب/خراب ⇒ `None` + نامِ فیلد در `unknown`،
     نه صفرِ جعلی (درسِ «نبودِ داده حکم نیست»).
  ۳) **معنایِ live** — بدونِ مهرِ انسانیِ GATE-STAMP-GO هرگز live نشود؛ و
     KILL/HALT/pause بر همه‌چیز مقدم باشند.
  ۴) **ثبت در رجیستری** — واقعاً از مسیرِ `business_legs_beat` دیده شود
     (نه فقط تابعِ تنها؛ درسِ «صداکننده گم بود»).

هرمتیک: همه‌چیز در tmp؛ هیچ فایلِ زنده‌ای خوانده/نوشته نمی‌شود.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import studio_pf_leg as L  # noqa: E402

CANARY = "CANARY-LEG-TEXT-must-not-leak-51ab"


def _tree(root: Path, *, with_stamp=False, kill=False, halt=False) -> Path:
    pf = root / "03 - Projects" / "pf-fixture"
    (pf / "brain").mkdir(parents=True, exist_ok=True)
    (pf / "studio").mkdir(parents=True, exist_ok=True)
    (pf / "00 - Control").mkdir(parents=True, exist_ok=True)
    (pf / "langar").mkdir(parents=True, exist_ok=True)
    (pf / "brain" / "acq_queue.json").write_text(json.dumps([
        {"id": "a1", "status": "ready", "hook": CANARY, "caption": CANARY},
        {"id": "a2", "status": "drafted", "hook": CANARY},
        {"id": "a3", "status": "drafted", "hook": CANARY},
    ], ensure_ascii=False), encoding="utf-8")
    (pf / "brain" / "dm_queue.json").write_text(json.dumps([
        {"id": "d1", "status": "pending_review", "body": CANARY},
    ], ensure_ascii=False), encoding="utf-8")
    (pf / "studio" / "drafts.json").write_text(json.dumps([
        {"id": "s1", "status": "pending", "title": CANARY},
        {"id": "s2", "status": "approved", "title": CANARY},
    ], ensure_ascii=False), encoding="utf-8")
    if with_stamp:
        (pf / "00 - Control" / "GATE-STAMP-GO").write_text("go", encoding="utf-8")
    if kill:
        (pf / "langar" / "KILL").write_text("", encoding="utf-8")
    if halt:
        (pf / "studio" / "HALT").write_text("", encoding="utf-8")
    return pf


class TestStudioPfLeg(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._orig_root = L.PF_ROOT
        self._orig_ops = L._OPS

    def tearDown(self):
        L.PF_ROOT = self._orig_root
        L._OPS = self._orig_ops
        self._tmp.cleanup()

    def _point_at(self, pf: Path):
        L.PF_ROOT = pf
        L._OPS = self.root / "_ops"          # تا فلگِ pause/پلِ زنده لمس نشود
        (L._OPS / "state").mkdir(parents=True, exist_ok=True)

    # ۱) قلبِ قاعدهٔ #۷
    def test_no_content_crosses_the_boundary(self):
        self._point_at(_tree(self.root))
        blob = json.dumps(L.studio_pf_status(), ensure_ascii=False)
        self.assertNotIn(CANARY, blob,
                         "متنِ محتوا از مرزِ پوشهٔ پروژه بیرون رفت — نقضِ قاعدهٔ #۷")
        self.assertTrue(json.loads(blob)["content_free"])

    def test_counts_are_real(self):
        self._point_at(_tree(self.root))
        s = L.studio_pf_status()
        self.assertEqual(s["acq_ready"], 1)
        self.assertEqual(s["acq_drafted"], 2)
        self.assertEqual(s["dm_pending"], 1)
        self.assertEqual(s["drafts_pending"], 1)     # فقط pending، نه approved
        self.assertEqual(s["queue_total"], 5)

    # ۲) سه‌حالتیِ صادق
    def test_missing_files_are_none_not_zero(self):
        empty = self.root / "empty"
        (empty / "00 - Control").mkdir(parents=True)
        self._point_at(empty)
        s = L.studio_pf_status()
        for f in ("acq_ready", "dm_pending", "drafts_pending"):
            self.assertIsNone(s[f], f"{f} باید نامعلوم باشد نه صفرِ جعلی")
        self.assertTrue(any(u.startswith("acq_ready:") for u in s["unknown"]))

    def test_corrupt_json_is_unknown(self):
        pf = _tree(self.root)
        (pf / "brain" / "acq_queue.json").write_text("{broken", encoding="utf-8")
        self._point_at(pf)
        s = L.studio_pf_status()
        self.assertIsNone(s["acq_ready"])
        self.assertTrue(any("corrupt" in u for u in s["unknown"]))

    def test_absent_project_root(self):
        self._point_at(self.root / "nope")
        s = L.studio_pf_status()
        self.assertEqual(s["signal"], "absent")
        self.assertFalse(s["live"])

    # ۳) معنایِ live و تقدمِ کلیدهای کشتار
    def test_never_live_without_human_stamp(self):
        self._point_at(_tree(self.root))
        s = L.studio_pf_status()
        self.assertFalse(s["live"], "بدونِ مهرِ انسانی هرگز نباید live شود")
        self.assertEqual(s["signal"], "gated")
        self.assertFalse(s["gate_stamp_go"])

    def test_live_only_with_stamp(self):
        self._point_at(_tree(self.root, with_stamp=True))
        s = L.studio_pf_status()
        self.assertTrue(s["live"])
        self.assertEqual(s["signal"], "armed")
        self.assertFalse(s["outward_execution"], "حتی armed هم اجرای خودکار ندارد")

    def test_kill_beats_stamp(self):
        self._point_at(_tree(self.root, with_stamp=True, kill=True))
        s = L.studio_pf_status()
        self.assertEqual(s["signal"], "killed")
        self.assertFalse(s["live"])

    def test_halt_beats_stamp(self):
        self._point_at(_tree(self.root, with_stamp=True, halt=True))
        s = L.studio_pf_status()
        self.assertEqual(s["signal"], "halted")
        self.assertFalse(s["live"])

    # ۴) ثبت در رجیستری — «صداکننده» واقعاً وجود دارد
    def test_registered_in_business_legs_spec(self):
        import wiring  # noqa: WPS433
        names = [n for n, _m, _f in wiring._BUSINESS_LEGS_SPEC]
        self.assertIn("studio_pf", names,
                      "پا در _BUSINESS_LEGS_SPEC ثبت نشده — دوباره نامرئی می‌شود")

    def test_visible_through_registry_beat(self):
        import wiring  # noqa: WPS433
        res = wiring.business_legs_beat(beat=1, write=False)
        self.assertIsNotNone(res, "kill-switch زنده beat را بست — تست معتبر نیست")
        self.assertIn("studio_pf", res["business_legs"])
        leg = res["business_legs"]["studio_pf"]
        self.assertEqual(leg.get("leg"), "studio_pf")
        self.assertIn("signal", leg)

    def test_registered_in_weekly_review(self):
        sys.path.insert(0, str(_OPS / "telegram_center"))
        import weekly_review  # noqa: WPS433
        self.assertIn("studio_pf", weekly_review.BUSINESS_LEGS,
                      "سکوتِ این پا در گزارشِ هفتگی دیده نمی‌شود")
        self.assertIn("studio_pf", weekly_review.DISPLAY)
        # قاعدهٔ #۷: نامِ نمایشی بیرون از پوشه فقط کدِ Project-F
        self.assertNotIn("اونلی", weekly_review.DISPLAY["studio_pf"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
