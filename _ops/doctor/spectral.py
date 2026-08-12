#!/usr/bin/env python3
"""spectral.py — M-2: سنسورِ طیفیِ read-only برای دکتر (additive، کنارِ mine).

claim F-Spectral (fusion-doctor-spectral-sense §۳): «بحرانیتِ طیفیِ گرافِ رویدادها
(σ≈1 و/یا شکافِ طیفیِ کوچک بینِ λ₁,λ₂) گلوگاه‌های واقعی را بهتر از heuristicِ mine()
پیش‌بینی می‌کند.»

از trace یک گرافِ G می‌سازد → L(G)=D−A → طیفِ {λ_i} + برآوردِ σ (شاخصِ بحرانیت).
گلوگاه = زیرگرافِ نزدیکِ گذارِ فاز (σ≈1 یا شکافِ طیفیِ کوچک = شکننده).
خروجی = همان proposal-eventِ RFC، هرگز اثر.

خطوطِ قرمز (§۵):
  • هیچ import/تماس به *_gate یا chrono production.
  • γ/σ هدفِ reward نشود (λ_persist دست‌نخورده منفی).
  • propose-only، production لمس‌نشده.
fail-soft: نبودِ numpy → fallback به mine() heuristic (دکترِ core بی‌وابستگی).
additive: mine() دست‌نخورده؛ spectral_mine یک متدِ جدا/اختیاری است.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent              # _ops/doctor
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

# λ_persist از doctor.py (دست‌نخورده منفی — §۵.۳) — تک‌منبع 2026-07-10
from doctor import LAMBDA_PERSIST  # noqa: E402

# Single-source spectral definitions -- legacy formula lives there now.
try:  # noqa: SIM105
    from spectral_definitions import (  # noqa: E402
        LEGACY_EPS,
        LEGACY_SIGMA_CAP,
        FORMULA_LEGACY_SIGMA,
        compute_legacy_sigma,
    )
except ImportError:  # هنگام بارگذاری به‌عنوان doctor.spectral
    from doctor.spectral_definitions import (  # noqa: E402
        LEGACY_EPS,
        LEGACY_SIGMA_CAP,
        FORMULA_LEGACY_SIGMA,
        compute_legacy_sigma,
    )


def build_event_graph(trace: dict) -> "tuple[list, int]":
    """از trace یک گراف می‌سازد. نودها = ارگان‌ها/منابعِ خطا. یال‌ها = هم‌وقوعی.
    ⚑ برای معمار: تعریفِ دقیقِ G باز است (§۷) — فعلاً نودها = ارگان‌ها با خطا."""
    organs = trace.get("organs", {})
    errors = trace.get("errors", [])
    nodes = list(organs.keys()) if isinstance(organs, dict) else ["_global"]
    n = max(1, len(nodes))
    node_idx = {name: i for i, name in enumerate(nodes)}
    edges = set()
    # یال بینِ هر دو ارگانی که هم‌زمان خطا داشتند (هم‌وقوعی = وابستگی)
    for err in errors:
        src = err.get("organ") if isinstance(err, dict) else None
        if src and src in node_idx:
            for other in nodes:
                if other != src:
                    edges.add((min(node_idx[src], node_idx[other]),
                               max(node_idx[src], node_idx[other])))
    return list(edges), n


def laplacian_spectrum(edges: list, n: int) -> "tuple[list, object]":
    """طیفِ {λ_i} از L(G)=D−A. خروجی: (eigenvalues_sorted, L_matrix)."""
    if not _HAS_NUMPY:
        return _spectrum_pure(edges, n)
    L = np.zeros((n, n))
    A = np.zeros((n, n))
    for (i, j) in edges:
        if i < n and j < n:
            A[i][j] = A[j][i] = 1.0
            L[i][i] += 1.0
            L[j][j] += 1.0
    L = L - A
    eigvals = np.linalg.eigvalsh(L)
    return sorted(float(e) for e in eigvals), L


def _spectrum_pure(edges, n):
    """طیف بدونِ numpy (تقریبی — فقط eigvalsِ یک ماتریسِ متقارن کوچک)."""
    # برای ماتریسِ کوچک (n≤۳) این فقط diagonal تقریبی می‌دهد — کافی برای fail-soft
    L = [[0.0] * n for _ in range(n)]
    for (i, j) in edges:
        if i < n and j < n:
            L[i][i] += 1.0
            L[j][j] += 1.0
            L[i][j] -= 1.0
            L[j][i] -= 1.0
    # diagonal فقط (تقریب)
    eigvals = sorted(L[k][k] for k in range(n))
    return eigvals, L


def spectral_gap(eigvals: list) -> float:
    """شکافِ طیفی = λ₂ − λ₁ (λ₁ همیشه ۰ برای گرافِ همبند). شکافِ کوچک = شکننده."""
    if len(eigvals) < 2:
        return 0.0
    return eigvals[1] - eigvals[0]


def _legacy_sigma_from_eigvals(eigvals: list) -> float:
    """Internal legacy helper: extracts lambda_2/lambda_max from eigvals, delegates
    to compute_legacy_sigma from spectral_definitions. Falls back to 0.0 when
    the delegation returns None (preserving historical behaviour for callers
    that always received a float)."""
    if not eigvals:
        return 0.0
    l_max = max(eigvals) or 1e-6
    l2 = eigvals[1] if len(eigvals) > 1 else l_max
    result = compute_legacy_sigma(l2, l_max, eps=LEGACY_EPS, cap=LEGACY_SIGMA_CAP)
    if result is not None:
        return result
    return 0.0


def estimate_sigma(eigvals: list) -> float:
    """برآوردِ σ (شاخصِ بحرانیت/SOC). σ≈1 = گذارِ فاز.
    تقریب: σ ∝ (λ_max / (λ₂ + ε)). ⚑ برای معمار: تعریفِ دقیق باز (§۷).
    Delegates to spectral_definitions.compute_legacy_sigma; identical public
    contract: always returns a float in [0, 10]."""
    return _legacy_sigma_from_eigvals(eigvals)


def spectral_mine(trace: dict) -> "dict | None":
    """سنسورِ طیفیِ read-only. از trace گراف → طیف → گلوگاه.
    خروجی = {bottleneck, evidence, severity} یا None — همان قراردادِ mine()، هرگز اثر.
    fail-soft: numpy نباشد → ساختار کار می‌کند ولی طیفِ تقریبی."""
    if not trace:
        return None
    edges, n = build_event_graph(trace)
    # ── گاردِ گرافِ دژنره (2026-07-25، شاهدِ زندهٔ ارگانیسم) ─────────────────────
    # یال در build_event_graph **فقط از «خطا»** ساخته می‌شود. پس ارگانیسمِ بی‌خطا
    # گرافِ بی‌یال می‌دهد → L(G)=۰ → همهٔ λها صفر → gap=0.000 و σ=1.00 →
    # near_critical ∧ fragile هر دو True → این سنسور **سلامتِ کامل را «critical»**
    # اعلام می‌کرد. گواه: ۸ RFCِ بایت‌به‌بایت یکسان با متنِ «σ≈1 (σ=1.00)؛ gap=0.000»
    # در صفِ زنده، در حالی که phi_tِ خودِ Box روی همان ارگانیسم در همان دقیقه
    # sigma=0.0 و spectral_gap=0.7321 داد (box-latest.json 2026-07-25T14:15:50).
    # بدونِ ساختارِ خطا هیچ ادعای طیفی معنا ندارد → سکوتِ صادق، نه هشدارِ ساختگی.
    if n < 2 or not edges:
        return None
    eigvals, L = laplacian_spectrum(edges, n)
    gap = spectral_gap(eigvals)
    sigma = estimate_sigma(eigvals)
    # گلوگاه: σ≈1 (گذار) یا شکافِ طیفیِ کوچک (شکننده)
    near_critical = abs(sigma - 1.0) < 0.3
    fragile = gap < 0.5 and n > 1
    if not near_critical and not fragile:
        return None   # ساختار پایدار است
    reason = []
    if near_critical:
        reason.append(f"σ≈1 (σ={sigma:.2f} = نزدیکِ گذارِ فاز/SOC)")
    if fragile:
        reason.append(f"شکافِ طیفیِ کوچک (gap={gap:.3f} = شکننده)")
    severity = "critical" if (near_critical and fragile) else "high"
    # reward-integrity: σ و gap توصیفی‌اند، نه هدف (λ_persist دست‌نخورده)
    score = -abs(sigma - 1.0) * 50 - (1.0 / (gap + 0.01)) * 5   # نزدیکِ گذار = بدتر
    return {"bottleneck": "؛ ".join(reason),
            "evidence": {"sigma": round(sigma, 3), "spectral_gap": round(gap, 4),
                         "eigvals": [round(e, 4) for e in eigvals[:5]],
                         "n_nodes": n, "n_edges": len(edges),
                         "numpy_used": _HAS_NUMPY,
                         "lambda_persist_unchanged": LAMBDA_PERSIST,
                         "score": round(score, 2)},
            "severity": severity}
