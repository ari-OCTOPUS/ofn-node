# -*- coding: utf-8 -*-
"""ساختِ بردارِ حالت از مشاهده‌ها — محافظه‌کار و fail-closed.

قاعده‌ها:
- بُعدی که هیچ شاهدی ندارد → مقدارِ «بدبینانهٔ خنثی» (نه سالم): برای ابعادِ
  target=1 مقدارِ 0.5، برای target=0 مقدارِ 0.5 — و در coverage حساب نمی‌شود.
- evidence_coverage = میانگینِ وزنیِ قوتِ شواهد روی ابعادِ پوشش‌داده‌شده × نسبتِ پوشش.
- uncertainty از پراکندگیِ شواهدِ متناقض + کمبودِ پوشش می‌آید.
"""
from __future__ import annotations

from .schemas import (DIMENSIONS, DEFAULT_TARGETS, DEFAULT_WEIGHTS,
                      Observation, StateVector, clamp01)

# هر مشاهده می‌تواند برای یک یا چند بُعد «ادعا» داشته باشد:
# obs_dims = {"test_health": 1.0, "operational_risk": 0.2}
NEUTRAL_VALUE = 0.5


def build_state_vector(observations: list,
                       dim_claims: list | None = None,
                       weights: dict | None = None,
                       targets: dict | None = None) -> StateVector:
    """observations: list[Observation] — فقط برای provenance/قوت/تناقض.
    dim_claims: list[dict] هم‌طولِ observations؛ هر dict نگاشتِ dim→value ادعایی.
    (جداسازی عمدی است: مشاهده «چه دیدیم»، claim «به کدام بُعد می‌خورد».)
    """
    dim_claims = dim_claims or []
    obs_ids, contradictions = [], 0
    per_dim: dict = {d: [] for d in DIMENSIONS}

    for i, ob in enumerate(observations or []):
        if not isinstance(ob, Observation):
            continue
        errs = ob.validate()
        if errs:  # مشاهدهٔ بی‌منبع اصلاً وارد محاسبه نمی‌شود
            continue
        obs_ids.append(ob.observation_id)
        contradictions += len(ob.contradictions or [])
        claims = dim_claims[i] if i < len(dim_claims) and isinstance(dim_claims[i], dict) else {}
        for d, v in claims.items():
            if d in per_dim:
                per_dim[d].append((clamp01(v), clamp01(ob.evidence_strength)))

    values, covered, strength_acc = {}, 0, 0.0
    for d in DIMENSIONS:
        pts = per_dim[d]
        if not pts:
            values[d] = NEUTRAL_VALUE
            continue
        wsum = sum(s for _, s in pts) or 1e-9
        values[d] = sum(v * s for v, s in pts) / wsum
        covered += 1
        strength_acc += min(1.0, wsum / max(1, len(pts)))

    coverage_ratio = covered / len(DIMENSIONS)
    avg_strength = (strength_acc / covered) if covered else 0.0
    evidence_coverage = clamp01(coverage_ratio * avg_strength)

    # عدم‌قطعیت: پایه از کمبودِ پوشش + جریمهٔ تناقض (هر تناقض 0.15+، سقف 1).
    uncertainty = clamp01((1.0 - evidence_coverage) * 0.8 + 0.2 * min(1.0, contradictions * 0.75)
                          + (0.15 * contradictions if contradictions else 0.0))

    # بُعدِ uncertainty داخلِ خودِ بردار هم منعکس می‌شود (اگر claim صریح نبود).
    if not per_dim["uncertainty"]:
        values["uncertainty"] = uncertainty

    return StateVector(
        values=values,
        weights=dict(weights or DEFAULT_WEIGHTS),
        targets=dict(targets or DEFAULT_TARGETS),
        evidence_coverage=evidence_coverage,
        uncertainty=uncertainty,
        generated_from=obs_ids,
    )
