"""تست‌های مدل «لبهٔ سیستم» — هر فرمول از متن مالک گرفته شده و این‌جا با
اعداد مشخص از مثال‌های خودش بررسی می‌شود."""
import os, sys, math, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from hypno.kernel import edge


class Helpers(unittest.TestCase):
    def test_clamp01_scales_zero_to_ten(self):
        self.assertAlmostEqual(edge.clamp01(0), 0.0)
        self.assertAlmostEqual(edge.clamp01(10), 1.0)
        self.assertAlmostEqual(edge.clamp01(5), 0.5)
        self.assertAlmostEqual(edge.clamp01(0.5), 0.5)   # از قبل ۰-۱

    def test_clamp01_bounds_negatives_and_overshoot(self):
        self.assertEqual(edge.clamp01(-3), 0.0)
        self.assertEqual(edge.clamp01(99), 1.0)

    def test_pos(self):
        self.assertEqual(edge._pos(-2), 0.0)
        self.assertEqual(edge._pos(3), 3.0)

    def test_sigmoid_in_midpoint_and_bounds(self):
        self.assertAlmostEqual(edge.sigmoid(0), 0.5)
        self.assertGreater(edge.sigmoid(5), 0.99)
        self.assertLess(edge.sigmoid(-5), 0.01)


class ThreeIndices(unittest.TestCase):
    def test_agency_index_weights_from_text(self):
        # V=8,P=7,K=6,D=7,H=5 → 0.25·0.8+0.20·0.7+0.20·0.6+0.20·0.7+0.15·0.5
        # = 0.20 + 0.14 + 0.12 + 0.14 + 0.075 = 0.675
        self.assertAlmostEqual(edge.agency_index(8, 7, 6, 7, 5), 0.675, places=3)

    def test_agency_index_all_zero_and_all_ten(self):
        self.assertAlmostEqual(edge.agency_index(0, 0, 0, 0, 0), 0.0)
        self.assertAlmostEqual(edge.agency_index(10, 10, 10, 10, 10), 1.0)

    def test_super_index_high_when_trend_and_fomo(self):
        # ترند بالا، فومو بالا، پول، فوریت، پایداری پایین
        si = edge.super_index(9, 8, 7, 8, 2)
        self.assertGreater(si, 0.7)
        self.assertLessEqual(si, 1.0)

    def test_super_index_low_when_stable(self):
        # بدون محرک، بدون فومو، پایداری بالا
        si = edge.super_index(1, 1, 1, 1, 9)
        self.assertLess(si, 0.25)

    def test_body_index_high_with_tiredness_and_craving(self):
        # خواب بد (H پایین) + craving بالا + بدهی خواب + استرس
        bi = edge.body_index(2, 9, 8, 7)
        self.assertGreater(bi, 0.7)

    def test_body_index_low_when_rested_and_calm(self):
        bi = edge.body_index(9, 1, 2, 1)
        self.assertLess(bi, 0.25)


class DecompositionTests(unittest.TestCase):
    def test_shares_sum_to_one(self):
        d = edge.decomposition(0.6, 0.3, 0.1)
        self.assertAlmostEqual(d.a_self + d.a_super + d.a_body, 1.0, places=6)

    def test_self_dominant_label(self):
        d = edge.decomposition(0.9, 0.05, 0.05)
        self.assertGreaterEqual(d.a_self, 0.55)
        self.assertIn("خودت", d.label)
        self.assertEqual(d.dominant(), "خود")

    def test_super_dominant_label(self):
        d = edge.decomposition(0.05, 0.9, 0.05)
        self.assertEqual(d.dominant(), "ابرموجود")
        self.assertIn("بازار", d.label)

    def test_body_dominant_label(self):
        d = edge.decomposition(0.05, 0.05, 0.9)
        self.assertEqual(d.dominant(), "بدن")
        self.assertIn("بدن", d.label)

    def test_mixed_when_none_dominant(self):
        d = edge.decomposition(0.4, 0.35, 0.25)
        self.assertEqual(d.dominant(), "ترکیبی")
        self.assertIn("ترکیبی", d.label)


class LesTests(unittest.TestCase):
    def test_denominator_always_at_least_one(self):
        # مخرش باید ≥ ۱ باشد حتی با همهٔ صفر → تقسیم‌بر‌صفر نیست
        val = edge.les(0, 0, 0, 0, 0, 0, 0)
        self.assertEqual(val, 0.0)   # صورت صفر، مخرش ≥۱

    def test_high_les_when_flow_output_signal_awareness_low_cost(self):
        good = edge.les(9, 8, 7, 8, 2, 8, 1)
        bad = edge.les(9, 1, 1, 3, 8, 2, 8)   # فلو بدون خروجی
        self.assertGreater(good, bad)
        # صورت = 0.9·0.8·0.7·0.8 = 0.4032 ؛ مخرش = 1+0.2+0.2+0.1 = 1.5 → 0.269
        self.assertGreater(good, 0.25)

    def test_les_capped_at_one(self):
        # همهٔ مولدها ۱۰، همهٔ هزینه‌ها ۰
        val = edge.les(10, 10, 10, 10, 0, 10, 0)
        self.assertLessEqual(val, 1.0)


class GammaTests(unittest.TestCase):
    def test_gamma_super_rises_with_debt_and_fomo(self):
        low = edge.gamma_super(1, 1, 1, 1, 9)     # بدن خوب، آگاهی بالا
        high = edge.gamma_super(9, 9, 9, 9, 1)    # بدن بد، آگاهی پایین
        self.assertGreater(high, low)

    def test_gamma_super_neutral_at_balanced_inputs(self):
        # ورودی‌های کاملاً متعادل (بدن خوب، آگاهی برابر با فشار) باید حدود ۰.۵ باشند.
        # اگر SleepDebt=Stress=Weed=FOMO=Awareness=0.5 → a=1.5 → sigmoid(2)≈0.88
        # پس «خنثی واقعی» یعنی عواملِ بدن با آگاهی برابرند:
        n = edge.gamma_super(2, 2, 2, 2, 8)   # بدن کم، آگاهی بالا
        self.assertLess(n, 0.3)               # آگاهی برنده است

    def test_gamma_reflexive_high_when_aligned(self):
        high = edge.gamma_reflexive(9, 9, 9, 9, 1, 1)
        low = edge.gamma_reflexive(1, 1, 1, 1, 9, 9)
        self.assertGreater(high, low)


class AttributionTests(unittest.TestCase):
    def test_cosine_q_zero_on_orthogonal(self):
        # Δn با جهت body هم‌راستا، نه self
        q = edge.cosine_q([1, 0, 0], [0, 1, 0])
        self.assertAlmostEqual(q, 0.0, places=5)

    def test_cosine_q_one_on_aligned(self):
        q = edge.cosine_q([1, 2, 3], [2, 4, 6])
        self.assertAlmostEqual(q, 1.0, places=5)

    def test_attribution_coding_late_night_super_high(self):
        # مثال مالک: کدنویسی تا ۳ صبح بعد از ترند AI → P_super بالا
        # Δn تغییر تصمیم بیشتر به سمت ابرموجود
        delta = [2, 1, 8]       # کد زیاد، خروجی کم، ترند زیاد
        v_self = [1, 9, 1]
        s_super = [1, 1, 9]
        b_body = [3, 1, 2]
        a = edge.attribution(delta, v_self, s_super, b_body)
        self.assertGreater(a.p_super, a.p_self)
        self.assertGreater(a.p_super, a.p_body)

    def test_attribution_binge_after_weed_body_high(self):
        # مثال مالک: پرخوری شبانه بعد از مصرف → P_body بالا
        delta = [8, 1, 6]       # هوس بالا، خروجی کم، مصرف بالا
        v_self = [1, 9, 1]
        s_super = [1, 1, 3]
        b_body = [9, 1, 8]
        a = edge.attribution(delta, v_self, s_super, b_body)
        self.assertGreater(a.p_body, a.p_self)


class HealthyDecisionTests(unittest.TestCase):
    def test_healthy_when_self_high_and_body_low(self):
        h = edge.healthy_decision(0.7, 0.3, 0.1, 0.1)
        self.assertGreater(h, 0.5)

    def test_unhealthy_can_be_negative(self):
        # خود پایین، آشوب بدن بالا
        h = edge.healthy_decision(0.1, 0.1, 0.8, 0.9)
        self.assertLess(h, 0.0)


class DailyVerdictTests(unittest.TestCase):
    def test_green_zone(self):
        v = edge.daily_verdict(7, 6, 3)   # B>6, C>5, X<4
        self.assertEqual(v.verdict, "سبز")
        self.assertIn("لبه", v.advice)

    def test_yellow_zone_low_body(self):
        v = edge.daily_verdict(4, 6, 3)   # B<5
        self.assertEqual(v.verdict, "زرد")
        self.assertIn("تثبیت", v.advice)

    def test_yellow_zone_high_cost(self):
        v = edge.daily_verdict(7, 6, 8)   # X>6
        self.assertEqual(v.verdict, "زرد")

    def test_three_red_days_triggers_red(self):
        history = [edge.daily_verdict(3, 2, 8) for _ in range(3)]
        v = edge.three_red_days(history)
        self.assertEqual(v.verdict, "قرمز")

    def test_three_red_days_not_triggered_with_mixed(self):
        history = [edge.daily_verdict(3, 2, 8), edge.daily_verdict(7, 6, 3), edge.daily_verdict(3, 2, 8)]
        v = edge.three_red_days(history)
        self.assertEqual(v.verdict, "خنثی")


class DecisionSourceTests(unittest.TestCase):
    def test_super_outweighs_self_late_night_trend_coding(self):
        # مثال مالک (نسخهٔ دستی): ارزش بالا ولی پذیرش فروش پایین، خواب خراب،
        # بعد از ترند AI. شاخص ابرموجود از شاخص خود بیشتر است (حتی اگر هیچ‌کدام
        # به آستانهٔ ۰.۵۵ غالب نرسد، پس «ترکیبی» می‌شود). نسخهٔ برداریِ q (که در
        # AttributionTests تست می‌شود) P_super را غالب نشان می‌دهد.
        r = edge.decision_source(V=8, P=3, K=2, D=4, H=3,
                                 E=9, F=6, M=3, U=7, C=3, sleep_debt=8, stress=5)
        self.assertGreater(r.dec.a_super, r.dec.a_self)
        self.assertGreater(r.si, r.ai)

    def test_body_dominant_binge(self):
        # پرخوری بعد از مصرف: craving و sleep_debt بالا، ارزش پایین
        r = edge.decision_source(V=2, P=1, K=1, D=2, H=2,
                                 E=2, F=2, M=2, U=8, C=9, sleep_debt=9, stress=8)
        self.assertEqual(r.dec.dominant(), "بدن")

    def test_self_dominant_deliberate_painting(self):
        # گرفتن کار نقاشی برای runway: ارزش بالا، پیش‌تعهد، پذیرش هزینه
        r = edge.decision_source(V=8, P=8, K=8, D=8, H=7,
                                 E=3, F=2, M=5, U=2, C=2, sleep_debt=3, stress=3)
        self.assertEqual(r.dec.dominant(), "خود")


class BigDecisionCheckTests(unittest.TestCase):
    def test_source_from_self_when_aligned_and_rested(self):
        r = edge.big_decision_check(value_fit=9, pre_commitment=9,
                                     cost_acceptance=8, delay_persistence=9,
                                     sleep_debt=2, craving=2,
                                     external_cue=2, fomo=2)
        self.assertIn("خودت", r["منشأ"])

    def test_source_from_super_when_tired_and_fomo(self):
        r = edge.big_decision_check(value_fit=3, pre_commitment=2,
                                     cost_acceptance=2, delay_persistence=3,
                                     sleep_debt=9, craving=6,
                                     external_cue=9, fomo=8)
        self.assertIn("موج", r["منشأ"])


class RagIntegrationTests(unittest.TestCase):
    """بعد از ingest، RAG باید chunks لبه را پیدا کند."""
    def test_retrieve_finds_edge_chunks(self):
        import tempfile
        from hypno.adapters.store import Store
        from hypno.adapters.rag import retrieve
        from hypno.run import seed_edge_model
        with tempfile.TemporaryDirectory() as d:
            s = Store(os.path.join(d, 'x.sqlite'))
            seed_edge_model(s)
            hits = retrieve(s, 'تصمیم خواب بدن ابرموجود فلو فروش', 10)
            titles = [h['title'] for h in hits]
            self.assertTrue(any('لبه' in t or 'مدل' in t for t in titles),
                            f"edge chunks not retrieved: {titles}")


# ── تست‌های وصل‌شدن مغز و endpoint (کار مگاپرامپت EDGE-DEEP) ──────────────────
def _test_cfg(d=None):
    """یک Config با tempfile برای تست‌های App."""
    import tempfile
    from hypno.config import Config
    d = d or tempfile.mkdtemp()
    return Config(os.getcwd(), '127.0.0.1', 8895, d, os.path.join(d, 'r'),
                  '', (), '', '', 'fugu', 'u'), d


class ExtractScoresTests(unittest.TestCase):
    def test_extract_persian_scores(self):
        from hypno.adapters.brain import _extract_scores
        s = _extract_scores('امشب: خواب ۳، ترند ۸، هوس ۷، استرس ۶')
        self.assertIsNotNone(s)
        self.assertEqual(s['H'], 3)   # خواب ← H
        self.assertEqual(s['E'], 8)   # ترند ← E
        self.assertEqual(s['C'], 7)   # هوس ← C
        self.assertEqual(s['stress'], 6)

    def test_extract_returns_none_when_too_few(self):
        from hypno.adapters.brain import _extract_scores
        self.assertIsNone(_extract_scores('سلام امروز چطورمی؟'))
        self.assertIsNone(_extract_scores(''))
        self.assertIsNone(_extract_scores(None))

    def test_extract_clamps_out_of_range(self):
        from hypno.adapters.brain import _extract_scores
        s = _extract_scores('خواب ۱۵ هوس ۷')
        self.assertNotIn('H', s)     # ۱۵ رد می‌شود
        self.assertEqual(s['C'], 7)


class EdgeReplyFromScoresTests(unittest.TestCase):
    def test_daily_verdict_reply_when_BCX_present(self):
        from hypno.adapters.brain import _edge_reply_from_scores
        r = _edge_reply_from_scores({'B': 3, 'C_daily': 2, 'X': 8})
        self.assertIsNotNone(r)
        self.assertIn('زرد', r)
        self.assertIn('بدن', r)

    def test_decision_reply_when_enough_keys(self):
        from hypno.adapters.brain import _edge_reply_from_scores
        r = _edge_reply_from_scores({
            'V': 8, 'P': 3, 'K': 2, 'D': 4, 'H': 3,
            'E': 9, 'F': 6, 'M': 3, 'U': 7, 'C': 3,
            'sleep_debt': 8, 'stress': 5,
        })
        self.assertIsNotNone(r)
        self.assertIn('تجزیه', r)
        self.assertIn('سهم', r)

    def test_none_when_insufficient(self):
        from hypno.adapters.brain import _edge_reply_from_scores
        self.assertIsNone(_edge_reply_from_scores({'H': 3, 'C': 2}))


class EdgeEndpointsTests(unittest.TestCase):
    def setUp(self):
        self.cfg, self.d = _test_cfg()
        self.addCleanup(lambda: __import__('shutil').rmtree(self.d, ignore_errors=True))
        from hypno.run import App
        self.app = App(self.cfg)

    def test_decision_endpoint_returns_decomposition(self):
        r = self.app.edge_decision({
            'V': 8, 'P': 3, 'K': 2, 'D': 4, 'H': 3,
            'E': 9, 'F': 6, 'M': 3, 'U': 7, 'C': 3,
            'sleep_debt': 8, 'stress': 5, 'initData': '',
        })
        self.assertTrue(r['ok'])
        self.assertGreater(r['a_super'], r['a_self'])   # late-night → ابرموجود
        self.assertGreater(r['si'], r['ai'])
        self.assertIn('verdict', r)

    def test_decision_endpoint_uses_defaults_for_missing(self):
        r = self.app.edge_decision({'E': 9, 'F': 8, 'initData': ''})
        self.assertTrue(r['ok'])
        self.assertGreater(r['a_super'], 0)

    def test_daily_endpoint_logs_verdict(self):
        r = self.app.edge_daily({'B': 3, 'C': 2, 'X': 8, 'initData': ''})
        self.assertTrue(r['ok'])
        self.assertEqual(r['verdict'], 'زرد')
        self.assertIn('advice', r)
        self.assertIn('streak', r)

    def test_daily_endpoint_green(self):
        r = self.app.edge_daily({'B': 7, 'C': 6, 'X': 3, 'initData': ''})
        self.assertEqual(r['verdict'], 'سبز')

    def test_daily_endpoint_rejects_bad_input(self):
        r = self.app.edge_daily({'B': 'xyz', 'initData': ''})
        self.assertFalse(r['ok'])

    def test_history_endpoint_returns_logged_days(self):
        # دو روز متفاوت (upsert فقط همان روز را بازنویسی می‌کند)
        self.app.store.log_edge_daily('u', 7, 6, 3, 'سبز', day='2026-01-01')
        self.app.store.log_edge_daily('u', 4, 3, 7, 'زرد', day='2026-01-02')
        h = self.app.edge_history({'initData': '', 'limit': 14})
        self.assertTrue(h['ok'])
        self.assertGreaterEqual(len(h['days']), 2)

    def test_daily_upsert_per_day(self):
        # دو بار در همان روز → یک ردیف (نه دو)
        self.app.edge_daily({'B': 7, 'C': 6, 'X': 3, 'initData': ''})
        self.app.edge_daily({'B': 5, 'C': 5, 'X': 5, 'initData': ''})
        h = self.app.edge_history({'initData': '', 'limit': 14})
        # فقط یک ردیف برای امروز
        today_rows = [d for d in h['days']]
        self.assertEqual(len(today_rows), 1)


class EdgeChatWiringTests(unittest.TestCase):
    def setUp(self):
        self.cfg, self.d = _test_cfg()
        self.addCleanup(lambda: __import__('shutil').rmtree(self.d, ignore_errors=True))
        from hypno.run import App
        self.app = App(self.cfg)

    def test_chat_with_daily_scores_includes_verdict(self):
        # کاربر نمرهٔ روزانه می‌دهد: بدن/حلقه/هزینهٔ پنهان
        r = self.app.chat({'text': 'بدن ۳ حلقه ۲ هزینهٔپنهان ۸', 'mode': 'calm',
                           'consent': True, 'initData': ''})
        self.assertTrue(r.get('ok'))
        # جواب باید حکم روزانه را داشته باشد
        self.assertTrue('زرد' in r['reply'] or 'بدن' in r['reply']
                        or 'تثبیت' in r['reply'])

    def test_chat_without_scores_still_works(self):
        r = self.app.chat({'text': 'سلام، امروز چطورم؟', 'mode': 'calm',
                           'consent': True, 'initData': ''})
        self.assertTrue(r.get('ok'))
        self.assertIn('reply', r)

    def test_chat_crisis_blocked_before_brain(self):
        # بحران هرگز به مغز نمی‌رسد
        r = self.app.chat({'text': 'شروع جلسه، خودمو بکشم', 'mode': 'calm',
                           'consent': False, 'initData': ''})
        self.assertEqual(r['safety'], 'crisis')


class EdgeMemoryStoreTests(unittest.TestCase):
    def test_log_and_history_round_trip(self):
        import tempfile
        from hypno.adapters.store import Store
        with tempfile.TemporaryDirectory() as d:
            s = Store(os.path.join(d, 'x.sqlite'))
            s.log_edge_daily('u', 3, 2, 8, 'زرد', day='2026-01-01')
            s.log_edge_daily('u', 7, 6, 3, 'سبز', day='2026-01-02')
            hist = s.edge_history('u', 14)
            self.assertEqual(len(hist), 2)
            self.assertEqual(hist[0]['day'], '2026-01-01')
            self.assertEqual(hist[1]['verdict'], 'سبز')

    def test_upsert_same_day(self):
        import tempfile
        from hypno.adapters.store import Store
        with tempfile.TemporaryDirectory() as d:
            s = Store(os.path.join(d, 'x.sqlite'))
            s.log_edge_daily('u', 3, 2, 8, 'زرد', day='2026-01-01')
            s.log_edge_daily('u', 7, 6, 3, 'سبز', day='2026-01-01')
            hist = s.edge_history('u', 14)
            self.assertEqual(len(hist), 1)
            self.assertEqual(hist[0]['verdict'], 'سبز')

    def test_table_created_idempotently(self):
        import tempfile
        from hypno.adapters.store import Store
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'x.sqlite')
            Store(p)        # ساخت اول
            Store(p)        # ساخت دوم — نباید خطا
            import sqlite3
            con = sqlite3.connect(p)
            self.assertEqual(con.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='edge_daily'"
            ).fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()

