#!/usr/bin/env python3
"""activate_providers.py — record measured health, freeze the route table,
and prove default route selection end-to-end through the budget broker.

Statuses come from this session's recorded verdicts (canary + models endpoint),
so the per-provider canary cap (one, <= $0.25) is respected. No value is printed.
"""
import json
import sys
import time

sys.path.insert(0, "/home/ari/ofn/state/api-budget")
import api_budget  # noqa: E402
import providers  # noqa: E402

now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# --- measured verdicts from this session (evidence: budget-ledger.jsonl) -----
health = {
    "local-llamacpp-180": {
        "status": "LIVE", "paid": False, "cost_usd": 0.0,
        "evidence": "GET http://192.168.0.180:8081/health -> 200 {'status':'ok'}",
        "reachable_from": "138 via 192.168.0.180 (env declares 127.0.0.1:180-local only)",
    },
    "gemini": {
        "status": "LIVE", "paid": True,
        "models_http": 200, "models_count": 50,
        "evidence": "canary served gemini-3.8-flash",
        "tier_source": "configured names verified present in discovery",
    },
    "deepseek": {
        "status": "LIVE", "paid": True,
        "models_http": 200, "models_count": 2,
        "evidence": "canary served deepseek-flash",
        "tier_source": "discovery-resolved (configured deepseek-chat/reasoner absent)",
    },
    "openai": {
        "status": "LIVE", "paid": True,
        "models_http": 200, "models_count": 130,
        "evidence": "canary served gpt-5.6-terra",
        "quirk": ("requires max_completion_tokens; temperature must be omitted "
                  "(model rejects any non-default value)"),
    },
    "sakana-fugu": {
        "status": "ACCOUNT_LIMIT_REACHED", "paid": True,
        "models_http": 200, "models_count": 8,
        "evidence": "canary AND models-scope call -> HTTP 429 usage_limit_reached",
        "note": ("credential is valid (models list works); the ACCOUNT window is "
                 "exhausted. Not a routing failure: it is skipped by name."),
    },
    "anthropic": {
        "status": "BLOCKED_WORKSPACE_SCOPE", "paid": True,
        "models_http": 400,
        "evidence": ("HTTP 400 invalid_request_error: 'This API key is not scoped to "
                     "a workspace, so this request must include the "
                     "anthropic-workspace-id header with the ID of the workspace'"),
        "owner_action": "supply ANTHROPIC_WORKSPACE_ID (Anthropic console workspace id)",
        "adapter_ready": True,
    },
}
health["_meta"] = {"recorded_at": now, "session": "API-BUDGET-ACTIVATION-20260913",
                   "canary_cap_usd_per_provider": 0.25,
                   "credential_values_recorded": False}
print("health written:", providers.write_health(health))

routes = {
    "schema": "octopus.provider-routes.v1",
    "recorded_at": now,
    "chain": providers.route(),
    "rank": list(providers.ROUTE_RANK),
    "skipped": {pid: health[pid]["status"] for pid in providers.ROUTE_RANK
                if health.get(pid, {}).get("status") not in ("LIVE", None)},
    "policy": {
        "local_first": True,
        "no_silent_failover": True,
        "every_selection_emits_receipt": True,
        "shared_global_budget": True,
        "budget_contract": "config/api-budget-contract.json (unchanged)",
        "per_provider_canary_cap_usd": 0.25,
    },
}
providers.ROUTES_FILE.write_text(json.dumps(routes, indent=1, sort_keys=True) + "\n",
                                 encoding="utf-8")
print("routes written:", providers.ROUTES_FILE)
print("chain:", routes["chain"])
print("skipped:", routes["skipped"])
print()

# --- end-to-end proof: default selection through the broker -----------------
print("=== ACTIVATION PROOF (default route selection, capped) ===")
cands = providers.candidates()
print("live paid candidates in rank order:", cands)
r = api_budget.paid_call("activation-proof-20260913", "route-activation-proof",
                         "Reply with the single word: ok",
                         est_in_tok=64, max_out_tok=16, first_call_cap=0.25)
st = r.get("settle") or {}
print("ok=%s provider=%s served=%s cost=%s window_spent=%s"
      % (r.get("ok"), r.get("provider"), r.get("served_model"),
         st.get("cost_usd"), st.get("window_spent_usd")))
print()
print("budget:", json.dumps(api_budget.status()))
print("local rung reachable:", providers.health("local-llamacpp-180"))
