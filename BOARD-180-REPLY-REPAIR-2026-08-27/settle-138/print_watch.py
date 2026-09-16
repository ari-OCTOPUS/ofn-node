import json, os, re
base = r"F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\settle-138"
e=json.load(open(os.path.join(base,"obs182_focus.json"),encoding="utf-8"))
print("182 now", e.get("now_utc"), "inbox", e.get("inbox_count"), "pos", e.get("inbox_pos_04af67d5"), "still", e.get("still_in_inbox"))
print("hits", len(e.get("processed_hits") or []), "audit", len(e.get("audit") or []))
print("timer", (e.get("timer") or "").replace("\n"," | "))
print("service", e.get("service"), (e.get("service_show") or "").replace("\n"," | "))
print("receipts", e.get("recent_receipts"))
j = e.get("journal") or ""
# extract claimed mids and 04af action
claimed = re.findall(r'"claimed":\s*(\d+)', j)
maxn = re.findall(r'"max_n":\s*(\d+)', j)
print("journal_claimed", claimed[-3:], "max_n", maxn[-3:])
# find 04af action
for m in re.finditer(r'"mid": "04af67d5[^"]*"\s*,\s*"action": "([^"]+)"', j):
    print("04af_action", m.group(1))
# last claimed from receipts
if e.get("recent_receipts"):
    print("last_claim_receipt", e["recent_receipts"][0])
# safe_hold
if "safe_hold" in j.lower() or "SAFE_HOLD" in j:
    print("SAFE_HOLD_SEEN")
print("JOURNAL_TAIL")
print(j[-1800:])
d=json.load(open(os.path.join(base,"obs138_focus.json"),encoding="utf-8"))
print("138 now", d.get("now_utc"), "audit", len(d.get("audit") or []), "proc", len(d.get("processed_hits") or []), "receipts", len(d.get("receipt_hits") or []))
print("138 ids", [(p.get("message_type"), p.get("message_id"), p.get("sender")) for p in (d.get("processed_hits") or [])])