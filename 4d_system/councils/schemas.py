"""شوراها — قرارداد دادهٔ DecisionArtifact (octopus.decision.v1، سایه).

نگاشت وفادار به COUNCIL-MESH-v0.1 §قرارداد: claims/evidence_refs/
falsification_status/gates/capability_token/provenance + dissent حفظ می‌شود.
سایه = capability_token همیشه None؛ هیچ مسیری به اجرا ندارد.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

ARTIFACT_VERSION = "octopus.decision.v1"

# ضرایب امتیاز (COUNCIL-MESH §قوانین ضد-توهم) — P دروازه است نه وزنِ نرم:
# P≠1 ⇒ رد، فارغ از مجموع. نگاشت حروف (تفسیر وفادارِ این پیاده‌سازی):
#   E = پوشش شواهد (evidence coverage)      0.30
#   C = هم‌بستگی/استقلال منابع              0.20
#   R = بازتولیدپذیری                        0.15
#   P = انطباق سیاست (دروازهٔ دودویی)       0.15 (گیت)
#   D = رسیدگی به dissent                    0.10
#   K = وضعیت ابطال‌پذیری (falsification)   0.10
WEIGHTS = {"E": 0.30, "C": 0.20, "R": 0.15, "P": 0.15, "D": 0.10, "K": 0.10}


@dataclass
class Claim:
    claim_id: str
    text: str
    evidence_refs: list[str] = field(default_factory=list)
    falsification_status: str = "unfalsified"   # falsified | unfalsified | untestable


@dataclass
class SealedOpinion:
    """نظرِ مهرشده — ناشناس برای هم‌خانه‌ها؛ هویت فقط در provenanceِ کنترل‌شده."""
    digest: str                      # sha256 محتوای نظر (بدون نام)
    payload: dict[str, Any]          # opinion/evidence/confidence/dissent
    family: str                      # خانوادهٔ شواهد (برای تستِ استقلال)


@dataclass
class DecisionArtifact:
    schema_version: str
    artifact_id: str
    created_at: str
    council: str
    task: dict[str, Any]
    claims: list[Claim]
    evidence_refs: dict[str, str]    # ref_id → توصیف منبع (بدون راز)
    falsification_status: str
    gates: dict[str, Any]            # go/no-go + P + سایه
    capability_token: None           # سایه: همیشه None — مسیر اجرا وجود ندارد
    provenance: dict[str, Any]
    dissent: list[dict[str, Any]]
    scoring: dict[str, float]
    decision: dict[str, str]
    shadow: bool = True

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["claims"] = [c.__dict__ for c in self.claims]
        return d


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def score_opinions(sealed: list[SealedOpinion]) -> dict[str, float]:
    """امتیازِ ضد-توهم: اکثریت ساده وجود ندارد؛ consensusِ هم‌خانواده مستقل
    حساب نمی‌شود؛ confidenceِ بالا بیِ evidence ⇒ جریمهٔ scrutiny نه پاداش."""
    n = len(sealed) or 1
    evidence_counts = [len((s.payload.get("evidence") or [])) for s in sealed]
    confidences = [float(s.payload.get("confidence") or 0.0) for s in sealed]

    with_ev = sum(1 for c in evidence_counts if c > 0)
    E = with_ev / n

    families = {s.family for s, c in zip(sealed, evidence_counts) if c > 0}
    C = (len(families) / n) if n else 0.0     # استقلال خانواده‌ها

    R = sum(1 for s in sealed if s.payload.get("reproducible")) / n

    P = 1.0
    for s in sealed:
        if s.payload.get("policy_violation"):
            P = 0.0
            break

    has_dissent = any(s.payload.get("dissent") for s in sealed)
    addressed = any(s.payload.get("dissent_addressed") for s in sealed) or not has_dissent
    D = 1.0 if addressed else 0.0

    K = sum(1 for s in sealed
            if (s.payload.get("falsifiable") is True)) / n

    total = (WEIGHTS["E"] * E + WEIGHTS["C"] * C + WEIGHTS["R"] * R
             + WEIGHTS["P"] * P + WEIGHTS["D"] * D + WEIGHTS["K"] * K)

    # جریمهٔ scrutiny: confidence بالا وقتی evidence ضعیف است — نه امتیاز
    high_conf_low_ev = [i for i, (c, e) in enumerate(zip(confidences, evidence_counts))
                        if c >= 0.8 and e == 0]
    if high_conf_low_ev:
        total *= (1.0 - 0.10 * len(high_conf_low_ev))

    return {"E": round(E, 4), "C": round(C, 4), "R": round(R, 4),
            "P": round(P, 4), "D": round(D, 4), "K": round(K, 4),
            "total": round(max(0.0, total), 4),
            "rogue_confidence_no_evidence": len(high_conf_low_ev)}
