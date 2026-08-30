#!/usr/bin/env python3
"""test_learning.py — تست‌های لایهٔ یادگیریِ قوی ($0، آفلاین، deterministic)."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

import learning as L


class T(unittest.TestCase):
    def _bandit(self, seed=1):
        p = Path(tempfile.mkdtemp()) / "b.json"
        return L.ThompsonBandit(data_path=p, seed=seed)

    # ۱) پاداشِ نرمال اشباع نمی‌شود (برخلافِ min(1,...) قدیمی)
    def test_reward_no_saturation(self):
        weak = L.normalize_reward(upvotes=10)
        strong = L.normalize_reward(upvotes=90, comments=15, unlocks=4)
        vstrong = L.normalize_reward(upvotes=300, comments=60, unlocks=20)
        self.assertLess(weak, strong)
        self.assertLess(strong, vstrong)      # هنوز تفکیک دارد
        self.assertLessEqual(vstrong, 1.0)

    # ۲) یاد می‌گیرد بهترین arm را (exploitation)
    def test_learns_best_arm(self):
        b = self._bandit()
        for _ in range(40):
            b.observe("nylon", 0.9); b.observe("oil", 0.1)
        # با داده کافی، nylon باید اکثراً انتخاب شود
        picks = [b.select(["nylon", "oil"]) for _ in range(50)]
        self.assertGreater(picks.count("nylon"), 40)
        self.assertGreater(b.mean("nylon"), b.mean("oil"))

    # ۳) armِ کم‌داده explore می‌شود (min-pull guard)
    def test_explores_undersampled(self):
        b = self._bandit()
        for _ in range(30):
            b.observe("known", 0.8)
        # "new" هیچ داده‌ای ندارد → باید در رتبه‌بندی گاهی بالا بیاید
        picks = [b.select(["known", "new"]) for _ in range(40)]
        self.assertIn("new", picks, "armِ نادیده هرگز explore نشد (greedy bug)")

    # ۴) نرخِ اکتشاف در فلور/سقف می‌ماند (governance)
    def test_explore_rate_bounds(self):
        b = self._bandit()
        r0 = b.explore_rate(["a", "b", "c"])           # بدون داده → بالا
        self.assertLessEqual(r0, L.EXPLORE_CAP)
        self.assertGreaterEqual(r0, L.EXPLORE_FLOOR)
        for _ in range(200):
            b.observe("a", 0.5)
        r1 = b.explore_rate(["a", "b", "c"])           # داده زیاد → پایین‌تر
        self.assertGreaterEqual(r1, L.EXPLORE_FLOOR)   # ولی هرگز زیرِ فلور
        self.assertLess(r1, r0)

    # ۵) approval-gated: داده‌ی تأییدنشده وارد یادگیری نمی‌شود
    def test_approval_gated(self):
        b = self._bandit()
        for _ in range(20):
            b.observe("x", 0.9, approved=False)    # همه رد
        post = b.posterior()
        self.assertNotIn("x", post, "دادهٔ تأییدنشده نباید یاد گرفته شود")

    # ۶) recency: مشاهده‌ی جدید بر قدیمی می‌چربد (non-stationarity)
    def test_recency_adaptation(self):
        b = L.ThompsonBandit(halflife_days=7, data_path=Path(tempfile.mkdtemp())/"b.json", seed=3)
        import time
        now = time.time()
        old = now - 60 * 86400        # ۶۰ روز پیش
        for _ in range(30):
            b.observe("t", 0.9, ts=old)     # قدیمی: عالی بود
        for _ in range(30):
            b.observe("t", 0.1, ts=now)     # حالا: بد شده
        # میانگینِ recency-weighted باید به «بد» نزدیک باشد، نه «خوب»
        self.assertLess(b.mean("t", now=now), 0.5, "recency ترندِ جدید را نگرفت")

    # ۷) شفافیت (responsible-AI): explain همه‌چیز را می‌دهد
    def test_explain_transparency(self):
        b = self._bandit()
        b.observe("a", 0.7)
        e = b.explain(["a", "b"])
        self.assertTrue(e["propose_only"])
        self.assertIn("mean", e["arms"]["a"])
        self.assertIn("uncertainty", e["arms"]["a"])

    # ۸) EVAL: روی میانگینِ چند seed، Thompson از Greedy بهتر است (regret کمتر)
    #    (مقایسهٔ درست: greedy واریانس/lock-in دارد؛ یک seedِ خوش‌شانس معیار نیست)
    def test_beats_greedy_stationary_avg(self):
        r = L.regret_eval_avg({"a": 0.6, "b": 0.3, "c": 0.4, "d": 0.35, "e": 0.5},
                              steps=300, seeds=40)
        self.assertTrue(r["thompson_better_on_mean"], f"Thompson باید روی میانگین ببرد: {r}")
        # و worst-case اش هم از greedy مهارشده‌تر است
        self.assertLessEqual(r["thompson_worst"], r["greedy_worst"] + 1e-6)

    # ۹) EVAL: در محیطِ غیرایستا (شیفتِ ترند) هم روی میانگین بهتر است
    def test_beats_greedy_nonstationary_avg(self):
        r = L.regret_eval_avg({"a": 0.5, "b": 0.2, "c": 0.3, "d": 0.25, "e": 0.35},
                              steps=300, seeds=40, shift_at=150,
                              shifted_means={"a": 0.2, "b": 0.2, "c": 0.6, "d": 0.25, "e": 0.3})
        self.assertTrue(r["thompson_better_on_mean"], f"Thompson باید در شیفت هم ببرد: {r}")

    # ۱۰) UCB1 هم armِ نادیده را اول explore می‌کند
    def test_ucb_explores_first(self):
        u = L.UCB1()
        u.observe("a", 0.9); u.observe("a", 0.9)
        self.assertEqual(u.select(["a", "b"]), "b")   # b نادیده → inf score

    # ۱۱) persistence: state روی دیسک می‌ماند
    def test_persistence(self):
        p = Path(tempfile.mkdtemp()) / "b.json"
        b1 = L.ThompsonBandit(data_path=p, seed=1)
        for _ in range(10):
            b1.observe("z", 0.7)
        b2 = L.ThompsonBandit(data_path=p, seed=1)
        self.assertGreater(b2.mean("z"), 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
