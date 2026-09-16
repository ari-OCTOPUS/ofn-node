#!/usr/bin/env python3
"""canary_and_reconcile.py — second canary pass + honest ledger reconciliation.

Runs on 138. Prints no credential value.
"""
import json
import sys
import time

sys.path.insert(0, "/home/ari/ofn/state/api-budget")
import api_budget  # noqa: E402
import providers  # noqa: E402

print("=== RECONCILE: two out-of-band diagnostic calls (openai) ===")
for endpoint in ("/v1/chat/completions", "/v1/responses"):
    task = "diag-reconcile-openai-" + endpoint.rsplit("/", 1)[-1]
    r = api_budget.reserve(task, "out-of-band-diagnostic", 64, 16,
                           "diagnosis: max_tokens vs max_completion_tokens",
                           provider="openai", model="gpt-5.6-terra")
    if not r.get("ok"):
        print("  reserve failed:", r)
        continue
    s = api_budget.settle(r["request_id"], 64, 0, 0.6, "", True,
                          "out-of-band diagnostic diagnosis call")
    print("  %-28s reserved=%.6f settled_cost=%s"
          % (endpoint, r["est_max_usd"], s.get("cost_usd")))

print()
print("=== CANARY PASS 2 (one capped call per provider, via broker) ===")
for pid in providers.paid_ids():
    if not providers.enabled(pid):
        print("%-12s SKIP disabled" % pid)
        continue
    if not providers.key_present(pid):
        print("%-12s SKIP no key" % pid)
        continue
    mdl = providers.model(pid)
    r = api_budget.canary(pid)
    st = r.get("settle") or {}
    print("%-12s model=%-24s ok=%-5s served=%-22s http=%-4s err=%-28s cost=%s"
          % (pid, mdl, r.get("ok"), str(r.get("served_model"))[:22],
             r.get("http_status"), str(r.get("detail") or r.get("error"))[:28],
             st.get("cost_usd")))

print()
print("=== anthropic message-endpoint error (key redacted) ===")
import urllib.error  # noqa: E402
import urllib.request  # noqa: E402
key = providers._key("anthropic")
h = {"x-api-key": key, "anthropic-version": providers.env().get("ANTHROPIC_VERSION", "2023-06-01"),
     "Content-Type": "application/json"}
body = {"model": providers.model("anthropic"), "max_tokens": 16,
        "messages": [{"role": "user", "content": "Reply with the single word: ok"}]}
try:
    req = urllib.request.Request(providers.chat_url("anthropic", providers.model("anthropic")),
                                data=json.dumps(body).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=40) as resp:
        print("OK", resp.status)
except urllib.error.HTTPError as e:
    txt = e.read().decode()[:400]
    print("HTTP", e.code, (txt.replace(key, "<REDACTED>") if key else txt))

print()
print("budget after:", json.dumps(api_budget.status())[:300])
print("now:", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
