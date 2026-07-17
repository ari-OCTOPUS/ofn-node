#!/usr/bin/env python3
"""test_saba_studio.py — تست‌های $0 و آفلاین رابط صبا (خطوط قرمز + wiring)."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path

import saba_studio as S


class T(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self._orig = (S.HALT_FILE, S.INBOX_JSON, S.CAPACITY_JSON,
                      S.BOUNDARY_LOG, S.DRAFTS_JSON, S.CONFIG_JSON)
        S.HALT_FILE = tmp / "HALT"
        S.INBOX_JSON = tmp / "for_saba.json"
        S.CAPACITY_JSON = tmp / "capacity.json"
        S.BOUNDARY_LOG = tmp / "boundary_log.json"
        S.DRAFTS_JSON = tmp / "drafts.json"
        S.CONFIG_JSON = tmp / "config.json"
        S.HERE = tmp  # to_ari.json و … داخل tmp
        (tmp / "config.json").write_text(json.dumps({
            "calendar": {"season": "summer", "slots": [{"week": 1, "theme": "warm-up", "task": "x"}]},
            "trends": [{"tag": "faceless-feet", "note": "n", "optimal_time": "eve"}],
            "ppv": {"wall_pct": 0.55, "tiers": {"low": {"price": 5, "desc": "d"}}},
            "analytics": {"retention_30d": 0.65, "ppv_unlock_rate": 0.28, "arpu": 60},
        }, ensure_ascii=False), encoding="utf-8")
        (tmp / "drafts.json").write_text(json.dumps([
            {"draft_id": "DRAFT-0001", "title": "t", "status": "pending"},
            {"draft_id": "DRAFT-0002", "title": "t2", "status": "approved"},
        ], ensure_ascii=False), encoding="utf-8")
        # studio=None → مسیر fallback (بدون وابستگی به موتور واقعی)
        self.bot = S.SabaStudio(studio=None, token="", saba_chat_id=555)

    def tearDown(self):
        (S.HALT_FILE, S.INBOX_JSON, S.CAPACITY_JSON,
         S.BOUNDARY_LOG, S.DRAFTS_JSON, S.CONFIG_JSON) = self._orig
        self._tmp.cleanup()

    # ۱) غریبه = سکوت مطلق
    def test_stranger_silence(self):
        self.assertIsNone(self.bot.route(999, text="/start"))
        self.assertIsNone(self.bot.route(999, data="s:drafts"))

    # ۲) خانه + منو برای صبا
    def test_home_and_menu(self):
        txt, kb = self.bot.route(555, text="/start")
        self.assertIn("استودیوی محتوا", txt)
        self.assertIn("inline_keyboard", kb)

    # ۳) halt پایدار + آری مطلع + resume
    def test_halt_persist_and_notify(self):
        txt, _ = self.bot.route(555, text="/halt")
        self.assertTrue(S.HALT_FILE.exists())
        self.assertIn("وایساد", txt)
        to_ari = json.loads((S.HERE / "to_ari.json").read_text(encoding="utf-8"))
        self.assertTrue(any("توقف" in m["text"] for m in to_ari))
        # در حالت halt، دکمه‌های عادی کار نمی‌کنند
        txt2, _ = self.bot.route(555, data="s:drafts")
        self.assertIn("توقف", txt2)
        # resume
        txt3, _ = self.bot.route(555, text="/resume")
        self.assertFalse(S.HALT_FILE.exists())

    # ۴) درفت‌ها فقط pending را نشان می‌دهد
    def test_drafts_shows_only_pending(self):
        txt, _ = self.bot.route(555, data="s:drafts")
        self.assertIn("DRAFT-0001", txt)
        self.assertNotIn("DRAFT-0002", txt)  # approved نمایش داده نمی‌شود

    # ۵) جریان ثبت درفت: عنوان → cert → done (با موتور fake)
    def test_submit_flow(self):
        class FakeStudio:
            def __init__(self): self.saved = None
            _config = {}
            def submit_draft(self, title, self_cert=None, **k):
                self.saved = (title, self_cert); return {"ok": True, "draft_id": "DRAFT-0003"}
        self.bot.studio = FakeStudio()
        self.bot.route(555, data="s:new")
        self.bot.route(555, text="ست ابریشم")
        for k in S.COMPLIANCE_CHECKS:
            self.bot.route(555, data=f"cert:{k}")
        txt, _ = self.bot.route(555, data="cert:done")
        self.assertIn("DRAFT-0003", txt)
        self.assertEqual(self.bot.studio.saved[0], "ست ابریشم")

    # ۶) cert ناقص → ثبت نمی‌شود
    def test_incomplete_cert_blocks(self):
        self.bot.route(555, data="s:new")
        self.bot.route(555, text="عنوان")
        self.bot.route(555, data="cert:faceless")  # فقط یکی
        txt, _ = self.bot.route(555, data="cert:done")
        self.assertIn("هنوز", txt)

    # ۷) ظرفیت هفته ثبت و persist می‌شود
    def test_capacity_flow(self):
        self.bot.route(555, data="s:cap")
        txt, _ = self.bot.route(555, text="۳")
        self.assertTrue(S.CAPACITY_JSON.exists())
        cap = json.loads(S.CAPACITY_JSON.read_text(encoding="utf-8"))
        self.assertEqual(cap["hours"], 3.0)

    # ۸) تنگ‌کردن محدوده → لاگ + اطلاع آری
    def test_scope_tighten_logs_and_notifies(self):
        self.bot.route(555, data="s:scope")
        txt, _ = self.bot.route(555, text="دیگه کلیپ صدادار نه")
        self.assertTrue(S.BOUNDARY_LOG.exists())
        to_ari = json.loads((S.HERE / "to_ari.json").read_text(encoding="utf-8"))
        self.assertTrue(any("محدوده" in m["text"] for m in to_ari))

    # ۹) inbox آری خوانده و mark-read می‌شود
    def test_inbox_reads_and_marks(self):
        S.INBOX_JSON.write_text(json.dumps(
            [{"date": "2026-07-11", "text": "این هفته ۵ کلیک، ۱ فروش", "read": False}],
            ensure_ascii=False), encoding="utf-8")
        txt, _ = self.bot.route(555, data="s:inbox")
        self.assertIn("فروش", txt)
        after = json.loads(S.INBOX_JSON.read_text(encoding="utf-8"))
        self.assertTrue(after[0]["read"])

    # ۱۰) هیچ متد رسانه‌ای (صفر media)
    def test_no_media_methods(self):
        for n in dir(self.bot):
            for bad in ("photo", "video", "document", "sticker"):
                self.assertNotIn(bad, n.lower())

    # ۱۱) shadow-mode بدون env باید روی stdin/chat=0 کار کند
    def test_shadow_mode_authorizes_stdin_chat_zero(self):
        b = S.SabaStudio(studio=None, token="", saba_chat_id=0)
        txt, kb = b.route(0, text="/start")
        self.assertIn("استودیوی محتوا", txt)
        self.assertIn("inline_keyboard", kb)

    # ۱۲) ارقام فارسی/عربی ظرفیت درست parse می‌شوند
    def test_capacity_accepts_persian_digits(self):
        self.bot.route(555, data="s:cap")
        self.bot.route(555, text="۳٫۵")
        cap = json.loads(S.CAPACITY_JSON.read_text(encoding="utf-8"))
        self.assertEqual(cap["hours"], 3.5)

    # ۱۳) aliasهای متنی برای shadow-mode بدون inline keyboard کار می‌کنند
    def test_text_aliases_for_shadow_mode(self):
        txt, _ = self.bot.route(555, text="/new")
        self.assertIn("ثبت ایده", txt)
        txt2, _ = self.bot.route(555, text="/drafts")
        self.assertIn("درفت", txt2)

    # ۱۴) self-cert هم در shadow-mode با دستور متنی قابل تست است
    def test_text_cert_aliases_complete_submit(self):
        class FakeStudio:
            def submit_draft(self, title, self_cert=None, **k):
                return {"ok": True, "draft_id": "DRAFT-0099"}
        self.bot.studio = FakeStudio()
        self.bot.route(555, text="/new")
        self.bot.route(555, text="عنوان تست")
        for cmd in ("/faceless", "/feet", "/no_explicit", "/18"):
            self.bot.route(555, text=cmd)
        txt, _ = self.bot.route(555, text="/done")
        self.assertIn("DRAFT-0099", txt)

    # ۱۵) رفتن به صفحهٔ دیگر flow نیمه‌کاره را لغو می‌کند
    def test_navigation_cancels_partial_flow(self):
        self.bot.route(555, text="/new")
        self.bot.route(555, text="/drafts")
        txt, _ = self.bot.route(555, text="این نباید عنوان شود")
        self.assertIn("نفهمیدم", txt)

    # ۱۶) در حالت HALT فقط مسیر resume باز است، نه منوی کامل
    def test_halt_blocks_menu_until_resume(self):
        self.bot.route(555, text="/halt")
        txt, kb = self.bot.route(555, data="s:menu")
        self.assertIn("توقف", txt)
        self.assertEqual(kb["inline_keyboard"][0][0]["callback_data"], "s:resume")
        txt2, kb2 = self.bot.route(555, data="s:resume")
        self.assertIn("خوش برگشتی", txt2)
        self.assertIn("inline_keyboard", kb2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
