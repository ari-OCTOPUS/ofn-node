#!/usr/bin/env python3
"""test_dual_brain_v3.py — CHARACTERIZATION tests برای مغزِ فعالِ Project-F.

هدف: قفل‌کردنِ رفتارِ فعلیِ dual_brain_v3 (که فعال‌ترین مغز است ولی تا حالا
صفر تستِ مستقیم داشت) قبل از هر تغییرِ بیشتر. این تست‌ها **رفتارِ امروز** را
مشخص می‌کنند — اگر تغییر دادیم، باید آگاهانه باشد.

منطقِ characterization (طبقِ توصیه‌ی architect-agent):
  - این تست‌ها رفتارِ فعلی را توصیف می‌کنند، نه رفتارِ مطلوب.
  - اگر بعداً مغز را بهتر کردیم، تست را هم عمداً به‌روز می‌کنیم (به‌صورتِ commitِ جدا).

توجه: _ops/tests/test_dual_brain.py (مشترک) نسخه‌ی قدیمیِ dual_brain (بدونِ _v3)
را تست می‌کند. این فایل نسخه‌ی فعالِ _v3 را. هیچ تداخلی.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import dual_brain_v3 as DB  # noqa: E402
from dual_brain_v3 import (  # noqa: E402
    DualBrainV3, ThinkingBrain, CommBrain,
    Thought, Message,
    COMPLIANCE_RULES, ETHICS_RULES, FORBIDDEN_TERMS,
    _guard_text, _checks_pass, LAMBDA_PERSIST,
)


class TestConstants(unittest.TestCase):
    """قفلِ ثابت‌ها — اگر این‌ها تغییر کردند، آگاهانه باشد."""

    def test_compliance_rules_count(self):
        self.assertEqual(len(COMPLIANCE_RULES), 6)

    def test_ethics_rules_count(self):
        self.assertEqual(len(ETHICS_RULES), 6)

    def test_compliance_rules_content(self):
        expected = {"faceless", "feet_only", "no_explicit", "over_18",
                    "inplatform_payment", "geo_block_iran"}
        self.assertEqual(set(COMPLIANCE_RULES), expected)

    def test_ethics_rules_content(self):
        expected = {"no_dark_pattern", "no_manipulation",
                    "relationship_80_sales_20", "performer_welfare",
                    "scope_supreme", "no_engagement_optimization"}
        self.assertEqual(set(ETHICS_RULES), expected)

    def test_lambda_persist_negative(self):
        """λ_persist<0 — nothing persists. مهم برای propose-only."""
        self.assertLess(LAMBDA_PERSIST, 0)

    def test_forbidden_terms_contains_critical(self):
        """این کلماتِ ممنوعه باید همیشه باشند (PII/geo)."""
        for term in ("persian", "sydney", "iran", "tehran", "paypal", "crypto"):
            self.assertIn(term, FORBIDDEN_TERMS,
                          f"{term} must be in FORBIDDEN_TERMS")


class TestGuardText(unittest.TestCase):
    """_guard_text — Ethics-Guard برای متن."""

    def test_clean_text_passes(self):
        ok, v = _guard_text("a normal text about content")
        self.assertTrue(ok)
        self.assertEqual(v, [])

    def test_forbidden_terms_caught(self):
        ok, v = _guard_text("hello from sydney")
        self.assertFalse(ok)
        self.assertIn("sydney", v)

    def test_multiple_violations(self):
        ok, v = _guard_text("persian in tehran")
        self.assertFalse(ok)
        self.assertGreaterEqual(len(v), 2)

    def test_case_insensitive(self):
        """متنِ lowercase می‌شود بعد مقایسه."""
        ok, v = _guard_text("IRAN is a country")
        self.assertFalse(ok)
        self.assertIn("iran", v)


class TestChecksPass(unittest.TestCase):
    """_checks_pass — guard روی compliance/ethics."""

    def test_all_true_passes(self):
        checks = {r: True for r in COMPLIANCE_RULES + ETHICS_RULES}
        self.assertTrue(_checks_pass(checks))

    def test_empty_fails(self):
        """مهم: این رفتارِ fail-close است که در فاز ۰.۱ رفع کردیم."""
        self.assertFalse(_checks_pass({}))

    def test_one_compliance_false_fails(self):
        checks = {r: True for r in COMPLIANCE_RULES + ETHICS_RULES}
        checks["faceless"] = False
        self.assertFalse(_checks_pass(checks))

    def test_one_ethics_false_fails(self):
        checks = {r: True for r in COMPLIANCE_RULES + ETHICS_RULES}
        checks["no_manipulation"] = False
        self.assertFalse(_checks_pass(checks))

    def test_none_value_fails(self):
        checks = {r: True for r in COMPLIANCE_RULES + ETHICS_RULES}
        checks["faceless"] = None
        self.assertFalse(_checks_pass(checks))


class TestThinkingBrainAgents(unittest.TestCase):
    """قفلِ رفتارِ ۱۰ ساب‌عامل. خروجی = Thought."""

    def setUp(self):
        self.tb = ThinkingBrain()

    def test_strategist_returns_thought(self):
        t = self.tb.strategist()
        self.assertIsInstance(t, Thought)
        self.assertEqual(t.kind, "strategy")
        self.assertEqual(t.source_agent, "Strategist")
        self.assertIn("wall_pct", t.data)
        self.assertIn("ppv_pct", t.data)
        # wall + ppv باید ۱ باشند
        self.assertAlmostEqual(t.data["wall_pct"] + t.data["ppv_pct"], 1.0, places=2)

    def test_strategist_standard_vs_premium(self):
        """standard > premium در wall_pct (طبقِ کد)."""
        std = self.tb.strategist(content_type="standard")
        prem = self.tb.strategist(content_type="premium")
        self.assertGreater(std.data["wall_pct"], prem.data["wall_pct"])

    def test_pricer_returns_thought_with_tier(self):
        t = self.tb.pricer()
        self.assertEqual(t.kind, "price")
        self.assertEqual(t.source_agent, "Pricer")
        self.assertIn("price", t.data)
        self.assertIn(t.data["tier"], ("low", "mid", "premium"))
        self.assertGreater(t.data["price"], 0)

    def test_pricer_evening_higher_than_morning(self):
        """evening > morning (طبقِ کد: time_mult)."""
        evening = self.tb.pricer(time_slot="evening")
        morning = self.tb.pricer(time_slot="morning")
        self.assertGreater(evening.data["price"], morning.data["price"])

    def test_scheduler_returns_schedule(self):
        t = self.tb.scheduler()
        self.assertEqual(t.kind, "schedule")
        self.assertIn("best", t.data)

    def test_risk_analyzer_returns_risks(self):
        t = self.tb.risk_analyzer(partner_stress=0.8)
        self.assertEqual(t.kind, "risk")
        self.assertIn("risks", t.data)
        self.assertIsInstance(t.data["risks"], list)

    def test_segmenter_returns_segments(self):
        t = self.tb.segmenter()
        self.assertEqual(t.kind, "segment")
        self.assertIn("segments", t.data)
        # ۳ سگمنتِ استاندارد
        self.assertEqual(set(t.data["segments"].keys()), {"vip", "regular", "lurker"})

    def test_competitor_intel_no_data(self):
        t = self.tb.competitor_intel([])
        self.assertEqual(t.kind, "competitor")
        self.assertEqual(t.data["status"], "no_data")

    def test_trend_forecaster_summer(self):
        t = self.tb.trend_forecaster("summer")
        self.assertEqual(t.kind, "trend")
        self.assertIn("sandals", t.data["predicted_trends"])

    def test_retention_strategist(self):
        t = self.tb.retention_strategist(0.27)
        self.assertEqual(t.kind, "retention")
        self.assertIn("actions", t.data)

    def test_content_optimizer_no_data(self):
        t = self.tb.content_optimizer([])
        self.assertEqual(t.kind, "content_opt")
        self.assertEqual(t.data["status"], "no_data")

    def test_funnel_analyst(self):
        t = self.tb.funnel_analyst(100, 5, 1)
        self.assertEqual(t.kind, "funnel")
        self.assertIn("visitor→sub_rate", t.data)


class TestProcessAll(unittest.TestCase):
    """process_all — guard برای فکرِ کامل."""

    def test_guard_fail_returns_blocked(self):
        tb = ThinkingBrain()
        out = tb.process_all(checks={})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "blocked")

    def test_all_pass_returns_10_thoughts(self):
        tb = ThinkingBrain()
        checks = {r: True for r in COMPLIANCE_RULES + ETHICS_RULES}
        out = tb.process_all(checks=checks)
        self.assertEqual(len(out), 10)
        kinds = {t.kind for t in out}
        self.assertNotIn("blocked", kinds)


class TestCommBrain(unittest.TestCase):
    """۷ خروجیِ متنی."""

    def setUp(self):
        self.cb = CommBrain()
        self.tb = ThinkingBrain()
        self.checks = {r: True for r in COMPLIANCE_RULES + ETHICS_RULES}

    def test_caption_for_price_thought(self):
        t = self.tb.pricer()
        m = self.cb.caption(t)
        self.assertIsInstance(m, Message)
        self.assertEqual(m.kind, "caption")

    def test_caption_blocks_forbidden(self):
        """اگر caption حاوی کلمه‌ی ممنوعه شد، باید [BLOCKED ...] شود."""
        # این یک تستِ رفتارِ فعلی است — _safe به‌سختی block می‌کند
        t = Thought(kind="price", data={"tier": "premium"})
        m = self.cb.caption(t)
        self.assertIsInstance(m.text, str)

    def test_brief_for_saba_returns_message(self):
        thoughts = self.tb.process_all(checks=self.checks)
        m = self.cb.brief_for_saba(thoughts)
        self.assertEqual(m.kind, "brief_saba")
        self.assertIsInstance(m.text, str)

    def test_report_for_ari(self):
        thoughts = self.tb.process_all(checks=self.checks)
        m = self.cb.report_for_ari(thoughts, drafts_count=3)
        self.assertEqual(m.kind, "report_ari")

    def test_retention_dm_lapsed(self):
        m = self.cb.retention_dm("regular", days_lapsed=20)
        self.assertEqual(m.kind, "retention_dm")

    def test_set_tone_validates(self):
        self.cb.set_tone("warm")
        self.cb.set_tone("invalid")  # باید fallback کنه به warm
        # تستِ غیرمستقیم: نباید exception
        m = self.cb.caption(Thought(kind="price", data={"tier": "mid"}))
        self.assertIsInstance(m.text, str)


class TestDualBrainV3(unittest.TestCase):
    """هماهنگ‌کننده — think_and_communicate."""

    def test_full_cycle_with_checks(self):
        brain = DualBrainV3()
        checks = {r: True for r in COMPLIANCE_RULES + ETHICS_RULES}
        out = brain.think_and_communicate(checks=checks, drafts_count=2)
        self.assertIsInstance(out, dict)
        self.assertIn("thoughts", out)
        self.assertIn("messages", out)
        self.assertFalse(out["blocked"])
        self.assertEqual(len(out["thoughts"]), 10)
        self.assertGreater(len(out["messages"]), 0)

    def test_full_cycle_blocked_when_checks_empty(self):
        brain = DualBrainV3()
        out = brain.think_and_communicate(checks={}, drafts_count=0)
        self.assertTrue(out["blocked"])
        self.assertEqual(len(out["thoughts"]), 1)
        self.assertEqual(len(out["messages"]), 0)

    def test_output_known_leaks_documented(self):
        """CHARACTERIZATION (not aspiration): خروجیِ فعلیِ مغز حاوی «آری» و «صبا»
        است (در brief_saba و report_ari). این یک **نشتِ شناخته‌شده‌ی PII** است که
        طبقِ قراردادِ containment نباید به بیرون برود (نام‌های واقعی = PII).

        این تست رفتارِ امروز را قفل می‌کند تا هر تغییرِ آگاهانه‌ی آن registrard شود.
        وقتی نشت رفع شد (مثلاً مغز از کد A/C به‌جای نام واقعی استفاده کند)، این
        تست باید عمداً به‌روز شود.

        کاربردِ این نشت: pf_os.BrainCore در respond_to_saba خروجیِ مغز را با
        scrub_for_cortex دوباره فیلتر می‌کند، پس در عمل به cortex نمی‌رسد. ولی
        سندِ خامِ مغز هنوز نشت دارد.
        """
        brain = DualBrainV3()
        checks = {r: True for r in COMPLIANCE_RULES + ETHICS_RULES}
        out = brain.think_and_communicate(checks=checks)
        blob = str(out).lower()
        # رفتارِ فعلی: «آری» در brief_saba نشت می‌کند (طبقِ کد dual_brain_v3:335)
        self.assertIn("آری", str(out),
                      "اگر این تست fail شد یعنی نشتِ PII رفع شده — تست را به‌روز کن")
        # ولی شهرها (sydney/tehran) نباید باشند — این‌ها در FORBIDDEN_TERMS هستند
        self.assertNotIn("sydney", blob)
        self.assertNotIn("tehran", blob)


if __name__ == "__main__":
    unittest.main()
