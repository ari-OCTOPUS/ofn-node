import json, os
base = r"F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\settle-138"

print("======== 138 ========")
d=json.load(open(os.path.join(base,"obs138_poll.json"),encoding="utf-8"))
print("now", d.get("now_utc"), "verify_has_run", d.get("verify_has_run"))
print("AUDIT")
for a in d.get("audit") or []:
    print(json.dumps(a, default=str)[:800])
print("RECEIPT_HITS", len(d.get("receipt_hits") or []))
for r in d.get("receipt_hits") or []:
    print(json.dumps(r, default=str)[:800])
print("PROCESSED_HITS")
for r in d.get("processed_hits") or []:
    print("---", r.get("path"))
    print(json.dumps(r.get("data") or r, indent=2, default=str)[:3500])
print("VERIFY_MATCH")
print(json.dumps(d.get("verify_match"), indent=2, default=str)[:4000])
print("RECENT_PROCESSED")
for it in ((d.get("processed") or {}).get("recent") or [])[:10]:
    print(it)
print("RECENT_RECEIPTS")
for it in ((d.get("receipts") or {}).get("recent") or [])[:8]:
    print(it)

print("\n======== 180 ========")
e=json.load(open(os.path.join(base,"obs180_poll.json"),encoding="utf-8"))
print("now", e.get("now_utc"), "outbox_sha", e.get("outbox_sha"))
print("INBOX", e.get("inbox"))
print("PROCESSED", e.get("processed"))
print("OUTBOX recent", (e.get("outbox") or {}).get("recent"))
print("RECEIPTS", e.get("receipts"))
print("ARCHIVE", e.get("archive"))
print("STATE", e.get("state"))
print("STATE_REPLIES", e.get("state_replies"))
print("STATE_COG", e.get("state_cognition"))
print("UNITS")
for ln in e.get("units") or []:
    print(ln)
print("TIMERS")
for ln in e.get("timers") or []:
    print(ln)
print("BIN", e.get("bin"))
print("HITS", len(e.get("hits") or []))
for h in e.get("hits") or []:
    print("---", h.get("path"), h.get("size"), h.get("mtime_iso"))
    if "data" in h:
        print(json.dumps(h["data"], indent=2, default=str)[:3000])
    else:
        print((h.get("snippet") or "")[:800])

print("\n======== 182 ========")
f=json.load(open(os.path.join(base,"obs182_poll.json"),encoding="utf-8"))
print("now", f.get("now_utc"), "leftover_c3", f.get("leftover_c3f085a8_inbox"), "service", f.get("service"))
print("TIMER", f.get("timer"))
print("MAX_N", f.get("max_n_mentions"))
print("HITS", len(f.get("hits") or []))
for h in f.get("hits") or []:
    print("---", h.get("path"), h.get("size"), h.get("mtime_iso"))
    if "data" in h:
        print(json.dumps(h["data"], indent=2, default=str)[:2500])
    else:
        print((h.get("snippet") or "")[:800])
print("INBOX recent", ((f.get("inbox") or {}).get("recent") or [])[:6])
print("PROCESSED recent", ((f.get("processed") or {}).get("recent") or [])[:6])
print("OUTBOX recent", ((f.get("outbox") or {}).get("recent") or [])[:6])