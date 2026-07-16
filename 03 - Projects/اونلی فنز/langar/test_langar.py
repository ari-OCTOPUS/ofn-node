#!/usr/bin/env python3
"""test_langar.py — تست‌های $0 و آفلاین لنگر (خطوط قرمز LANGAR-SPEC §۸)."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path

import langar_bot as L


class T(unittest.TestCase):
    """هرمتیک: همهٔ فایل‌های قابل‌نوشتن به tempdir هدایت می‌شوند
    (پوشهٔ واقعی پروژه فقط read-only لمس می‌شود)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self._orig = (L.KILL_FILE, L.COST_FILE, L.LOG_FILE, L.PROPOSALS_DIR)
        L.KILL_FILE = tmp / "KILL"
        L.COST_FILE = tmp / "cost_meter.json"
        L.LOG_FILE = tmp / "langar_log.jsonl"
        L.PROPOSALS_DIR = tmp / "upgrade_proposals"
        self.bot = L.LangarBot(token="", ari_chat_id=111,
                               http_get=lambda *a, **k: {"result": []},
                               http_post=lambda *a, **k: {})
        self.bot.cost = L.CostMeter(path=L.COST_FILE)
        self.bot.upgrader = L.UpgradeEngine(self.bot.model, self.bot.cost)

    def tearDown(self):
        L.KILL_FILE, L.COST_FILE, L.LOG_FILE, L.PROPOSALS_DIR = self._orig
        self._tmp.cleanup()

    # ۱) گارد هویت
    def test_guard_redacts_identity(self):
        g = L.OpsecGuard({"blocklist": ["RealName"],
                          "city_terms": ["Sydney", "سیدنی"],
                          "name_map": {"صبا": "C", "آری": "A"}})
        out = g.clean("صبا و آری در Sydney با RealName — سیدنی")
        for bad in ("صبا", "آری", "Sydney", "سیدنی", "RealName"):
            self.assertNotIn(bad, out)
        self.assertIn("C", out)

    def test_guard_redacts_paths(self):
        g = L.OpsecGuard({})
        self.assertNotIn("backup", g.clean(r"C:\backup\secret\file.md"))
        self.assertNotIn("quirky", g.clean("/sessions/quirky/mnt/x"))

    # ۲) غریبه = سکوت مطلق
    def test_stranger_gets_silence(self):
        self.assertIsNone(self.bot.handle(999, "/status"))
        self.assertIsNone(self.bot.handle(999, "hi"))

    # ۳) KILL همه‌چیز جز status/revive را می‌بندد
    def test_kill_switch(self):
        self.assertIn("KILL فعال", self.bot.handle(111, "/kill"))
        self.assertIn("KILL", self.bot.handle(111, "/upgrade"))
        self.assertIn("وضعیت", self.bot.handle(111, "/status"))
        self.assertIn("برگشت", self.bot.handle(111, "/revive"))
        self.assertNotIn("KILL است", self.bot.handle(111, "/help"))

    # ۴) proposal فقط داخل upgrade_proposals
    def test_upgrade_writes_only_inside_proposals(self):
        before = {p: p.stat().st_mtime for p in L.PROJECT_ROOT.glob("*.md")}
        path, items = self.bot.upgrader.propose()
        self.assertTrue(str(path).startswith(str(L.PROPOSALS_DIR)))
        self.assertTrue(path.exists())
        self.assertLessEqual(len(items), 3)
        after = {p: p.stat().st_mtime for p in L.PROJECT_ROOT.glob("*.md")}
        self.assertEqual(before, after)  # هیچ فایل ریشه دست نخورد

    # ۵) CostMeter fail-closed
    def test_cost_meter_fail_closed(self):
        m = L.CostMeter(cap_aud=1.0, path=Path(self._tmp.name) / "cost_test.json")
        self.assertTrue(m.can_spend(0.5))
        m.add(0.9)
        self.assertFalse(m.can_spend(0.2))
        m.path.write_text("{corrupt", encoding="utf-8")
        self.assertFalse(m.can_spend(0.01))  # خطا = ممنوع
        m.path.unlink(missing_ok=True)

    # ۶) تا نبودِ Branch A → outward قفل
    def test_outward_locked_until_branch_a(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "PROJECT.md").write_text("محل اقامت پارتنر: ___", encoding="utf-8")
            self.assertTrue(L.SelfModel(root).outward_locked())
            (root / "PROJECT.md").write_text("پیامد: Branch A ثبت شد", encoding="utf-8")
            self.assertFalse(L.SelfModel(root).outward_locked())

    # ۷) هیچ متد رسانه‌ای وجود ندارد (صفر media به بیرون)
    def test_no_media_methods(self):
        for name in dir(self.bot):
            self.assertNotIn("photo", name.lower())
            self.assertNotIn("video", name.lower())
            self.assertNotIn("document", name.lower())

    # ۸) خروجی send از گارد رد می‌شود (سیاست معتبر → عبور + redact)
    def test_send_passes_guard(self):
        captured = []
        # سیاست معتبر (blocklist ناخالی) لازم است وگرنه fail-closed بلاک می‌کند
        self.bot.guard = L.OpsecGuard({"name_map": {"صبا": "C"}, "city_terms": [],
                                       "blocklist": ["RealName"]})
        self.bot.token, self.bot.ari = "T", 111
        self.bot._http_post = lambda url, body, timeout=10: captured.append(body) or {}
        self.bot.send("گزارش صبا آماده است")
        self.assertNotIn("صبا", captured[0]["text"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
