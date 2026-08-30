#!/usr/bin/env python3
"""test_sparse_filter.py — تستِ Blueprint Phase 4: فیلتر ورودیِ sparse (L1 / prediction error).

متریک‌های پیش‌ثبت‌شده (state/phase-metrics.jsonl → blueprint-phase-4-sparse):
  input_sparsity_ratio ∈ [0,1] و > 0.5 روی دادهٔ تکراری ·
  prediction_error_distribution دُم‌سنگین · no_regression (flag خاموش).
$0 آفلاین: همهٔ persistها tmpdir. هیچ لمسِ state واقعی.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness

ENV = harness.setup("sparse-filter")

import os
import tempfile

from neural.sparse_filter import SparseInputFilter, SparseFilterReport, heavy_tail_share


def _tmp_path(name="sparse-test.json"):
    return Path(tempfile.mkdtemp()) / name


def _make(**kw):
    kw.setdefault("persist_path", _tmp_path())
    return SparseInputFilter(**kw)


# ─── هستهٔ فیلتر ─────────────────────────────────────────────────────────────

def t_novel_passes():
    """کلید تازه بی‌قید عبور می‌کند؛ err = |x|؛ در novel_keys ثبت می‌شود."""
    f = _make(error_threshold=0.05)
    r = f.filter({"rev": 42.0})
    assert "rev" in r.passed and r.passed["rev"] == 42.0
    assert "rev" in r.novel_keys
    assert "rev" not in r.filtered
    assert r.prediction_errors["rev"] == 42.0


def t_constant_filtered_and_sparsity():
    """متریکِ پیش‌ثبت‌شده: سیگنالِ ثابت بعد از همگراییِ EMA فیلتر می‌شود و
    sparsity_ratio > 0.5 روی دیکشنریِ چند ثابتِ همگراشده."""
    f = _make(error_threshold=0.05, ema_alpha=0.2)
    obs = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0}
    last = None
    for _ in range(10):
        last = f.filter(dict(obs))
    assert last is not None
    for k in obs:
        assert k in last.filtered, f"{k} باید فیلتر می‌شد؛ filtered={last.filtered}"
    assert last.passed == {}, f"سیگنالِ قابل‌پیش‌بینی نباید عبور کند: {last.passed}"
    assert last.sparsity_ratio > 0.5, \
        f"input_sparsity_ratio باید > 0.5 روی دادهٔ تکراری باشد، شد {last.sparsity_ratio}"


def t_changed_signal_passes_again():
    """جهشِ خطا: سیگنالِ همگراشده که ناگهان عوض شود دوباره عبور می‌کند."""
    f = _make(error_threshold=0.05, ema_alpha=0.2)
    for _ in range(5):
        f.filter({"a": 1.0})
    r = f.filter({"a": 5.0})
    assert "a" in r.passed, "تغییرِ ناگهانی باید عبور کند (novelty spike)"
    assert "a" not in r.novel_keys, "کلیدِ دیده‌شده novel نیست"
    assert r.prediction_errors["a"] > 3.0, f"err باید بزرگ باشد: {r.prediction_errors}"


def t_env_override():
    """پارامترِ صریح بر env می‌چربد؛ env بر پیش‌فرض؛ env خراب → پیش‌فرض."""
    old = os.environ.get("OCTOPUS_SPARSE_ERROR_THRESHOLD")
    try:
        os.environ["OCTOPUS_SPARSE_ERROR_THRESHOLD"] = "0.33"
        assert _make().error_threshold == 0.33
        assert _make(error_threshold=0.11).error_threshold == 0.11
        os.environ["OCTOPUS_SPARSE_ERROR_THRESHOLD"] = "junk"
        assert _make().error_threshold == 0.05   # پیش‌فرض
    finally:
        if old is None:
            os.environ.pop("OCTOPUS_SPARSE_ERROR_THRESHOLD", None)
        else:
            os.environ["OCTOPUS_SPARSE_ERROR_THRESHOLD"] = old


def t_l1_soft_shrink():
    """هندسهٔ الماس L1: سیگنالِ مرزی با λ=0 عبور می‌کند، با λ>0 صفر و فیلتر می‌شود."""
    borderline = 1.12   # err = 0.12؛ λ=0 → 0.12 > 0.05 عبور؛ λ=0.1 → 0.02 ≤ 0.05 فیلتر
    f0 = _make(error_threshold=0.05, l1_lambda=0.0)
    f0.filter({"a": 1.0})
    r0 = f0.filter({"a": borderline})
    assert "a" in r0.passed, f"با λ=0 باید عبور می‌کرد: {r0.filtered}"

    f1 = _make(error_threshold=0.05, l1_lambda=0.1)
    f1.filter({"a": 1.0})
    r1 = f1.filter({"a": borderline})
    assert "a" in r1.filtered, f"انقباض L1 باید مرزی را فیلتر می‌کرد: passed={r1.passed}"


def t_sparsity_ratio_bounded():
    """sparsity_ratio همیشه در [0,1]."""
    f = _make(error_threshold=0.05)
    seqs = [{"a": 1.0}, {"a": 1.0, "b": 2.0}, {"a": 9.0, "b": 2.0, "c": "متن"},
            {}, {"a": 9.0}]
    for obs in seqs:
        r = f.filter(obs)
        assert 0.0 <= r.sparsity_ratio <= 1.0, f"ratio={r.sparsity_ratio} خارج از [0,1]"


def t_deterministic():
    """همان دنباله دو بار → گزارش‌های identical (هیچ تصادف/زمانی در تصمیم)."""
    seq = [{"a": 1.0, "b": 5.0}, {"a": 1.1, "b": 5.0}, {"a": 4.0, "c": 2.0},
           {"a": 4.0, "b": 5.0, "c": 2.0}]
    runs = []
    for _ in range(2):
        f = _make(error_threshold=0.05, ema_alpha=0.2, l1_lambda=0.01)
        runs.append([f.filter(dict(obs)) for obs in seq])
    assert runs[0] == runs[1], f"باید deterministic باشد:\n{runs[0]}\n{runs[1]}"


def t_persist_roundtrip():
    """persist اتمیک + reload: نمونهٔ جدید پیش‌بینی‌ها و step را حفظ می‌کند."""
    p = _tmp_path("roundtrip.json")
    f1 = SparseInputFilter(persist_path=p, error_threshold=0.05)
    for _ in range(3):
        f1.filter({"a": 1.0})
    f2 = SparseInputFilter(persist_path=p, error_threshold=0.05)
    assert f2.prediction("a") == f1.prediction("a")
    assert f2.step_count == f1.step_count == 3
    r = f2.filter({"a": 1.0})
    assert "a" in r.filtered, "پیش‌بینیِ بازیابی‌شده باید سیگنالِ ثابت را فیلتر کند"
    assert "a" not in r.novel_keys


def t_corrupt_persist_fail_soft():
    """فایل خراب → شروع تازه بدون crash (fail-soft)."""
    p = _tmp_path("corrupt.json")
    p.write_text("{not json", "utf-8")
    f = SparseInputFilter(persist_path=p)
    assert f.keys() == []
    assert f.step_count == 0
    r = f.filter({"a": 1.0})
    assert "a" in r.passed


def t_input_not_mutated():
    """فیلتر هرگز دیکشنریِ ورودی را mutate نمی‌کند."""
    obs = {"a": 1.0, "b": True, "c": "متن", "d": None}
    snapshot = dict(obs)
    f = _make()
    f.filter(obs)
    f.filter(obs)
    assert obs == snapshot, f"ورودی mutate شده: {obs}"


def t_non_numeric_ignored():
    """مقادیر غیرعددی (str/None/list) و bool نه در passed نه در filtered."""
    f = _make()
    r = f.filter({"s": "متن", "n": None, "l": [1, 2], "flag": True, "x": 3.0})
    for k in ("s", "n", "l", "flag"):
        assert k not in r.passed and k not in r.filtered, f"{k} نباید سنجیده شود"
        assert k not in r.prediction_errors
        assert f.prediction(k) is None, f"{k} نباید وارد پیش‌بینی‌گر شود"
    assert "x" in r.passed
    assert r.sparsity_ratio == 0.0   # فقط یک عددی و آن هم عبور کرد


def t_empty_input():
    """ورودی خالی → ratio صفر، بدون crash."""
    f = _make()
    r = f.filter({})
    assert r.sparsity_ratio == 0.0
    assert r.passed == {} and r.filtered == [] and r.novel_keys == []
    assert r.step == 1


def t_eviction_max_keys():
    """eviction قطعی: کم‌آپدیت‌ترین‌ها (کمترین n، tie-break با کلید) تا max_keys."""
    f = _make(max_keys=3)
    f.filter({"a": 1.0, "b": 1.0})                                # a,b → n=1
    f.filter({"a": 1.0, "b": 1.0, "c": 1.0, "d": 1.0, "e": 1.0})  # a,b → n=2؛ c,d,e → n=1
    assert len(f.keys()) == 3, f"باید تا max_keys هرس می‌شد: {f.keys()}"
    # کمترین n با tie-break الفبایی: c و d حذف؛ e و a و b می‌مانند
    assert sorted(f.keys()) == ["a", "b", "e"], f"ترتیبِ eviction قطعی نیست: {sorted(f.keys())}"
    r = f.filter({"c": 1.0})
    assert "c" in r.novel_keys, "کلیدِ evict‌شده باید دوباره novel باشد"


def t_heavy_tail_share():
    """متریکِ پیش‌ثبت‌شده: توزیعِ خطای دُم‌سنگین سهم > 0.4؛ یکنواخت ≈ top_frac؛ خالی 0.0."""
    heavy = [100.0] + [0.1] * 20
    assert heavy_tail_share(heavy) > 0.4, f"دُم‌سنگین: {heavy_tail_share(heavy)}"
    uniform = [1.0] * 100
    share = heavy_tail_share(uniform)
    assert abs(share - 0.1) < 1e-9, f"یکنواخت باید ≈ top_frac باشد: {share}"
    assert heavy_tail_share([]) == 0.0
    assert heavy_tail_share({}) == 0.0
    assert heavy_tail_share([0.0, 0.0]) == 0.0   # جرمِ صفر → 0.0 نه تقسیم بر صفر
    # ورودی dict (خروجیِ report.prediction_errors)
    d = {f"k{i}": 0.01 for i in range(9)}
    d["big"] = 50.0
    assert heavy_tail_share(d) > 0.4


def t_report_dataclass():
    """SparseFilterReport همهٔ فیلدهای متریک را دارد."""
    f = _make()
    r = f.filter({"m1": 0.5})
    assert isinstance(r, SparseFilterReport)
    assert r.step == 1
    assert isinstance(r.passed, dict)
    assert isinstance(r.filtered, list)
    assert isinstance(r.prediction_errors, dict)
    assert isinstance(r.sparsity_ratio, float)
    assert isinstance(r.novel_keys, list)


if __name__ == "__main__":
    failed = harness.run([
        ("کلید تازه عبور می‌کند", t_novel_passes),
        ("سیگنالِ ثابت فیلتر + sparsity > 0.5", t_constant_filtered_and_sparsity),
        ("تغییرِ سیگنال دوباره عبور می‌کند", t_changed_signal_passes_again),
        ("env override + تقدم آرگومان", t_env_override),
        ("انقباض نرم L1 مرزی را فیلتر می‌کند", t_l1_soft_shrink),
        ("sparsity_ratio در [0,1]", t_sparsity_ratio_bounded),
        ("deterministic", t_deterministic),
        ("persist roundtrip", t_persist_roundtrip),
        ("فایل خراب → fail-soft", t_corrupt_persist_fail_soft),
        ("ورودی mutate نمی‌شود", t_input_not_mutated),
        ("غیرعددی/bool نادیده گرفته می‌شود", t_non_numeric_ignored),
        ("ورودی خالی → ratio صفر", t_empty_input),
        ("eviction قطعی تا max_keys", t_eviction_max_keys),
        ("heavy_tail_share — دُم‌سنگین/یکنواخت/خالی", t_heavy_tail_share),
        ("SparseFilterReport dataclass", t_report_dataclass),
    ])
    sys.exit(1 if failed else 0)
