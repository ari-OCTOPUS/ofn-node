"""تستِ llm/shadow_analyze (B11 فاز ۲).

decide() روی دیکشنری‌های دستی برای هر ۶ حکم + همهٔ مرزها؛ analyze() روی
رکوردهای ساختگی؛ load_records روی فایلِ خراب/نبود؛ و اثباتِ اینکه importِ
ماژول stdlib-only است (نه langchain، نه httpx).
"""
from tests import _bootstrap  # noqa: F401

import importlib
import json
import os
import sys
import tempfile
import unittest

from llm.shadow_analyze import (
    MIN_RECORDS, SIM_FORBID, SIM_MIGRATE,
    decide, analyze, load_records, render_report,
)


def _summary(count=30, er_a=0.0, er_b=0.0, lat_a=1.0, lat_b=1.0, sim=0.9) -> dict:
    return {"count": count,
            "error_rate_a": er_a, "error_rate_b": er_b,
            "mean_latency_a_s": lat_a, "mean_latency_b_s": lat_b,
            "mean_similarity": sim}


# ── decide(): پیش‌شرطِ تعداد رکورد ──────────────────────────────────────────
class TestDecidePrecondition(unittest.TestCase):
    def test_below_threshold_insufficient(self):
        d = decide(_summary(count=29))
        self.assertEqual(d["verdict"], "INSUFFICIENT_DATA")
        self.assertFalse(d["switch_allowed"])
        self.assertIn("1", d["reason"])   # «۱ رکوردِ دیگر»

    def test_zero_count_insufficient(self):
        self.assertEqual(decide(_summary(count=0))["verdict"], "INSUFFICIENT_DATA")

    def test_thirty_exactly_passes_precondition(self):
        # ۳۰ دقیقاً باید از پیش‌شرط بگذرد (این‌جا similarity بالا + بازندهٔ روشن → MIGRATE)
        d = decide(_summary(count=30, er_a=0.2, lat_a=2.0, sim=0.9))
        self.assertNotEqual(d["verdict"], "INSUFFICIENT_DATA")

    def test_non_int_count_coerced_to_zero(self):
        self.assertEqual(decide(_summary(count=None))["verdict"], "INSUFFICIENT_DATA")
        self.assertEqual(decide(_summary(count=True))["verdict"], "INSUFFICIENT_DATA")


# ── decide(): similarity غایب ───────────────────────────────────────────────
class TestDecideNoSimilarity(unittest.TestCase):
    def test_none_similarity(self):
        d = decide(_summary(sim=None))
        self.assertEqual(d["verdict"], "NO_SIMILARITY_DATA")
        self.assertFalse(d["switch_allowed"])

    def test_nan_similarity(self):
        self.assertEqual(decide(_summary(sim=float("nan")))["verdict"], "NO_SIMILARITY_DATA")


# ── decide(): گیتِ ممنوعیتِ سوییچ (بندِ ۲) ──────────────────────────────────
class TestDecideForbid(unittest.TestCase):
    def test_low_similarity_forbids(self):
        d = decide(_summary(sim=0.49))
        self.assertEqual(d["verdict"], "HOLD_INVESTIGATE_DIVERGENCE")
        self.assertFalse(d["switch_allowed"])

    def test_forbid_wins_over_clear_loser(self):
        # حتی با بازندهٔ روشن (a بدترِ هر دو)، similarity پایین سوییچ را وتو می‌کند
        d = decide(_summary(sim=0.4, er_a=0.3, lat_a=5.0))
        self.assertEqual(d["verdict"], "HOLD_INVESTIGATE_DIVERGENCE")
        self.assertFalse(d["switch_allowed"])
        self.assertIsNone(d["winner"])          # برنده اقدام‌پذیر نیست
        self.assertEqual(d["loser"], "a")        # بازنده فقط شاهد است

    def test_exactly_0_5_not_forbidden(self):
        d = decide(_summary(sim=0.5, er_a=0.3, lat_a=5.0))
        self.assertEqual(d["verdict"], "HOLD_SIMILARITY_INCONCLUSIVE")


# ── decide(): بندِ خاکستریِ [0.5, 0.7] ──────────────────────────────────────
class TestDecideGrayBand(unittest.TestCase):
    def test_mid_band_with_clear_loser_holds(self):
        d = decide(_summary(sim=0.6, er_a=0.3, lat_a=5.0))
        self.assertEqual(d["verdict"], "HOLD_SIMILARITY_INCONCLUSIVE")
        self.assertFalse(d["switch_allowed"])
        self.assertEqual(d["loser"], "a")        # شاهد

    def test_exactly_0_7_not_migrate(self):
        d = decide(_summary(sim=0.7, er_a=0.3, lat_a=5.0))
        self.assertEqual(d["verdict"], "HOLD_SIMILARITY_INCONCLUSIVE")


# ── decide(): بالای ۰٫۷ اما بدونِ بازندهٔ روشن ──────────────────────────────
class TestDecideNoClearLoser(unittest.TestCase):
    def test_error_rate_tie_holds(self):
        # تساویِ error_rate؛ برتریِ latency به‌تنهایی کافی نیست
        d = decide(_summary(sim=0.9, er_a=0.1, er_b=0.1, lat_a=5.0, lat_b=1.0))
        self.assertEqual(d["verdict"], "HOLD_NO_CLEAR_LOSER")
        self.assertFalse(d["switch_allowed"])

    def test_split_holds(self):
        # a روی خطا بدتر، b روی تأخیر بدتر → هیچ بازندهٔ واحدی نیست
        d = decide(_summary(sim=0.9, er_a=0.3, er_b=0.1, lat_a=1.0, lat_b=5.0))
        self.assertEqual(d["verdict"], "HOLD_NO_CLEAR_LOSER")

    def test_identical_metrics_holds(self):
        d = decide(_summary(sim=1.0, er_a=0.1, er_b=0.1, lat_a=1.0, lat_b=1.0))
        self.assertEqual(d["verdict"], "HOLD_NO_CLEAR_LOSER")

    def test_uncomparable_metric_holds(self):
        # latency یکی None (پاتولوژیک) → بازندهٔ واحد نه → HOLD_NO_CLEAR_LOSER (بدونِ crash)
        d = decide(_summary(sim=0.9, er_a=0.3, lat_a=None, lat_b=1.0))
        self.assertEqual(d["verdict"], "HOLD_NO_CLEAR_LOSER")


# ── decide(): تنها راهِ MIGRATE ─────────────────────────────────────────────
class TestDecideMigrate(unittest.TestCase):
    def test_migrate_winner_b(self):
        # a بدترِ هر دو سنجه، sim>0.7 → مهاجرت به b
        d = decide(_summary(sim=0.85, er_a=0.2, er_b=0.05, lat_a=3.0, lat_b=1.0))
        self.assertEqual(d["verdict"], "MIGRATE")
        self.assertTrue(d["switch_allowed"])
        self.assertEqual(d["winner"], "b")
        self.assertEqual(d["loser"], "a")

    def test_migrate_winner_a(self):
        d = decide(_summary(sim=0.85, er_a=0.05, er_b=0.2, lat_a=1.0, lat_b=3.0))
        self.assertEqual(d["verdict"], "MIGRATE")
        self.assertEqual(d["winner"], "a")
        self.assertEqual(d["loser"], "b")

    def test_migrate_is_only_true_switch(self):
        d = decide(_summary(sim=0.71, er_a=0.2, er_b=0.05, lat_a=3.0, lat_b=1.0))
        self.assertEqual(d["verdict"], "MIGRATE")   # 0.71 اکیداً >0.7
        self.assertTrue(d["switch_allowed"])

    def test_criterion_trace_populated(self):
        d = decide(_summary(sim=0.85, er_a=0.2, er_b=0.05, lat_a=3.0, lat_b=1.0))
        c = d["criterion"]
        self.assertTrue(c["records_sufficient"])
        self.assertTrue(c["similarity_gt_0_7"])
        self.assertFalse(c["similarity_lt_0_5"])
        self.assertEqual(c["single_loser"], "a")
        self.assertEqual(c["winner_side"], "b")


# ── analyze(): روی رکوردهای ساختگی ──────────────────────────────────────────
def _rec(prompt="p1", sim=0.9, err_a=None, err_b=None, lat_a=2.0, lat_b=1.0,
         out_a="AAAA", out_b="BBBB", run_id="r1", ts="2026-07-11T10:00:00",
         stack_a="router[fugu]", stack_b="langchain[ChatOpenAI]") -> dict:
    return {
        "prompt": prompt,
        "a": {"output": None if err_a else out_a, "length": None if err_a else len(out_a),
              "latency_s": lat_a, "error": err_a},
        "b": {"output": None if err_b else out_b, "length": None if err_b else len(out_b),
              "latency_s": lat_b, "error": err_b},
        "metrics": {"length_ratio": 1.0, "similarity": None if (err_a or err_b) else sim},
        "run_id": run_id, "idx": 0, "ts": ts,
        "stack_a": stack_a, "stack_b": stack_b,
    }


class TestAnalyze(unittest.TestCase):
    def test_migrate_end_to_end_with_real_summarize(self):
        # ۲۷ رکوردِ سالمِ sim=0.9 + ۳ رکورد که a خطا می‌دهد → error_rate_a=0.1، lat_a>lat_b
        recs = [_rec(sim=0.9) for _ in range(27)]
        recs += [_rec(err_a="TimeoutError") for _ in range(3)]
        a = analyze(recs)                      # summarizer واقعی (import داخلی)
        self.assertEqual(a["decision"]["verdict"], "MIGRATE")
        self.assertEqual(a["decision"]["winner"], "b")
        self.assertEqual(a["migration_target"], "langchain[ChatOpenAI]")
        self.assertEqual(a["winner_label"], "langchain[ChatOpenAI]")
        self.assertEqual(a["loser_label"], "router[fugu]")
        self.assertIn("MIGRATE", a["report_text"])

    def test_investigate_divergence(self):
        recs = [_rec(sim=0.3) for _ in range(30)]
        a = analyze(recs)
        self.assertEqual(a["decision"]["verdict"], "HOLD_INVESTIGATE_DIVERGENCE")
        self.assertEqual(a["similarity_bands"]["lt_0_5"], 30)

    def test_degenerate_stack_all_error_no_similarity(self):
        recs = [_rec(err_b="ConnectError") for _ in range(30)]
        a = analyze(recs)
        self.assertEqual(a["decision"]["verdict"], "NO_SIMILARITY_DATA")
        self.assertTrue(a["degenerate"]["stack_b_all_error"])
        self.assertEqual(a["error_types"]["b"], {"ConnectError": 30})

    def test_insufficient_data(self):
        a = analyze([_rec() for _ in range(10)])
        self.assertEqual(a["decision"]["verdict"], "INSUFFICIENT_DATA")

    def test_per_prompt_sorted_worst_first(self):
        recs = ([_rec(prompt="high", sim=0.95) for _ in range(15)]
                + [_rec(prompt="low", sim=0.2) for _ in range(15)])
        a = analyze(recs)
        self.assertEqual(a["per_prompt"][0]["prompt"], "low")   # بدترین اول
        self.assertEqual(a["per_prompt"][-1]["prompt"], "high")

    def test_mixed_stack_pairs_flag(self):
        recs = ([_rec(stack_a="router[fugu]") for _ in range(15)]
                + [_rec(stack_a="stub[X]") for _ in range(15)])
        a = analyze(recs)
        self.assertTrue(a["mixed_stack_pairs"])
        self.assertGreater(len(a["stack_pairs"]), 1)

    def test_runs_and_date_span(self):
        recs = [_rec(run_id="r1", ts="2026-07-10T10:00:00") for _ in range(15)]
        recs += [_rec(run_id="r2", ts="2026-07-12T10:00:00") for _ in range(15)]
        a = analyze(recs)
        self.assertEqual(a["runs"], 2)
        self.assertEqual(a["date_span"]["days"], 2)

    def test_non_dict_records_filtered(self):
        recs = [_rec() for _ in range(30)] + [None, 42, "junk", []]  # type: ignore
        a = analyze(recs)                      # نباید crash کند
        self.assertEqual(a["summary"]["count"], 30)

    def test_injected_summarizer(self):
        # summarizer تزریق‌شده → decide بدونِ importِ shadow_compare هم آزمون‌پذیر است
        a = analyze([], summarizer=lambda recs: _summary(count=0))
        self.assertEqual(a["decision"]["verdict"], "INSUFFICIENT_DATA")

    def test_margin_caveat_on_thin_migrate(self):
        # ۲۹ سالم + ۱ خطای a → error_rate_a=0.033<0.05 → مهاجرتِ نازک
        recs = [_rec(sim=0.9) for _ in range(29)] + [_rec(err_a="TimeoutError")]
        a = analyze(recs)
        self.assertEqual(a["decision"]["verdict"], "MIGRATE")
        self.assertTrue(a["margin_caveat"])
        self.assertIn("نازک", a["report_text"])

    def test_early_divergence_flag_on_insufficient(self):
        # <۳۰ رکورد اما similarity قبلاً <0.5 → پرچمِ هشدارِ زودهنگام
        a = analyze([_rec(sim=0.3) for _ in range(20)])
        self.assertEqual(a["decision"]["verdict"], "INSUFFICIENT_DATA")
        self.assertTrue(a["early_divergence_flag"])
        self.assertIn("هشدارِ زودهنگام", a["report_text"])

    def test_mixed_tz_timestamps_no_crash(self):
        # ts مختلطِ naive + offset-aware نباید min/max را بشکند (نرمال به UTC)
        recs = ([_rec(ts="2026-07-10T10:00:00") for _ in range(15)]
                + [_rec(ts="2026-07-12T10:00:00+00:00") for _ in range(15)])
        a = analyze(recs)                       # نباید TypeError بدهد
        self.assertEqual(a["date_span"]["days"], 2)

    def test_unhashable_run_id_no_crash(self):
        # run_idِ ناهش‌پذیر (list) نباید set را بشکند؛ فقط str شمرده می‌شود
        bad = _rec()
        bad["run_id"] = ["not-hashable"]
        recs = [_rec(run_id="r1") for _ in range(29)] + [bad]
        a = analyze(recs)                       # نباید TypeError بدهد
        self.assertEqual(a["runs"], 1)


# ── load_records(): تحملِ ورودیِ خراب ───────────────────────────────────────
class TestLoadRecords(unittest.TestCase):
    def test_skips_blank_and_corrupt_and_non_dict(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "ev.jsonl")
            with open(p, "w", encoding="utf-8") as f:
                f.write(json.dumps({"prompt": "ok1"}) + "\n")
                f.write("\n")                       # خطِ خالی
                f.write("{ not json\n")             # JSONِ خراب
                f.write("42\n")                     # غیرِدیکشنری
                f.write(json.dumps({"prompt": "ok2"}) + "\n")
            recs = load_records(p)
            self.assertEqual(len(recs), 2)
            self.assertEqual([r["prompt"] for r in recs], ["ok1", "ok2"])

    def test_missing_file_returns_empty(self):
        self.assertEqual(load_records(os.path.join(tempfile.gettempdir(), "nope_xyz.jsonl")), [])


# ── render_report(): خالص، رشته، حاویِ حکم ──────────────────────────────────
class TestRenderReport(unittest.TestCase):
    def test_report_is_str_with_verdict(self):
        a = analyze([_rec(sim=0.3) for _ in range(30)])
        txt = render_report(a)
        self.assertIsInstance(txt, str)
        self.assertIn("HOLD_INVESTIGATE_DIVERGENCE", txt)
        self.assertIn("shadow-first", txt)


# ── importِ ماژول باید stdlib-only باشد (نه langchain/httpx) ────────────────
_HEAVY_PREFIXES = ("langchain", "httpx")
# علاوه بر پشته‌های سنگین، importِ سطحِ ماژولِ خودِ پروژه هم ممنوع است: قرارداد
# «importهای پروژه فقط داخلِ توابع» — پس اگر کسی shadow_compare/config.settings را
# به سطحِ ماژول ببرد این تست باید قرمز شود (نه‌فقط langchain/httpx).
_HEAVY_EXACT = ("llm.router", "llm.langchain_models", "llm.glm_client", "llm.fugu_client",
                "llm.shadow_compare", "config.settings")


class _BlockHeavyImports:
    def find_spec(self, fullname, path=None, target=None):
        top = fullname.split(".", 1)[0]
        if top.startswith(_HEAVY_PREFIXES) or fullname in _HEAVY_EXACT:
            raise ImportError(f"blocked by test: {fullname}")
        return None


class TestImportIsStdlibOnly(unittest.TestCase):
    def test_fresh_import_with_heavy_deps_blocked(self):
        blocker = _BlockHeavyImports()
        saved = sys.modules.pop("llm.shadow_analyze", None)
        popped = {}
        for name in list(sys.modules):
            top = name.split(".", 1)[0]
            if top.startswith(_HEAVY_PREFIXES) or name in _HEAVY_EXACT:
                popped[name] = sys.modules.pop(name)
        sys.meta_path.insert(0, blocker)
        try:
            mod = importlib.import_module("llm.shadow_analyze")
            self.assertTrue(callable(mod.decide))
            self.assertTrue(callable(mod.analyze))
        finally:
            sys.meta_path.remove(blocker)
            sys.modules.pop("llm.shadow_analyze", None)
            if saved is not None:
                sys.modules["llm.shadow_analyze"] = saved
            sys.modules.update(popped)


if __name__ == "__main__":
    unittest.main()
