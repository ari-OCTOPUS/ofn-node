#!/usr/bin/env python3
"""WHY gemini scores 0/2: raw probe. Prints status + finishReason + text len.
No secrets printed. Read-only (one paid call, ~cents)."""
import json
import os
import pathlib
import sys
import urllib.request

sys.path.insert(0, "/home/ari/ofn/tools")
import brain_factory as bf  # noqa: E402

bf._load_env_files()
reg = bf._registry()
table = getattr(reg, "REGISTRY", {}) or {}
entry = table.get("gemini") or {}
model = reg.model("gemini", "standard") if hasattr(reg, "model") else "?"
url = reg.chat_url("gemini", model)
key = os.environ.get(entry.get("key_var") or "GEMINI_API_KEY", "")
print("model:", model)
print("url:", url)
print("key_present:", bool(key))

brain = bf.GeminiBrain(key, model, url)
body = brain._body("Reply with exactly: OK", 64)
req = urllib.request.Request(url, data=json.dumps(body).encode(),
                             headers={**brain._headers(), "Content-Type": "application/json"},
                             method="POST")
try:
    with urllib.request.urlopen(req, timeout=40) as r:
        status = r.status
        payload = json.load(r)
except urllib.error.HTTPError as e:
    status = e.code
    payload = json.loads(e.read().decode() or "{}")
except Exception as e:  # noqa: BLE001
    print("EXC:", type(e).__name__, str(e)[:200])
    raise SystemExit(0)

print("status:", status)
print("top-level keys:", sorted(payload.keys())[:8])
cands = payload.get("candidates") or []
print("candidates:", len(cands))
if cands:
    c0 = cands[0]
    print("finishReason:", c0.get("finishReason"))
    print("content keys:", sorted((c0.get("content") or {}).keys()))
    parts = (c0.get("content") or {}).get("parts") or []
    print("parts:", len(parts), "| first part keys:",
          sorted(parts[0].keys()) if parts and isinstance(parts[0], dict) else "-")
    print("extract len:", len(brain._extract(payload)))
    print("extract preview:", repr(brain._extract(payload))[:80])
else:
    print("NO CANDIDATES -> promptFeedback:", json.dumps(payload.get("promptFeedback"))[:200])
