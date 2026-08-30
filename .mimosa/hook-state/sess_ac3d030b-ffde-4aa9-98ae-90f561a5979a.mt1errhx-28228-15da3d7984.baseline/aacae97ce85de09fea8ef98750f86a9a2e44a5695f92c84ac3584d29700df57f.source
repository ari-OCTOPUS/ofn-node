#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_epistemic_invariants.py — Phase 2.5 MVE (بازبینیِ Hypothesis-Ledger, 2026-08-13).

سه قطعهٔ گمشدهٔ epistemic را pin می‌کند:
  ۱. WorldMode / ExecutionScope labels (ضدِ hallucination، invariant #4)
  ۲. ۱۰ invariant صریح و قابلِتست (invariants.py)
  ۳. ساختارِ ۸-بخشی: assumptions / evidence_for / evidence_against

همهٔ فیلدهای نو default دارند → backward-compatible با C1/C2. sandbox-only؛ هیچ
وصل‌شدنی به چت/tool/memory.
"""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from epistemics.schemas import (  # noqa: E402
    Assumption,
    Authority,
    ClaimType,
    EpistemicClaim,
    EvidenceLink,
    EvidenceReceipt,
    ExecutionScope,
    Falsifier,
    GateDecision,
    GateOutcome,
    Prediction,
    PredictionDirection,
    BindHashes,
    WorldMode,
)
import epistemics.invariants as INV  # noqa: E402
from epistemics.validator import validate_world_mode_consistency  # noqa: E402


def _prediction() -> Prediction:
    return Prediction(
        variable="discovery_rate",
        direction=PredictionDirection.INCREASE,
        operational_ref="holdout mean over S1 family",
    )


def _falsifier() -> Falsifier:
    return Falsifier(
        description="B does not beat A",
        operational_ref="holdout mean",
        metric="discovery_rate",
        threshold="discovery_B - discovery_A <= 0",
    )


def _claim(**over) -> EpistemicClaim:
    base = dict(
        claim_id="CLM-1",
        claim_type=ClaimType.CAUSAL,
        operational_definition="B discovers the deceptive optimum more often than A.",
        competing_claim_ids=["CLM-null"],
        predictions=[_prediction()],
        falsifier=_falsifier(),
        testability=0.8,
        prior=0.5,
        source_git_sha="abc1234",
        source_config_hash="deadbeefdeadbeef",
        requested_authority=Authority.PROPOSE,
    )
    base.update(over)
    return EpistemicClaim(**base)


def _binds() -> BindHashes:
    return BindHashes(
        git_sha="abc1234",
        material_hash="m" * 16,
        config_hash="c" * 16,
        environment_hash="e" * 16,
        seed_set_hash="s" * 16,
        command_hash="cmd" * 6,
        artifact_hashes={},
    )


def _receipt(**over) -> EvidenceReceipt:
    base = dict(
        receipt_id="R-1",
        plan_id="P-1",
        claim_id="CLM-1",
        binds=_binds(),
        parent_receipt_hash="GENESIS",
        canonical_payload_hash="x" * 16,
        produced_by="epistemic_sandbox_runner",
        produced_at="2026-08-13T00:00:00Z",
        verdict="pending",
    )
    base.update(over)
    return EvidenceReceipt(**base)


# ---------------------------------------------------------------------------
# قطعهٔ ۱: labels
# ---------------------------------------------------------------------------
def t_worldmode_enum_closed():
    """WorldMode دقیقاً ۵ مقدارِ بسته دارد؛ REALITY فقط برای runtime_truth بیرون است."""
    assert {m.value for m in WorldMode} == {
        "reality", "hypothesis", "simulation", "counterfactual", "fictional"
    }


def t_executionscope_enum_closed():
    """ExecutionScope دقیقاً ۴ مقدار دارد."""
    assert {m.value for m in ExecutionScope} == {
        "read_only", "sandbox_only", "approval_required", "prohibited"
    }


def t_claim_defaults_worldmode_hypothesis():
    """claimِ جدید پیش‌فرض HYPOTHESIS + SANDBOX_ONLY — هیچ‌گاه REALITY به‌صورت پیش‌فرض."""
    c = _claim()
    assert c.world_mode is WorldMode.HYPOTHESIS
    assert c.execution_scope is ExecutionScope.SANDBOX_ONLY


def t_reality_worldmode_forbidden_on_claim():
    """invariant #4: یک claimِ epistemic هرگز نمی‌تواند REALITY باشد (ضدِ hallucination)."""
    try:
        _claim(world_mode=WorldMode.REALITY)
        raise AssertionError("REALITY باید روی claim رد شود")
    except ValueError as exc:
        assert "REALITY" in str(exc) or "simulation" in str(exc)


def t_non_reality_worldmodes_allowed():
    """سایر labelها مجازند (claim می‌تواند simulation/counterfactual/fictional باشد)."""
    for wm in (WorldMode.HYPOTHESIS, WorldMode.SIMULATION,
               WorldMode.COUNTERFACTUAL, WorldMode.FICTIONAL):
        c = _claim(world_mode=wm)
        assert c.world_mode is wm


# ---------------------------------------------------------------------------
# قطعهٔ ۳: ساختارِ ۸-بخشی
# ---------------------------------------------------------------------------
def t_assumption_model_strict():
    """Assumption: assumption_id/text الزامی، status سه‌حالتی، forbid extra."""
    a = Assumption(assumption_id="a-1", text="adapter supports idempotency")
    assert a.status == "unverified"
    try:
        Assumption(assumption_id="a-1", text="x", bogus=True)  # type: ignore[call-arg]
        raise AssertionError("extra field باید forbid شود")
    except Exception:
        pass


def t_evidencelink_relevance_bounds():
    """EvidenceLink.relevance ∈ [0,1]؛ خارج رد می‌شود؛ trust_level سه‌حالتی."""
    el = EvidenceLink(evidence_id="e-1", source_type="test_artifact",
                      source_ref="tests/fixtures/r.json")
    assert el.trust_level == "unverified"
    assert el.relevance == 0.0
    el2 = EvidenceLink(evidence_id="e-2", source_type="runtime",
                       source_ref="state/x.json", trust_level="verified",
                       relevance=0.71)
    assert el2.relevance == 0.71
    try:
        EvidenceLink(evidence_id="e-3", source_type="x", source_ref="y",
                     relevance=1.5)
        raise AssertionError("relevance>1 باید رد شود")
    except Exception:
        pass


def t_full_8part_claim_constructs():
    """claim با assumptions + evidence_for + evidence_against ساخته می‌شود."""
    c = _claim(
        assumptions=[
            Assumption(assumption_id="a-1", text="idempotency works",
                       status="verified"),
            Assumption(assumption_id="a-2", text="replay is faithful",
                       status="unverified"),
        ],
        evidence_for=[
            EvidenceLink(evidence_id="ef-1", source_type="test_artifact",
                         source_ref="tests/fixtures/r.json",
                         trust_level="verified", relevance=0.71),
        ],
        evidence_against=[
            EvidenceLink(evidence_id="ea-1", source_type="runtime",
                         source_ref="state/probe.json",
                         trust_level="derived", relevance=0.3),
        ],
    )
    assert len(c.assumptions) == 2
    assert len(c.evidence_for) == 1
    assert len(c.evidence_against) == 1
    assert c.evidence_for[0].relevance == 0.71


# ---------------------------------------------------------------------------
# قطعهٔ ۲: ۱۰ invariant
# ---------------------------------------------------------------------------
def t_ten_invariants_registered():
    """دقیقاً ۱۰ invariant با idهای ۱..۱۰ و نام‌های یکتا."""
    assert INV.count() == 10
    assert [inv.id for inv in INV.ALL_INVARIANTS] == list(range(1, 11))
    names = INV.names()
    assert len(set(names)) == 10          # یکتا
    assert INV.BY_ID[1].name == "possible != true"
    assert INV.BY_ID[10].name == "sandbox-approval != production-authorization"


def t_every_invariant_has_statement_and_enforcement():
    """هر invariant statement غیرخالی + enforcement_point معتبر دارد."""
    valid_points = {"schema", "validator", "runtime", "advisory"}
    for inv in INV.ALL_INVARIANTS:
        assert inv.statement.strip(), f"invariant {inv.id} statement خالی"
        assert inv.enforcement_point in valid_points, f"invariant {inv.id} point بد"
        assert inv.enforced_by.strip(), f"invariant {inv.id} enforced_by خالی"


def t_structural_invariants_subset():
    """structural_invariants فقط schema-enforced ها را برمی‌گرداند (شامل #1,#4,#9,#10)."""
    s = INV.structural_invariants()
    ids = {inv.id for inv in s}
    for required in (1, 4, 9, 10):
        assert required in ids, f"invariant #{required} باید structural باشد"
    for inv in s:
        assert inv.enforcement_point == "schema"


# ---------------------------------------------------------------------------
# enforcement واقعیِ structural invariants
# ---------------------------------------------------------------------------
def t_invariant1_no_true_outcome():
    """#1 possible!=true: GateOutcome مقدارِ TRUE ندارد."""
    assert not any(m.value == "TRUE" for m in GateOutcome)
    assert GateOutcome.SUPPORTED.value == "SUPPORTED"


def t_invariant9_inconclusive_zero_delta():
    """#9 no-evidence!=evidence-of-absence: INCONCLUSIVE با delta!=0 رد می‌شود."""
    try:
        GateDecision(decision_id="d1", receipt_id="R-1", claim_id="CLM-1",
                     outcome=GateOutcome.INCONCLUSIVE, belief_delta_log_odds=0.5)
        raise AssertionError("INCONCLUSIVE+delta باید رد شود")
    except ValueError:
        pass
    # delta=0 مجاز
    d = GateDecision(decision_id="d2", receipt_id="R-1", claim_id="CLM-1",
                     outcome=GateOutcome.INCONCLUSIVE, belief_delta_log_odds=0.0)
    assert d.belief_delta_log_odds == 0.0


def t_invariant10_may_execute_never_true():
    """#10 sandbox-approval!=production-authorization: may_execute=True رد می‌شود."""
    try:
        GateDecision(decision_id="d3", receipt_id="R-1", claim_id="CLM-1",
                     outcome=GateOutcome.SUPPORTED, belief_delta_log_odds=1.0,
                     may_execute=True)
        raise AssertionError("may_execute=True باید رد شود")
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# label preservation در طولِ زنجیره
# ---------------------------------------------------------------------------
def t_receipt_has_world_mode():
    """EvidenceReceipt فیلدِ world_mode دارد (پیش‌فرض hypothesis، str tag سریالشدنی)."""
    r = _receipt()
    assert r.world_mode == "hypothesis"


def t_world_mode_consistency_detects_drift():
    """validate_world_mode_consistency اختلافِ label را می‌گیرد (invariant #4).

    claim enum + receipt str tag — مقایسهٔ value."""
    c = _claim(world_mode=WorldMode.SIMULATION)
    r_ok = _receipt(world_mode="simulation")
    assert validate_world_mode_consistency(c, r_ok).ok is True

    r_drift = _receipt(world_mode="hypothesis")
    res = validate_world_mode_consistency(c, r_drift)
    assert res.ok is False
    assert "world_mode_drift" in res.reason_codes[0]


def t_receipt_world_mode_membership():
    """receipt.world_mode فقط مقادیرِ مجاز را می‌پذیرد (بد عضویت رد)."""
    _receipt(world_mode="counterfactual")   # مجاز
    try:
        _receipt(world_mode="bogus")
        raise AssertionError("world_mode bogus باید رد شود")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# regression: backward-compatible با C1/C2
# ---------------------------------------------------------------------------
def t_legacy_claim_without_new_fields_still_works():
    """claim بدونِ فیلدهای نو (مثل C1) همچنان ساخته می‌شود."""
    c = _claim()
    assert c.assumptions == []
    assert c.evidence_for == []
    assert c.evidence_against == []
    assert c.world_mode is WorldMode.HYPOTHESIS   # default پر شده


def t_legacy_receipt_without_worldmode_works():
    """receipt بدونِ world_mode (مثل C2) همچنان ساخته می‌شود (default hypothesis)."""
    r = _receipt()
    assert r.world_mode == "hypothesis"


TESTS = [
    t_worldmode_enum_closed,
    t_executionscope_enum_closed,
    t_claim_defaults_worldmode_hypothesis,
    t_reality_worldmode_forbidden_on_claim,
    t_non_reality_worldmodes_allowed,
    t_assumption_model_strict,
    t_evidencelink_relevance_bounds,
    t_full_8part_claim_constructs,
    t_ten_invariants_registered,
    t_every_invariant_has_statement_and_enforcement,
    t_structural_invariants_subset,
    t_invariant1_no_true_outcome,
    t_invariant9_inconclusive_zero_delta,
    t_invariant10_may_execute_never_true,
    t_receipt_has_world_mode,
    t_world_mode_consistency_detects_drift,
    t_receipt_world_mode_membership,
    t_legacy_claim_without_new_fields_still_works,
    t_legacy_receipt_without_worldmode_works,
]

if __name__ == "__main__":
    failed = 0
    for _t in TESTS:
        try:
            _t()
            print(f"  PASS  {_t.__name__}")
        except Exception as exc:
            print(f"  FAIL  {_t.__name__}: {exc}")
            failed += 1
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(failed)
