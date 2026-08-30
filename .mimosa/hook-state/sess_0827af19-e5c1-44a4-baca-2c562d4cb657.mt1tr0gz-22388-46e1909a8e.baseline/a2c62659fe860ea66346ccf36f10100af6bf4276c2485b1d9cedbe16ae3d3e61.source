"""تستِ بخش‌های خالصِ llm/shadow_compare (B11 فاز ۱).

فقط build_record / summarize (و ثابتِ DEFAULT_PROMPTS) import می‌شود؛
هیچ شبکه‌ای، هیچ langchain ای — importِ ماژول باید stdlib-only باشد و
یک تست همین را با مسدودکردنِ langchain اثبات می‌کند.
"""
from tests import _bootstrap  # noqa: F401

import importlib
import sys
import time
import unittest

from llm.shadow_compare import DEFAULT_PROMPTS, build_record, summarize


# ── پشته‌های ساختگی (بدونِ شبکه) ─────────────────────────────────────────────
def _fast(p: str) -> str:
    return "The quick brown fox " + p


def _slow(p: str) -> str:
    time.sleep(0.02)
    return "The quick brown cat " + p


def _boom(p: str) -> str:
    raise ValueError("nope")


def _long(p: str) -> str:
    return "x" * 800


class TestBuildRecord(unittest.TestCase):
    def test_fields_latency_and_metrics(self):
        rec = build_record("jumps", _fast, _slow)

        self.assertEqual(rec["prompt"], "jumps")
        self.assertIsNone(rec["a"]["error"])
        self.assertIsNone(rec["b"]["error"])
        self.assertEqual(rec["a"]["output"], "The quick brown fox jumps")
        self.assertEqual(rec["b"]["output"], "The quick brown cat jumps")
        self.assertEqual(rec["a"]["length"], len("The quick brown fox jumps"))

        # پشتهٔ کند (sleep 0.02) باید تأخیرِ بیشتری ثبت کند
        self.assertGreaterEqual(rec["b"]["latency_s"], 0.015)
        self.assertGreater(rec["b"]["latency_s"], rec["a"]["latency_s"])

        # سنجه‌های واگرایی
        self.assertEqual(rec["metrics"]["length_ratio"], 1.0)  # طول‌ها برابرند
        sim = rec["metrics"]["similarity"]
        self.assertGreaterEqual(sim, 0.0)
        self.assertLessEqual(sim, 1.0)
        self.assertGreater(sim, 0.5)  # پیشوندِ مشترکِ بلند

    def test_error_captured_and_truncation(self):
        rec = build_record("p", _long, _boom)

        # سمتِ خطا: نامِ نوعِ exception، خروجی None
        self.assertEqual(rec["b"]["error"], "ValueError")
        self.assertIsNone(rec["b"]["output"])
        self.assertIsNone(rec["b"]["length"])

        # سمتِ سالم: ذخیره ≤۵۰۰ کاراکتر ولی طولِ کامل ثبت می‌شود
        self.assertEqual(len(rec["a"]["output"]), 500)
        self.assertEqual(rec["a"]["length"], 800)

        # تأخیر برای هر دو سمت (حتی سمتِ خطا) ثبت شده
        self.assertIsInstance(rec["a"]["latency_s"], float)
        self.assertIsInstance(rec["b"]["latency_s"], float)
        self.assertGreaterEqual(rec["b"]["latency_s"], 0.0)

        # بدونِ هر دو خروجی، سنجه‌ها None
        self.assertIsNone(rec["metrics"]["similarity"])
        self.assertIsNone(rec["metrics"]["length_ratio"])

    def test_never_raises_even_with_non_callable(self):
        rec = build_record("p", None, _fast)  # فراخوانیِ None → TypeError داخلی
        self.assertEqual(rec["a"]["error"], "TypeError")
        self.assertIsNone(rec["a"]["output"])
        self.assertIsNone(rec["b"]["error"])

    def test_similarity_bounds(self):
        identical = build_record("p", _fast, _fast)
        self.assertEqual(identical["metrics"]["similarity"], 1.0)
        self.assertEqual(identical["metrics"]["length_ratio"], 1.0)

        disjoint = build_record("p", lambda p: "aaaaaaaa", lambda p: "zzzzzzzz")
        sim = disjoint["metrics"]["similarity"]
        self.assertGreaterEqual(sim, 0.0)
        self.assertLess(sim, 0.5)


class TestSummarize(unittest.TestCase):
    def test_aggregates(self):
        recs = [build_record("p1", _fast, _fast),
                build_record("p2", _fast, _boom)]
        s = summarize(recs)

        self.assertEqual(s["count"], 2)
        self.assertEqual(s["error_rate_a"], 0.0)
        self.assertEqual(s["error_rate_b"], 0.5)
        self.assertIsInstance(s["mean_latency_a_s"], float)
        self.assertIsInstance(s["mean_latency_b_s"], float)
        self.assertGreaterEqual(s["mean_latency_a_s"], 0.0)
        # فقط رکوردِ اول شباهت دارد (یکسان → 1.0)؛ میانگین همان 1.0
        self.assertEqual(s["mean_similarity"], 1.0)

    def test_empty(self):
        s = summarize([])
        self.assertEqual(s["count"], 0)
        self.assertIsNone(s["error_rate_a"])
        self.assertIsNone(s["error_rate_b"])
        self.assertIsNone(s["mean_latency_a_s"])
        self.assertIsNone(s["mean_latency_b_s"])
        self.assertIsNone(s["mean_similarity"])


class TestDefaultPrompts(unittest.TestCase):
    def test_fixed_set_of_six(self):
        self.assertEqual(len(DEFAULT_PROMPTS), 6)
        self.assertTrue(all(isinstance(p, str) and p.strip() for p in DEFAULT_PROMPTS))
        # دقیقاً ۳ پرامپتِ فارسی (بازهٔ عربی/فارسیِ یونی‌کد) و ۳ انگلیسی
        persian = sum(
            1 for p in DEFAULT_PROMPTS
            if any("؀" <= ch <= "ۿ" for ch in p))
        self.assertEqual(persian, 3)


# importِ سطحِ ماژول باید stdlib-only باشد: نه langchain، نه httpx، نه پشته‌های llm
_HEAVY_PREFIXES = ("langchain", "httpx")
_HEAVY_EXACT = ("llm.router", "llm.langchain_models", "llm.glm_client", "llm.fugu_client")


class _BlockHeavyImports:
    """meta_path finder که importِ وابستگی‌های سنگین را شکست می‌دهد."""

    def find_spec(self, fullname, path=None, target=None):
        top = fullname.split(".", 1)[0]
        if top.startswith(_HEAVY_PREFIXES) or fullname in _HEAVY_EXACT:
            raise ImportError(f"blocked by test: {fullname}")
        return None


class TestImportIsStdlibOnly(unittest.TestCase):
    def test_fresh_import_with_heavy_deps_blocked(self):
        """importِ ماژول نباید langchain/httpx/پشته‌های llm را بخواهد (فقط stdlib)."""
        blocker = _BlockHeavyImports()
        saved = sys.modules.pop("llm.shadow_compare", None)
        popped = {}
        for name in list(sys.modules):
            top = name.split(".", 1)[0]
            if top.startswith(_HEAVY_PREFIXES) or name in _HEAVY_EXACT:
                popped[name] = sys.modules.pop(name)
        sys.meta_path.insert(0, blocker)
        try:
            mod = importlib.import_module("llm.shadow_compare")
            self.assertTrue(callable(mod.build_record))
            self.assertTrue(callable(mod.summarize))
        finally:
            sys.meta_path.remove(blocker)
            sys.modules.pop("llm.shadow_compare", None)
            if saved is not None:
                sys.modules["llm.shadow_compare"] = saved
            sys.modules.update(popped)


if __name__ == "__main__":
    unittest.main()
