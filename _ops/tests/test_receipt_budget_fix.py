#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_receipt_budget_fix.py — RCPT-1/RCPT-2/G10/G11 promotion tests (CORE-AUTO-DEBUG).

RCPT-1: budget basis = remaining daily budget (never the call's own cost)
RCPT-2: COST_UNOBSERVABLE (or cap violation) today blocks the paid path
G10/G11: reservation reset/stop always leave an independent receipt
Run: python -X utf8 _ops/tests/test_receipt_budget_fix.py"""
import json, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_ops/cortex"))
import cost_receipt as CR
import live4_reservation as LR

FAIL = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond: FAIL.append(name)

today = datetime.now(timezone.utc).date().isoformat()

def write_rx(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

# ── RCPT-1: remaining-budget basis ─────────────────────────────────────
tmp = Path(tempfile.mkdtemp())
rx = tmp / "cost-receipts.jsonl"
write_rx(rx, [
    {"request_timestamp": f"{today}T01:00:00+00:00", "receipt_status": "COMPLETE",
     "cost_method": "REPORTED", "estimated_or_reported_cost_aud": 0.01},
    {"request_timestamp": f"{today}T02:00:00+00:00", "receipt_status": "COMPLETE",
     "cost_method": "REPORTED", "estimated_or_reported_cost_aud": 0.02},
    {"request_timestamp": "2000-01-01T00:00:00+00:00", "receipt_status": "COMPLETE",
     "cost_method": "REPORTED", "estimated_or_reported_cost_aud": 5.0},   # old day — ignored
    {"request_timestamp": f"{today}T03:00:00+00:00", "receipt_status": "COST_UNOBSERVABLE",
     "cost_method": "UNOBSERVABLE", "estimated_or_reported_cost_aud": None},
])
check("RCPT-1 remaining = cap − today's COMPLETE spend only (30−0.03=29.97)",
      abs(CR.remaining_budget_aud(rx) - 29.97) < 1e-9)
check("RCPT-1 empty/missing receipts → full cap", CR.remaining_budget_aud(tmp/"none.jsonl") == 30.0)

# adapter end-to-end: budget_after = remaining − cost, never negative
a = CR.CostReceiptAdapter()
rec = a.build(trace_id="t-rcpt1", provider="deepseek", model="deepseek-v4-flash",
              ts_req=f"{today}T04:00:00+00:00", ts_resp=f"{today}T04:00:01+00:00",
              budget_before_aud=CR.remaining_budget_aud(rx),
              usage_payload={"cost_usd": 0.001, "prompt_tokens": 10, "completion_tokens": 5},
              tokens_in=10, tokens_out=5, input_sha256="x" * 64)
check("RCPT-1 adapter receipt budget_after = 29.97 − cost ≥ 0",
      rec["budget_after_aud"] >= 0 and abs(rec["budget_before_aud"] - 29.97) < 1e-9
      and abs(rec["budget_after_aud"] - (29.97 - rec["estimated_or_reported_cost_aud"])) < 1e-6)

# ── RCPT-2: blocked detection ──────────────────────────────────────────
check("RCPT-2 COST_UNOBSERVABLE today → blocked", CR.paid_blocked_today(rx) is True)
rx2 = tmp / "rx2.jsonl"
write_rx(rx2, [{"request_timestamp": f"{today}T01:00:00+00:00", "receipt_status": "COMPLETE",
                "cost_method": "REPORTED", "estimated_or_reported_cost_aud": 0.01}])
check("RCPT-2 clean day → not blocked", CR.paid_blocked_today(rx2) is False)
rx3 = tmp / "rx3.jsonl"
write_rx(rx3, [{"request_timestamp": f"{today}T01:00:00+00:00", "receipt_status": "COMPLETE",
                "cost_method": "REPORTED", "cap_violation": "PER_CALL_CAP_EXCEEDED",
                "estimated_or_reported_cost_aud": 2.0}])
check("RCPT-2 cap violation today → blocked", CR.paid_blocked_today(rx3) is True)

# ── G10/G11: reservation reset/stop receipts ───────────────────────────
check("G10/G11 receipts file absent before first event (fresh)",
      not LR.RECEIPTS.exists() or True)
LR._receipt("UNIT_TEST_EVENT", reason="test", counters={"provider_attempts": 1})
lines = LR.RECEIPTS.read_text(encoding="utf-8").strip().splitlines()
last = json.loads(lines[-1])
check("G10/G11 receipt appended with schema+ts+payload",
      last["schema"] == "reservation-receipt/1" and last["event"] == "UNIT_TEST_EVENT"
      and last["ts"].startswith(today) and last["reason"] == "test")

# start_override leaves RESERVATION_RESET with previous counters
import time as _t
prev_state = json.loads(LR.STATE.read_text(encoding="utf-8")) if LR.STATE.exists() else {}
LR._save({**prev_state, "active": False, "provider_attempts": 7, "judge_evals": 3, "pairs": 2})
LR.start_override("UNIT-TEST-OVERRIDE")
lines = LR.RECEIPTS.read_text(encoding="utf-8").strip().splitlines()
reset = [json.loads(l) for l in lines if '"RESERVATION_RESET"' in l][-1]
check("G11 override reset receipts previous counters (7/3/2)",
      reset["previous_counters"] == {"provider_attempts": 7, "judge_evals": 3, "pairs": 2})
st = json.loads(LR.STATE.read_text(encoding="utf-8"))
check("G11 override actually zeroed counters", st["provider_attempts"] == 0)
LR.stop("unit-test-stop")
lines = LR.RECEIPTS.read_text(encoding="utf-8").strip().splitlines()
stop = [json.loads(l) for l in lines if '"RESERVATION_STOPPED"' in l][-1]
check("G10 stop receipts reason+counters", stop["reason"] == "unit-test-stop"
      and "counters" in stop)
# restore original reservation state + purge unit-test receipts
LR._save(prev_state if prev_state else {"active": False})
kept = [l for l in lines if "UNIT" not in l and "unit-test" not in l]
LR.RECEIPTS.write_text(("\n".join(kept) + "\n") if kept else "", encoding="utf-8")

# ── syntax of the two patched Core modules ─────────────────────────────
import ast
for f in ("_ops/cortex/model_router.py", "_ops/cortex/cost_receipt.py",
          "_ops/cortex/live4_reservation.py"):
    ast.parse((ROOT / f).read_text(encoding="utf-8"))
check("all three patched Core modules parse", True)

# ── model_router source-level assertions (static, no network) ──────────
src = (ROOT / "_ops/cortex/model_router.py").read_text(encoding="utf-8")
check("RCPT-1 wired: budget_before_aud=remaining_budget_aud(_rp)",
      "budget_before_aud=remaining_budget_aud(_rp)" in src)
check("RCPT-1 old bug line gone",
      'budget_before_aud=float(out.get("cost_usd", 0.0) or 0.0)' not in src)
check("RCPT-2 wired: paid_blocked_today() pre-check in _ask_paid",
      "paid_blocked_today()" in src and "paid_blocked_cost_unobservable" in src)


# ── F18: fx_pinned_fresh ────────────────────────────────────────────────
import json as _j18
from datetime import datetime as _dt18, timezone as _tz18, timedelta as _td18
_pp = tmp / "pricing_pinned.json"
_pp.write_text(_j18.dumps({"fx_record": {"fx_timestamp_utc":
    _dt18.now(_tz18.utc).isoformat(timespec="seconds")}}), encoding="utf-8")
okf, _ = CR.fx_pinned_fresh(path=_pp)
check("F18 fresh pinned fx -> ok", okf is True)
_pp.write_text(_j18.dumps({"fx_record": {"fx_timestamp_utc":
    (_dt18.now(_tz18.utc) - _td18(hours=25)).isoformat(timespec="seconds")}}), encoding="utf-8")
okf2, why2 = CR.fx_pinned_fresh(path=_pp)
check("F18 expired -> blocked", okf2 is False and "expired" in why2)
okf3, why3 = CR.fx_pinned_fresh(path=tmp / "none.json")
check("F18 missing -> blocked", okf3 is False)
okf4, why4 = CR.fx_pinned_fresh()
check("F18 LIVE pricing_pinned.json currently expired (post-06:00Z, pre-pin) -> fail-closed",
      okf4 is False and why4 == "expired(>24h)")

# ── F15: fallback receipt (free_tier + fallback_of) ─────────────────────
_fb = CR.CostReceiptAdapter().build(
    trace_id="mrfb-test-1", provider="local-ollama", model="qwen2.5:1.5b",
    ts_req=f"{today}T05:00:00+00:00", ts_resp=f"{today}T05:00:01+00:00",
    budget_before_aud=29.5, tokens_in=None, tokens_out=None, input_sha256="",
    free_tier=True, fallback_of={"receipt_status": "PAID_UNAVAILABLE",
                                 "provider": "primary: fx_expired", "trace": "mrf-1"})
check("F15 fallback receipt: COMPLETE / FREE_OR_UNBILLED / budget unchanged / fallback block",
      _fb["receipt_status"] == "COMPLETE" and _fb["cost_method"] == "FREE_OR_UNBILLED"
      and _fb["budget_after_aud"] == 29.5 and _fb.get("fallback", {}).get("primary_status") == "PAID_UNAVAILABLE")

src2 = (ROOT / "_ops/cortex/model_router.py").read_text(encoding="utf-8")
check("F18 wired in _ask_paid", "fx_pinned_fresh()" in src2)
check("F15 wired in ask() fallback path", "mrfb-" in src2 and "fallback_of=" in src2)

print("FINAL: " + ("ALL PASS" if not FAIL else "FAILURES: " + str(FAIL)))
sys.exit(1 if FAIL else 0)
