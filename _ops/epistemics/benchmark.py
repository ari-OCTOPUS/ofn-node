"""benchmark.py — harness آفلاینِ A/B/C (ADR-039 §10، Phase 2.6).

سه بازو را روی یک datasetِ synthetic می‌چرخاند و Go verdict می‌سازد. هیچ شبکه/فایلِ
زنده — تماماً در tmp. هدف: تولیدِ Go/No-Go صادقانه که C6/C7 را gating می‌کند.

  بازو A — evidence-only: فقط observable evidence را می‌بیند، بدونِ ledger.
  بازو B — +ledger: claim → plan → run → receipt (بدون discovery ranker).
  بازو C — +ranker: مثل B اما experiment را با experiment_selector.rank_by_discovery_value
           انتخاب می‌کند.

نکتهٔ صادقانه: «useful outcome» اینجا predeclared است (case.useful_for_discovery).
Go criteria در benchmark_metrics.go_no_go — threshold پیش‌فرض ۰.۰۵ (مالک قبل از run
real تثبیت می‌کند). خروجی یک GoVerdict + گزارش.
"""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from . import benchmark_metrics as M
from . import experiment_selector as SEL
from . import sandbox_runner as SR
from . import test_planner as TP
from .bayes import update_bayesian
from .policy import load_policy
from .schemas import (
    Authority, ClaimType, EpistemicClaim, EvidenceLink, ExecutionScope,
    Falsifier, Prediction, PredictionDirection, TestDesign, TestPlan, WorldMode,
)


@dataclass(frozen=True)
class Case:
    """یک موردِ benchmarkِ synthetic."""
    case_id: str
    evidence_summary: str
    ground_truth: bool                # آیا فرضیهٔ اصلی واقعاً درست است
    useful_for_discovery: bool        # predeclared
    metric_under_h: float             # metric قابل‌مشاهده اگر H درست باشد
    metric_under_not_h: float         # اگر H غلط باشد
    pursued_false: int = 0
    useful_from_false: int = 0


# ۸ موردِ synthetic — چهار گروه (درست/مفید، درست/کم‌فایده، غلط/مفید، غلط/کم‌فایده)
DEFAULT_CASES: Tuple[Case, ...] = (
    Case("c-01", "strong signal A>B", True, True, 0.72, 0.30),
    Case("c-02", "clear improvement", True, True, 0.68, 0.35),
    Case("c-03", "marginal effect", True, False, 0.52, 0.48),
    Case("c-04", "negligible delta", True, False, 0.51, 0.49),
    Case("c-05", "wrong but explores dead-end fast", False, True,
         0.40, 0.55, pursued_false=1, useful_from_false=1),
    Case("c-06", "wrong, cheap to refute", False, True,
         0.38, 0.60, pursued_false=1, useful_from_false=1),
    Case("c-07", "wrong and noisy", False, False, 0.45, 0.50),
    Case("c-08", "wrong, low signal", False, False, 0.42, 0.52),
)


def _claim_for(case: Case) -> EpistemicClaim:
    return EpistemicClaim(
        claim_id=f"CLM-{case.case_id}", claim_type=ClaimType.CAUSAL,
        operational_definition=f"B beats A: {case.evidence_summary}",
        competing_claim_ids=["CLM-null"],
        predictions=[Prediction(variable="metric", direction=PredictionDirection.INCREASE,
                                operational_ref="holdout mean")],
        falsifier=Falsifier(description="metric under H not higher",
                            operational_ref="holdout", metric="metric",
                            threshold="metric_H - metric_notH <= 0"),
        testability=0.8, prior=0.5,
        source_git_sha="bench", source_config_hash="bench",
        requested_authority=Authority.PROPOSE,
        world_mode=WorldMode.HYPOTHESIS,
        execution_scope=ExecutionScope.SANDBOX_ONLY,
        evidence_for=[EvidenceLink(evidence_id=f"ef-{case.case_id}",
                                   source_type="fixture", source_ref="bench/fixtures",
                                   trust_level="verified", relevance=0.6)],
    )


def _plan_for(case: Case) -> TestPlan:
    return TestPlan(
        plan_id=f"P-{case.case_id}", claim_id=f"CLM-{case.case_id}",
        design=TestDesign.HOLDOUT,
        discriminating_prediction=Prediction(variable="metric",
                                             direction=PredictionDirection.INCREASE,
                                             operational_ref="holdout mean"),
        falsifier=Falsifier(description="x", operational_ref="r", metric="m",
                            threshold="t"),
        max_runs=3, max_wall_seconds=5, max_cost_aud=0.1, seed_set=[1, 2, 3],
    )


def _experiment_fn(case: Case):
    """تابعِ آزمونِ no_network: metric را از fixture (همان case) برمی‌گرداند."""
    def _fn(spec):
        return {"metric": case.metric_under_h if case.ground_truth
                else case.metric_under_not_h}
    return _fn


def _falsifier_check(raw: dict) -> bool:
    """falsifier: اگر metric پایین باشد (زیر ۰.۵)، فرضیه falsified."""
    return float(raw.get("metric", 0.0)) < 0.5


# ---------------------------------------------------------------------------
# سه بازو
# ---------------------------------------------------------------------------
def arm_a_evidence_only(cases: Tuple[Case, ...]) -> List[M.Outcome]:
    """فقط evidence را می‌بیند؛ پیش‌بینیِ خام بدون ledger."""
    out = []
    for c in cases:
        # evidence-only: confidence بر اساسِ evidence_summary (ساده: اگر 'strong'/'clear' → بالا)
        conf = 0.7 if any(w in c.evidence_summary for w in ("strong", "clear", "improvement")) else 0.5
        actual = 1.0 if c.ground_truth else 0.0
        out.append(M.Outcome(
            case_id=c.case_id, arm="A", predicted_prob=conf, actual_outcome=actual,
            had_useful_finding=c.useful_for_discovery, claim_count=1,
            unsupported_claims=0 if conf < 0.9 else 1,
            pursued_false_hypotheses=0, useful_from_false=0,
            label_leakage_events=0, cost=0.0, had_external_effect=False))
    return out


def _arm_ledger(cases, *, use_ranker: bool, store_path: Path, state_dir: Path,
                arm: str) -> List[M.Outcome]:
    """بازو B/C: claim → plan → run → receipt → bayes."""
    out = []
    policy = load_policy()
    # receipt_store را روی tmp confine کن
    import epistemics.receipt_store as RS
    RS._ALLOWED_ROOTS = (store_path.parent,)
    for c in cases:
        claim = _claim_for(c)
        plan = _plan_for(c)
        exp_type = "fixture_query"
        # بازو C: discovery ranker — در این dataset تفاوتی ندارد چون یک experiment
        # داریم، ولی مسیرِ rank_by_discovery_value صدا زده می‌شود (coverage).
        if use_ranker:
            cands = (SEL.ExperimentSpec(experiment_id=f"exp-{c.case_id}",
                                        type=exp_type, cost=0.05,
                                        has_preregistered_falsifier=True),)
            ranked = SEL.rank_by_discovery_value(cands)
            exp_type = ranked[0].type
        try:
            spec = TP.plan_run(claim=claim, plan=plan, experiment_type=exp_type,
                               experiment_id=f"exp-{c.case_id}",
                               falsifier_check=_falsifier_check, policy=policy)
            res = SR.run(spec, _experiment_fn(c), store_path=store_path,
                         state_dir=state_dir, produced_by="epistemic_benchmark")
            # posterior از receipt/falsification
            if res.falsified:
                conf = 0.2
            elif res.ok:
                delta = update_bayesian(prior=0.5, p_e_given_h=0.7,
                                        p_e_given_not_h=0.4, clip_log_odds=6.0)
                from .bayes import posterior_from_delta
                conf = posterior_from_delta(0.5, delta)
            else:
                conf = 0.5   # inconclusive
            actual = 1.0 if c.ground_truth else 0.0
            # unsupported claim: اگر confidence بالا ولی evidence ضعیف
            unsupp = 1 if (conf > 0.8 and not c.ground_truth) else 0
            out.append(M.Outcome(
                case_id=c.case_id, arm=arm, predicted_prob=conf,
                actual_outcome=actual, had_useful_finding=c.useful_for_discovery,
                claim_count=1, unsupported_claims=unsupp,
                pursued_false_hypotheses=c.pursued_false,
                useful_from_false=c.useful_from_false,
                label_leakage_events=0, cost=0.05, had_external_effect=False))
        except Exception:  # noqa: BLE001
            out.append(M.Outcome(case_id=c.case_id, arm=arm, predicted_prob=0.5,
                                 actual_outcome=1.0 if c.ground_truth else 0.0,
                                 claim_count=1, unsupported_claims=1, cost=0.05))
    return out


@dataclass(frozen=True)
class BenchmarkReport:
    verdict: M.GoVerdict
    arm_a: List[M.Outcome] = field(default_factory=list)
    arm_b: List[M.Outcome] = field(default_factory=list)
    arm_c: List[M.Outcome] = field(default_factory=list)
    brier_a: float = 0.0
    brier_c: float = 0.0
    n_cases: int = 0


def run_benchmark(cases: Tuple[Case, ...] = DEFAULT_CASES, *,
                  success_threshold: float = 0.05,
                  budget_ceiling: float = 1.0) -> BenchmarkReport:
    """سه بازو را بچرخان و Go verdict بساز. تماماً در tmp، آفلاین."""
    with tempfile.TemporaryDirectory(prefix="epi-bench-") as td:
        tdp = Path(td)
        store_root = tdp / "outputs" / "epistemics"
        store_root.mkdir(parents=True, exist_ok=True)
        store_path = store_root / "receipts.jsonl"

        a = arm_a_evidence_only(cases)
        b = _arm_ledger(cases, use_ranker=False, store_path=store_path,
                        state_dir=tdp, arm="B")
        c = _arm_ledger(cases, use_ranker=True, store_path=store_path,
                        state_dir=tdp, arm="C")

        verdict = M.go_no_go(arm_a=a, arm_c=c,
                             success_threshold=success_threshold,
                             budget_ceiling=budget_ceiling)
        return BenchmarkReport(
            verdict=verdict, arm_a=a, arm_b=b, arm_c=c,
            brier_a=M.brier_score(a), brier_c=M.brier_score(c),
            n_cases=len(cases),
        )


def format_report(rep: BenchmarkReport) -> str:
    v = rep.verdict
    lines = [
        f"# Epistemic A/B/C Benchmark — {rep.n_cases} cases",
        f"",
        f"## Go/No-Go verdict: {'✅ GO' if v.ok else '🛑 NO-GO'}",
        f"reason: {v.reason}",
        f"",
        f"## Criteria",
    ]
    for k, val in v.criteria.items():
        lines.append(f"  · {k}: {val}")
    lines += [
        f"",
        f"## Metrics",
        f"  · Brier A: {round(rep.brier_a, 4)} · Brier C: {round(rep.brier_c, 4)}",
        f"  · UFBR A: {round(M.ufbr(rep.arm_a), 4)} · UFBR C: {round(M.ufbr(rep.arm_c), 4)}",
        f"  · leakage A: {round(M.leakage_rate(rep.arm_a), 4)} · leakage C: {round(M.leakage_rate(rep.arm_c), 4)}",
        f"  · unsupported A: {round(M.unsupported_claim_rate(rep.arm_a), 4)} · unsupported C: {round(M.unsupported_claim_rate(rep.arm_c), 4)}",
        f"",
        f"## Honest note",
        f"این یک benchmark کوچکِ synthetic است (نمایشِ machinery، نه اثباتِ قابلیت).",
        f"Go criteria صادقانه اعمال شد؛ روی دادهٔ واقعیِ ۲۰-۴۰ موردی threshold باید",
        f"توسط مالک predeclare شود. C6/C7 (UI/live) فقط اگر Go پاس شود.",
    ]
    return "\n".join(lines)
