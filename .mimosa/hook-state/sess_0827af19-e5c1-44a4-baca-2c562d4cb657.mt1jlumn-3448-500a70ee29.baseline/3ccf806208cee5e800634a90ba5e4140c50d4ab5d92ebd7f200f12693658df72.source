#!/usr/bin/env python3
"""test_fisher.py — Blueprint Phase 6: متریکِ فیشر روی چشم‌اندازِ fitness (natural gradient).

قفلِ ناوردی (I4/I6): این ماژول فقط advisory JSON می‌نویسد — هیچ وزنِ واقعی‌ای عوض
نمی‌شود و budget هرگز برای نوشتن باز نمی‌شود. متریکِ پیش‌ثبت‌شده:
  fisher_condition_number متناهی و کران‌دار (regularized: min-eig ≥ eps).
"""
import ast
import json
import math
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness  # noqa: E402

ENV = harness.setup("fisher")
import opslib   # noqa: E402
import fitness  # noqa: E402
import fisher   # noqa: E402

_W = {"value": 0.30, "urgency": 0.25, "efficiency": 0.20, "human": 0.20, "waste": 0.05}


def _synthetic_report():
    """گزارشِ دست‌ساز — بدون هیچ وابستگی به fitness/fs (تزریقِ مستقیم)."""
    return {
        "weights": dict(_W),
        "cells": {
            "alpha": {"acceptance_rate": 0.7, "efficiency": 0.5, "waste": 0.2},
            "beta":  {"acceptance_rate": 0.4, "efficiency": 0.6, "waste": 0.1},
        },
    }


def _seed_two_honest_cells():
    """دو cellِ صادق (jsonl↔db منطبق + توکن) طبق دستورِ test_fitness_sigma."""
    harness.add_outbox_jsonl(ENV["brain"], [{"event": "sent", "business": "ziman"}] * 5
                             + [{"event": "rejected", "business": "ziman"}] * 2)
    harness.add_outbox_rows(ENV["brain"], [("ziman", "sent")] * 5 + [("ziman", "rejected")] * 2)
    harness.add_usage(ENV["brain"], [(opslib.today(), "deepseek", "ziman", 5000, 2000, 0.01)])
    harness.add_outbox_jsonl(ENV["brain"], [{"event": "sent", "business": "painting"}] * 6
                             + [{"event": "rejected", "business": "painting"}] * 1)
    harness.add_outbox_rows(ENV["brain"], [("painting", "sent")] * 6 + [("painting", "rejected")] * 1)
    harness.add_usage(ENV["brain"], [(opslib.today(), "deepseek", "painting", 4000, 1500, 0.008)])


_KEYS = {"ts", "cells_used", "fisher_condition_number", "current_weights", "advisory_weights",
         "natural_step", "eta", "eps", "advisory_only", "authoritative", "numpy_used", "note"}


# ── ۱: محیطِ تازه بدونِ cell (مسیرِ واقعی fitness) — باید صفر و بدونِ crash ──────────
def t_fresh_no_cells():
    out = fisher.compute_fisher(report=None)          # outbox خالی → cells={}
    assert out["cells_used"] == 0, out
    assert out["advisory_weights"] is None
    assert out["fisher_condition_number"] is None
    assert out["advisory_only"] is True and out["authoritative"] is False
    assert set(out.keys()) == _KEYS, out.keys()
    assert "no-cells" in out["note"]


# ── ۲: تزریقِ گزارشِ synthetic ──────────────────────────────────────────────────────
def t_synthetic_injection():
    out = fisher.compute_fisher(report=_synthetic_report())
    assert out["cells_used"] == 2, out
    c = out["fisher_condition_number"]
    assert c is not None and math.isfinite(c) and c > 0, c
    adv = out["advisory_weights"]
    assert adv is not None and all(v >= 0.0 for v in adv.values()), adv
    assert abs(sum(adv.values()) - sum(out["current_weights"].values())) < 1e-6, adv
    assert len(out["natural_step"]) == 5, out["natural_step"]
    assert out["numpy_used"] is True


# ── ۳: cellهای یکسان → G تکین؛ regularization باید cond را متناهی نگه دارد ──────────
def t_singular_regularized():
    cell = {"acceptance_rate": 0.6, "efficiency": 0.5, "waste": 0.15}
    rep = {"weights": dict(_W), "cells": {"a": dict(cell), "b": dict(cell)}}
    out = fisher.compute_fisher(report=rep)
    c = out["fisher_condition_number"]
    assert c is not None and math.isfinite(c) and c > 0, ("cond باید متناهی بماند", c)
    assert out["cells_used"] == 2


# ── ۴: eps بزرگ‌تر → cond کوچک‌تر-یا-مساوی (یکنواختیِ regularization روی دادهٔ ثابت) ──
def t_eps_monotonic():
    rep = _synthetic_report()
    c_small = fisher.compute_fisher(report=rep, eps=1e-3)["fisher_condition_number"]
    c_big = fisher.compute_fisher(report=rep, eps=1e-1)["fisher_condition_number"]
    assert c_big <= c_small + 1e-9, (c_small, c_big)


# ── ۵: دترمینیسم — دو فراخوانیِ یکسان → عددهای یکسان (بجز ts) ──────────────────────
def t_determinism():
    rep = _synthetic_report()
    a = fisher.compute_fisher(report=rep)
    b = fisher.compute_fisher(report=rep)
    for k in ("fisher_condition_number", "advisory_weights", "natural_step",
              "current_weights", "cells_used"):
        assert a[k] == b[k], (k, a[k], b[k])


# ── ۶: cellِ excluded/تمپر از cells_used حذف می‌شود ─────────────────────────────────
def t_excluded_skipped():
    rep = {"weights": dict(_W), "cells": {
        "good": {"acceptance_rate": 0.5, "efficiency": 0.5, "waste": 0.1},
        "bad": {"excluded": True, "reason": "integrity-mismatch"},
    }}
    out = fisher.compute_fisher(report=rep)
    assert out["cells_used"] == 1, out


# ── ۷: تلورانسِ bool/None در مؤلفه‌ها (acceptance_rate None → 0.0) ───────────────────
def t_bool_none_tolerance():
    assert fisher.component_vector({"excluded": True}) is None
    v = fisher.component_vector({"acceptance_rate": None, "efficiency": 0.4, "waste": 0.1})
    assert v == [0.0, 0.0, 0.4, 0.5, 0.1], v
    v2 = fisher.component_vector({"acceptance_rate": True, "efficiency": 0.4, "waste": None})
    assert v2[0] == 1.0 and v2[4] == 0.0, v2
    out = fisher.compute_fisher(report={"weights": dict(_W), "cells": {"x": {"acceptance_rate": None}}})
    assert out["cells_used"] == 1 and out["fisher_condition_number"] is not None, out


# ── ۸: advisory-only ساختاری — ماژول هرگز weights/cells را mutate نمی‌کند ────────────
def t_advisory_only_no_mutation():
    rep = _synthetic_report()
    w_before = dict(rep["weights"])
    cells_before = json.dumps(rep["cells"], sort_keys=True)
    out = fisher.compute_fisher(report=rep)
    assert rep["weights"] == w_before, rep["weights"]
    assert json.dumps(rep["cells"], sort_keys=True) == cells_before
    assert out["advisory_only"] is True and out["authoritative"] is False
    # وزن‌های واقعی fitness قبل==بعد (budget لمس نمی‌شود)
    before = fitness.compute(write=False)["weights"]
    fisher.compute_fisher(report=None)
    after = fitness.compute(write=False)["weights"]
    assert before == after, (before, after)


# ── ۹: منبعِ fisher.py هرگز budget را برای نوشتن باز نمی‌کند ─────────────────────────
def t_source_never_writes_budgets():
    src = Path(fisher.__file__).read_text("utf-8")
    tree = ast.parse(src)
    doc = tree.body[0].value
    doc_start, doc_end = doc.lineno, doc.end_lineno
    for i, ln in enumerate(src.splitlines(), start=1):
        if "budgets.yaml" in ln:
            in_doc = doc_start <= i <= doc_end
            in_comment = ln.lstrip().startswith("#")
            assert in_doc or in_comment, f"budgets.yaml در خطِ کد {i}: {ln}"
    # هیچ نوشتنِ مستقیم روی budgets/yaml
    assert "load_budgets" not in src, "fisher نباید مستقیم budget بخواند — وزن از report می‌آید"


# ── ۱۰: fallbackِ بدونِ numpy — dict تمیز، بدونِ crash ──────────────────────────────
def t_no_numpy_fallback():
    orig = fisher._HAS_NUMPY
    fisher._HAS_NUMPY = False
    try:
        out = fisher.compute_fisher(report=_synthetic_report())
        assert out["numpy_used"] is False
        assert out["fisher_condition_number"] is None
        assert out["advisory_weights"] is None
        assert out["natural_step"] is None
        assert out["cells_used"] == 2
        assert "numpy" in out["note"]
        assert set(out.keys()) == _KEYS, out.keys()
    finally:
        fisher._HAS_NUMPY = orig


# ── ۱۱: write=True با out_path موقت → فایل معتبر JSON + advisory_only ────────────────
def t_write_tmp():
    with tempfile.TemporaryDirectory() as td:
        outp = Path(td) / "fisher-latest.json"
        out = fisher.compute_fisher(report=_synthetic_report(), write=True, out_path=outp)
        assert outp.exists(), "فایل advisory باید نوشته می‌شد"
        loaded = json.loads(outp.read_text("utf-8"))
        assert loaded["advisory_only"] is True
        assert loaded["authoritative"] is False
        assert loaded["cells_used"] == 2
        assert loaded["fisher_condition_number"] == out["fisher_condition_number"]


# ── ۱۲: current_weights دقیقاً از weightsِ گزارش می‌آید ──────────────────────────────
def t_current_weights_from_report():
    rep = _synthetic_report()
    out = fisher.compute_fisher(report=rep)
    assert out["current_weights"] == {c: rep["weights"][c] for c in fisher.COMPONENT_ORDER}, out


# ── ۱۳: محیطِ seed‌شده (دو cellِ واقعی از مسیرِ fitness) ──────────────────────────────
def t_seeded_env():
    _seed_two_honest_cells()
    out = fisher.compute_fisher(report=None)
    assert out["cells_used"] >= 2, out
    c = out["fisher_condition_number"]
    assert c is not None and math.isfinite(c) and c > 0, c
    adv = out["advisory_weights"]
    assert adv is not None and all(v >= 0.0 for v in adv.values()), adv
    assert abs(sum(adv.values()) - sum(out["current_weights"].values())) < 1e-6, adv
    assert len(out["natural_step"]) == 5


if __name__ == "__main__":
    failed = harness.run([
        ("محیطِ تازه بدونِ cell → صفر/advisory None", t_fresh_no_cells),
        ("تزریقِ گزارشِ synthetic → cond متناهی + advisory معتبر", t_synthetic_injection),
        ("G تکین → regularization cond را متناهی نگه می‌دارد", t_singular_regularized),
        ("eps بزرگ‌تر → cond کوچک‌تر-یا-مساوی", t_eps_monotonic),
        ("دترمینیسم: دو فراخوانی یکسان", t_determinism),
        ("cellِ excluded از cells_used حذف", t_excluded_skipped),
        ("تلورانسِ bool/None در مؤلفه‌ها", t_bool_none_tolerance),
        ("advisory-only: بدونِ mutation وزن/cell + budget دست‌نخورده", t_advisory_only_no_mutation),
        ("منبع هرگز budget را برای نوشتن باز نمی‌کند", t_source_never_writes_budgets),
        ("fallbackِ بدونِ numpy تمیز", t_no_numpy_fallback),
        ("write=True با out_path موقت → JSON معتبر", t_write_tmp),
        ("current_weights از weightsِ گزارش", t_current_weights_from_report),
        ("محیطِ seed‌شده → cells_used≥۲ + cond>۰", t_seeded_env),
    ])
    sys.exit(1 if failed else 0)
