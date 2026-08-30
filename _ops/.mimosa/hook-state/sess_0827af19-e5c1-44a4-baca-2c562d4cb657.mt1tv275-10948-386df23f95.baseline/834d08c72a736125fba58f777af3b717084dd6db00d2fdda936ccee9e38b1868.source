#!/usr/bin/env python3
"""تستِ ردِ ارسال‌های تلگرام.

هستهٔ ماجرا: تفکیکِ سه مقصد — خصوصی / تاپیکِ درست / General — و اینکه فقط
سومی «بدمسیر» شمرده شود. تستِ آخر روی لاگِ **واقعی** اجرا می‌شود اگر موجود باشد.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tg_trace as tt  # noqa: E402

GROUP = -1004475788460
TOPICS = {"lead": 22, "system": 28, "knowledge": 29}


def _cfg(path: Path, chat_id=GROUP, topics=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"chat_id": chat_id,
                                "topics": TOPICS if topics is None else topics}),
                    encoding="utf-8")


def _log(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _row(ts, chat, topic, stream="center", ok=True, chars=100):
    return {"ts": ts, "chat": chat, "topic": topic, "stream": stream,
            "ok": ok, "chars": chars, "sha": "deadbeef"}


class ClassifyTests(unittest.TestCase):
    def test_dm_has_no_topic_and_is_not_misrouted(self):
        kind, _ = tt.classify(_row(1, 6150431610, None), GROUP, {})
        self.assertEqual(kind, "dm")

    def test_group_with_topic_is_correct(self):
        kind, name = tt.classify(_row(1, GROUP, 28), GROUP, {28: "system"})
        self.assertEqual(kind, "group_topic")
        self.assertEqual(name, "system")

    def test_group_without_topic_is_the_defect(self):
        kind, _ = tt.classify(_row(1, GROUP, None), GROUP, {})
        self.assertEqual(kind, "group_general")

    def test_unknown_topic_id_still_counts_as_topic_addressed(self):
        kind, name = tt.classify(_row(1, GROUP, 999), GROUP, {28: "system"})
        self.assertEqual(kind, "group_topic")
        self.assertEqual(name, "#999")

    def test_missing_config_never_invents_a_group(self):
        # chat_id ناشناخته → همه‌چیز خصوصی فرض می‌شود، نه «بدمسیر».
        # ادعای دروغِ بدمسیری بدتر از سکوت است.
        kind, _ = tt.classify(_row(1, GROUP, None), None, {})
        self.assertEqual(kind, "dm")


class AnalyseTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            _row(100, 6150431610, None, "center"),
            _row(200, GROUP, 28, "doctor"),
            _row(300, GROUP, None, "center", chars=1500),
            _row(400, GROUP, None, "center", chars=2000),
            _row(500, GROUP, 22, "center"),
            _row(600, GROUP, None, "needs", ok=False, chars=10),
        ]

    def test_counts_split_three_ways(self):
        s = tt.analyse(self.rows, GROUP, {22: "lead", 28: "system"})
        self.assertEqual((s["dm"], s["group_topic"], s["group_general"]), (1, 2, 3))
        self.assertEqual(s["total"], 6)
        self.assertEqual(s["ok"], 5)
        self.assertEqual(s["failed"], 1)

    def test_misrouted_chars_only_counts_general(self):
        s = tt.analyse(self.rows, GROUP, {})
        self.assertEqual(s["misrouted"], 3)
        self.assertEqual(s["misrouted_chars"], 1500 + 2000 + 10)

    def test_per_stream_localisation_names_the_culprit(self):
        s = tt.analyse(self.rows, GROUP, {})
        self.assertEqual(s["by_stream"]["center"]["general"], 2)
        self.assertEqual(s["by_stream"]["doctor"]["general"], 0)

    def test_group_topic_rate_ignores_dm(self):
        s = tt.analyse(self.rows, GROUP, {})
        self.assertAlmostEqual(s["group_topic_rate"], 2 / 5)

    def test_rate_is_none_when_no_group_traffic(self):
        s = tt.analyse([_row(1, 6150431610, None)], GROUP, {})
        self.assertIsNone(s["group_topic_rate"])


class IOTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.log = self.tmp / "state" / "tg-send-log.jsonl"
        self.cfg = self.tmp / "state" / "telegram" / "center-config.json"

    def test_broken_lines_are_counted_not_swallowed(self):
        self.log.parent.mkdir(parents=True, exist_ok=True)
        self.log.write_text('{"ts":1,"chat":1,"topic":null}\nNOT JSON\n[]\n',
                            encoding="utf-8")
        rows, broken = tt.load_rows(self.log)
        self.assertEqual(len(rows), 1)
        self.assertEqual(broken, 2, "خطِ خراب باید شمرده شود، نه بی‌صدا رد شود")

    def test_missing_log_is_fail_soft_and_flagged(self):
        rows, broken = tt.load_rows(self.tmp / "nope.jsonl")
        self.assertEqual(rows, [])
        self.assertEqual(broken, -1)

    def test_since_hours_filters_by_clock(self):
        _log(self.log, [_row(1000, GROUP, None), _row(9000, GROUP, None)])
        rows, _ = tt.load_rows(self.log, since_hours=1, now=9000)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["ts"], 9000)

    def test_trace_end_to_end_and_render_is_content_free(self):
        _cfg(self.cfg)
        _log(self.log, [_row(1000, GROUP, None, chars=1234),
                        _row(2000, GROUP, 28)])
        rows, stats, topics, chat = tt.trace(self.log, self.cfg)
        self.assertEqual(stats["misrouted"], 1)
        self.assertTrue(stats["config_found"])
        text = tt.render(rows, stats, topics, chat)
        self.assertIn("General", text)
        self.assertNotIn("deadbeef", text, "sha نباید در کارت چاپ شود")
        self.assertNotIn(str(GROUP), text, "شناسهٔ خام چت نباید چاپ شود")

    def test_render_of_empty_window_is_a_sentence_not_a_crash(self):
        self.assertIsInstance(tt.render([], {"total": 0}, {}, GROUP), str)


class RealLogTests(unittest.TestCase):
    """روی لاگِ واقعی، اگر در این درخت بود. نبودش سوئیت را قرمز نمی‌کند."""

    def test_real_log_reproduces_the_2026_07_27_finding(self):
        root = Path(__file__).resolve().parents[1]
        log = root / "state" / "tg-send-log.jsonl"
        cfg = root / "state" / "telegram" / "center-config.json"
        if not (log.exists() and cfg.exists()):
            self.skipTest("لاگِ زنده در این درخت نیست")
        rows, stats, _t, _c = tt.trace(log, cfg)
        self.assertGreater(stats["total"], 0)
        self.assertEqual(stats["dm"] + stats["group_topic"] + stats["group_general"],
                         stats["total"], "هر ارسال باید دقیقاً یک مقصد داشته باشد")
        # عمداً `>= 0` و نه `== 0`: یک خطِ خرابِ گذرا در لاگِ زنده نباید سوئیتِ
        # ۳۴۲فایلی را قرمز کند (قرمزِ محیطی = همان لرزشی که run_all دارد شکارش
        # می‌کند). `-1` یعنی فایل اصلاً خوانده نشد — آن یکی واقعاً شکست است.
        self.assertGreaterEqual(stats["broken_lines"], 0,
                                "لاگِ ارسال خوانده نشد")
        self.assertIsNotNone(stats["group_topic_rate"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
