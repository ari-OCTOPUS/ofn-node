#!/usr/bin/env python3
"""apply_owner_budget_decision.py — record the owner's 2026-09-13 budget ruling.

Ruling (verbatim decisions from the owner's answer card):
  * shared budget caps: UNCHANGED
  * default provider for ordinary work: deepseek (was cheapest-healthy = gemini)

Rewrites the frozen route table from the deployed registry and proves the new
default with ONE capped call. Prints no credential value.
"""
import json
import sys
import time

sys.path.insert(0, "/home/ari/ofn/state/api-budget")
import api_budget  # noqa: E402
import providers  # noqa: E402

now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# 1) refresh the frozen chain from the deployed registry ---------------------
routes = json.loads(providers.ROUTES_FILE.read_text(encoding="utf-8"))
routes["chain"] = providers.route()
routes["rank"] = list(providers.ROUTE_RANK)
routes["owner_decision"] = {
    "at": now,
    "budget": "UNCHANGED (window1 20 / window2 20 / steady 10 per 24h / month 100 "
              "/ per task 2 / 3 calls per task / concurrency 1 / no rollover / no borrowing)",
    "default_provider": "deepseek",
    "previously": "cheapest-healthy (gemini)",
}
routes["recorded_at"] = now
providers.ROUTES_FILE.write_text(json.dumps(routes, indent=1, sort_keys=True) + "\n",
                                 encoding="utf-8")
print("routes refreshed:", routes["chain"])
print()

# 2) prove the new default with one capped call ------------------------------
r = api_budget.paid_call("owner-default-proof-20260913", "route-default-proof",
                         "Reply with the single word: ok",
                         est_in_tok=64, max_out_tok=16, first_call_cap=0.25)
st = r.get("settle") or {}
print("default now selects: provider=%s served=%s ok=%s cost=%s"
      % (r.get("provider"), r.get("served_model"), r.get("ok"), st.get("cost_usd")))
print("budget:", json.dumps(api_budget.status()))
