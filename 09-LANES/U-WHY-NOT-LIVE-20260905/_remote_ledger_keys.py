import json
import os

p = "/home/ari/ofn/data/state/legs/claims-ledger.jsonl"
print("EXISTS", os.path.isfile(p))
keys = set()
types = {}
n = 0
last5_keys = []
with open(p, encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        n += 1
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            keys.update(obj.keys())
            t = obj.get("type") or obj.get("kind") or obj.get("event") or obj.get("claim_type")
            t = str(t) if t is not None else "_none"
            types[t] = types.get(t, 0) + 1
            last5_keys.append(sorted(obj.keys()))
            if len(last5_keys) > 5:
                last5_keys.pop(0)
print("N", n)
print("KEYSET", ",".join(sorted(map(str, keys))))
print("TYPE_COUNTS")
for k, v in sorted(types.items(), key=lambda kv: (-kv[1], kv[0]))[:30]:
    print(k, v)
print("LAST5_KEYSETS")
for row in last5_keys:
    print(",".join(row))

# HOLD lines from season notes — text only, no rewrite
for note in (
    "/home/ari/octopus-mesh/state/season/SEASON-5-2026-09-04.md",
    "/home/ari/octopus-mesh/state/season/SEASON.md",
):
    print("NOTE", note)
    if not os.path.isfile(note):
        continue
    for i, line in enumerate(open(note, encoding="utf-8", errors="replace"), 1):
        if "HOLD_EXTERNAL" in line or "hold_external" in line:
            print(f"{i}:{line.rstrip()[:200]}")
