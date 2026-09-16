import json, os
base = r"F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\settle-138"
d = json.load(open(os.path.join(base, "obs182_extract.json"), encoding="utf-8"))
print("===182===")
print("host", d.get("host"), "now", d.get("now_utc"), "mesh", d.get("mesh"))
print("HITS", len(d.get("hits") or []))
for h in d.get("hits") or []:
    print("---", h.get("path"), h.get("size"), h.get("mtime_iso"))
    if "data" in h:
        print(json.dumps(h["data"], indent=2, default=str)[:4000])
    else:
        print((h.get("snippet") or "")[:2000])
print("TREE")
for sub, t in (d.get("tree") or {}).items():
    if sub == "root":
        print("ROOT", t)
        continue
    print("SUB", sub, "exists", t.get("exists"), "count", t.get("count"))
    for it in (t.get("recent") or [])[:10]:
        print(" ", it.get("mtime_iso"), it.get("size"), it.get("name"))
print("TIMER")
print(json.dumps(d.get("timer"), indent=2, default=str)[:12000])