# -*- coding: utf-8 -*-
"""سیاستِ تعمیر — نگاشتِ (بردار + گیت + زمینه) → ChordAssessment.

مرزِ سخت (هم‌راستا با AUTONOMY-MATRIX «ردهٔ مهم» + allowlistِ mission_runner):
- پول/secret/حذف/ارسالِ بیرونی/کد-apply/ژنوم/schtasks → همیشه REQUEST_APPROVAL.
- allowed_actions هرگز شاملِ اجرای patch نیست (code.apply/code.patch ممنوعِ ساختاری).
- context["stop_organism"]=True یا مشاهدهٔ secret → BLOCK (fail-closed).
"""
from __future__ import annotations

from .metrics import component_gaps, top_gaps, weighted_distance
from .schemas import ChordAssessment, StateVector, Verdict, clamp01
from .uncertainty_gate import gate

# واژگانِ اکشن — زیرمجموعهٔ allowlistِ واقعیِ mission_runner + مشاهده.
SAFE_ACTIONS = ("observe.collect", "code.plan", "code.test", "code.diff",
                "doctor.review", "epistemics.review")
FORBIDDEN_ACTIONS = ("code.apply", "code.patch", "money.move", "secrets.read",
                     "external.send", "genome.write")

# پرچم‌های زمینه که ردهٔ «مهم» را فعال می‌کنند — مطابقِ دکترینِ vault.
IMPORTANT_CONTEXT_FLAGS = ("touches_money", "touches_secrets", "destructive",
                           "external_side_effect", "touches_genome",
                           "touches_credentials", "irreversible")

HEALTHY_DISTANCE = 0.15
HIGH_RISK = 0.60
LOW_REVERSIBILITY = 0.40


def assess(mission_id: str, vec: StateVector,
           context: dict | None = None,
           contradiction_count: int = 0) -> ChordAssessment:
    """داوریِ کامل. هرگز exception به بیرون نمی‌دهد مگر بردار از بیخ نامعتبر باشد."""
    context = dict(context or {})
    reasons: list = []

    # 0) BLOCK-های مطلق
    if context.get("stop_organism"):
        return _mk(mission_id, vec, 1.0, {}, Verdict.BLOCK, ["kill-switch present"],
                   ["observe.collect"], True, "wait for owner; do nothing")
    if context.get("secret_observation"):
        return _mk(mission_id, vec, 1.0, {}, Verdict.BLOCK,
                   ["secret-tainted observation must never enter chord"],
                   [], True, "purge input; check .agentignore boundaries")

    # 1) گیتِ عدم‌قطعیت — قبل از هر چیز
    g = gate(vec, contradiction_count=contradiction_count)
    dist = None
    try:
        dist = weighted_distance(vec)
        gaps = component_gaps(vec)
    except ValueError as e:
        return _mk(mission_id, vec, 1.0, {}, Verdict.UNKNOWN, [str(e)],
                   ["observe.collect"], False, "fix vector construction inputs")
    reasons.extend(g["reasons"])

    if not g["open"]:
        v = g["verdict_hint"] or Verdict.UNKNOWN
        probe = ("collect the missing evidence dimensions (read-only probe)"
                 if v == Verdict.UNKNOWN else
                 "run one read-only diagnostic and re-observe (24h logs / re-test)")
        return _mk(mission_id, vec, dist, gaps, v, reasons,
                   ["observe.collect"], False, probe)

    # 2) ردهٔ مهم — مستقل از فاصله
    important = [f for f in IMPORTANT_CONTEXT_FLAGS if context.get(f)]
    risk = clamp01(vec.values.get("operational_risk", 1.0), 1.0)
    rev = clamp01(vec.values.get("reversibility", 0.0), 0.0)
    if important:
        reasons.append("important-class context: " + ",".join(important))
        return _mk(mission_id, vec, dist, gaps, Verdict.REQUEST_APPROVAL, reasons,
                   ["observe.collect", "code.plan"], True,
                   "prepare evidence pack + reversible plan for owner vote")
    if risk >= HIGH_RISK or rev <= LOW_REVERSIBILITY:
        reasons.append(f"risk={risk:.2f} / reversibility={rev:.2f} → owner approval")
        return _mk(mission_id, vec, dist, gaps, Verdict.REQUEST_APPROVAL, reasons,
                   ["observe.collect", "code.plan", "code.test"], True,
                   "design smaller reversible slice; re-assess")

    # 3) سالم؟
    if dist <= HEALTHY_DISTANCE:
        reasons.append(f"distance={dist:.3f}<={HEALTHY_DISTANCE} with adequate evidence")
        return _mk(mission_id, vec, dist, gaps, Verdict.HEALTHY, reasons,
                   ["observe.collect"], False, "periodic re-observation only")

    # 4) شکافِ واقعی + کم‌ریسک + برگشت‌پذیر → پیشنهادِ patch کوچک (فقط پیشنهاد)
    worst = ", ".join(f"{d}({v['gap']:+.2f})" for d, v in top_gaps(vec, 3))
    reasons.append(f"meaningful gap; top: {worst}")
    return _mk(mission_id, vec, dist, gaps, Verdict.PROPOSE_PATCH, reasons,
               ["code.plan", "code.test", "code.diff", "doctor.review"], False,
               "draft smallest reversible patch; sandbox tests must pass first")


def _mk(mission_id, vec, dist, gaps, verdict, reasons,
        allowed, approval, probe) -> ChordAssessment:
    allowed = [a for a in allowed if a in SAFE_ACTIONS]  # ممنوع‌ها ساختاراً حذف
    conf = clamp01(vec.evidence_coverage * (1.0 - vec.uncertainty))
    ev = (f"coverage={vec.evidence_coverage:.2f} uncertainty={vec.uncertainty:.2f} "
          f"n_obs={len(vec.generated_from)}")
    return ChordAssessment(
        mission_id=mission_id or "MIS-UNSPECIFIED",
        weighted_distance=round(float(dist), 4) if dist is not None else 1.0,
        component_gaps=gaps, confidence=round(conf, 4),
        uncertainty=round(vec.uncertainty, 4), evidence_summary=ev,
        verdict=verdict, allowed_actions=allowed, approval_required=bool(approval),
        recommended_next_probe=probe, reasons=list(reasons),
    )
