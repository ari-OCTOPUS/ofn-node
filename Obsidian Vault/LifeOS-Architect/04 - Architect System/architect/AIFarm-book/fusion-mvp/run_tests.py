#!/usr/bin/env python3
"""
run_tests.py — رانر سبک تست بدون نیاز به pytest.
اگر pytest نصب باشد، بهتر است از آن استفاده کنی:  python -m pytest -q
این رانر همان منطق را پوشش می‌دهد تا بدون اینترنت/نصب هم بتوانی تست بگیری.
"""
import os, sys, tempfile, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.killswitch import KillSwitch, KillSwitchError
from src.budget import BudgetLedger, BudgetExceeded
from src.hitl import HITLGate
from src.tools import ToolGateway, ToolPermissionError
from src.tracing import AuditLog

passed = failed = 0


def check(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  ✅ {name}")
        passed += 1
    except Exception:
        print(f"  ❌ {name}")
        traceback.print_exc()
        failed += 1


def expect_raises(exc, fn):
    try:
        fn()
    except exc:
        return
    raise AssertionError(f"انتظار {exc.__name__} می‌رفت ولی پرتاب نشد")


# #2 kill-switch
def t_ks_software():
    ks = KillSwitch(stop_file="logs/_t1"); ks.check(); ks.trip("x")
    expect_raises(KillSwitchError, ks.check)

def t_ks_file():
    d = tempfile.mkdtemp(); stop = os.path.join(d, "STOP")
    ks = KillSwitch(stop_file=stop); ks.check()
    open(stop, "w").write("x")
    expect_raises(KillSwitchError, ks.check)

# #1 budget
def t_budget_cost():
    led = BudgetLedger(); led.precheck("researcher"); led.record("researcher", 1000, 1000)
    assert led.total.cost_usd > 0 and led.per_agent["researcher"].calls == 1

def t_budget_trip():
    cap = dict(config.PER_AGENT_BUDGET_USD); config.PER_AGENT_BUDGET_USD["researcher"] = 0.0001
    led = BudgetLedger()
    try:
        expect_raises(BudgetExceeded, lambda: led.record("researcher", 100000, 100000))
    finally:
        config.PER_AGENT_BUDGET_USD.update(cap)

# #2/#6 HITL
def t_hitl_reject():
    assert HITLGate(approver=lambda a, c: False).request("finalize", {}) is False

def t_hitl_approve():
    assert HITLGate(approver=lambda a, c: True).request("finalize", {}) is True

# #4 least-privilege
def t_tool_denied():
    expect_raises(ToolPermissionError, lambda: ToolGateway().call("analyst", "web_search_mock", query="x"))

def t_tool_allowed():
    assert "نمونه" in ToolGateway().call("researcher", "web_search_mock", query="x")

# #3 audit chain
def t_audit_chain():
    d = tempfile.mkdtemp(); p = os.path.join(d, "a.jsonl")
    log = AuditLog(path=p); log.log("a", "x", v=1); log.log("b", "y", v=2)
    assert log.verify_chain() is True
    lines = open(p, encoding="utf-8").read().splitlines()
    lines[0] = lines[0].replace('"v": 1', '"v": 999')
    open(p, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    assert AuditLog(path=p).verify_chain() is False


if __name__ == "__main__":
    print("اجرای تست‌ها (چک‌لیست ۱،۲،۳،۴،۶):")
    for n, f in [
        ("kill-switch نرم‌افزاری (#2)", t_ks_software),
        ("kill-switch فایل STOP (#2)", t_ks_file),
        ("ثبت هزینه (#1)", t_budget_cost),
        ("قطع خودکار بودجه (#1)", t_budget_trip),
        ("HITL رد می‌کند (#2/#6)", t_hitl_reject),
        ("HITL تأیید می‌کند (#2/#6)", t_hitl_approve),
        ("least-privilege رد ابزار (#4)", t_tool_denied),
        ("least-privilege ابزار مجاز (#4)", t_tool_allowed),
        ("صحت زنجیره‌ی audit (#3)", t_audit_chain),
    ]:
        check(n, f)
    print(f"\nنتیجه: {passed} موفق، {failed} ناموفق")
    sys.exit(1 if failed else 0)
