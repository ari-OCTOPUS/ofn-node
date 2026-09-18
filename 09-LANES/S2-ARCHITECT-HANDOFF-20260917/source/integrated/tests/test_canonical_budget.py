"""D-2 tests use fake cost scenarios; no measured spending or network calls."""
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from ofn.adapters.fake_executor import FakeProvider, execute_with_approval
from ofn.kernel.callbudget import CallBudget
from ofn.kernel.canonical_budget import (
    CANONICAL_LIMITS, BudgetLimits, BudgetRequest, BudgetUsage, admit_spend,
    effective_limits,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.routing import Rung
from tests.test_executor_fake import NOW, make_approval, make_decision

EPOCH = int(datetime.strptime(NOW, "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=timezone.utc).timestamp())
REQUEST = BudgetRequest("run-138-1", "USD", 200)
USAGE = BudgetUsage("run-138-1", "USD", EPOCH, 0, 0, 0, True)


def admit(request=REQUEST, usage=USAGE, **kw):
    return admit_spend(request=request, usage=usage, now_epoch_s=EPOCH, **kw)


def test_owner_ceilings_are_exact_usd_cents():
    assert CANONICAL_LIMITS == BudgetLimits(10000, 1000, 200)
    assert admit().allowed
    assert not admit(replace(REQUEST, amount=201)).allowed


@pytest.mark.parametrize("field,spent", [("monthly", 9800), ("rolling_24h", 800), ("per_task", 0)])
def test_exact_boundary_allowed_one_cent_over_denied(field, spent):
    usage = replace(USAGE, **{field: spent})
    assert admit(usage=usage).allowed
    assert admit(usage=replace(usage, **{field: spent + 1})).reason == "budget-" + field + "-exceeded"


@pytest.mark.parametrize("runtime", [BudgetLimits(100, 1000, 200), BudgetLimits(10000, 100, 200), BudgetLimits(10000, 1000, 100)])
def test_each_stricter_runtime_dimension_wins(runtime):
    assert not admit(runtime_limits=runtime).allowed


def test_larger_runtime_caps_never_expand_owner_policy():
    assert effective_limits(BudgetLimits(99999, 99999, 99999)) == CANONICAL_LIMITS
    assert not admit(replace(REQUEST, amount=201), runtime_limits=BudgetLimits(99999, 99999, 99999)).allowed


def test_zero_runtime_cap_is_not_unlimited():
    limits = BudgetLimits(0, 0, 0)
    assert not admit(runtime_limits=limits).allowed
    assert admit(replace(REQUEST, amount=0), runtime_limits=limits).allowed


@pytest.mark.parametrize("bad", [True, False, -1, 0.1, "0", None, float("nan"), float("inf")])
def test_invalid_numbers_cannot_coerce_into_permission(bad):
    assert not admit(replace(REQUEST, amount=bad)).allowed
    assert not admit(usage=replace(USAGE, monthly=bad)).allowed
    with pytest.raises(FailClosedError):
        BudgetLimits(bad, 1000, 200)


@pytest.mark.parametrize("usage", [None, replace(USAGE, complete=False), replace(USAGE, complete=1),
    replace(USAGE, observed_at_epoch_s=EPOCH - 1), replace(USAGE, observed_at_epoch_s=EPOCH + 1),
    replace(USAGE, observed_at_epoch_s=True), replace(USAGE, task_id="other"),
    replace(USAGE, currency="AUD")])
def test_unknown_stale_unbound_usage_denies(usage):
    assert not admit(usage=usage).allowed


def test_aud_business_values_are_outside_api_usd_policy():
    assert not admit(replace(REQUEST, currency="AUD"), replace(USAGE, currency="AUD")).allowed


def test_composed_callbudget_preserves_both_independent_guards():
    budget = CallBudget(caps={Rung.REMOTE: 1})
    assert budget.allows_spend(Rung.REMOTE, EPOCH, request=REQUEST, usage=USAGE)
    assert not budget.allows_spend(Rung.REMOTE, EPOCH, request=REQUEST, usage=None)
    assert not budget.allows_spend(Rung.REMOTE, EPOCH, request=REQUEST, usage=replace(USAGE, monthly=10000))
    budget.record(Rung.REMOTE, EPOCH)
    assert not budget.allows_spend(Rung.REMOTE, EPOCH, request=REQUEST, usage=USAGE)
    assert budget.grants_send() is False


@pytest.mark.parametrize("cost_request,usage,limits", [
    (replace(REQUEST, amount=201), USAGE, None),
    (REQUEST, None, None),
    (REQUEST, USAGE, BudgetLimits(100, 1000, 200)),
    (replace(REQUEST, task_id="other"), replace(USAGE, task_id="other"), None),
])
def test_fake_executor_denial_is_persisted_before_any_provider_call(tmp_path, cost_request, usage, limits):
    decision, provider = make_decision(), FakeProvider()
    receipt = execute_with_approval(decision, make_approval(decision), provider,
        state_dir=str(tmp_path), now_utc=NOW, budget_request=cost_request,
        budget_usage=usage, runtime_limits=limits)
    assert receipt["status"] == "DENIED"
    assert not receipt["provider_called"] and not provider.calls
    assert receipt["budget"]["currency"] == "USD"
    assert (tmp_path / "execution_receipts.jsonl").read_text().strip()


def test_fake_provider_admission_is_not_a_real_transport_authorization(tmp_path):
    class AnotherProvider(FakeProvider):
        pass
    provider, decision = AnotherProvider(), make_decision()
    receipt = execute_with_approval(decision, make_approval(decision), provider,
        state_dir=str(tmp_path), now_utc=NOW, budget_request=REQUEST, budget_usage=USAGE)
    assert receipt["rule"] == "real-transport-not-implemented"
    assert not provider.calls


def test_fake_zero_cost_receipt_preserves_stricter_limits(tmp_path):
    decision = make_decision()
    receipt = execute_with_approval(decision, make_approval(decision), FakeProvider(),
        state_dir=str(tmp_path), now_utc=NOW, runtime_limits=BudgetLimits(0, 0, 0))
    assert receipt["status"] == "EXECUTED"
    assert receipt["budget"]["reason"] == "fake-zero-cost"
    assert receipt["budget"]["limits"] == {"monthly": 0, "rolling_24h": 0, "per_task": 0}
    assert receipt["budget"]["reservation_created"] is False


def test_valid_cost_scenario_reaches_only_fake_provider(tmp_path):
    decision, provider = make_decision(), FakeProvider()
    receipt = execute_with_approval(decision, make_approval(decision), provider,
        state_dir=str(tmp_path), now_utc=NOW, budget_request=REQUEST, budget_usage=USAGE)
    assert receipt["status"] == "EXECUTED" and len(provider.calls) == 1
    assert receipt["budget"]["reason"] == "budget-fits"
    assert receipt["budget"]["reservation_created"] is False


def test_invalid_runtime_limits_deny_even_zero_cost_fake(tmp_path):
    decision, provider = make_decision(), FakeProvider()
    receipt = execute_with_approval(decision, make_approval(decision), provider,
        state_dir=str(tmp_path), now_utc=NOW, runtime_limits={})
    assert receipt["rule"] == "budget-input-invalid"
    assert not provider.calls
