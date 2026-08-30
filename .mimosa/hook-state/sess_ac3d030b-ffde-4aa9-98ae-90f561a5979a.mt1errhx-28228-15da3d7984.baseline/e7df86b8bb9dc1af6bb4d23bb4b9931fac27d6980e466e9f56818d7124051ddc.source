#!/usr/bin/env python3
"""fisher.py — Blueprint Phase 6 — گرادیان طبیعی: Δw = −η·G⁻¹·∇E روی چشم‌انداز fitness.
فقط advisory — وزن‌های واقعی فقط از budgets.yaml (I4/I6).

ایده (بلوپرینت فاز ۶): چشم‌اندازِ fitness یک منیفلد است؛ گرادیانِ اقلیدسیِ ساده
جهتِ درست را روی این منیفلد نمی‌دهد. متریکِ فیشرِ تجربی G (کوواریانسِ گرادیانِ
مؤلفه‌ای روی cellها) انحنای محلی را می‌سنجد و گامِ طبیعی G⁻¹·∇E جهتِ هموارتر
(reparameterization-invariant) را پیشنهاد می‌دهد.

ناوردی‌ها:
  I4/I6: هیچ وزنِ واقعی‌ای اینجا تغییر نمی‌کند — تنها یک JSONِ advisory نوشته می‌شود.
         وزن‌های مرجع فقط از فایلِ budget می‌آیند و این ماژول هرگز آن‌ها را نمی‌نویسد.
  advisory-only: authoritative:False همیشه؛ هیچ مصرف‌کننده‌ای حق تصمیم زنده بر پایهٔ
         این عدد ندارد (قفلِ verdict مثلِ fitness — تا ~۴ هفته دادهٔ EXPERIENCE).

پیش‌ثبتِ متریک (state/phase-metrics.jsonl → blueprint-phase-6-fisher):
  fisher_condition_number = cond(G+εI) همیشه متناهی و کران‌دار (min ≥ ε > 0).
  fitness_improvement_rate = فقط advisory تا دادهٔ کافی.

fail-soft: نبودِ numpy → ساختار کار می‌کند ولی متریکِ فیشر و advisory حساب نمی‌شود
(cells صادقانه شمرده می‌شود، عددها None).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opslib  # noqa: E402

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

COMPONENT_ORDER = ("value", "urgency", "efficiency", "human", "waste")

# پیش‌فرضِ وزن‌ها هم‌ارزِ fitness.py — فقط fallbackِ محلی وقتی گزارش وزنی همراه ندارد
# (منبعِ حقیقتِ وزن‌ها بیرونِ این ماژول است؛ اینجا هرگز نوشته نمی‌شود — I6).
_DEFAULT_WEIGHTS = {"value": 0.3, "urgency": 0.25, "efficiency": 0.2, "human": 0.2, "waste": 0.05}


def _comp(v) -> float:
    """عددِ امن برای یک مؤلفه: None/غیرعددی → 0.0 (تلورانسِ ورودیِ گزارش)."""
    if isinstance(v, bool):
        return float(v)
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def component_vector(cell: dict) -> "list[float] | None":
    """از یک cellِ گزارشِ fitness → بردارِ مؤلفه‌ها به ترتیبِ COMPONENT_ORDER.
      [acceptance_rate|0, 0.0(urgency), efficiency|0, 0.5(human), waste|0]
    cellِ excluded/تمپر → None (از fitness حذف شده، وارد فیشر نمی‌شود)."""
    if not isinstance(cell, dict) or cell.get("excluded"):
        return None
    return [
        _comp(cell.get("acceptance_rate")),
        0.0,                              # urgency — ثابتِ صفر برای cellهای بیزنسی
        _comp(cell.get("efficiency")),
        0.5,                              # human — ثابتِ 0.5 برای cellهای بیزنسی
        _comp(cell.get("waste")),
    ]


def _signed_gradient(cv: "list[float]") -> "list[float]":
    """gradientِ fitness نسبت به وزن‌ها. fitness خطی است:
      fit = w·[value, urgency, efficiency, human] − w_waste·waste
    پس ∂fit/∂w = [value, urgency, efficiency, human, −waste] (جملهٔ waste منفی)."""
    return [cv[0], cv[1], cv[2], cv[3], -cv[4]]


def _current_weights(report: "dict | None") -> "dict[str, float]":
    """وزن‌های مرجعِ فعلی از گزارش (فقط خوانده می‌شود — هرگز mutate نمی‌شود)."""
    w = (report or {}).get("weights") or {}
    return {c: _comp(w.get(c, _DEFAULT_WEIGHTS[c])) for c in COMPONENT_ORDER}


def _finish(result: dict, write: bool, out_path) -> dict:
    """نوشتنِ اتمیکِ advisory JSON (فقط اگر write). تست‌ها همیشه out_path موقت می‌دهند."""
    if write:
        target = Path(out_path) if out_path else opslib.STATE_DIR / "fisher-latest.json"
        with opslib.LockedJson(target) as lj:
            lj.write(result)
    return result


def compute_fisher(report: "dict | None" = None, eps: float = 1e-3, eta: float = 0.1,
                   write: bool = False, out_path=None) -> dict:
    """متریکِ فیشرِ تجربی روی مؤلفه‌های fitness + گامِ طبیعیِ advisory.

    report=None → lazy `import fitness`؛ report = fitness.compute(write=False).
    G = (1/N) Σ g_c g_cᵀ (5×5)؛ Gr = G + eps·I (regularized → min-eig ≥ eps).
    numpy: cond = λ_max/λ_min؛ natural_step = eta·Gr⁻¹·mean_g؛
           advisory = clip(current + step, ≥0) سپس rescale تا Σadvisory == Σcurrent.
    خروجی صرفاً advisory است؛ هیچ وزنِ واقعی‌ای تغییر نمی‌کند (I4/I6)."""
    if report is None:
        import fitness  # lazy — مسیرِ synthetic/تست هیچ وابستگی‌ای به fitness/fs ندارد
        report = fitness.compute(write=False)

    current_w = _current_weights(report)
    cells = (report or {}).get("cells") or {}

    grads: "list[list[float]]" = []
    for _biz, cell in cells.items():
        cv = component_vector(cell)
        if cv is None:
            continue
        grads.append(_signed_gradient(cv))
    n = len(grads)

    base = {
        "ts": opslib.now_iso(),
        "cells_used": n,
        "fisher_condition_number": None,
        "current_weights": current_w,
        "advisory_weights": None,
        "natural_step": None,
        "eta": float(eta),
        "eps": float(eps),
        "advisory_only": True,
        "authoritative": False,
        "numpy_used": _HAS_NUMPY,
        "note": "",
    }

    if n == 0:
        base["note"] = "no-cells (shadow) — منتظر دادهٔ EXPERIENCE"
        return _finish(base, write, out_path)

    if not _HAS_NUMPY:
        base["numpy_used"] = False
        base["note"] = ("numpy در دسترس نیست — fallback: متریکِ فیشر و advisory حساب نمی‌شود "
                        "(cells شمرده شد، عددها صادقانه None)")
        return _finish(base, write, out_path)

    try:
        M = np.asarray(grads, dtype=float)              # (N, 5) — هر ردیف g_c
        mean_g = M.mean(axis=0)                          # (5,) — ∇E متوسط
        G = (M.T @ M) / float(n)                          # فیشرِ تجربی 5×5 (PSD)
        Gr = G + float(eps) * np.eye(5)                   # regularized → PD
        eig = np.linalg.eigvalsh(Gr)                      # صعودی؛ min ≥ eps > 0
        lo, hi = float(eig[0]), float(eig[-1])
        cond = (hi / lo) if lo > 0 else float("inf")
        step = float(eta) * np.linalg.solve(Gr, mean_g)   # η·Gr⁻¹·∇E — گامِ طبیعی
        cur = np.array([current_w[c] for c in COMPONENT_ORDER], dtype=float)
        adv = np.clip(cur + step, 0.0, None)              # وزن ≥ 0
        sum_cur, sum_adv = float(cur.sum()), float(adv.sum())
        if sum_adv > 0 and sum_cur > 0:
            adv = adv * (sum_cur / sum_adv)               # حفظِ مقیاس: Σadvisory == Σcurrent
        else:
            adv = cur.copy()                              # همه صفر → fallback به وزنِ فعلی
        base["fisher_condition_number"] = float(round(cond, 6))
        base["natural_step"] = [float(x) for x in step]
        base["advisory_weights"] = {c: float(adv[i]) for i, c in enumerate(COMPONENT_ORDER)}
        base["note"] = ("advisory natural-gradient (Fisher metric) — پیشنهادی و غیرمرجع؛ "
                        "هیچ وزنِ واقعی‌ای تغییر نمی‌کند (I4/I6)")
    except Exception as e:  # noqa: BLE001 — fail-soft: مشاهده‌گر هرگز حلقه را نمی‌کشد
        base["fisher_condition_number"] = None
        base["advisory_weights"] = None
        base["natural_step"] = None
        base["note"] = f"fisher numpy path failed fail-soft: {type(e).__name__}: {e}"

    return _finish(base, write, out_path)


if __name__ == "__main__":
    print(json.dumps(compute_fisher(write="--dry" not in sys.argv), ensure_ascii=False, indent=2))
