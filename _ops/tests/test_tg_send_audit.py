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
    """`send_text`: اول `topic_id` صریح، بعد استنتاج از `stream`."""

    def test_explicit_chat_id_without_topic_can_never_get_a_topic(self):
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

    # ── `topic_id` روی send_text (اصلاحِ ۲۰۲۶-۰۷-۳۱) ─────────────────────────
    # این چهار تست همان قرمزِ دروغینی را قفل می‌کنند که طبقه‌بند تولید می‌کرد:
    # `send_text(..., chat_id=cid, topic_id=_thr)` صریحاً تاپیک می‌دهد، ولی
    # چون طبقه‌بند فقط `chat_id` را می‌دید، «بی‌تاپیک» اعلامش می‌کرد.

    def test_explicit_topic_id_beats_the_chat_id_rule(self):
        s = one("def f(self, cid, upd):\n"
                "    self.send_text('x', None, chat_id=cid, "
                "topic_id=_reply_thread_id(upd))\n")
        self.assertEqual(s["topic"], "conditional")
        self.assertEqual(s["topic_expr"], "_reply_thread_id(upd)")

    def test_literal_topic_id_on_send_text_is_certain(self):
        s = one("def f(self, cid):\n"
                "    self.send_text('x', None, chat_id=cid, topic_id=28)\n")
        self.assertEqual(s["topic"], "certain")
        self.assertEqual(s["topic_expr"], "28")

    def test_topic_id_none_falls_back_to_the_old_rules_not_a_new_class(self):
        """`isinstance(None, int)` رد می‌شود ⇒ عملاً «داده نشده»."""
        s = one("def f(self, cid):\n"
                "    self.send_text('x', None, chat_id=cid, topic_id=None)\n")
        self.assertEqual(s["topic"], "absent")

    def test_positional_topic_id_is_seen_too(self):
        s = one("def f(self, cid, thr):\n"
                "    self.send_text('x', None, cid, 'heart', thr)\n")
        self.assertEqual(s["topic"], "conditional")
        self.assertEqual(s["topic_expr"], "thr")

    def test_star_kwargs_on_send_text_is_conditional_not_absent(self):
        s = one("def f(self, cid, opts):\n"
                "    self.send_text('x', None, chat_id=cid, **opts)\n")
        self.assertEqual(s["topic"], "conditional")


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

    ── چرا عدد در ۲۰۲۶-۰۷-۳۱ از ۷ به ۳ آمد ─────────────────────────────────
    **کد بدتر یا بهتر نشد؛ ترازو دقیق‌تر شد.** خط‌پایهٔ ۷ روی طبقه‌بندی گرفته
    شده بود که `topic_id` را روی `send_text` اصلاً نگاه نمی‌کرد. چهار نقطه
    عملاً تاپیک می‌دادند و «بی‌تاپیک» شمرده می‌شدند:
        approval_channel.poll_once ×۳   `topic_id=_thr`  → conditional
        test_tg_stream_routing:164      `topic_id=7`     → certain
    یعنی ۴ تا از آن ۷ تا **قرمزِ دروغین** بودند. با دیدنِ `topic_id`، شمارشِ
    راست‌گو ۳ است — و هر سه فیکسچرِ عمدیِ تست‌اند، نه مسیرِ تولیدی.

    اگر خط‌پایه روی ۷ می‌ماند، چرخ‌دنده چهار واحد شل بود: می‌شد چهار ارسالِ
    بی‌تاپیکِ **واقعیِ** تازه اضافه کرد و تست همچنان سبز می‌ماند. پایین‌کشیدنِ
    عدد این‌جا سخت‌گیرانه‌تر است، نه آسان‌گیرانه‌تر — و همان جهتِ مجازِ
    چرخ‌دنده است (فقط پایین).
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


class NonProductionDirTests(unittest.TestCase):
    """`audit_paths` نباید نسخه‌های پشتیبان (`_bak`، `patch_backups`) را production بشمارد.

    رگرسیونِ ۲۰۲۶-۰۸-۱۱: یک snapshot زیرِ `_ops/_bak/talk-discovery-arm-*/` همان
    send-site ِ `center.py` را دوباره داشت و ratchet ِ `absent` را از ۲ به ۳ برد —
    قرمزِ دروغین، چون کدِ اجراشوندهٔ production عوض نشده بود.
    """

    def _tree(self):
        import tempfile
        d = Path(tempfile.mkdtemp(prefix="tgaudit-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        return d

    _ABSENT_SRC = ("def f(self, msg):\n"
                   "    self._client.send('x', chat_id=1)\n")

    def test_bak_snapshot_is_not_counted(self):
        root = self._tree()
        (root / "telegram_center").mkdir(parents=True)
        (root / "telegram_center" / "center.py").write_text(self._ABSENT_SRC, "utf-8")
        bak = root / "_bak" / "snap-20260811" / "telegram_center"
        bak.mkdir(parents=True)
        (bak / "center.py").write_text(self._ABSENT_SRC, "utf-8")
        _sites, summ = sa.audit_paths([root])
        # فقط نسخهٔ production شمرده می‌شود، نه کپیِ `_bak`.
        self.assertEqual(summ["by_topic"]["absent"], 1)

    def test_patch_backups_is_not_counted(self):
        root = self._tree()
        pb = root / "patch_backups" / "old" / "telegram_center"
        pb.mkdir(parents=True)
        (pb / "center.py").write_text(self._ABSENT_SRC, "utf-8")
        _sites, summ = sa.audit_paths([root])
        self.assertEqual(summ["by_topic"]["absent"], 0)

    def test_unknown_dirs_are_still_audited(self):
        """پوشهٔ ناشناخته باید همچنان audit شود — فقط لیستِ دقیق حذف می‌شود."""
        root = self._tree()
        sub = root / "telegram_center"
        sub.mkdir(parents=True)
        (sub / "center.py").write_text(self._ABSENT_SRC, "utf-8")
        _sites, summ = sa.audit_paths([root])
        self.assertEqual(summ["by_topic"]["absent"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
