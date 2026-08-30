"""contracts.py — قراردادهای دادهٔ اندام کشف دنیای واقعی.

تمام dataclassهای اصلی. versioned schemaها در schemas/ وجود دارند و این
ماژول منبع حقیقتِ runtime است.

اصول:
- همهٔ اشیاء JSON-serializable هستند (as_dict).
- همه sourceها URL + tier + date دارند.
- هیچ secret/personal-data ای نگه داشته نمی‌شود (redaction در public_web).
- side-effect بیرونی صفر در این لایه.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

SCHEMA_VERSION = "world-discovery.v1"

# ──────────────────────────────────────────────────────────────────────
# Source tiers (بند ۷ پرامپت)
# ──────────────────────────────────────────────────────────────────────
TIER_A = "A"  # primary: official site, report, pricing, changelog, filing, paper, repo
TIER_B = "B"  # secondary reputable: news, industry analysis, academic, interview
TIER_C = "C"  # weak signal: forum, reddit, social, review, job posting
TIER_D = "D"  # unreliable: unsourced, SEO farm, aggregation, generated

# Tier‌هایی که می‌توانند کشف را تأیید کنند (به‌تنهایی)
CONFIRMING_TIERS = {TIER_A, TIER_B}
# Tier C فقط کاندیدا می‌سازد
CANDIDATE_TIERS = {TIER_C}
# Tier D هیچ رأی‌ای نمی‌دهد
REJECTED_TIERS = {TIER_D}


def _now_iso(now: Optional[datetime] = None) -> str:
    """ISO-8601 UTC. اگر now داده شد از آن استفاده می‌شود (testability)."""
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ──────────────────────────────────────────────────────────────────────
# Direction (جهت مالک)
# ──────────────────────────────────────────────────────────────────────
@dataclass
class Direction:
    """جهت مالک برای یک مأموریت کشف."""

    mission_id: str
    domain: str                       # e.g. "ai-competition"
    geography: str                    # e.g. "global"
    horizon_days: int                 # افق زمانی
    competitors: list[str]            # رقبای مرجع
    discovery_definition: str         # "C+D+E" و غیره
    min_sources: int = 2              # حداقل منبع مستقل
    desired_output: str = "testable-opportunity"
    competition_dims: list[str] = field(default_factory=list)
    action_level: str = "L3"          # L0..L4
    owner_source: str = "WORLD-DISCOVERY-CHARTER-2026-07-30.md"
    notes: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────
# Source
# ──────────────────────────────────────────────────────────────────────
@dataclass
class Source:
    """یک منبع مستند. همیشه URL + tier + date دارد."""

    url: str
    title: str
    tier: str                         # A/B/C/D
    source_date: Optional[str] = None  # تاریخ انتشار/رویداد منبع (YYYY-MM-DD)
    retrieved_at: Optional[str] = None  # زمان fetch
    snippet: str = ""                 # گزیدهٔ raw (UNTRUSTED)
    publisher: str = ""               # ناشر/سازمان
    is_primary: bool = False          # آیا منبع اولیه است
    notes: str = ""

    def as_dict(self) -> dict:
        return asdict(self)

    @property
    def domain(self) -> str:
        from .source_policy import domain_of
        return domain_of(self.url)


# ──────────────────────────────────────────────────────────────────────
# Observation (مشاهدهٔ خام)
# ──────────────────────────────────────────────────────────────────────
@dataclass
class Observation:
    """یک مشاهدهٔ خام از وب. ممکن است prompt-injected باشد → untrusted."""

    observation_id: str
    claim: str                        # ادعای استخراج‌شده (UNTRUSTED until verified)
    source: Source
    competitor: str = ""              # رقیبِ مربوط (در صورت وجود)
    raw_kind: str = ""                # feature/pricing/release/research/job/hype
    retrieved_at: str = ""
    injection_risk: bool = False      # اگر محتوای مشکوک یافت شد

    def as_dict(self) -> dict:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────
# Freshness
# ──────────────────────────────────────────────────────────────────────
@dataclass
class Freshness:
    observed_at: str
    oldest_source_date: Optional[str] = None
    newest_source_date: Optional[str] = None
    stale: bool = False
    days_span: Optional[int] = None

    def as_dict(self) -> dict:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────
# Novelty receipt (بند ۸)
# ──────────────────────────────────────────────────────────────────────
NOVELTY_FACT = "fact"
NOVELTY_RELATION = "relation"
NOVELTY_STRATEGIC = "strategic"
NOVELTY_ACTION = "action"


@dataclass
class NoveltyReceipt:
    searched_scopes: list[str] = field(default_factory=list)
    nearest_existing_items: list[str] = field(default_factory=list)
    overlap_score: float = 0.0          # 0..1
    novel_parts: list[str] = field(default_factory=list)
    not_novel_parts: list[str] = field(default_factory=list)
    novelty_kinds: list[str] = field(default_factory=list)   # subset of fact/relation/strategic/action
    decision: str = "unknown"           # novel|partially-novel|known|unknown
    method: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────
# Contradiction
# ──────────────────────────────────────────────────────────────────────
@dataclass
class Contradiction:
    claim: str
    counter_claim: str
    source: Source
    severity: str = "minor"            # minor|major
    notes: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────
# Discovery status (بند ۶ + ۹)
# ──────────────────────────────────────────────────────────────────────
STATUS_CANDIDATE = "candidate"
STATUS_TRIANGULATED = "triangulated"
STATUS_CONTESTED = "contested"
STATUS_FALSIFIED = "falsified"
STATUS_ACTIONABLE = "actionable"
STATUS_BLOCKED = "blocked"

# وضعیت‌هایی که یک discovery نهایی می‌توانند باشند
FINAL_STATUSES = {
    STATUS_TRIANGULATED,
    STATUS_CONTESTED,
    STATUS_FALSIFIED,
    STATUS_ACTIONABLE,
    STATUS_BLOCKED,
}


@dataclass
class Discovery:
    """یک کشف. بدون موارد اجباری معتبر نیست (بند ۶)."""

    schema_: str = SCHEMA_VERSION
    discovery_id: str = ""
    created_at: str = ""
    mission_id: str = ""
    domain: str = ""
    geography: str = ""
    claim: str = ""
    why_it_matters: str = ""
    direction_link: str = ""           # اتصال به جهت مالک
    novelty: dict = field(default_factory=dict)
    evidence: list[dict] = field(default_factory=list)        # list of Source.as_dict
    contradictions: list[dict] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    freshness: dict = field(default_factory=dict)
    competitors: list[dict] = field(default_factory=list)
    opportunity: dict = field(default_factory=dict)
    falsifier: str = ""
    next_experiment: str = ""
    owner_gate: str = ""
    status: str = STATUS_CANDIDATE

    def as_dict(self) -> dict:
        d = asdict(self)
        # dataclass field به‌صورت schema_ است ولی JSON key انتظار "schema" دارد
        d["schema"] = d.pop("schema_")
        return d

    def validate_required(self) -> list[str]:
        """بازگرداندن لیست موارد اجباریِ فقدان‌شده (بند ۶)."""
        missing = []
        if not self.claim:
            missing.append("claim")
        if not self.direction_link:
            missing.append("direction_link")
        if not self.created_at:
            missing.append("created_at")
        if not self.evidence:
            missing.append("evidence")
        if not any(s.get("url") for s in self.evidence):
            missing.append("evidence_url")
        if not self.freshness.get("observed_at"):
            missing.append("freshness.observed_at")
        if not self.falsifier:
            missing.append("falsifier")
        if not self.next_experiment:
            missing.append("next_experiment")
        if not self.owner_gate:
            missing.append("owner_gate")
        return missing

    def is_valid(self) -> bool:
        return len(self.validate_required()) == 0


# ──────────────────────────────────────────────────────────────────────
# Competitor row (بند ۱۰)
# ──────────────────────────────────────────────────────────────────────
@dataclass
class CompetitorRow:
    company: str
    strengths: list[str]
    weaknesses: list[str]
    evidence: list[dict] = field(default_factory=list)        # Source dicts
    novelty: str = "unknown"
    learn_for_octopus: list[str] = field(default_factory=list)
    do_not_imitate: list[str] = field(default_factory=list)
    real_use_evidence: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────
# Opportunity (بند ۱۱)
# ──────────────────────────────────────────────────────────────────────
OPP_TYPES = {
    "opportunity", "threat", "capability", "trend",
    "unmet-need", "market-gap", "competitor-weakness", "regulatory-change",
    "pricing-anomaly", "distribution-gap", "workflow-inefficiency",
    "new-public-dataset", "new-tender-pattern", "underserved-geography",
    "capability-composition", "tool-opportunity", "partnership-opportunity",
    "customer-acquisition-signal", "operational-risk", "ai-architecture-insight",
}


@dataclass
class Opportunity:
    type: str                          # one of OPP_TYPES
    claim: str
    estimated_value: Optional[str] = None
    time_to_test_days: Optional[int] = None
    reversibility: str = "high"        # high|medium|low
    confidence: float = 0.0            # 0..1
    discovery_id: str = ""
    asymmetry: str = ""                # مزیت نامتقارن اختاپوس
    scores: dict = field(default_factory=dict)
    evidence_strength: int = 0         # 0..5
    novelty: int = 0                   # 0..5
    owner_alignment: int = 0           # 0..5
    potential_value: int = 0           # 0..5
    time_to_evidence: int = 0          # 0..5
    reversibility_score: int = 0       # 0..5
    competitive_asymmetry: int = 0     # 0..5
    execution_readiness: int = 0       # 0..5
    uncertainty_penalty: int = 0       # 0..5
    risk_penalty: int = 0             # 0..5

    def as_dict(self) -> dict:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────
# Experiment (بند ۱۲)
# ──────────────────────────────────────────────────────────────────────
EXP_E0 = "E0"  # فقط داده عمومی
EXP_E1 = "E1"  # artifact واقعی بدون ارسال
EXP_E2 = "E2"  # draft تعامل، ارسال با رأی
EXP_E3 = "E3"  # تعامل واقعی، فقط با رأی تازه
EXP_E4 = "E4"  # خرج/قرارداد، بدون رأی ممنوع

ALLOWED_EXP_LEVELS = {EXP_E0, EXP_E1, EXP_E2, EXP_E3, EXP_E4}


@dataclass
class Experiment:
    schema_: str = "world-discovery.experiment.v1"
    experiment_id: str = ""
    discovery_id: str = ""
    level: str = EXP_E0
    hypothesis: str = ""
    baseline: str = ""
    observable_metric: str = ""
    target: str = ""
    deadline: str = ""
    public_data_required: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    owner_gate: str = ""
    expected_evidence: str = ""
    falsifier: str = ""
    stop_condition: str = ""
    cost_ceiling: str = "0 AUD"
    privacy_boundary: str = "no-personal-data"
    rollback: str = ""

    def as_dict(self) -> dict:
        d = asdict(self)
        d["schema"] = d.pop("schema_")
        return d

    def validate(self) -> list[str]:
        problems = []
        if self.level not in ALLOWED_EXP_LEVELS:
            problems.append("invalid-level")
        if not self.hypothesis:
            problems.append("missing-hypothesis")
        if not self.falsifier:
            problems.append("missing-falsifier")
        if not self.observable_metric:
            problems.append("missing-metric")
        if not self.target:
            problems.append("missing-target")
        if not self.owner_gate:
            problems.append("missing-owner-gate")
        return problems


# ──────────────────────────────────────────────────────────────────────
# Owner Action Card (بند ۱۳) — L3/تلگرام
# ──────────────────────────────────────────────────────────────────────
@dataclass
class OwnerActionCard:
    schema_: str = "world-discovery.owner-action.v1"
    action_id: str = ""
    discovery_id: str = ""
    exact_action: str = ""             # دقیقاً چه کاری
    why_needed: str = ""
    expected_information_gain: str = ""
    risk: str = ""
    cost: str = "0 AUD"
    external_effect: bool = False
    channel: str = "telegram"          # telegram|none
    target_recipient: str = ""         # owner
    draft_message: str = ""            # متن draft پیام (L3)
    expires_at: str = ""
    default_without_approval: str = "do-not-execute"
    status: str = "BLOCKED_BY_OWNER"

    def as_dict(self) -> dict:
        d = asdict(self)
        d["schema"] = d.pop("schema_")
        return d


# ──────────────────────────────────────────────────────────────────────
# Mission metrics (بند ۱۸)
# ──────────────────────────────────────────────────────────────────────
@dataclass
class Metrics:
    candidates_found: int = 0
    candidates_deduplicated: int = 0
    source_independence_rate: float = 0.0
    primary_source_rate: float = 0.0
    freshness_rate: float = 0.0
    contradiction_search_rate: float = 0.0
    falsifiable_claim_rate: float = 0.0
    novel_candidate_rate: float = 0.0
    triangulated_discovery_count: int = 0
    contested_discovery_count: int = 0
    falsified_discovery_count: int = 0
    actionable_discovery_count: int = 0
    blocked_by_owner_count: int = 0
    external_effect_count: int = 0
    spend_amount: float = 0.0
    privacy_violation_count: int = 0
    unsupported_claim_count: int = 0
    duplicate_claim_count: int = 0
    time_to_first_valid_discovery: Optional[str] = None
    competitor_coverage: float = 0.0
    asymmetry_hypotheses: int = 0
    experiments_designed: int = 0
    experiments_with_falsifier: int = 0
    owner_direction_alignment: float = 0.0

    HARD_INVARIANTS = (
        "external_effect_count",
        "spend_amount",
        "privacy_violation_count",
        "unsupported_claim_count",
    )

    def check_hard_invariants(self) -> list[str]:
        """برگرداندان لیست invariant‌های نقض‌شده (همگی باید ۰ باشند)."""
        violations = []
        for inv in self.HARD_INVARIANTS:
            val = getattr(self, inv)
            if isinstance(val, (int, float)) and val != 0:
                violations.append(inv)
        return violations

    def as_dict(self) -> dict:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────
# Helper: build a discovery from parts (validation-friendly)
# ──────────────────────────────────────────────────────────────────────
def make_discovery_id(claim: str, mission_id: str) -> str:
    return "wd-" + _sha(f"{mission_id}|{claim}")


def make_action_id(discovery_id: str, exact_action: str) -> str:
    return "oac-" + _sha(f"{discovery_id}|{exact_action}")


def make_observation_id(claim: str, url: str) -> str:
    return "obs-" + _sha(f"{claim}|{url}")
