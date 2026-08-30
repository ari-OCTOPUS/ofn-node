"""test_close_reason_ask_budget_20260816 — ERRORHUNT ۳.

جدول نقش reason باید سقف ۲۰۰۰توکن را جا بدهد (need≈127.5s ⇒ ask≥212).
ثبت در run_all نشده (WORKLOCK).
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "debate"))
sys.path.insert(0, str(_HERE.parent / "budget"))

# isolate from live env overrides
os.environ.pop("PAID_ASK_BUDGET_S_REASON", None)
os.environ.pop("PAID_ASK_BUDGET_S", None)

import client  # noqa: E402


def test_reason_ask_budget_covers_2000_tokens():
    ask = client._ask_budget("reason")
    assert ask >= 212.0, ask
    cap = ask * client._ASK_BUDGET_SHARE
    t = client._http_timeout("reason", 2000)
    assert t + 1e-9 >= 127.5, (t, cap)
    assert t <= cap + 1e-9
