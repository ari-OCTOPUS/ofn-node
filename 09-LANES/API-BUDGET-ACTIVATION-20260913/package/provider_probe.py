#!/usr/bin/env python3
"""Provider probe: metadata-only models discovery. Prints no credential value."""
import json
import sys

sys.path.insert(0, "/home/ari/ofn/state/api-budget")
import providers  # noqa: E402

print("=== REDACTED REGISTRY ===")
for pid, st in providers.redacted_status().items():
    print("  %-22s enabled=%-5s paid=%-5s key=%-5s auth=%-9s models_url=%s"
          % (pid, st["enabled"], st["paid"], st["key_present"], st["auth"],
             st["models_url"] or "-"))

print()
print("=== MODELS ENDPOINT (metadata, unbilled) ===")
res = {}
for pid in providers.provider_ids():
    if not providers.enabled(pid):
        print("  %-22s SKIP (disabled)" % pid)
        continue
    if not providers.REGISTRY[pid]["paid"]:
        h = providers.health(pid)
        print("  %-22s local health=%s" % (pid, h))
        res[pid] = {"health": h}
        continue
    r = providers.list_models(pid)
    print("  %-22s ok=%s http=%s count=%s err=%s"
          % (pid, r.get("ok"), r.get("http_status"), r.get("count"), r.get("error")))
    cfg = providers.models(pid)
    print("       configured: %s" % cfg)
    ids = r.get("ids") or []
    if ids:
        print("       discovered(first 25): %s" % ids[:25])
        missing = {t: m for t, m in cfg.items() if m and m not in ids}
        print("       configured_model_NOT_in_list: %s" % (missing or "none"))
    res[pid] = r

with open("/tmp/probe-result.json", "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=1)
print()
print("probe written: /tmp/probe-result.json")
