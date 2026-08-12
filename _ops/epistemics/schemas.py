"""schemas.py — قراردادهای دادهٔ موتورِ آزمونِ معرفتی (ADR-039).

این دومین کابینِ Pydanticِ _ops است (ADR-037 amend). Pydantic v2:
  strict=True · extra="forbid" · frozen=True
هم‌الگو با hypothesis_engine/impl/schemas.py، اما TCB-grade و fail-closed.
Pydantic در کلِ epistemics فقط در همین یک فایل مجاز است؛ بقیهٔ فایل‌های کابین stdlib-only‌اند.

سخت‌مرزها (ADR-039 §7) که در سطحِ schema تضمین می‌شوند:
  - may_execute همیشه False (هیچ‌گاه True نمی‌شود — validator بعدی هم باز-check می‌کند).
  - sandbox_profile همیشه no_network (هیچ مقدارِ دیگری در enum نیست).
  - requested_authority همیشه propose (execute اصلاً در enum نیست؛ ADR-034 propose-only).
  - testability > 0 (ادعای non-testable در زمانِ ساخت رد می‌شود).
  - prior ∈ (0,1) (dogmatic 0/1 ممنوع).
  - operational_definition / competing_claim_ids(≥1) / predictions(≥1) / falsifier الزامی.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Enums — مجموعهٔ مجازِ بسته (fail-closed: مقدارِ خارج از مجموعه رد می‌شود)
# ---------------------------------------------------------------------------
class ClaimType(str, Enum):
    """انواعِ ادعای مجاز (ADR-039 §6)."""
    DESCRIPTIVE = "descriptive"
    CAUSAL = "causal"
    PREDICTIVE = "predictive"
    COMPARATIVE = "comparative"
    SAFETY = "safety"


class Authority(str, Enum):
    """تنها مقدارِ مجاز: propose. execute ممنوع (ADR-034 propose-only)."""
    PROPOSE = "propose"


class SandboxProfile(str, Enum):
    """تنها مقدارِ مجاز: no_network. write فقط در outputs/epistemics/."""
    NO_NETWORK = "no_network"


class TestDesign(str, Enum):
    """نوعِ طرحِ آزمون — ماتریسِ مداخلهٔ علّی §4."""
    ABLATION = "ablation"
    RULE_REVERSAL = "rule_reversal"
    HOLDOUT = "holdout"
    COUNTERFACTUAL = "counterfactual"
    CHAOS = "chaos"


class GateOutcome(str, Enum):
    """خروجیِ گیتِ deterministic. INCONCLUSIVE هرگز به SUPPORTED تبدیل نمی‌شود."""
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    BLOCKED = "BLOCKED"


class PredictionDirection(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    UNCHANGED = "unchanged"
    CHANGE = "change"


# ---------------------------------------------------------------------------
# Config مشترک: strict + forbid + frozen
# ---------------------------------------------------------------------------
_STRICT_FROZEN = ConfigDict(strict=True, extra="forbid", frozen=True)


# ---------------------------------------------------------------------------
# مدل‌های پایه
# ---------------------------------------------------------------------------
class Prediction(BaseModel):
    """یک پیش‌بینیِ متمایزکننده (discriminating) — باید falsifiable باشد."""
    model_config = _STRICT_FROZEN

    variable: str = Field(min_length=1)
    direction: PredictionDirection
    operational_ref: str = Field(min_length=1)   # چگونه اندازه گرفته می‌شود
    quantile: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class Falsifier(BaseModel):
    """مشاهده‌ای که اگر رخ دهد، ادعا را رد می‌کند (قلبِ آزمون‌پذیری)."""
    model_config = _STRICT_FROZEN

    description: str = Field(min_length=1)
    operational_ref: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    threshold: str = Field(min_length=1)   # متن، مثلاً "discovery_B - discovery_A <= 0"


# ---------------------------------------------------------------------------
# مدل‌های اصلیِ زنجیرهٔ epistemic
# ---------------------------------------------------------------------------
class EpistemicClaim(BaseModel):
    """واحدِ معرفتیِ frozen. کلیدهای غیرقابل‌حذف توسط forbid + validators تضمین می‌شوند."""
    model_config = _STRICT_FROZEN

    claim_id: str = Field(min_length=1)
    claim_type: ClaimType
    operational_definition: str = Field(min_length=1)            # الزامی، غیرخالی
    competing_claim_ids: List[str] = Field(min_length=1)         # ≥1 فرضیهٔ رقیب
    predictions: List[Prediction] = Field(min_length=1)          # ≥1 پیش‌بینیِ متمایزکننده
    falsifier: Falsifier                                         # الزامی
    testability: float = Field(gt=0.0, le=1.0)                   # 0 → block در ساخت
    prior: float = Field(gt=0.0, lt=1.0)                         # بدونِ prior جزمی 0/1
    source_git_sha: str = Field(min_length=1)
    source_config_hash: str = Field(min_length=1)
    requested_authority: Authority = Authority.PROPOSE           # فقط propose
    maturity_target: Optional[str] = None                        # E0..E6 (اختیاری)

    @model_validator(mode="after")
    def _authority_invariant(self) -> "EpistemicClaim":
        # defense-in-depth: enum فقط propose دارد، اما صریحًا هم check می‌شود.
        if self.requested_authority is not Authority.PROPOSE:
            raise ValueError(
                "requested_authority must be 'propose'; 'execute' is forbidden (ADR-034)"
            )
        return self


class TestPlan(BaseModel):
    """طرحِ آزمونِ bounded. sandbox_profile به‌اجبار no_network است."""
    model_config = _STRICT_FROZEN

    plan_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    design: TestDesign
    sandbox_profile: SandboxProfile = SandboxProfile.NO_NETWORK  # forced
    interventions: List[str] = Field(default_factory=list)
    discriminating_prediction: Prediction
    falsifier: Falsifier
    max_runs: int = Field(gt=0)                                  # سقف در validator ↔ policy
    max_wall_seconds: int = Field(gt=0)
    max_cost_aud: float = Field(ge=0.0)
    seed_set: List[int] = Field(min_length=1)
    holdout: bool = False

    @model_validator(mode="after")
    def _force_no_network(self) -> "TestPlan":
        if self.sandbox_profile is not SandboxProfile.NO_NETWORK:
            raise ValueError("sandbox_profile must be 'no_network' (ADR-039 §7.3)")
        return self


class BindHashes(BaseModel):
    """hashهای binding یک receipt — بازتولیدپذیریِ کاملِ آزمون."""
    model_config = _STRICT_FROZEN

    git_sha: str = Field(min_length=1)
    material_hash: str = Field(min_length=1)
    config_hash: str = Field(min_length=1)
    environment_hash: str = Field(min_length=1)
    seed_set_hash: str = Field(min_length=1)
    command_hash: str = Field(min_length=1)
    artifact_hashes: Dict[str, str] = Field(default_factory=dict)


class EvidenceReceipt(BaseModel):
    """رسیدِ tamper-evident با زنجیرهٔ parent_receipt_hash (C2 آن را append می‌کند)."""
    model_config = _STRICT_FROZEN

    receipt_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    binds: BindHashes
    parent_receipt_hash: str = Field(min_length=1)   # GENESIS برای اولین
    canonical_payload_hash: str = Field(min_length=1)
    produced_by: str = Field(min_length=1)           # فقط producerِ مجاز (validator check)
    produced_at: str = Field(min_length=1)           # ISO8601
    verdict: str = Field(min_length=1)               # پیش‌ثبت؛ نهایی در GateDecision
    signature_b64: Optional[str] = None              # امضای segment در C2


class GateDecision(BaseModel):
    """تصمیمِ گیتِ deterministic. may_execute همیشه False (هیچ‌گاه True نمی‌شود)."""
    model_config = _STRICT_FROZEN

    decision_id: str = Field(min_length=1)
    receipt_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    outcome: GateOutcome
    reason_codes: List[str] = Field(default_factory=list)
    belief_delta_log_odds: float = Field(ge=-20.0, le=20.0)
    may_execute: bool = False                         # هرگز True
    maturity_claim: Optional[str] = None

    @model_validator(mode="after")
    def _fail_closed(self) -> "GateDecision":
        # سخت‌مرزِ ADR-039 §7.2: may_execute ثابتِ False.
        if self.may_execute is not False:
            raise ValueError("may_execute is hard-coded False (ADR-039 §7.2)")
        # fail-closed epistemics: INCONCLUSIVE نباید باور را تغییر دهد (§5).
        if self.outcome is GateOutcome.INCONCLUSIVE and self.belief_delta_log_odds != 0.0:
            raise ValueError(
                "INCONCLUSIVE must not change belief (belief_delta_log_odds must be 0.0)"
            )
        return self


# ---------------------------------------------------------------------------
# Provenance — یالِ DAG خودمختاری (ADR-039 §2، C2)
# ---------------------------------------------------------------------------
class Initiator(str, Enum):
    """آغازگرِ یک یالِ provenance."""
    SELF = "self"        # ارگانیسم خودش (telemetry → proposal)
    HUMAN = "human"      # دخالتِ مالک/انسان
    SYSTEM = "system"    # سیستم/زیرساخت


class ProvenanceEdge(BaseModel):
    """یک یالِ DAG خودمختاری (همان artifactِ توصیه‌شده در ممیزی #1).

    نکتهٔ صادقانه (ADR-039 §2): اگر هر یالِ پس از start دارای `human_prompt_id`
    یا `initiator==HUMAN` باشد، آن run دیگر شاهدِ self-initiation نیست —
    می‌تواند شاهدِ capability باشد ولی باید صادقانه برچسب بخورد.
    """
    model_config = _STRICT_FROZEN

    edge_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    plan_id: Optional[str] = None
    receipt_id: Optional[str] = None
    decision_id: Optional[str] = None
    trigger_source: str = Field(min_length=1)          # "telemetry" / "human_prompt" / ...
    initiator: Initiator
    human_prompt_id: Optional[str] = None              # پر بودن ⇒ human edge
    goal_id: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)
    approval_id: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    side_effects: List[str] = Field(default_factory=list)
    rollback_id: Optional[str] = None
    fencing_token: Optional[str] = None
