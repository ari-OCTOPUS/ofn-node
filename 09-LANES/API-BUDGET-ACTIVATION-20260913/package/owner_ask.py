#!/usr/bin/env python3
"""owner_ask.py — the octopus ASKS the owner via Telegram (no owner polling).

Owner order 2026-09-13: «اختاپوس خودش باید از تلگرام دیگه ازم بگیره وابسته ما
نباشه». Reads state/revenue-drive/owner-review.json, sends each NEW item to the
owner chat as one compact card (GOV-V7 ALLOW_WITH_RECEIPT path; owner contact is
the sanctioned channel), remembers what was already sent (no spam), and records
receipts. The bot token is read in-process from secrets.env and never printed.
Replies flow back through the existing owner channels (owner-go packets / chat).
"""
import json
import pathlib
import re
import time
import urllib.request

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
REVIEW = ROOT / "owner-review.json"
SENT = ROOT / "owner-ask-sent.json"
RECEIPTS = ROOT / "receipts.jsonl"
SECRETS = pathlib.Path("/home/ari/.config/ofn/secrets.env")

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def env_val(name):
    try:
        for line in SECRETS.read_text().splitlines():
            m = re.match(r"%s=(.+)" % name, line.strip())
            if m:
                return m.group(1).strip().strip('"')
    except OSError:
        pass
    return ""


def send_card(text):
    token = env_val("OFN_BOT_TOKEN_OWNER")
    chat = env_val("OFN_OWNER_USER_IDS").split(",")[0].strip()
    if not token or not chat:
        return False, "NO_TOKEN_OR_CHAT"
    body = json.dumps({"chat_id": chat, "text": text,
                       "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/sendMessage" % token,
        data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200, "http_%s" % r.status
    except Exception as exc:  # noqa: BLE001
        return False, type(exc).__name__


review = json.loads(REVIEW.read_text(encoding="utf-8")) if REVIEW.exists() else {"items": []}
sent = json.loads(SENT.read_text(encoding="utf-8")) if SENT.exists() else {"sent": {}}
newly = []
for it in review.get("items", []):
    key = "%s@%s" % (it.get("id"), str(it.get("at", ""))[:13])
    if sent["sent"].get(key):
        continue
    lines = ["🐙 کارت تصمیم — %s" % it.get("id", "?")]
    why = str(it.get("why", ""))[:280]
    if why:
        lines.append(why)
    for i, ch in enumerate(it.get("owner_one_card", []) or [], 1):
        lines.append("%d) %s" % (i, str(ch)[:240]))
    lines.append("— octopus (auto; پاسخ در همین چت)")
    ok, detail = send_card("\n".join(lines))
    sent["sent"][key] = {"at": NOW, "ok": ok, "detail": detail}
    newly.append({"id": it.get("id"), "ok": ok, "detail": detail})
    with RECEIPTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"schema": "octopus.owner-ask.v1", "at": NOW,
                             "item": it.get("id"), "sent_ok": ok,
                             "detail": detail}, sort_keys=True) + "\n")

SENT.write_text(json.dumps(sent, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"at": NOW, "new_cards_sent": newly}))
