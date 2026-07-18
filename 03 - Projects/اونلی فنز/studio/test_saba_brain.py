#!/usr/bin/env python3
"""test_saba_brain.py — تست‌های saba_brain (guard + memory + classify + integration).

$0، آفلاین (LLM واقعی فراخوانی نمی‌شود — فقط stub). ۱۲ تست.
هدف: خطوط قرمزِ manifest (PII/geo/forbidden) و حافظه و classify.
"""
from __future__ import annotations
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# import قبل از setUp تا مسیرها درست بشه
import saba_brain as B


class TestGuardLayer(unittest.TestCase):
    """GuardLayer: redact ورودی + filter خروجی."""

    def setUp(self):
        # config موقت با PII تستی
        self._tmp = tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w", encoding="utf-8")
        json.dump({
            "blocklist": ["Armin Test", "1234567890", "secret street"],
            "city_terms": ["Sydney", "سیدنی", "testville"],
            "name_map": {"صبا": "C", "آری": "A"},
        }, self._tmp, ensure_ascii=False)
        self._tmp.close()
        self.guard = B.GuardLayer(config_path=Path(self._tmp.name))

    def tearDown(self):
        try: os.unlink(self._tmp.name)
        except OSError: pass

    def test_redact_removes_blocklist_pii(self):
        """نام/تلفن/آدرس باید [REDACTED] شوند."""
        r = self.guard.redact_input("Armin Test با شماره 1234567890 از secret street")
        self.assertNotIn("Armin Test", r)
        self.assertNotIn("1234567890", r)
        self.assertNotIn("secret street", r)
        self.assertIn("[REDACTED]", r)

    def test_redact_replaces_city_terms(self):
        """شهر باید [LOC] شود."""
        r = self.guard.redact_input("من از Sydney و سیدنی هستم")
        self.assertNotIn("Sydney", r)
        self.assertNotIn("سیدنی", r)

    def test_redact_applies_name_map(self):
        """اسامی واقعی به role code تبدیل شوند."""
        r = self.guard.redact_input("صبا و آری صحبت کردند")
        self.assertNotIn("صبا", r)
        self.assertNotIn("آری", r)

    def test_filter_blocks_forbidden_terms(self):
        """پاسخ‌های حاوی forbidden terms باید reject شوند."""
        for bad in ["come to sydney", "use paypal", "iran is nice", "onlyfans link",
                    "send crypto", "your address is"]:
            ok, _ = self.guard.filter_output(bad)
            self.assertFalse(ok, f"应该 blocked: {bad}")

    def test_filter_allows_clean_persian(self):
        """پاسخِ تمیز فارسی باید عبور کند."""
        ok, _ = self.guard.filter_output("ایدهٔ پاییزی با لاک نارنجی — چه می‌گویی؟")
        self.assertTrue(ok)
        ok2, _ = self.guard.filter_output("چند ساعت این هفته وقت داری؟")
        self.assertTrue(ok2)

    def test_filter_handles_empty(self):
        ok, _ = self.guard.filter_output("")
        self.assertFalse(ok)


class TestMemoryStore(unittest.TestCase):
    """MemoryStore: append-only JSONL + recent + stats."""

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(
            suffix=".jsonl", delete=False, mode="w")
        self._tmp.close()
        self.mem = B.MemoryStore(path=Path(self._tmp.name))

    def tearDown(self):
        try: os.unlink(self._tmp.name)
        except OSError: pass

    def test_append_and_recent(self):
        """append باید ورودی‌ها را به ترتیب نگه دارد."""
        self.mem.append("saba", "hello")
        self.mem.append("bot", "hi back")
        rec = self.mem.recent(5)
        self.assertEqual(len(rec), 2)
        self.assertEqual(rec[0]["role"], "saba")
        self.assertEqual(rec[1]["role"], "bot")
        self.assertIn("ts", rec[0])

    def test_recent_respects_limit(self):
        """recent(n) فقط n آخر را برمی‌گرداند."""
        for i in range(10):
            self.mem.append("saba", f"msg {i}")
        rec = self.mem.recent(3)
        self.assertEqual(len(rec), 3)
        self.assertIn("msg 9", rec[-1]["text"])

    def test_stats_counts_roles(self):
        self.mem.append("saba", "a"); self.mem.append("saba", "b")
        self.mem.append("bot", "c")
        st = self.mem.stats()
        self.assertEqual(st["total"], 3)
        self.assertEqual(st["saba"], 2)
        self.assertEqual(st["bot"], 1)

    def test_recent_empty_file(self):
        """فایلِ خالی یا نباید exception بدهد."""
        empty = B.MemoryStore(path=Path("/nonexistent/path.jsonl"))
        self.assertEqual(empty.recent(), [])
        self.assertEqual(empty.stats()["total"], 0)


class TestClassify(unittest.TestCase):
    """intent classifier: keyword matching."""

    def test_emotional(self):
        self.assertEqual(B._classify("امروز خیلی خسته‌ام"), "emotional")
        self.assertEqual(B._classify("بی‌حالم"), "emotional")

    def test_content(self):
        self.assertEqual(B._classify("می‌خوام یه ست بسازم"), "content")
        self.assertEqual(B._classify("لاک نارنجی"), "content")

    def test_capacity(self):
        self.assertEqual(B._classify("سه ساعت وقت دارم"), "capacity")

    def test_halt(self):
        self.assertEqual(B._classify("دیگه نه، وایسا"), "halt")

    def test_greeting(self):
        self.assertEqual(B._classify("سلام"), "greeting")

    def test_random(self):
        self.assertEqual(B._classify("برنامهٔ فردا"), "random")


class TestSabaBrainIntegration(unittest.TestCase):
    """SabaBrain.respond_to_saba با LLM stub شده — فقط منطق، بدون network."""

    def setUp(self):
        self._tmp_mem = tempfile.NamedTemporaryFile(
            suffix=".jsonl", delete=False, mode="w")
        self._tmp_mem.close()
        # brain با memory موقت
        self.brain = B.SabaBrain()
        self.brain._memory = B.MemoryStore(path=Path(self._tmp_mem.name))

    def tearDown(self):
        try: os.unlink(self._tmp_mem.name)
        except OSError: pass

    def test_halt_returns_none_delegates_to_studio(self):
        """halt/boundary باید None برگرداند تا saba_studio با /halt برخورد کند."""
        self.assertIsNone(self.brain.respond_to_saba("دیگه نه، وایسا"))
        self.assertIsNone(self.brain.respond_to_saba("محدوده را تنگ‌تر کن"))

    def test_empty_returns_none(self):
        self.assertIsNone(self.brain.respond_to_saba(""))
        self.assertIsNone(self.brain.respond_to_saba("   "))

    def test_fallback_when_llm_offline(self):
        """اگه LLM خاموش باشد، heuristic fallback باید پاسخ بدهد (نه None)."""
        with patch.object(self.brain._llm, "chat", return_value=None):
            resp = self.brain.respond_to_saba("امروز خیلی خسته‌ام")
        self.assertIsNotNone(resp)
        self.assertIn("استراحت", resp)  # fallback emotional باید استراحت بگه

    def test_blocks_unsafe_llm_output(self):
        """اگه LLM پاسخِ forbidden بدهد، fallback تمیز برگردانده می‌شود."""
        with patch.object(self.brain._llm, "chat",
                          return_value={"text": "come to sydney for paypal", "source": "local"}):
            resp = self.brain.respond_to_saba("سلام")
        # باید fallback شده باشد، نه متنِ forbidden
        self.assertNotIn("sydney", resp.lower())
        self.assertNotIn("paypal", resp.lower())

    def test_memory_logged_on_each_exchange(self):
        """هر exchange باید دو entry در memory بگذارد (saba + bot)."""
        with patch.object(self.brain._llm, "chat",
                          return_value={"text": "سوال تستی", "source": "local"}):
            self.brain.respond_to_saba("یه ست می‌خوام")
        rec = self.brain._memory.recent(5)
        self.assertEqual(len(rec), 2)
        self.assertEqual(rec[0]["role"], "saba")
        self.assertEqual(rec[1]["role"], "bot")

    def test_think_and_communicate_compat(self):
        """think_and_communicate باید dict با messages برگرداند (compat با brief_page)."""
        out = self.brain.think_and_communicate(draft_title="weekly")
        self.assertIsInstance(out, dict)
        self.assertIn("messages", out)
        self.assertIn("blocked", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
