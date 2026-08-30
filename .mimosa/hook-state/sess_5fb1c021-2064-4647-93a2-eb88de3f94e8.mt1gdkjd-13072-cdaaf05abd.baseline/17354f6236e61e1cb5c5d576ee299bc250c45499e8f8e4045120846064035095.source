"""test_planner.py — تبدیلِ claim+plan به run-specِ bounded (ADR-039 C3، Plane-2→3).

این لایهٔ مرزیِ بینِ Validate+Plan (Plane-2) و Bounded Exec (Plane-3) است. یک
EpistemicClaim و TestPlanِ اعتبارسنجی‌شده را می‌گیرد، صلاحیتِ آزمون را از طریقِ
experiment_selector بررسی می‌کند، و یک BoundedRunSpec می‌سازد که sandbox_runner اجرا
می‌کند. هیچ I/O، هیچ side-effect — فقط تصمیمِ برنامه‌ریزی.

fail-closed: هر شکست → PlanError (نه برگشتِ specِ ناقص).
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple

from . import experiment_selector as SEL
from .policy import PolicyConfig
from .schemas import EpistemicClaim, Prediction, TestPlan


class PlanError(Exception):
    """برنامه‌ریزیِ یک run شکست خورد (claim/plan نامجواز یا ineligible)."""


@dataclass(frozen=True)
class BoundedRunSpec:
    """مشخصاتِ concreteِ یک run برای sandbox_runner.

    falsifier_check: (raw_result: dict) -> bool؛ True یعنی فرضیه falsified شد.
    experiment_fn و falsifier_check توسط caller فراهم می‌شوند — runner فقط bound
    می‌کند (نه اجرای خودکارِ شبکه/فایل)."""
    run_id: str
    claim_id: str
    plan_id: str
    experiment_type: str           # تاییدِ membership در SAFE_EXPERIMENTS
    experiment_id: str
    seeds: Tuple[int, ...]
    max_runs: int
    max_wall_seconds: int
    max_cost_aud: float
    discriminating_prediction: Prediction
    falsifier_check: Callable[[dict], bool]
    extra: dict = field(default_factory=dict)


def plan_run(
    *,
    claim: EpistemicClaim,
    plan: TestPlan,
    experiment_type: str,
    experiment_id: str,
    falsifier_check: Callable[[dict], bool],
    policy: PolicyConfig,
    cost: float = 0.0,
    risk_penalty: float = 0.0,
    now: Optional[float] = None,
) -> BoundedRunSpec:
    """یک claim+plan را به BoundedRunSpec تبدیل کن.

    مراحل:
      ۱. نوعِ آزمون باید در SAFE_EXPERIMENTS و نه در FORBIDDEN باشد.
      ۲. eligible() صدا زده می‌شود (world_mode/scope/budget/risk/falsifier).
      ۳. caps از policy.min(plan.caps, policy.caps) — سخت‌گیرانه‌ترین برنده.
    """
    # ۱. نوعِ آزمون
    if SEL.is_forbidden_type(experiment_type):
        raise PlanError(f"forbidden experiment type: {experiment_type}")
    if not SEL.is_safe_type(experiment_type):
        raise PlanError(f"unsafe experiment type: {experiment_type}")

    # ۲. eligible (بررسیِ claim + experiment)
    exp = SEL.ExperimentSpec(
        experiment_id=experiment_id, type=experiment_type,
        cost=min(cost, 1.0), risk_penalty=risk_penalty,
        has_preregistered_falsifier=True,   # falsifier_check داریم → predeclared
    )
    decision = SEL.eligible(
        claim=claim, experiment=exp,
        remaining_budget=1.0,   # budget نسبی؛ capsِ قطعی در plan/policy
    )
    if not decision.ok:
        raise PlanError(f"ineligible: {decision.reason}")

    # ۳. caps سخت‌گیرانه (plan vs policy — کوچک‌ترین برنده)
    max_runs = min(plan.max_runs, policy.caps.max_runs)
    max_wall = min(plan.max_wall_seconds, policy.caps.max_wall_seconds)
    max_cost = min(plan.max_cost_aud, policy.caps.max_cost_aud)

    # run_id: deterministic از claim/plan/experiment + ts (replay-safe)
    ts = int(now if now is not None else time.time())
    seed_material = f"{claim.claim_id}|{plan.plan_id}|{experiment_id}|{ts}"
    run_id = "run-" + hashlib.sha256(seed_material.encode("utf-8")).hexdigest()[:12]

    return BoundedRunSpec(
        run_id=run_id,
        claim_id=claim.claim_id,
        plan_id=plan.plan_id,
        experiment_type=experiment_type,
        experiment_id=experiment_id,
        seeds=tuple(plan.seed_set),
        max_runs=max_runs,
        max_wall_seconds=max_wall,
        max_cost_aud=max_cost,
        discriminating_prediction=plan.discriminating_prediction,
        falsifier_check=falsifier_check,
    )
