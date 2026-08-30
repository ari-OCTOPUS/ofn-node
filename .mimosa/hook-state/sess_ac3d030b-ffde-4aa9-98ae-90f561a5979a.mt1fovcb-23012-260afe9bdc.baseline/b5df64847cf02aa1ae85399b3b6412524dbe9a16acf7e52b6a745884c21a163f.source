#!/usr/bin/env python3
"""تستِ ممیزیِ مسیرِ ارسال.

قانونی که این تست محافظت می‌کند: **ممیزیِ ایستا حق ندارد سبز اعلام کند.**
`topic_id=self._reply_thread(msg)` ایستا درست به‌نظر می‌رسد و زنده `None`
برمی‌گرداند؛ اگر این ماژول آن را `certain` بشمارد، خودش سبزِ دروغین می‌سازد.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tg_send_audit as sa  # noqa: E402


def one(src, fn="m.py"):
    sites = sa.audit_source(src, fn)
    return sites[0] if sites else None


class TopicParamTests(unittest.TestCase):
    def test_literal_int_is_the_only_certain_case(self):
        s = one("def f(self):\n    self._client.send('x', topic_id=28)\n")
        self.assertEqual(s["topic"], "certain")

    def test_runtime_expression_is_conditional_never_certain(self):
        """قلبِ تست — این همان الگویی است که ۴۸ پیام را به General فرستاد."""
        s = one("def f(self, msg):\n"
                "    self._client.send('x', topic_id=self._reply_thread(msg))\n")
        self.assertEqual(s["topic"], "conditional")
        self.assertEqual(s["topic_expr"], "self._reply_thread(msg)")
        self.assertTrue(s["is_reply_path"])

    def test_dict_get_is_conditional_because_the_key_may_be_missing(self):
        s = one("def f(self, topics, leg):\n"
                "    self._client.send('x', topic_id=topics.get(leg))\n")
        self.assertEqual(s["topic"], "conditional")

    def test_explicit_none_is_absent(self):
        s = one("def f(self):\n    self._client.send('x', topic_id=None)\n")
        self.assertEqual(s["topic"], "absent")

    def test_missing_kwarg_is_absent(self):
        s = one("def f(self):\n    self._client.send('x', chat_id=1)\n")
        self.assertEqual(s["topic"], "absent")

    def test_star_kwargs_is_conditional_not_absent(self):
        s = one("def f(self, opts):\n    self._client.send('x', chat_id=1, **opts)\n")
        self.assertEqual(s["topic"], "conditional")


class StreamRoutedTests(unittest.TestCase):
    """`send_text` تاپیک را فقط از `stream` می‌گیرد، و فقط بدونِ `chat_id`."""

    def test_explicit_chat_id_can_never_get_a_topic(self):
        s = one("def f(self, chat_id):\n"
                "    self.send_text('x', None, chat_id=chat_id)\n")
        self.assertEqual(s["topic"], "absent")
        self.assertEqual(s["sender"], "stream_routed")

    def test_stream_only_is_conditional(self):
        s = one("def f(self):\n    self.send_text('x', None, stream='needs')\n")
        self.assertEqual(s["topic"], "conditional")

    def test_neither_is_owner_dm_and_not_a_defect(self):
        s = one("def f(self):\n    self.send_text('x')\n")
        self.assertEqual(s["topic"], "dm")

    def test_positional_chat_id_is_detected(self):
        s = one("def f(self, cid):\n    self.send_text('x', None, cid)\n")
        self.assertEqual(s["topic"], "absent")


class ScopeTests(unittest.TestCase):
    def test_non_telegram_send_is_excluded(self):
        """`sock.send(buf)` نباید به‌عنوانِ ارسالِ بی‌تاپیک شمرده شود."""
        self.assertIsNone(one("def f(sock, buf):\n    sock.send(buf)\n"))
        self.assertIsNone(one("def f(q, item):\n    q.send(item)\n"))

    def test_client_like_receivers_are_included(self):
        for recv in ("self._client", "channel", "tg", "self.bot", "telegram_api"):
            s = one(f"def f(self):\n    {recv}.send('x')\n")
            self.assertIsNotNone(s, recv)

    def test_reply_path_detected_from_any_message_param_name(self):
        for p in ("msg", "message", "update"):
            s = one(f"def f(self, {p}):\n    self._client.send('x', chat_id=1)\n")
            self.assertTrue(s["is_reply_path"], p)

    def test_module_level_send_has_no_enclosing_function(self):
        s = one("client.send('x', chat_id=1)\n")
        self.assertEqual(s["func"], "<module>")

    def test_syntax_error_is_reported_not_raised(self):
        sites = sa.audit_source("def f(:\n", "bad.py")
        self.assertEqual(len(sites), 1)
        self.assertIn("SyntaxError", sites[0]["error"])


class SummaryTests(unittest.TestCase):
    def test_proven_rate_counts_only_literals(self):
        src = ("def a(self):\n    self._client.send('x', topic_id=28)\n"
               "def b(self, msg):\n"
               "    self._client.send('x', topic_id=self._reply_thread(msg))\n"
               "def c(self):\n    self._client.send('x', chat_id=1)\n")
        s = sa.summarise(sa.audit_source(src))
        self.assertEqual(s["total_sites"], 3)
        self.assertAlmostEqual(s["proven_rate"], 1 / 3)
        self.assertEqual(s["unproven"], 2)

    def test_summary_survives_parse_errors_without_counting_them(self):
        s = sa.summarise(sa.audit_source("def f(:\n", "bad.py"))
        self.assertEqual(s["total_sites"], 0)
        self.assertEqual(len(s["parse_errors"]), 1)

    def test_render_never_raises(self):
        s = sa.summarise(sa.audit_source("def f(self):\n    tg.send('x')\n"))
        self.assertIsInstance(sa.render([], s), str)


class RealTreeRatchetTests(unittest.TestCase):
    """چرخ‌دنده — این اعداد فقط اجازه دارند **کم** شوند.

    چرا خط‌پایه ثابت هاردکد نشد: این ماژول روی یک کپیِ **ناقص** از درخت اندازه
    گرفته شد (۵ نقطهٔ بی‌تاپیک: ۳ در `approval_channel.poll_once` که هیچ فلگی
    درستشان نمی‌کند، ۲ در `center`). عددِ درختِ کامل ممکن است بیشتر باشد. یک
    خط‌پایهٔ هاردکدشده در آن حالت یک **قرمزِ دروغین** می‌سازد — دقیقاً همان
    چیزی که کلِ این کار علیهش است.

    پس خط‌پایه خودش را بارِ اول از واقعیت می‌سازد و در
    `_ops/tests/_baselines/tg-send-audit.json` می‌نشیند. بعد از آن فقط سفت‌تر
    می‌شود: هر بهبود، خط‌پایه را پایین می‌کشد و برگشت‌ناپذیر می‌کند.
    """

    @staticmethod
    def _baseline_path():
        d = Path(__file__).resolve().parent / "_baselines"
        d.mkdir(exist_ok=True)
        return d / "tg-send-audit.json"

    def _ratchet(self, key: str, current: int, why: str):
        import json
        p = self._baseline_path()
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            data = {}
        prior = data.get(key)
        if prior is None:
            data[key] = current
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                         encoding="utf-8")
            print(f"\n   [ratchet] خط‌پایهٔ {key} = {current} ثبت شد (اولین اجرا)")
            return
        self.assertLessEqual(current, prior, f"{why} (خط‌پایه {prior} → حالا {current})")
        if current < prior:
            data[key] = current
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                         encoding="utf-8")
            print(f"\n   [ratchet] {key}: {prior} → {current} ✅ سفت‌تر شد")

    def _audit(self):
        ops = Path(__file__).resolve().parents[1]
        if not (ops / "telegram_center" / "center.py").exists():
            self.skipTest("درختِ زندهٔ _ops این‌جا نیست")
        return sa.audit_paths([ops])[1]

    def test_absent_sites_never_increase(self):
        s = self._audit()
        self._ratchet("absent", s["by_topic"]["absent"],
                      "یک مسیرِ ارسالِ بی‌تاپیکِ تازه اضافه شده — پیامش در General می‌افتد")

    def test_reply_paths_without_topic_never_increase(self):
        s = self._audit()
        self._ratchet("reply_absent", s["reply_absent"],
                      "یک مسیرِ پاسخ بدونِ topic_id اضافه شده")


if __name__ == "__main__":
    unittest.main(verbosity=2)
