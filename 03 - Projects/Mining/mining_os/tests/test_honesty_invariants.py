"""نامتغیرهای صداقتِ زیر-OSِ Mining (۲۰۲۶-۰۸-۰۱).

چهار چیزی که تا امروز می‌شکستند و هیچ تستی نمی‌دیدشان:

  ۱. «unknown» جزوِ وضعیتِ معلوم حساب می‌شد → رجیستریِ پر از نودِ اندازه‌گیری‌نشده
     سیستم را `live=True` می‌کرد بدونِ یک اندازه‌گیریِ واقعی.
  ۲. اسکلت سه کلید از شش کلیدِ ناوگان را نمی‌داد → UI کلیدِ غایب را ۰ چاپ می‌کرد،
     یعنی «اندازه گرفتیم، صفر بود».
  ۳. اسکلت گیتِ HALT می‌داد ولی `halt_proposal=False` → کارت «برق OK» می‌نوشت.
  ۴. `tick(write=False)` باز هم می‌نوشت → تست‌ها داخلِ ولتِ زنده می‌نوشتند.

هیچ‌کدام به دیسکِ زنده دست نمی‌زند: مسیرِ snapshot به tmp منتقل می‌شود.
"""
import json
import tempfile
import unittest
from pathlib import Path

from mining_os import loop
from mining_os.brains.hardware_brain import summarize_fleet
from mining_os.core import mining_beat


def _fleet(nodes, **kw):
    d = {"nodes": nodes}
    d.update(kw)
    return d


class TestUnknownIsNotKnown(unittest.TestCase):
    """۱ — «نامعلوم» هرگز نباید سیستم را زنده اعلام کند."""

    def test_all_unknown_nodes_are_not_a_known_status(self):
        f = summarize_fleet(_fleet([{"id": f"OPI-{i}", "status": "unknown"} for i in range(160)]))
        self.assertEqual(f["nodes_total"], 160)
        self.assertEqual(f["unknown"], 160)
        self.assertFalse(f["status_known"], "«unknown» نباید وضعیتِ معلوم حساب شود")

    def test_full_unknown_registry_plus_solar_stays_not_live(self):
        # دقیقاً سناریوی خطرناک: رجیستری پر، برق تأییدشده، صفر اندازه‌گیری.
        state = {"fleet": _fleet(
            [{"id": f"OPI-{i}", "status": "unknown"} for i in range(162)], solar=True)}
        snap = mining_beat(state)
        self.assertFalse(snap["live"], "بدونِ یک اندازه‌گیریِ واقعی live نباید True شود")
        self.assertEqual(snap["signal"], "skeleton")

    def test_one_real_measurement_flips_status_known(self):
        # پایه باید زیرِ سطحِ هدف باشد وگرنه تست بی‌معناست: یک نودِ واقعی کافی است.
        nodes = [{"id": f"OPI-{i}", "status": "unknown"} for i in range(9)]
        nodes.append({"id": "OPI-10", "status": "running"})
        f = summarize_fleet(_fleet(nodes))
        self.assertTrue(f["status_known"])
        self.assertEqual(f["running"], 1)
        self.assertEqual(f["unknown"], 9)

    def test_broken_also_counts_as_measured(self):
        f = summarize_fleet(_fleet([{"id": "OPI-1", "status": "broken"}]))
        self.assertTrue(f["status_known"])
        self.assertEqual(f["broken"], 1)


class TestSkeletonTellsTheTruth(unittest.TestCase):
    """۲+۳ — اسکلت نه کلید گم می‌کند نه برعکس گزارش می‌دهد."""

    def _skel(self):
        return mining_beat(None)          # هیچ stateی → مسیرِ اسکلت

    def test_skeleton_exposes_same_six_fleet_keys_as_live(self):
        skel_keys = set(self._skel()["fleet"])
        live_keys = set(summarize_fleet(_fleet([{"id": "OPI-1", "status": "running"}])))
        self.assertEqual(skel_keys, live_keys,
                         "کلیدهای اسکلت باید دقیقاً همان کلیدهای مسیرِ زنده باشند")

    def test_skeleton_halt_gate_implies_halt_proposal(self):
        s = self._skel()
        self.assertEqual(s["electricity"]["gate"], "HALT")
        self.assertTrue(s["halt_proposal"],
                        "گیتِ HALT با halt_proposal=False یعنی کارت «برق OK» می‌نویسد")

    def test_skeleton_is_never_live(self):
        s = self._skel()
        self.assertFalse(s["live"])
        self.assertFalse(s["wallet_access"])      # D-11


class TestWriteFalseWritesNothing(unittest.TestCase):
    """۴ — قولِ write=False باید واقعی باشد (شاهدِ تاریخی: beat=7 روی دیسکِ زنده)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._real = loop._SNAPSHOT
        loop._SNAPSHOT = Path(self._tmp.name) / "last-beat.json"

    def tearDown(self):
        loop._SNAPSHOT = self._real            # هرگز مسیرِ زنده را جا نگذار
        self._tmp.cleanup()

    def test_write_false_creates_no_file(self):
        snap = loop.tick(7, write=False)
        self.assertEqual(snap["beat"], 7)
        self.assertFalse(loop._SNAPSHOT.exists(),
                         "write=False نباید هیچ فایلی بسازد")

    def test_write_true_still_writes(self):
        # پایهٔ مثبت: اگر این سبز نشود، تستِ بالا به‌دلیلِ اشتباه سبز است.
        loop.tick(8, write=True)
        self.assertTrue(loop._SNAPSHOT.exists())
        self.assertEqual(json.loads(loop._SNAPSHOT.read_text("utf-8"))["beat"], 8)

    def test_default_still_writes(self):
        loop.tick(9)
        self.assertTrue(loop._SNAPSHOT.exists(), "پیش‌فرض نباید عوض شده باشد")


if __name__ == "__main__":
    unittest.main()
