#!/usr/bin/env python3
"""تستِ parity برای مسیرِ دومِ ارسال (`approval_channel`).

پس‌زمینه
────────
۲۰۲۶-۰۷-۲۸: `tg_send_audit` نشان داد سیستم **دو** فرستندهٔ مستقل دارد.
`tg_api.TgClient.send` پارامترِ `topic_id` داشت؛ `approval_channel.send_text`
نداشت و تاپیک را فقط از `stream` حدس می‌زد — و آن هم فقط وقتی `chat_id` صریح
داده نشده بود. یعنی هر **پاسخِ مستقیم** به گروه بی‌تاپیک می‌رفت و در General
می‌نشست. برخلافِ باگِ `center.py` که رانشِ فلگ بود و با ری‌استارت حل شد، این
یکی باگِ کد بود و ری‌استارت درستش نمی‌کرد.

چه چیزی این تست محافظت می‌کند
──────────────────────────────
۱. **parity**: با فلگِ خاموش، رفتار باید بایت‌به‌بایت همان قبل باشد.
۲. **fail-closed**: هر ابهام → None، نه یک `message_thread_id`ِ حدسی
   (thread_idِ نامعتبر خطای ۴۰۰ می‌دهد و کلِ پیام گم می‌شود).
۳. **یک رأی برای هر دو مسیر**: همان `OCTOPUS_TG_TOPIC_REPLY`، نه فلگِ دوم.

منطق مستقیم از **سورسِ فایلِ زنده** استخراج و اجرا می‌شود (نه import)، چون
`approval_channel` ۲۸۷ کیلوبایت است و وابستگیِ سنگین دارد؛ این‌طور همان کدی
تست می‌شود که واقعاً روی دیسک است، بدونِ بارِ import.
"""
from __future__ import annotations

import ast
import os
import unittest
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_SRC = _OPS / "budget" / "approval_channel.py"
FLAG = "OCTOPUS_TG_TOPIC_REPLY"


def _load_reply_thread_id():
    """تابع را از سورسِ زنده بیرون می‌کشد و در فضای نامِ ایزوله اجرا می‌کند."""
    tree = ast.parse(_SRC.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_reply_thread_id":
            ns: dict = {"os": os}
            exec(compile(ast.Module([node], []), "<extracted>", "exec"), ns)
            return ns["_reply_thread_id"]
    return None


def msg(thread=28, is_topic=True, nest=False):
    m = {"message_thread_id": thread, "is_topic_message": is_topic}
    return {"callback_query": {"message": m}} if nest else {"message": m}


class _Base(unittest.TestCase):
    def setUp(self):
        if not _SRC.exists():
            self.skipTest("approval_channel.py در این درخت نیست")
        self.fn = _load_reply_thread_id()
        if self.fn is None:
            self.fail("_reply_thread_id در approval_channel.py پیدا نشد — "
                      "فیکسِ ۲۰۲۶-۰۷-۲۸ برگشت خورده است")
        self._prev = os.environ.get(FLAG)

    def tearDown(self):
        if self._prev is None:
            os.environ.pop(FLAG, None)
        else:
            os.environ[FLAG] = self._prev

    def _flag(self, value):
        if value is None:
            os.environ.pop(FLAG, None)
        else:
            os.environ[FLAG] = value


class ParityTests(_Base):
    def test_flag_absent_means_exactly_todays_behaviour(self):
        self._flag(None)
        self.assertIsNone(self.fn(msg()))

    def test_flag_off_means_exactly_todays_behaviour(self):
        for off in ("0", "", "false", "no", "off", "غلط"):
            self._flag(off)
            self.assertIsNone(self.fn(msg()), off)

    def test_flag_on_accepts_the_usual_truthy_spellings(self):
        for on in ("1", "true", "TRUE", "yes", "on", " on "):
            self._flag(on)
            self.assertEqual(self.fn(msg(28)), 28, on)


class FailClosedTests(_Base):
    def setUp(self):
        super().setUp()
        self._flag("1")

    def test_general_has_no_topic_flag_so_no_thread_is_sent(self):
        self.assertIsNone(self.fn(msg(is_topic=False)))

    def test_missing_is_topic_message_is_not_assumed(self):
        self.assertIsNone(self.fn({"message": {"message_thread_id": 28}}))

    def test_non_integer_thread_is_refused(self):
        for bad in ("28", 28.0, None, [28]):
            self.assertIsNone(self.fn(msg(thread=bad)), repr(bad))

    def test_garbage_update_never_raises(self):
        for bad in (None, [], "x", {}, {"message": None}, {"message": "x"}):
            self.assertIsNone(self.fn(bad), repr(bad))

    def test_callback_query_message_is_reached(self):
        self.assertEqual(self.fn(msg(65, nest=True)), 65)

    def test_callback_query_in_general_is_still_refused(self):
        self.assertIsNone(self.fn(msg(65, is_topic=False, nest=True)))


class SourceContractTests(unittest.TestCase):
    """قراردادهایی که باید در سورس بمانند، وگرنه فیکس بی‌صدا برمی‌گردد."""

    def setUp(self):
        if not _SRC.exists():
            self.skipTest("approval_channel.py در این درخت نیست")
        self.src = _SRC.read_text(encoding="utf-8")

    def test_send_text_still_accepts_topic_id(self):
        self.assertIn("topic_id: int | None = None", self.src,
                      "پارامترِ topic_id از send_text حذف شده")

    def test_explicit_topic_wins_over_stream_routing(self):
        self.assertIn("if thread is None and chat_id is None and stream:", self.src,
                      "شرطِ مسیریابیِ stream به حالتِ قبل برگشته")

    def test_every_poll_once_reply_passes_a_topic(self):
        """سه نقطهٔ پاسخ در poll_once باید topic_id بگیرند — وگرنه دوباره General."""
        self.assertEqual(self.src.count("topic_id=_thr"), 3,
                         "تعدادِ نقاطِ پاسخِ تاپیک‌دار در poll_once ۳ نیست")

    def test_the_second_sender_uses_the_same_flag_not_a_new_one(self):
        self.assertIn('"OCTOPUS_TG_TOPIC_REPLY"', self.src,
                      "مسیرِ دوم باید همان فلگِ مرکز را بخواند، نه فلگِ دوم")


if __name__ == "__main__":
    unittest.main(verbosity=2)
