#!/usr/bin/env python3
"""Peek Telegram for pending owner updates (token never printed).
Spools any unseen owner message to the MONEY inbox and advances the glass
offset so glass won't duplicate it."""
import json
import pathlib
import re
import sys
import urllib.request

SEC = pathlib.Path("/home/ari/.config/ofn/secrets.env").read_text()
TOK = re.search(r"^OFN_BOT_TOKEN_OWNER=(.+)$", SEC, re.M).group(1).strip().strip('"')
ALLOWED = re.search(r"^OFN_OWNER_USER_IDS=(.+)$", SEC, re.M).group(1).strip().strip('"')
OFF_FILE = pathlib.Path("/home/ari/ofn/data/state/glass-offset.txt")
INBOX = pathlib.Path("/home/ari/ofn/state/revenue-drive/tg-inbox.jsonl")
off = int(OFF_FILE.read_text().strip() or 0) if OFF_FILE.exists() else 0
print("glass offset on disk:", off)

body = json.dumps({"offset": off + 1, "timeout": 0, "limit": 100}).encode()
req = urllib.request.Request("https://api.telegram.org/bot%s/getUpdates" % TOK,
                             data=body, headers={"Content-Type": "application/json"},
                             method="POST")
d = json.load(urllib.request.urlopen(req, timeout=20))
ups = d.get("result", [])
print("pending updates returned:", len(ups))

import time
spooled = 0
max_id = off
for u in ups:
    max_id = max(max_id, int(u.get("update_id", 0)))
    cb = u.get("callback_query")
    m = u.get("message") or {}
    chat = str(((m.get("chat") or ((cb or {}).get("message") or {}).get("chat") or {})).get("id", ""))
    txt = str(m.get("text") or (cb or {}).get("data") or "")
    kind = "callback" if cb else "message"
    print("  ", u.get("update_id"), kind, "chat=", chat, repr(txt[:70]))
    if chat in ALLOWED.split(",") and txt:
        with INBOX.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"chat": chat, "text": txt[:600],
                                 "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                 "lane": "MONEY", "route_reason": "peek-backfill",
                                 "kind": kind, "backfilled": True},
                                ensure_ascii=False) + "\n")
        spooled += 1
if max_id > off:
    OFF_FILE.write_text(str(max_id), encoding="utf-8")
    print("offset advanced to:", max_id)
print("spooled owner updates:", spooled)
print("OPEN_CARDS_HINT: run owner_reply next")
sys.exit(0)
