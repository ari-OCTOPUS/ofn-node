# -*- coding: utf-8 -*-
"""قراردادهای دادهٔ chord — stdlib فقط (بدون pydantic؛ قراردادِ ارگانیسم).

همهٔ مقادیرِ ابعاد در [0,1] نرمال‌اند. «جهتِ خوب» را target تعیین می‌کند
(مثلاً operational_risk هدفش 0 است، evidence_quality هدفش 1).
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict


class Verdict:
    """نتیجهٔ داوری. ترتیبِ سخت‌گیری: BLOCK > REQUEST_APPROVAL > OBSERVE_MORE > UNKNOWN."""
    HEALTHY = "HEALTHY"
    OBSERVE_MORE = "OBSERVE_MORE"
    PROPOSE_PATCH = "PROPOSE_PATCH"
    REQUEST_APPROVAL = "REQUEST_APPROVAL"
    BLOCK = "BLOCK"
    UNKNOWN = "UNKNOWN"
    ALL = (HEALTHY, OBSERVE_MORE, PROPOSE_PATCH, REQUEST_APPROVAL, BLOCK, UNKNOWN)


# ابعادِ v0 — فقط کیفیتِ تصمیمِ عملیاتی (نه هوش/آگاهی).
DIMENSIONS = (
    "evidence_quality",    # کیفیت/پوششِ شواهد (لاگ، تست، خروجی واقعی)
    "test_health",         # سبزیِ تست‌های مرتبط
    "goal_alignment",      # هم‌راستایی با GOALS/mission
    "operational_risk",    # ریسکِ عملیاتی تغییر (هدف: 0)
    "reversibility",       # برگشت‌پذیری (worktree/flag/revert)
    "cost_budget",         # سهمِ بودجهٔ مصرفی/موردنیاز (هدف: 0)
    "uncertainty",         # عدم‌قطعیتِ مدل/داده (هدف: 0)
    "dependency_health",   # سلامتِ وابستگی‌ها (ollama/fugu/فایل‌ها/سرویس‌ها)
)

DEFAULT_TARGETS = {
    "evidence_quality": 1.0, "test_health": 1.0, "goal_alignment": 1.0,
    "operational_risk": 0.0, "reversibility": 1.0, "cost_budget": 0.0,
    "uncertainty": 0.0, "dependency_health": 1.0,
}

# ریسک و شواهد از «زیباییِ جوابِ LLM» مهم‌ترند — وزنِ بیشتر.
DEFAULT_WEIGHTS = {
    "evidence_quality": 1.5, "test_health": 1.5, "goal_alignment": 1.0,
    "operational_risk": 2.0, "reversibility": 1.5, "cost_budget": 0.75,
    "uncertainty": 1.25, "dependency_health": 1.0,
}

# سطوحِ حساسیتِ مشاهده — secret هرگز نباید این‌جا برسد (agentignore)؛ اگر رسید → BLOCK.
SENSITIVITY = ("public", "internal", "pii", "secret")

# سطحِ شواهدِ لایهٔ تحقیق (برای research_claims — نه هستهٔ عملیاتی).
EVIDENCE_LABELS = ("established", "supported", "hypothesis", "speculative")


def clamp01(x, default: float = 0.0) -> float:
    """هر ورودی → float در [0,1]؛ ورودیِ خراب → default (بی‌صدا سالم فرض نمی‌کنیم)."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return float(default)
    if v != v:  # NaN
        return float(default)
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def new_id(prefix: str) -> str:
    return f"{prefix}-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"


def sha256_of(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


@dataclass
class Observation:
    """یک مشاهدهٔ ساخت‌یافته با منبع (provenance اجباری)."""
    source_type: str                 # test|log|file|api|llm|telegram|manual
    source_ref: str                  # مسیر/شناسهٔ قابلِ‌ردگیری — خالی ممنوع
    payload_summary: str             # خلاصهٔ PII-امن؛ هرگز secret/مبلغ خام
    evidence_strength: float = 0.5   # [0,1] — llm پیش‌فرض ضعیف، تستِ واقعی قوی
    mission_id: str = ""
    observation_id: str = field(default_factory=lambda: new_id("OBS"))
    timestamp: str = field(default_factory=_now_iso)
    provenance: str = ""             # چه کسی/چه ابزاری تولید کرد
    contradictions: list = field(default_factory=list)  # شناسهٔ مشاهده‌های متناقض
    sensitivity_level: str = "internal"

    def validate(self) -> list:
        errs = []
        if not (self.source_type or "").strip():
            errs.append("source_type-empty")
        if not (self.source_ref or "").strip():
            errs.append("source_ref-empty (provenance is mandatory)")
        if self.sensitivity_level not in SENSITIVITY:
            errs.append(f"sensitivity-invalid:{self.sensitivity_level}")
        self.evidence_strength = clamp01(self.evidence_strength, 0.0)
        return errs

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class StateVector:
    """بردارِ حالتِ یک mission/جزء — فقط ابعادِ نرمالِ [0,1]."""
    values: dict                     # dim -> [0,1]
    weights: dict = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    targets: dict = field(default_factory=lambda: dict(DEFAULT_TARGETS))
    evidence_coverage: float = 0.0   # چه کسری از ابعاد شاهدِ واقعی دارند
    uncertainty: float = 1.0         # پیش‌فرض: نامطمئن (fail-closed)
    generated_from: list = field(default_factory=list)  # observation_ids
    dimensions: tuple = DIMENSIONS

    def validate(self) -> list:
        errs = []
        for d in self.dimensions:
            if d not in self.values:
                errs.append(f"missing-dim:{d}")
            if d not in self.weights:
                errs.append(f"missing-weight:{d}")
            elif not isinstance(self.weights[d], (int, float)) or self.weights[d] < 0:
                errs.append(f"negative-or-bad-weight:{d}")
            if d not in self.targets:
                errs.append(f"missing-target:{d}")
        for k in self.values:
            self.values[k] = clamp01(self.values[k], 0.0)
        for k in self.targets:
            self.targets[k] = clamp01(self.targets[k], 0.0)
        self.evidence_coverage = clamp01(self.evidence_coverage, 0.0)
        self.uncertainty = clamp01(self.uncertainty, 1.0)
        return errs

    def to_dict(self) -> dict:
        d = asdict(self)
        d["dimensions"] = list(self.dimensions)
        return d


@dataclass
class ChordAssessment:
    """خروجیِ داوری — رکوردِ قابلِ‌ممیزی؛ هرگز فرمانِ اجرا نیست."""
    mission_id: str
    weighted_distance: float
    component_gaps: dict
    confidence: float
    uncertainty: float
    evidence_summary: str
    verdict: str
    allowed_actions: list
    approval_required: bool
    recommended_next_probe: str
    reasons: list = field(default_factory=list)
    assessment_id: str = field(default_factory=lambda: new_id("CHA"))
    created_at: str = field(default_factory=_now_iso)
    schema: str = "chord.assessment.v0"
    shadow: bool = True              # v0: همیشه سایه — هیچ گیتِ زنده‌ای نیست

    def to_dict(self) -> dict:
        return asdict(self)
