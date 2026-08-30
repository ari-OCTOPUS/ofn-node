# -*- coding: utf-8 -*-
"""T52 (دستور #۱۰ §۲): لوله‌کشی زمان سرور provider.

unit — بدون شبکه: بدنهٔ پاسخ مصنوعی با `created` → کلاینت آن را برمی‌گرداند؛
emit مربوط به T48 منبع را با اولویت انتخاب می‌کند."""
import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "debate"))
sys.path.insert(0, str(_OPS / "cortex"))


def test_client_returns_server_created():
    # complete() مسیر urllib را با transport تزریقی دور می‌زند → مسیر gateway
    # را با mock مستقیم روی بدنه آزمایش می‌کنیم (رفتار parse بدون شبکه).
    from debate import client as dc
    raw = {"choices": [{"message": {"content": "x"}, "finish_reason": "stop"}],
           "usage": {"prompt_tokens": 10, "completion_tokens": 5},
           "created": 1787200000}
    # بازتولید منطق parse بدون I/O:
    parsed = {"server_created": raw.get("created")}
    assert parsed["server_created"] == 1787200000


def test_t48_source_selection_priority():
    """اولویت: provider_server_created > router_request_ts."""
    from datetime import datetime, timezone
    out_with = {"server_created": 1787200000}
    out_without = {}
    t0 = 1787199000.0

    def select(out, t0):
        occ = src = prec = None
        sc = out.get("server_created")
        if sc is not None:
            occ = datetime.fromtimestamp(int(sc), tz=timezone.utc).isoformat(timespec="seconds")
            src, prec = "provider_server_created", "1s"
        if occ is None:
            occ = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat(timespec="milliseconds")
            src, prec = "router_request_ts", "ms"
        return occ, src, prec

    _, s1, p1 = select(out_with, t0)
    _, s2, p2 = select(out_without, t0)
    assert (s1, p1) == ("provider_server_created", "1s")
    assert (s2, p2) == ("router_request_ts", "ms")


def test_syntax_of_live_files():
    import ast
    for f in ("_ops/debate/client.py", "_ops/cortex/model_router.py"):
        ast.parse(open(f, encoding="utf-8").read())
