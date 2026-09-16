import json, os
base = r"F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\settle-138"
print("===138 FOCUS===")
d=json.load(open(os.path.join(base,"obs138_focus.json"),encoding="utf-8"))
print("now", d.get("now_utc"))
print("AUDIT")
for a in d.get("audit") or []:
    print(json.dumps(a, default=str)[:500])
print("RECEIPTS")
print(json.dumps(d.get("receipt_hits"), indent=2, default=str)[:2000])
print("VERIFY", d.get("verify"))
print("PROC")
for p in d.get("processed_hits") or []:
    print(p.get("mtime_iso"), p.get("message_type"), p.get("message_id"), p.get("sender"), p.get("path"))

print("\n===182 FOCUS===")
e=json.load(open(os.path.join(base,"obs182_focus.json"),encoding="utf-8"))
print("now", e.get("now_utc"), "inbox", e.get("inbox_count"), "pos", e.get("inbox_pos_04af67d5"), "still", e.get("still_in_inbox"))
print("AUDIT", json.dumps(e.get("audit"), default=str)[:1500])
print("HITS", e.get("processed_hits"))
print("WITNESS", json.dumps(e.get("witness_state"), indent=2, default=str)[:4000])
print("TIMER", e.get("timer"))
print("SERVICE", e.get("service"))
print("SERVICE_SHOW", e.get("service_show"))
print("RECENT_RECEIPTS", e.get("recent_receipts"))
print("RECENT_OUTBOX", e.get("recent_outbox"))
print("RECENT_PROCESSED", e.get("recent_processed"))
print("JOURNAL")
print((e.get("journal") or "")[-3500:])