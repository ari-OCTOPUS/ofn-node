"""experiment_selector.py — انتخابگرِ آزمونِ sandbox-safe (ADR-039 §11, Phase 2.5).

بازبینیِ Hypothesis-Ledger صریحاً فهرستِ مجاز/ممنوع را تعریف کرد. این ماژول آن را
به‌صورتِ یک تابعِ eligible() پیاده می‌کند که fail-closed است: هر چیزی خارجِ
SAFE_EXPERIMENTS یا در FORBIDDEN_EXPERIMENTS → نامجواز.

هیچ اجرایی اینجا انجام نمی‌شود — فقط تصمیمِ صلاحیت. اجرای واقعی در sandbox_runner
(C3) و فقط برای انواعِ مجاز. این جدا کردن (تصمیم ≠ اجرا) همان invariant #10
(sandbox-approval != production-authorization) را در سطحِ کد تضمین می‌کند.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


# ── انواعِ مجاز (MVE-only، بازبینیِ Hypothesis-Ledger) ──
SAFE_EXPERIMENTS: frozenset = frozenset({
    "historical_replay",
    "fixture_query",
    "sandbox_simulation",
    "read_only_retrieval",
    "test_execution_with_mocked_tools",
})

# ── صراحتاً ممنون (اثرِ واقعی/حافظه/سیاست/شبکه/اعتبار) ──
FORBIDDEN_EXPERIMENTS: frozenset = frozenset({
    "network_scan",
    "real_world_outreach",
    "state_mutation",
    "credential_use",
    "production_tool_call",
    "memory_promotion",
    "policy_change",
})


@dataclass(frozen=True)
class ExperimentSpec:
    """مشخصاتِ یک آزمونِ نامزد برای انتخاب."""
    experiment_id: str
    type: str                       # باید در SAFE_EXPERIMENTS باشد
    cost: float = 0.0               # ∈ [0,1]؛ نسبی به budget
    risk_penalty: float = 0.0       # باید ۰ برای eligible
    has_preregistered_falsifier: bool = False
    safety_scope: str = "sandbox_only"   # read_only | sandbox_only | ...


@dataclass(frozen=True)
class SelectionDecision:
    """خروجیِ eligible(): ok=True یعنی مجاز برای اجرا در sandbox."""
    ok: bool
    reason: str
    experiment_id: str


def is_safe_type(exp_type: str) -> bool:
    """نوع مجاز است؟ (fail-closed: ناشناخته → False، نه True)."""
    return exp_type in SAFE_EXPERIMENTS


def is_forbidden_type(exp_type: str) -> bool:
    """صریحاً ممنون است؟"""
    return exp_type in FORBIDDEN_EXPERIMENTS


def eligible(
    *,
    claim,
    experiment: ExperimentSpec,
    remaining_budget: float = 1.0,
) -> SelectionDecision:
    """آیا این آزمون روی این claim مجاز است؟ (طبقِ بازبینیِ Hypothesis-Ledger).

    شرط‌ها (همه باید برقرار باشند):
      - claim.world_mode == "hypothesis" (نه reality — invariant #4)
      - claim.execution_scope == "sandbox_only"
      - experiment.type در SAFE_EXPERIMENTS
      - experiment.type NOT در FORBIDDEN_EXPERIMENTS (defense-in-depth)
      - experiment.cost <= remaining_budget
      - experiment.risk_penalty == 0
      - experiment.has_preregistered_falsifier (invariant: آزمونِ بی‌فalsifier آزمون نیست)

    `claim` یک EpistemicClaim است (world_mode/execution_scope دارد).
    """
    eid = experiment.experiment_id
    # ۱. label واقعیت ممنون
    wm = getattr(claim, "world_mode", None)
    wm_val = wm.value if hasattr(wm, "value") else wm
    if wm_val != "hypothesis":
        return SelectionDecision(False, f"world_mode={wm_val!r} != hypothesis", eid)
    # ۲. scope
    es = getattr(claim, "execution_scope", None)
    es_val = es.value if hasattr(es, "value") else es
    if es_val != "sandbox_only":
        return SelectionDecision(False, f"execution_scope={es_val!r} != sandbox_only", eid)
    # ۳/۴. نوعِ مجاز و نه ممنون
    if is_forbidden_type(experiment.type):
        return SelectionDecision(False, f"forbidden_type:{experiment.type}", eid)
    if not is_safe_type(experiment.type):
        return SelectionDecision(False, f"unsafe_type:{experiment.type}", eid)
    # ۵. budget
    if experiment.cost > remaining_budget:
        return SelectionDecision(
            False, f"cost {experiment.cost} > budget {remaining_budget}", eid)
    # ۶. risk
    if experiment.risk_penalty != 0.0:
        return SelectionDecision(
            False, f"risk_penalty={experiment.risk_penalty} != 0", eid)
    # ۷. falsifier پیش‌ثبت‌شده
    if not experiment.has_preregistered_falsifier:
        return SelectionDecision(False, "no_preregistered_falsifier", eid)
    return SelectionDecision(True, "eligible", eid)


def rank_by_discovery_value(
    experiments: Tuple[ExperimentSpec, ...],
    *,
    discovery_of=None,
) -> Tuple[ExperimentSpec, ...]:
    """مرتب‌سازیٔ نزولی بر اساس net_value (DiscoveryBlock).

    discovery_of: نگاشتِ experiment_id → DiscoveryBlock. آزمون‌های بدون discovery
    یا نامجواز در انتها می‌آیند. فقط نامزد می‌سازد؛ انتخابِ نهایی با eligible()."""
    def _key(exp: ExperimentSpec):
        if discovery_of and exp.experiment_id in discovery_of:
            db = discovery_of[exp.experiment_id]
            return (is_safe_type(exp.type) and not is_forbidden_type(exp.type),
                    getattr(db, "net_value", 0.0))
        return (is_safe_type(exp.type) and not is_forbidden_type(exp.type), 0.0)
    return tuple(sorted(experiments, key=_key, reverse=True))
