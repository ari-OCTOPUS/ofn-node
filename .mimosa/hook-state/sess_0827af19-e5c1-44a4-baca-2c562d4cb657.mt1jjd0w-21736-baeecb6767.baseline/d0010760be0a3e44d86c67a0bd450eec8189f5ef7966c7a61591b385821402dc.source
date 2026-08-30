#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_epistemic_runner.py — test_planner + sandbox_runner (ADR-039 C3, Plane-3).

مسیرِ کاملِ claim → plan → BoundedRunSpec → run → receipt را در tmp تست می‌کند.
هیچ شبکه/فایلِ زنده — experiment_fn یک callableِ تستی است.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from epistemics import experiment_selector as SEL  # noqa: E402
from epistemics import test_planner as TP  # noqa: E402
from epistemics import sandbox_runner as SR  # noqa: E402
from epistemics.policy import load_policy  # noqa: E402
from epistemics.schemas import (  # noqa: E402
    Authority, ClaimType, EpistemicClaim, ExecutionScope, Falsifier,
    Prediction, PredictionDirection, TestDesign, TestPlan, WorldMode,
)


def _claim(**over):
    base = dict(
        claim_id="CLM-1", claim_type=ClaimType.CAUSAL,
        operational_definition="B beats A on holdout.",
        competing_claim_ids=["CLM-null"],
        predictions=[Prediction(variable="discovery_rate",
                                direction=PredictionDirection.INCREASE,
                                operational_ref="holdout mean")],
        falsifier=Falsifier(description="x", operational_ref="r", metric="m",
                            threshold="t"),
        testability=0.8, prior=0.5, source_git_sha="abc1234",
        source_config_hash="deadbeefdeadbeef",
        requested_authority=Authority.PROPOSE,
        world_mode=WorldMode.HYPOTHESIS,
        execution_scope=ExecutionScope.SANDBOX_ONLY,
    )
    base.update(over)
    return EpistemicClaim(**base)


def _plan(**over):
    base = dict(
        plan_id="P-1", claim_id="CLM-1", design=TestDesign.HOLDOUT,
        discriminating_prediction=Prediction(variable="discovery_rate",
                                             direction=PredictionDirection.INCREASE,
                                             operational_ref="holdout mean"),
        falsifier=Falsifier(description="x", operational_ref="r", metric="m",
                            threshold="t"),
        max_runs=5, max_wall_seconds=10, max_cost_aud=0.5, seed_set=[1, 2, 3],
    )
    base.update(over)
    return TestPlan(**base)


def _policy():
    # policy.yaml از مسیرِ ماژول لود می‌شود
    return load_policy()


# ---------------------------------------------------------------------------
# test_planner
# ---------------------------------------------------------------------------
def t_planner_happy_path():
    c = _claim(); p = _plan()
    spec = TP.plan_run(
        claim=c, plan=p, experiment_type="historical_replay",
        experiment_id="exp-1", falsifier_check=lambda r: False,
        policy=_policy())
    assert spec.run_id.startswith("run-")
    assert spec.experiment_type == "historical_replay"
    assert spec.max_runs <= p.max_runs     # cap سخت‌گیرانه
    assert spec.seeds == (1, 2, 3)


def t_planner_rejects_forbidden_type():
    c = _claim(); p = _plan()
    try:
        TP.plan_run(claim=c, plan=p, experiment_type="network_scan",
                    experiment_id="e", falsifier_check=lambda r: False,
                    policy=_policy())
        raise AssertionError("network_scan باید رد شود")
    except TP.PlanError as exc:
        assert "forbidden" in str(exc)


def t_planner_rejects_unsafe_type():
    c = _claim(); p = _plan()
    try:
        TP.plan_run(claim=c, plan=p, experiment_type="bogus",
                    experiment_id="e", falsifier_check=lambda r: False,
                    policy=_policy())
        raise AssertionError("bogus باید رد شود")
    except TP.PlanError as exc:
        assert "unsafe" in str(exc)


def t_planner_rejects_non_hypothesis_claim():
    """claim با simulation (نه hypothesis) → PlanError از eligible."""
    c = _claim(world_mode=WorldMode.SIMULATION); p = _plan()
    try:
        TP.plan_run(claim=c, plan=p, experiment_type="historical_replay",
                    experiment_id="e", falsifier_check=lambda r: False,
                    policy=_policy())
        raise AssertionError("non-hypothesis claim باید رد شود")
    except TP.PlanError as exc:
        assert "world_mode" in str(exc)


def t_planner_caps_are_min_of_plan_and_policy():
    c = _claim()
    p = _plan(max_runs=100000)   # بزرگ‌تر از policy cap
    spec = TP.plan_run(claim=c, plan=p, experiment_type="fixture_query",
                       experiment_id="e", falsifier_check=lambda r: False,
                       policy=_policy())
    pol = _policy()
    assert spec.max_runs == min(100000, pol.caps.max_runs)


# ---------------------------------------------------------------------------
# sandbox_runner
# ---------------------------------------------------------------------------
def _run_in_tmp(spec_fn):
    """spec_fn(policy) -> spec؛ در یک tmp dir اجرا می‌کند (output-path safe)."""
    with tempfile.TemporaryDirectory(prefix="epi-runner-") as td:
        tdp = Path(td)
        # store_path زیرِ outputs/epistemics لازم است — tmp را شبیه‌سازی کن
        store_root = tdp / "outputs" / "epistemics"
        store_root.mkdir(parents=True, exist_ok=True)
        store_path = store_root / "receipts.jsonl"
        # ReceiptStore _check_confined مسیر را resolve می‌کند؛ tmp را allowed کن
        # با override کردن _ALLOWED_ROOTS برای این تست
        import epistemics.receipt_store as RS
        orig = RS._ALLOWED_ROOTS
        RS._ALLOWED_ROOTS = (store_root,)
        # state_dir روی tmp تا HALT فلگهای زنده چک نشوند
        try:
            return spec_fn(store_path, tdp)
        finally:
            RS._ALLOWED_ROOTS = orig


def t_runner_completes_and_produces_receipt():
    def body(store_path, tdp):
        c = _claim(); p = _plan()
        spec = TP.plan_run(claim=c, plan=p, experiment_type="historical_replay",
                           experiment_id="e", falsifier_check=lambda r: r.get("f"),
                           policy=_policy())
        res = SR.run(spec, lambda s: {"metric": 0.9, "f": False},
                     store_path=store_path, state_dir=tdp,
                     produced_by="epistemic_sandbox_runner")
        assert res.ok is True
        assert res.receipt is not None
        assert res.receipt.verdict == "not_falsified"
        assert res.falsified is False
        assert res.receipt.world_mode == "hypothesis"
        # receipt واقعاً در store نوشته شد
        assert store_path.is_file()
    _run_in_tmp(body)


def t_runner_falsifier_triggers_falsified():
    def body(store_path, tdp):
        c = _claim(); p = _plan()
        spec = TP.plan_run(claim=c, plan=p, experiment_type="historical_replay",
                           experiment_id="e",
                           falsifier_check=lambda r: r.get("metric", 0) < 0.2,
                           policy=_policy())
        res = SR.run(spec, lambda s: {"metric": 0.1},
                     store_path=store_path, state_dir=tdp)
        assert res.falsified is True
        assert res.receipt.verdict == "falsified"
    _run_in_tmp(body)


def t_runner_crash_yields_inconclusive_not_pass():
    """§11 #8: crash → INCONCLUSIVE، نه pass."""
    def boom(spec):
        raise RuntimeError("experiment blew up")
    def body(store_path, tdp):
        c = _claim(); p = _plan()
        spec = TP.plan_run(claim=c, plan=p, experiment_type="historical_replay",
                           experiment_id="e", falsifier_check=lambda r: False,
                           policy=_policy())
        res = SR.run(spec, boom, store_path=store_path, state_dir=tdp)
        assert res.reason == "crash"
        assert res.receipt.verdict == "inconclusive"
        assert res.falsified is False
    _run_in_tmp(body)


def t_runner_halt_fail_closed():
    """§11 #11: STOP/HALT → فقط receipt محدود، نه اجرا — اینجا halted برگرداند."""
    def body(store_path, tdp):
        c = _claim(); p = _plan()
        spec = TP.plan_run(claim=c, plan=p, experiment_type="historical_replay",
                           experiment_id="e", falsifier_check=lambda r: False,
                           policy=_policy())
        # یک فلگِ STOP در parentِ state_dir بساز
        (tdp.parent / "HALT-ALL").touch()
        try:
            res = SR.run(spec, lambda s: {"m": 1}, store_path=store_path,
                         state_dir=tdp)
            assert res.reason == "halted"
            assert res.receipt is None
        finally:
            (tdp.parent / "HALT-ALL").unlink(missing_ok=True)
    _run_in_tmp(body)


def t_runner_world_mode_carried_to_receipt():
    """label preservation: world_mode به receipt منتقل می‌شود."""
    def body(store_path, tdp):
        c = _claim(); p = _plan()
        spec = TP.plan_run(claim=c, plan=p, experiment_type="fixture_query",
                           experiment_id="e", falsifier_check=lambda r: False,
                           policy=_policy())
        res = SR.run(spec, lambda s: {}, store_path=store_path, state_dir=tdp,
                     world_mode="simulation")
        assert res.receipt.world_mode == "simulation"
    _run_in_tmp(body)


def t_runner_invalid_world_mode_defaults_to_hypothesis():
    def body(store_path, tdp):
        c = _claim(); p = _plan()
        spec = TP.plan_run(claim=c, plan=p, experiment_type="fixture_query",
                           experiment_id="e", falsifier_check=lambda r: False,
                           policy=_policy())
        res = SR.run(spec, lambda s: {}, store_path=store_path, state_dir=tdp,
                     world_mode="bogus")
        assert res.receipt.world_mode == "hypothesis"
    _run_in_tmp(body)


TESTS = [
    t_planner_happy_path,
    t_planner_rejects_forbidden_type,
    t_planner_rejects_unsafe_type,
    t_planner_rejects_non_hypothesis_claim,
    t_planner_caps_are_min_of_plan_and_policy,
    t_runner_completes_and_produces_receipt,
    t_runner_falsifier_triggers_falsified,
    t_runner_crash_yields_inconclusive_not_pass,
    t_runner_halt_fail_closed,
    t_runner_world_mode_carried_to_receipt,
    t_runner_invalid_world_mode_defaults_to_hypothesis,
]

if __name__ == "__main__":
    failed = 0
    for _t in TESTS:
        try:
            _t()
            print(f"  PASS  {_t.__name__}")
        except Exception as exc:
            import traceback
            print(f"  FAIL  {_t.__name__}: {exc}")
            traceback.print_exc()
            failed += 1
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(failed)
