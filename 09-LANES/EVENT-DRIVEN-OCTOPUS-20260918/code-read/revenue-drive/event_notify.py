#!/usr/bin/env python3
"""Event-driven owner reporting (owner 2026-09-18: event-driven only, no digest).
Sends ONE Telegram line when something real happened since the last look:
  - a new send (sent-log row)
  - a customer reply (REPLY_DETECTED)
  - a failure/pause (SEND-PAUSED, *_FAILED)
Silent otherwise. Cursor = hashes of material events already reported."""
import hashlib, json, pathlib, time
RD = pathlib.Path(__file__).resolve().parent
CURSOR = RD / "event-notify-cursor.json"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def load(p, default):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default

def lines(p):
    try:
        return [json.loads(l) for l in pathlib.Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []

def main():
    seen = set(load(CURSOR, {"hashes": []}).get("hashes", []))
    events, new_hashes = [], set(seen)
    for r in lines(RD / "sent-log.jsonl")[-40:]:
        h = hashlib.sha256(json.dumps([r.get("at"), r.get("packet"), r.get("kind")], sort_keys=True).encode()).hexdigest()[:16]
        if h in seen:
            continue
        new_hashes.add(h)
        if r.get("kind") in ("quote", "followup_1", "followup_7"):
            if r.get("outcome") == "sent":
                events.append("\U0001F4E4 \u0627\u0631\u0633\u0627\u0644: %s (%s)" % (r.get("packet"), r.get("to_domain") or r.get("kind")))
    for r in lines(RD / "tg-inbox.jsonl")[-40:]:
        if r.get("kind") != "REPLY_DETECTED":
            continue
        h = hashlib.sha256(json.dumps([r.get("at"), r.get("from"), "reply"], sort_keys=True).encode()).hexdigest()[:16]
        if h in seen:
            continue
        new_hashes.add(h)
        events.append("\U0001F4E5 \u067E\u0627\u0633\u062E \u0645\u0634\u062a\u0631\u06cc: %s" % str(r.get("from", ""))[-40:])
    for r in lines(RD / "receipts.jsonl")[-60:]:
        k = str(r.get("kind", ""))
        if not (k.endswith("_FAILED") or k == "SEND_PAUSED"):
            continue
        h = hashlib.sha256(json.dumps([r.get("at"), k], sort_keys=True).encode()).hexdigest()[:16]
        if h in seen:
            continue
        new_hashes.add(h)
        events.append("\u26A0 \u062E\u0637\u0627: %s" % k)
    if events:
        try:
            import sys as _s
            _s.path.insert(0, str(RD))
            import owner_reply as _or
            _or.send_owner_text("\U0001F419 \u0627\u062E\u0628\u0627\u0631 \u062a\u0627\u0632\u0647:\n" + "\n".join(events[:8]))
        except Exception:
            pass
    CURSOR.write_text(json.dumps({"hashes": sorted(new_hashes)[-400:], "at": NOW}), encoding="utf-8")
    print(json.dumps({"at": NOW, "events": len(events)}))

if __name__ == "__main__":
    main()
