#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""budget_transfer.py — مبادلهٔ آزادِ بودجه با لاگ (D4: free_with_log).

رأیِ مالک (DECISIONS-REGISTRY D4): ایجنت‌ها آزادانه بودجه را مبادله یا **قرض**
می‌کنند — DEBT_FORBIDDEN=false؛ تنها الزام، لاگ است. پس این ماژول مانعِ هیچ
انتقالی نمی‌شود (نه بررسیِ موجودی، نه سقفِ بدهی): فقط حساب‌ها را جابه‌جا
می‌کند و رکورد را با trace_id در دو جا می‌نویسد:

  ۱. ledgerِ محلی: `state/pulse/budget-transfers.jsonl` (append-only)
  ۲. رویدادِ ساختاریافته: `events.jsonl` با event_name=task.started از agent_id
     «budget_transfer» (taxonomy موجود؛ summary بدونِ محتوای خصوصی) — R8.

از life_currency.LifeBudget استفاده می‌کند ولی مستقل از فلگِ نوشتنِ آن است —
لاگِ انتقال همیشه انجام می‌شود (الزامِ D4)، فارغ از dry-run بودنِ تخصیص.

total · fail-soft (خطای لاگ، انتقال را بی‌صدا نمی‌بلعد — برمی‌گرداند و در
خروجی می‌گوید) · تک‌نویسنده: فقط این ماژول به budget-transfers.jsonl می‌نویسد.
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

LEDGER_PATH = opslib.STATE_DIR / "pulse" / "budget-transfers.jsonl"


def transfer(budgets: dict, from_m: str, to_m: str,
             tokens: float, calls: int, reason: str = "") -> dict:
    """انتقالِ آزاد — تنها الزامِ D4 لاگ است.

    budgets: dictِ member → LifeBudget (یا dict با کلیدهای tokens/calls).
    موجودی بررسی نمی‌شود: بدهی مجاز است (DEBT_FORBIDDEN=false) و در لاگ دیده می‌شود.
    خروجی: رکوردِ انتقال (+ کلیدِ logged: True/False)."""
    src = budgets.get(from_m)
    dst = budgets.get(to_m)
    if src is None or dst is None:
        return {"error": "unknown-member", "from": from_m, "to": to_m,
                "trace_id": "", "logged": False}
    trace_id = f"bt-{time.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
    # deduct — hasattr برای پشتیبانی از LifeBudget و dict خام
    try:
        if hasattr(src, "tokens"):
            src.tokens -= float(tokens)
            src.calls -= int(calls)
        else:
            src["tokens"] = float(src.get("tokens", 0.0)) - float(tokens)
            src["calls"] = int(src.get("calls", 0)) - int(calls)
        if hasattr(dst, "tokens"):
            dst.tokens += float(tokens)
            dst.calls += int(calls)
        else:
            dst["tokens"] = float(dst.get("tokens", 0.0)) + float(tokens)
            dst["calls"] = int(dst.get("calls", 0)) + int(calls)
    except (TypeError, ValueError):
        return {"error": "bad-amount", "from": from_m, "to": to_m,
                "trace_id": trace_id, "logged": False}
    rec = {
        "event_type": "budget.transfer",
        "trace_id": trace_id,
        "from": from_m, "to": to_m,
        "tokens": round(float(tokens), 3), "calls": int(calls),
        "reason": str(reason or "")[:200],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "debt": bool(_net_tokens(budgets, from_m) < 0),
    }
    rec["logged"] = _log(rec)
    return rec


def _net_tokens(budgets: dict, member: str) -> float:
    b = budgets.get(member)
    if b is None:
        return 0.0
    try:
        return float(b.tokens if hasattr(b, "tokens") else b.get("tokens", 0.0))
    except (TypeError, ValueError):
        return 0.0


def _log(rec: dict) -> bool:
    """نوشتنِ رکورد در ledger + events.jsonl. fail-soft، خروجی bool."""
    ok = True
    try:
        LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        ok = False
    try:   # رویداد ساختاریافته — R8 (trace_id)؛ خطا ارزشِ انتقال را نمی‌کشد
        import events as _ev   # noqa: WPS433
        _ev.emit("task.started", "budget_transfer", status="ok",
                 summary=f"budget.transfer {rec['from']}→{rec['to']} "
                         f"tokens={rec['tokens']} calls={rec['calls']} "
                         f"debt={rec.get('debt')}",
                 trace_id=rec["trace_id"], correlation_id=rec["trace_id"],
                 approval_state="none")
    except Exception:  # noqa: BLE001
        pass
    return ok


if __name__ == "__main__":   # pragma: no cover
    from life_currency import LifeBudget
    bs = {"heart": LifeBudget("heart", 100.0, 10, 50.0),
          "sigma": LifeBudget("sigma", 100.0, 10, 50.0)}
    print(json.dumps(transfer(bs, "heart", "sigma", 30.0, 3, "demo"),
                     ensure_ascii=False, indent=1))
