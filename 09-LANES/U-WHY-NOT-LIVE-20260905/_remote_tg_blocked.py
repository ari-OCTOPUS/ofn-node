import json
import os

for p in (
    "/home/ari/octopus-mesh/state/telegram_blocked.json",
    "/home/ari/octopus-mesh/state/heartbeats/octopus-telegram-bridge.json",
):
    print("PATH", p)
    print("EXISTS", os.path.isfile(p))
    if not os.path.isfile(p):
        continue
    raw = open(p, encoding="utf-8", errors="replace").read()
    print("N", len(raw))
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        print("NOT_JSON")
        continue
    if isinstance(d, dict):
        print("KEYS", ",".join(sorted(map(str, d.keys()))))
        for k, v in d.items():
            kl = str(k).lower()
            if any(s in kl for s in ("token", "secret", "password", "key", "chat")):
                print("KV", k, "=", "<redacted>")
            else:
                print("KV", k, "=", v)
    else:
        print("TYPE", type(d).__name__)
