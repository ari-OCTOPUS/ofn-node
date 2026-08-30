#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_money_pulse.py — تست‌های money-pulse (۲۰۲۶-۰۷-۲۵).

پوشش:
  ۱) flag-off: beat() no-op، هیچ فایلی نوشته نمی‌شه.
  ۲) flag-on: beat() یک sample به money-pulse.jsonl اضافه می‌کنه.
  ۳) هرگز MONEY_ATTRIBUTION جعلی نمی‌نویسه (wall anti-reward-hacking).
  ۴) فرصتِ بزرگ (≥HOT_THRESHOLD) → center.push_alert صدا زده می‌شه.
  ۵) beat() هرگز raise نمی‌کنه (fail-soft).
  ۶) status() ساختار درست.

$0 و آفلاین. attribution با mock patch می‌شه.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("money-pulse")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "heart"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import money_pulse as mp  # noqa: E402


class _FakeCenter:
    def __init__(self):
        self.alerts = []
    def push_alert(self, text):
        self.alerts.append(text)
        return True


class TestMoneyPulse(unittest.TestCase):
    def setUp(self):
        os.environ.pop(mp.FLAG, None)
        # pulse stream به sandbox
        mp.STREAM_PATH = opslib.STATE_DIR / "pulse" / "money-pulse.jsonl"

    def _with_revenue(self, confirmed_aud):
        """attribution.confirmed_revenue را mock کن تا درآمد برگرداند."""
        cents = int(confirmed_aud * 100)
        return mock.patch("attribution.confirmed_revenue",
                          return_value={"by_cell": {"mining": cents},
                                        "confirmed": cents})

    # ═══ ۱) flag-off = no-op ═══════════════════════════════════════════════
    def test_flag_off_noop(self):
        fc = _FakeCenter()
        out = mp.beat(center=fc)
        self.assertEqual(out.get("reason"), "flag-off")
        self.assertFalse(out.get("hot"))
        self.assertFalse(out.get("notified"))
        self.assertEqual(len(fc.alerts), 0)

    # ═══ ۲) flag-on = sample نوشته می‌شه ══════════════════════════════════
    def test_flag_on_writes_sample(self):
        os.environ[mp.FLAG] = "1"
        fc = _FakeCenter()
        with self._with_revenue(0.0):  # صفر ولی حس می‌کنه
            out = mp.beat(center=fc)
        self.assertIn("sense", out)
        self.assertTrue(mp.STREAM_PATH.exists(), "sample باید نوشته بشه")
        lines = mp.STREAM_PATH.read_text(encoding="utf-8").strip().splitlines()
        self.assertGreaterEqual(len(lines), 1)

    # ═══ ۳) هرگز MONEY_ATTRIBUTION جعلی ═══════════════════════════════════
    def test_never_writes_money_attribution(self):
        """money-pulse فقط می‌خونه. نوشتنِ پول باید از مسیرِ claim→confirm بیاد."""
        os.environ[mp.FLAG] = "1"
        # ledger.append را spy کن — نباید با MONEY_ATTRIBUTION صدا زده بشه
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent /
                                   "07 - Knowledge" / "genome-system" / "ledger"))
            import ledger
        except ImportError:
            self.skipTest("ledger module در دسترس نیست")
            return
        with mock.patch.object(ledger.Ledger, "append") as mock_append:
            with self._with_revenue(100.0):
                mp.beat(center=_FakeCenter())
            # هیچ فراخوانی با event_type=MONEY_ATTRIBUTION نباید رخ داده باشه
            for call in mock_append.call_args_list:
                args = call[0]
                if args and args[0] == "MONEY_ATTRIBUTION":
                    self.fail("money-pulse نباید MONEY_ATTRIBUTION بنویسه "
                              "(wall anti-reward-hacking)")

    # ═══ ۴) فرصتِ بزرگ → notify ═══════════════════════════════════════════
    def test_hot_revenue_notifies(self):
        os.environ[mp.FLAG] = "1"
        fc = _FakeCenter()
        with self._with_revenue(mp.HOT_THRESHOLD_AUD + 10):  # هات
            out = mp.beat(center=fc)
        self.assertTrue(out.get("hot"), "درآمدِ ≥threshold باید hot باشه")
        self.assertTrue(out.get("notified"), "باید notify بشه")
        self.assertEqual(len(fc.alerts), 1)
        self.assertIn("money-pulse", fc.alerts[0])

    # ═══ ۵) درآمدِ کم → notify نمی‌شه ═════════════════════════════════════
    def test_cold_revenue_no_notify(self):
        os.environ[mp.FLAG] = "1"
        fc = _FakeCenter()
        with self._with_revenue(0.5):  # زیرِ threshold
            out = mp.beat(center=fc)
        self.assertFalse(out.get("hot"))
        self.assertFalse(out.get("notified"))

    # ═══ ۶) beat هرگز raise ═══════════════════════════════════════════════
    def test_beat_never_raises(self):
        os.environ[mp.FLAG] = "1"
        # attribution را خراب کن
        with mock.patch("attribution.confirmed_revenue",
                        side_effect=RuntimeError("boom")):
            out = mp.beat(center=_FakeCenter())  # نباید raise کنه
        # fail-soft: sense ممکنه partial باشه ولی نباید exception

    # ═══ ۷) status ساختار ════════════════════════════════════════════════
    def test_status_structure(self):
        os.environ[mp.FLAG] = "1"
        with self._with_revenue(1.5):
            s = mp.status()
        self.assertTrue(s["flag_on"])
        self.assertIn("confirmed_aud", s)
        self.assertIn("hot_threshold_aud", s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
