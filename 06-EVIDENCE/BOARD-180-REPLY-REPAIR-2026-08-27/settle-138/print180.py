import json, os
base = r"F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\settle-138"
needles = ["be612088", "fresh-e2e-canary-20260827B"]
d = json.load(open(os.path.join(base, "obs180_extract.json"), encoding="utf-8"))
print("===180===")
print("host", d.get("host"), "now", d.get("now_utc"), "mesh", d.get("mesh"))
print("HITS_TOTAL", len(d.get("hits") or []))
print("OUTBOX_PY")
print(json.dumps(d.get("outbox_py_all"), indent=2)[:4000])
print("OUTBOX_CAND", json.dumps(d.get("outbox_py_candidates"), indent=2))
print("TREE_KEYS", list((d.get("tree") or {}).keys()))
for sub in ["pending","outbox","replies","processed","logs","inbox","receipts","audit","state","runtime"]:
    t = (d.get("tree") or {}).get(sub)
    if not t:
        continue
    print("SUB", sub, "exists", t.get("exists"), "count", t.get("count"), "err", t.get("err"))
    for it in (t.get("recent") or [])[:12]:
        print(" ", it.get("mtime_iso"), it.get("size"), it.get("name"))

print("===180 HITS FOR THIS CANARY===")
kept = 0
for h in d.get("hits") or []:
    blob = json.dumps(h, default=str)
    if not any(n in blob for n in needles):
        continue
    kept += 1
    print("---HIT", kept, h.get("path"), h.get("size"), h.get("mtime_iso"))
    if "data" in h:
        print(json.dumps(h["data"], indent=2, default=str)[:3500])
    else:
        print((h.get("snippet") or "")[:1500])
print("KEPT", kept)

print("===180 SYSTEMCTL===")
sc = d.get("systemctl") or {}
print("mesh_active", (sc.get("mesh_active") or "")[:500])
units = sc.get("units") or ""
for line in units.splitlines():
    low = line.lower()
    if any(x in low for x in ["octopus", "outbox", "reply", "worker", "mesh"]):
        print(line)