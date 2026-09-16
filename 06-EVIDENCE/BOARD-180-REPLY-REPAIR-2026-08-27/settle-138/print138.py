import json, os, sys

base = r"F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\settle-138"
needles = ["be612088", "fresh-e2e-canary-20260827B"]

def keep_obj(obj):
    try:
        s = json.dumps(obj, default=str)
    except Exception:
        s = str(obj)
    return any(n in s for n in needles)

# 138
p138 = os.path.join(base, "obs138_extract.json")
d138 = json.load(open(p138, encoding="utf-8"))
print("===138===")
print("now", d138.get("now_utc"))
print("AUDIT_COUNT", len(d138.get("audit") or []))
for a in d138.get("audit") or []:
    print(json.dumps(a, indent=2, default=str)[:4000])
print("RECEIPTS", len(d138.get("receipts") or []))
for r in d138.get("receipts") or []:
    print(json.dumps(r, indent=2, default=str)[:3000])
print("RELATED", len(d138.get("related_processed") or []))
for r in d138.get("related_processed") or []:
    print(json.dumps(r, indent=2, default=str)[:4000])
vd = d138.get("verify_dispatch")
print("VERIFY_DISPATCH")
print(json.dumps(vd, indent=2, default=str)[:8000])
print("RECENT_PROCESSED_NEEDLES")
for r in d138.get("recent_processed") or []:
    if r.get("has_needle"):
        print(json.dumps(r, indent=2, default=str)[:2500])
print("RECENT_TOP5")
for r in (d138.get("recent_processed") or [])[:8]:
    data = r.get("data") or {}
    print(r.get("mtime_iso"), r.get("path"), data.get("message_type"), data.get("message_id"), data.get("run_id"), data.get("sender_node"), data.get("recipient_node"), (data.get("payload") or {}).get("task") if isinstance(data.get("payload"), dict) else None)