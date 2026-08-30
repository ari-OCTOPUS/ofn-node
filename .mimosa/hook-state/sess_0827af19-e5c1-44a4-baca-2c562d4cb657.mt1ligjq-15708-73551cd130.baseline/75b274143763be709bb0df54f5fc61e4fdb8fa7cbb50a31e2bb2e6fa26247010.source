"""تست چک‌لیست #۱: عبور از بودجه باید اجرا را قطع کند + شمارش فراخوانی."""
import pytest
import config
from src.budget import BudgetLedger, BudgetExceeded


def test_cost_accumulates():
    led = BudgetLedger()
    led.precheck("researcher")
    led.record("researcher", 1000, 1000)
    assert led.per_agent["researcher"].calls == 1
    assert led.total.cost_usd > 0


def test_per_agent_budget_trips(monkeypatch):
    monkeypatch.setitem(config.PER_AGENT_BUDGET_USD, "researcher", 0.0001)
    led = BudgetLedger()
    with pytest.raises(BudgetExceeded):
        led.record("researcher", 100000, 100000)  # هزینه زیاد → قطع خودکار


def test_call_limit(monkeypatch):
    monkeypatch.setattr(config, "MAX_CALLS_PER_AGENT", 1)
    led = BudgetLedger()
    led.precheck("analyst")
    led.record("analyst", 10, 10)
    with pytest.raises(BudgetExceeded):
        led.precheck("analyst")        # فراخوانی دوم مجاز نیست
