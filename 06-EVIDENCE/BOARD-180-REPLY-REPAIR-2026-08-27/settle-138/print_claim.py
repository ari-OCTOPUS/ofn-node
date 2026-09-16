import json, os
base = r"F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\settle-138"
print("======== 138 ========")
d=json.load(open(os.path.join(base,"obs138_focus.json"),encoding="utf-8"))
print("now", d.get("now_utc"))
print("AUDIT")
for a in d.get("audit") or []:
    print(json.dumps(a, default=str)[:700])
print("RECEIPTS")
print(json.dumps(d.get("receipt_hits"), indent=2, default=str)[:3000])
print("VERIFY", d.get("verify"))
print("PROC")
for p in d.get("processed_hits") or []:
    print("---", p.get("mtime_iso"), p.get("message_type"), p.get("message_id"), p.get("sender"), p.get("path"))
    print(json.dumps(p.get("data"), indent=2, default=str)[:3500])

print("\n======== 182 ========")
e=json.load(open(os.path.join(base,"obs182_focus.json"),encoding="utf-8"))
print("now", e.get("now_utc"), "inbox", e.get("inbox_count"), "pos", e.get("inbox_pos_04af67d5"), "still", e.get("still_in_inbox"))
print("AUDIT")
for a in e.get("audit") or []:
    print(json.dumps(a, default=str)[:800])
print("HITS")
for h in e.get("processed_hits") or []:
    print("---", h.get("path"), h.get("mtime_iso"))
    print(json.dumps(h.get("data"), indent=2, default=str)[:3500])
print("RECEIPTS", e.get("recent_receipts"))
print("OUTBOX", e.get("recent_outbox"))
print("PROCESSED", e.get("recent_processed"))
print("TIMER", e.get("timer"))
print("SERVICE", e.get("service"), e.get("service_show"))
print("JOURNAL_TAIL")
print((e.get("journal") or "")[-2500:])