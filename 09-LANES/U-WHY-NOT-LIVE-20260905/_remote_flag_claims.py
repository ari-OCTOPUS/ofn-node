import json

want = {
    "flag:OCTOPUS_WIRE_LEAD_OUTBOUND",
    "flag:OFN_WIRE_OUTBOUND",
    "flag:OCTOPUS_BRIDGE_OUTBOUND_ENABLED",
    "flag:OCTOPUS_WIRE_LEAD_OUTBOUND_WAL",
}
last = {}
p = "/home/ari/ofn/data/state/legs/claims-ledger.jsonl"
with open(p, encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        claim = obj.get("claim")
        if claim in want:
            last[claim] = {
                "recorded_at": obj.get("recorded_at"),
                "value": obj.get("value"),
                "verdict": obj.get("verdict"),
            }
for k in sorted(last):
    row = last[k]
    print(k, "at", row.get("recorded_at"), "value", row.get("value"), "verdict", row.get("verdict"))
