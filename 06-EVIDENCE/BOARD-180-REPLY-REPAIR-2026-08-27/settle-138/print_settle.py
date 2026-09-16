import json, os
p=r"F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\settle-138\obs138_settle.json"
d=json.load(open(p,encoding="utf-8"))
print("now", d.get("now_utc"))
print("RECEIPT_577")
print(json.dumps(d.get("receipt_577"), indent=2))
print("STATE_HITS")
for h in d.get("state_hits") or []:
    print(h.get("path"), h.get("mtime_iso"))
    if "data" in h:
        data=h["data"]
        if isinstance(data, dict) and "be612088-7154-45ea-a96b-0d777c7689ff" in data:
            print("verify_key", json.dumps(data.get("be612088-7154-45ea-a96b-0d777c7689ff"), indent=2, default=str)[:2000])
        else:
            print(json.dumps(data, indent=2, default=str)[:2000])
    else:
        print(h.get("snippet"))
print("AUDIT this-run")
for a in d.get("audit") or []:
    s=json.dumps(a, default=str)
    if any(n in s for n in ["577b0e22","04af67d5","fresh-e2e-canary-20260827B","7ae7326a"]):
        print(s[:600])