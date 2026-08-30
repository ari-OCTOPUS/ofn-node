#!/usr/bin/env python3
"""test_dm_inbox_wiring.py — رگرسیونِ باگِ ۲۰۲۶-۰۸-۰۳: ‏`/dm_inbox` صداکننده داشت
ولی متدش تعریف نشده بود (بدنه‌اش کدِ مردهٔ داخلِ `_code_card` افتاده بود) ⇒ هر
فراخوانی AttributeError می‌داد و کاربر هیچ جوابی نمی‌گرفت.

سنجهٔ این تست «نبودِ استثنا» نیست — چون router هر استثنا را می‌بلعد و رشتهٔ
خطا برمی‌گرداند (سبزِ کاذب). پس دو شاهدِ مستقل می‌گیریم:
  ۱) شاهدِ ساختاری: متد واقعاً روی کلاس تعریف شده و امضایش درست است.
  ۲) شاهدِ رفتاری: مسیرِ router به همان متد می‌رسد (با یک جاسوس اثبات می‌شود)
     و خروجی هیچ نشانی از AttributeError ندارد.
هرمتیک/آفلاین/$0 — هم‌سبکِ test_langar.py؛ هیچ فایلِ زنده‌ای لمس نمی‌شود.
"""
from __future__ import annotations

import inspect
import os
import sys
import tempfile
import unittest
from pathlib import Path

import langar_bot as L


class TestDmInboxWiring(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self._orig = (L.KILL_FILE, L.COST_FILE, L.LOG_FILE, L.PROPOSALS_DIR)
        L.KILL_FILE = tmp / "KILL"
        L.COST_FILE = tmp / "cost_meter.json"
        L.LOG_FILE = tmp / "langar_log.jsonl"
        L.PROPOSALS_DIR = tmp / "upgrade_proposals"

        # ⚠️ درسِ ۲۰۲۶-۰۸-۰۳ (خودم مرتکب شدم): مسیرِ واقعیِ `_dm_inbox` یک
        # `DmPipeline()` بدونِ آرگومان می‌سازد ⇒ `DEFAULT_STORE` ِ **زنده**
        # (`brain/dm_queue.json`). تستِ اولیه یک درفتِ ساختگی در صفِ زندهٔ
        # مالک نوشت. هر مسیرِ تحتِ آزمون باید ایزوله شود — نه فقط آن‌هایی که
        # به‌نظر می‌رسد می‌نویسند.
        sys.path.insert(0, str(L.PROJECT_ROOT / "brain"))
        import dm_pipeline as _dm
        self._dm_mod = _dm
        self._orig_store = _dm.DEFAULT_STORE
        _dm.DEFAULT_STORE = tmp / "dm_queue.json"
        self._orig_audit = os.environ.get("PF_AUDIT_FILE")
        os.environ["PF_AUDIT_FILE"] = str(tmp / "approvals.jsonl")
        os.environ["PF_AUDIT_ORIGIN"] = "test"

        self.bot = L.LangarBot(token="", ari_chat_id=111,
                               http_get=lambda *a, **k: {"result": []},
                               http_post=lambda *a, **k: {})

    def tearDown(self):
        L.KILL_FILE, L.COST_FILE, L.LOG_FILE, L.PROPOSALS_DIR = self._orig
        self._dm_mod.DEFAULT_STORE = self._orig_store
        if self._orig_audit is None:
            os.environ.pop("PF_AUDIT_FILE", None)
        else:
            os.environ["PF_AUDIT_FILE"] = self._orig_audit
        self._tmp.cleanup()

    # ۰) گاردِ ایزولاسیون — اگر روزی کسی این ایزوله را برداشت، این تست فریاد بزند
    def test_live_queue_is_not_touched(self):
        live = L.PROJECT_ROOT / "brain" / "dm_queue.json"
        before = live.read_bytes() if live.exists() else None
        self.bot.handle(111, '/dm_inbox hello, do you take customs?')
        after = live.read_bytes() if live.exists() else None
        self.assertEqual(before, after,
                         "تست به صفِ زندهٔ DM نوشت — ایزولاسیون شکسته است")

    # ۱) شاهدِ ساختاری — دقیقاً چیزی که باگ نداشت
    def test_method_is_defined_on_class(self):
        self.assertTrue(hasattr(L.LangarBot, "_dm_inbox"),
                        "متدِ _dm_inbox روی کلاس تعریف نشده — همان باگِ ۰۸-۰۳")
        self.assertTrue(callable(getattr(L.LangarBot, "_dm_inbox")))
        params = list(inspect.signature(L.LangarBot._dm_inbox).parameters)
        self.assertEqual(params[:2], ["self", "text"],
                         "امضای متد با صداکنندهٔ router جور نیست")

    # ۲) شاهدِ رفتاری — router واقعاً به متد می‌رسد (جاسوس، نه حدس)
    def test_router_reaches_the_method(self):
        seen = {}

        def spy(text):
            seen["text"] = text
            return "SPY-OK"

        self.bot._dm_inbox = spy                      # فقط روی همین نمونه
        out = self.bot.handle(111, '/dm_inbox how much for a custom?')
        self.assertEqual(seen.get("text"), "how much for a custom?",
                         "router متن را به _dm_inbox نرساند")
        self.assertIn("SPY-OK", out)

    # ۳) alias ِ /inbox هم همان مسیر را می‌رود
    def test_inbox_alias_reaches_the_method(self):
        seen = {}
        self.bot._dm_inbox = lambda text: seen.setdefault("text", text) and "SPY-OK"
        self.bot.handle(111, "/inbox hi there")
        self.assertEqual(seen.get("text"), "hi there")

    # ۴) مسیرِ واقعی (بدون جاسوس) دیگر AttributeError نمی‌دهد
    def test_real_call_has_no_attribute_error(self):
        out = self.bot.handle(111, '/dm_inbox hello, do you take customs?')
        self.assertIsInstance(out, str)
        self.assertNotIn("AttributeError", out)

    # ۵) بدونِ آرگومان راهنما می‌دهد (نه crash)
    def test_empty_arg_returns_usage(self):
        out = self.bot.handle(111, "/dm_inbox")
        self.assertIsInstance(out, str)
        self.assertIn("/dm_inbox", out)
        self.assertNotIn("AttributeError", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
