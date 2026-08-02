#!/usr/bin/env python3
"""test_brain_saba.py — تست‌های فاز ۲: brain (BrainCore) + saba_link.

تمام تست‌ها $0، آفلاین، و مستقل از ارگانیسمِ زنده. cortex با flag-off تست می‌شود
(یعنی همیشه heuristic/fallback). scrub را به‌سختی می‌آزماید (مهم‌ترین نامتغیرِ PII).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

from pf_os import brain as B  # noqa: E402
from pf_os import saba_link as SL  # noqa: E402
from pf_os import config  # noqa: E402


class TestScrubPII(unittest.TestCase):
    """مهم‌ترین نامتغیر: هیچ PII/محتوا به cortex نمی‌رود."""

    def test_clean_text_passes(self):
        self.assertEqual(B.scrub_for_cortex("what is the price"), "what is the price")

    def test_empty_returns_empty(self):
        self.assertEqual(B.scrub_for_cortex(""), "")

    def test_name_ari_blocked(self):
        # نامِ اپراتور باید scrub شود
        self.assertEqual(B.scrub_for_cortex("tell ari about the plan"), "")

    def test_name_saba_blocked(self):
        self.assertEqual(B.scrub_for_cortex("is saba here"), "")

    def test_city_sydney_blocked(self):
        self.assertEqual(B.scrub_for_cortex("in sydney today"), "")

    def test_country_iran_blocked(self):
        self.assertEqual(B.scrub_for_cortex("users from iran"), "")

    def test_long_text_truncated(self):
        long = "x" * 500
        out = B.scrub_for_cortex(long)
        self.assertEqual(len(out), 200)


class TestIntentClassification(unittest.TestCase):
    def setUp(self):
        self.core = B.BrainCore()

    def test_price_intent(self):
        self.assertEqual(self.core._classify_saba_intent("قیمت چقدر؟"), "price")
        self.assertEqual(self.core._classify_saba_intent("how much price?"), "price")

    def test_schedule_intent(self):
        self.assertEqual(self.core._classify_saba_intent("کی پست کنم؟"), "schedule")
        self.assertEqual(self.core._classify_saba_intent("what time?"), "schedule")

    def test_trend_intent(self):
        self.assertEqual(self.core._classify_saba_intent("ترند چی هست؟"), "trend")

    def test_boundary_intent(self):
        self.assertEqual(self.core._classify_saba_intent("خسته شدم"), "boundary")
        self.assertEqual(self.core._classify_saba_intent("می‌خوام halt کنم"), "boundary")

    def test_general_intent(self):
        self.assertEqual(self.core._classify_saba_intent("سلام"), "general")

    def test_empty_unknown(self):
        self.assertEqual(self.core._classify_saba_intent(""), "unknown")


class TestRespondToSaba(unittest.TestCase):
    """گفتگوی دوطرفه با مغز — مهم‌ترین رابط."""

    def setUp(self):
        os.environ.pop(config.WIRE_CORTEX, None)  # cortex off → heuristic
        self.core = B.BrainCore()

    def test_returns_string_for_clean_text(self):
        r = self.core.respond_to_saba("قیمت چقدر باید باشه؟")
        self.assertIsInstance(r, str)
        self.assertTrue(len(r) > 5)

    def test_returns_none_for_pii_text(self):
        """اگر متن PII داشته باشد (scrub fail)، None برمی‌گرداند."""
        r = self.core.respond_to_saba("ari چه وقت میاد؟")
        self.assertIsNone(r)

    def test_returns_none_for_empty(self):
        r = self.core.respond_to_saba("")
        self.assertIsNone(r)

    def test_response_is_content_free(self):
        """پاسخ نباید نام/شهر/محتوا داشته باشد."""
        for text in ["قیمت", "کی پست کنم", "ترند", "سلام"]:
            r = self.core.respond_to_saba(text)
            if r is None:
                continue
            rl = r.lower()
            for bad in ("ari", "saba", "sydney", "iran", "tehran"):
                self.assertNotIn(bad, rl, f"response contains PII '{bad}': {r}")

    def test_price_response_has_price_keyword(self):
        r = self.core.respond_to_saba("قیمت؟")
        self.assertIsNotNone(r)
        self.assertIn("قیمت", r)  # heuristic price response mentions قیمت

    def test_boundary_response_mentions_halt_or_scope(self):
        r = self.core.respond_to_saba("خسته شدم")
        self.assertIsNotNone(r)
        # باید به halt/محدوده/استراحت اشاره کند
        self.assertTrue(any(k in r for k in ("halt", "محدوده", "استراحت", "/halt")))

    def test_never_raises_on_garbage(self):
        # هر ورودی نباید exception بدهد
        for text in [None, 123, "<script>", "x" * 1000, "\x00\x01"]:
            try:
                self.core.respond_to_saba(text)  # type: ignore
            except Exception as e:
                self.fail(f"respond_to_saba raised on {text!r}: {e}")

    def test_last_saba_response_tracked(self):
        self.core.respond_to_saba("قیمت؟")
        last = self.core._last_saba_response
        self.assertIn("intent", last)
        self.assertEqual(last["intent"], "price")
        self.assertIn(last["source"], ("cortex", "heuristic", "fallback"))


class TestThink(unittest.TestCase):
    def setUp(self):
        os.environ.pop(config.WIRE_CORTEX, None)
        self.core = B.BrainCore()

    def test_pii_rejected(self):
        r = self.core.think("daily", "tell ari the plan")
        self.assertFalse(r.ok)
        self.assertIn("scrub", r.reason)

    def test_clean_think_returns_brainresponse(self):
        r = self.core.think("daily", "what is the weather")
        self.assertIsInstance(r, B.BrainResponse)
        # flag-off → fallback
        self.assertFalse(r.ok)
        self.assertEqual(r.source, "fallback")


class TestBrainStatus(unittest.TestCase):
    def test_status_returns_dict(self):
        core = B.BrainCore()
        s = core.status()
        self.assertIn("heuristic_loaded", s)
        self.assertIn("compliance_rules", s)
        self.assertIn("cortex", s)
        self.assertIn("ticks", s)
        self.assertIsInstance(s["ticks"], int)


class TestSabaLink(unittest.TestCase):
    """پلِ من↔صبا — send_to_saba, pending_drafts, snapshot."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["PF_STUDIO_DIR"] = self._tmp.name
        # reimport not needed — saba_link هر بار مسیر را از env می‌خواند

    def tearDown(self):
        os.environ.pop("PF_STUDIO_DIR", None)
        self._tmp.cleanup()

    def test_send_to_saba_creates_file(self):
        ok = SL.send_to_saba("hi from pf_os")
        self.assertTrue(ok)
        msgs = json.loads((Path(self._tmp.name) / "for_saba.json").read_text(encoding="utf-8"))
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["text"], "hi from pf_os")
        self.assertFalse(msgs[0]["read"])

    def test_send_to_saba_empty_rejected(self):
        self.assertFalse(SL.send_to_saba(""))
        self.assertFalse(SL.send_to_saba("   "))

    def test_send_to_saba_caps_at_50(self):
        for i in range(60):
            SL.send_to_saba(f"msg {i}")
        msgs = json.loads((Path(self._tmp.name) / "for_saba.json").read_text(encoding="utf-8"))
        self.assertEqual(len(msgs), 50)
        # آخرین‌ها باقی مانده
        self.assertEqual(msgs[-1]["text"], "msg 59")

    def test_send_brief(self):
        ok = SL.send_brief(["line1", "line2"])
        self.assertTrue(ok)
        msgs = json.loads((Path(self._tmp.name) / "for_saba.json").read_text(encoding="utf-8"))
        self.assertIn("بریف", msgs[0]["text"])

    def test_send_notify(self):
        ok = SL.send_notify("warmup", "channel ok")
        self.assertTrue(ok)

    def test_pending_drafts(self):
        drafts = [{"draft_id": "D1", "status": "pending"},
                  {"draft_id": "D2", "status": "approved"},
                  {"draft_id": "D3", "status": "pending"}]
        (Path(self._tmp.name) / "drafts.json").write_text(json.dumps(drafts))
        pend = SL.pending_drafts()
        self.assertEqual(len(pend), 2)

    def test_saba_halted_false_by_default(self):
        self.assertFalse(SL.saba_halted())

    def test_saba_halted_true_when_file_exists(self):
        (Path(self._tmp.name) / "HALT").write_text("x")
        self.assertTrue(SL.saba_halted())

    def test_saba_capacity_empty_default(self):
        self.assertEqual(SL.saba_capacity(), {})

    def test_saba_capacity_set(self):
        (Path(self._tmp.name) / "capacity.json").write_text(
            json.dumps({"hours": 3, "date": "2026-07-19"}))
        cap = SL.saba_capacity()
        self.assertEqual(cap["hours"], 3)

    def test_snapshot(self):
        SL.send_to_saba("x")
        snap = SL.snapshot()
        self.assertIn("pending_drafts", snap)
        self.assertIn("saba_halted", snap)
        self.assertIn("messages_in_inbox", snap)
        self.assertEqual(snap["messages_in_inbox"], 1)

    def test_on_new_draft_sends_ack(self):
        draft = {"title": "some title"}
        out = SL.on_new_draft(draft)
        self.assertIsNotNone(out)
        msgs = json.loads((Path(self._tmp.name) / "for_saba.json").read_text(encoding="utf-8"))
        self.assertEqual(len(msgs), 1)
        self.assertIn("kind", msgs[0])
        self.assertEqual(msgs[0]["kind"], "draft_ack")

    def test_on_new_draft_empty_title_returns_none(self):
        self.assertIsNone(SL.on_new_draft({"title": ""}))


class TestOnNewDraftBrainReal(unittest.TestCase):
    """fix #1 (metaphor → REAL): on_new_draft باید مغز را *واقعاً* صدا بزند.

    قانونِ مالک: «استعاره‌ها باید در کد واقعی باشند — نه تظاهر.» قبلاً فقط
    hasattr(brain, "_classify_saba_intent") چک می‌شد و یک پیامِ دروغ
    («مغز داره بهترین قیمت/زمان رو محاسبه می‌کنه») فرستاده می‌شد بدونِ اینکه
    هیچ متدِ مغز اجرا شود. این تست‌ها اثبات می‌کنند مغز حالا واقعاً اجرا می‌شود
    و پیشنهاد از خروجیِ واقعیِ مغز ساخته می‌شود.
    """

    OLD_LIE = "مغز داره بهترین قیمت/زمان"  # رشته‌ی دروغِ قدیمی — نباید هرگز تولید شود

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["PF_STUDIO_DIR"] = self._tmp.name
        os.environ.pop(config.WIRE_CORTEX, None)  # cortex off → heuristicِ واقعی

    def tearDown(self):
        os.environ.pop("PF_STUDIO_DIR", None)
        self._tmp.cleanup()

    def _acks(self):
        p = Path(self._tmp.name) / "for_saba.json"
        if not p.exists():
            return []
        return [m for m in json.loads(p.read_text(encoding="utf-8"))
                if m.get("kind") == "draft_ack"]

    def test_brain_respond_is_actually_invoked(self):
        """spy-brain اثبات می‌کند respond_to_saba واقعاً با محتوای درفت صدا زده شد."""
        class SpyBrain:
            def __init__(self):
                self.classify_calls, self.respond_calls = [], []

            def _classify_saba_intent(self, text):
                self.classify_calls.append(text)
                return "price"

            def respond_to_saba(self, text):
                self.respond_calls.append(text)
                return "PRICE_ADVICE_FROM_BRAIN"

        spy = SpyBrain()
        out = SL.on_new_draft({"title": "winter socks pricing"}, brain=spy)
        # مغز *واقعاً* صدا زده شد (نه فقط hasattr)
        self.assertEqual(len(spy.respond_calls), 1, "respond_to_saba must be called")
        self.assertEqual(len(spy.classify_calls), 1,
                         "_classify_saba_intent must be called")
        # محتوای واقعیِ درفت به مغز رسید (نه یک رشته‌ی هاردکد)
        self.assertIn("winter socks", spy.respond_calls[0])
        # پیشنهاد از خروجیِ واقعیِ مغز ساخته شد، نه رشته‌ی canned/دروغ
        self.assertIn("PRICE_ADVICE_FROM_BRAIN", out)
        self.assertNotIn(self.OLD_LIE, out)
        # همان به for_saba.json رفت (kind=draft_ack)
        acks = self._acks()
        self.assertEqual(len(acks), 1)
        self.assertIn("PRICE_ADVICE_FROM_BRAIN", acks[0]["text"])

    def test_no_brain_stays_default_and_honest(self):
        """brain-off (پیش‌فرض): پیامِ صادقانه‌ی پیش‌فرض؛ هیچ ادعای دروغِ مغز.

        این byte-identical با رفتارِ قبلی است (سازگاریِ flag-off).
        """
        out = SL.on_new_draft({"title": "some title"})
        self.assertIsNotNone(out)
        self.assertNotIn(self.OLD_LIE, out)
        self.assertIn("درفتِ جدیدت رسید", out)

    def test_brain_called_but_none_gives_honest_fallback(self):
        """اگر مغز پاسخِ کامل نداد (None، مثلِ PII/scrub-reject): مغز باز هم
        صدا زده شده، ولی هیچ ادعای «مغز محاسبه کرد» ساخته نمی‌شود."""
        class NullBrain:
            def __init__(self):
                self.respond_calls = []

            def _classify_saba_intent(self, text):
                return "price"

            def respond_to_saba(self, text):
                self.respond_calls.append(text)
                return None

        nb = NullBrain()
        out = SL.on_new_draft({"title": "pricing question"}, brain=nb)
        self.assertEqual(len(nb.respond_calls), 1)  # مغز واقعاً صدا زده شد
        self.assertNotIn(self.OLD_LIE, out)         # دروغِ قدیمی نیست
        self.assertIn("قیمت", out)                  # ackِ صادقانه‌ی intent=price

    def test_real_braincore_end_to_end(self):
        """با BrainCore واقعی + cortex off: پیشنهاد از پاسخِ heuristicِ واقعیِ مغز."""
        core = B.BrainCore()
        out = SL.on_new_draft({"title": "قیمت این ست چطوری باشه؟"}, brain=core)
        self.assertIsNotNone(out)
        self.assertNotIn(self.OLD_LIE, out)
        self.assertIn("قیمت", out)  # heuristic price response شاملِ «قیمت»
        # مغز واقعاً پردازش کرد → intent ثبت شد
        self.assertEqual(core._last_saba_response.get("intent"), "price")


if __name__ == "__main__":
    unittest.main()
