import json
from collections import Counter

p = "/home/ari/ofn/data/state/legs/claims-ledger.jsonl"
c = Counter()
with open(p, encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            claim = obj.get("claim")
            c[str(claim) if claim is not None else "_none"] += 1
print("CLAIM_N", sum(c.values()))
print("CLAIM_UNIQUE", len(c))
for name, n in c.most_common(40):
    # names only + counts; no value/verdict payloads
    print("CLAIM", n, name[:80])
