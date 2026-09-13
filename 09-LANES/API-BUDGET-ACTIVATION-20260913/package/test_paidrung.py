#!/usr/bin/env python3
"""Test the coding worker's paid rung with a stubbed broker.

Zero spend, zero ledger writes: the module's receipt() is captured in memory
and api_budget is replaced by a stub before the call.
"""
import importlib.util
import json
import pathlib
import sys
import types

WORKER = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py")
spec = importlib.util.spec_from_file_location("coding_worker_undertest", WORKER)
mod = importlib.util.module_from_spec(spec)
sys.modules["coding_worker_undertest"] = mod
spec.loader.exec_module(mod)

captured = []
mod.receipt = lambda kind, **kw: captured.append({"kind": kind, **kw})

stub = types.ModuleType("api_budget")
calls = []


def fake_paid_call(task_id, purpose, prompt, est_in_tok=0, max_out_tok=0,
                   first_call_cap=None, provider=None, model=None):
    calls.append({"task_id": task_id, "purpose": purpose, "cap": first_call_cap,
                  "prompt_len": len(prompt), "provider": provider})
    return {"ok": True, "provider": "gemini", "served_model": "gemini-3.8-flash",
            "text": "ok", "settle": {"cost_usd": 0.00014}}


stub.paid_call = fake_paid_call
sys.modules["api_budget"] = stub

task = {"task_id": "TEST-PAIDRUNG-001", "purpose": "unit-test",
        "context": {"hint": "no secrets here", "k": "slice"}}
out = mod.paid_fallback(task)
print("paid_fallback returned:", json.dumps(out))
print("broker call recorded:", json.dumps(calls))
print("receipts captured:", json.dumps(captured))
print("cap enforced <=0.25:", all(c["cap"] is not None and c["cap"] <= 0.25 for c in calls))
print("test PASS" if out and out.get("paid") and out.get("provider") == "gemini" else "test FAIL")
