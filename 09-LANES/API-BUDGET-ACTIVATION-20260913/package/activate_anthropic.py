#!/usr/bin/env python3
"""activate_anthropic.py — record Anthropic LIVE and refresh the frozen table.

Anthropic was unblocked by a WORKSPACE IDENTIFIER (not a credential) added to the
secure file; the credential used is the one already stored there. No value printed.
"""
import json
import sys
import time

sys.path.insert(0, "/home/ari/ofn/state/api-budget")
import providers  # noqa: E402

now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

h = providers.health_record()
h["anthropic"] = {
    "status": "LIVE", "paid": True,
    "models_http": 200, "models_count": 11,
    "evidence": "canary served claude-sonnet-5",
    "unblocked_by": ("ANTHROPIC_WORKSPACE_ID (a workspace identifier, not a credential) "
                     "added to the secure file; the credential itself is the one already "
                     "stored there and was never printed or copied"),
    "tier_source": "all four configured names verified present in the discovery list",
    "credential_from_chat_transcript": False,
}
h["_meta"]["recorded_at"] = now
h["_meta"]["anthropic_activation"] = ("workspace header supplied by owner 2026-09-13; "
                                      "a separate key posted in chat was NOT used")
providers.write_health(h)
print("health updated: anthropic -> LIVE")

routes = json.loads(providers.ROUTES_FILE.read_text(encoding="utf-8"))
routes["chain"] = providers.route()
routes["rank"] = list(providers.ROUTE_RANK)
routes["skipped"] = {p: h[p]["status"] for p in providers.ROUTE_RANK
                     if h.get(p, {}).get("status") not in ("LIVE", None)}
routes["recorded_at"] = now
providers.ROUTES_FILE.write_text(json.dumps(routes, indent=1, sort_keys=True) + "\n",
                                 encoding="utf-8")
print("chain:", routes["chain"])
print("skipped:", routes["skipped"])
print("candidates:", providers.candidates())
