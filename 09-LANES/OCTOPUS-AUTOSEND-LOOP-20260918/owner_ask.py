#!/usr/bin/env python3
"""owner_ask.py — the octopus ASKS the owner via Telegram (no owner polling).

Owner order 2026-09-13: «اختاپوس خودش باید از تلگرام دیگه ازم بگیره وابسته ما
نباشه». Reads state/revenue-drive/owner-review.json, sends each NEW item to the
owner chat as one compact card (GOV-V7 ALLOW_WITH_RECEIPT path; owner contact is
the sanctioned channel), remembers what was already sent (no spam), and records
receipts. The bot token is read in-process from secrets.env and never printed.

Owner order 2026-09-18: «ارسالم یک‌کاری کن اختاپوس خودکار هر وقت نیاز دید تایید
بگیره و بفرسته در تلگرام» — so every card now carries a decision id (8 hex) and
an inline keyboard: one TAP is the per-item approval, and the button label names
the channel (ایمیل) exactly as the retired-email ruling requires. The tap is
consumed by owner_reply.py through the glass spool; nothing needs the chat.
"""
import hashlib
import json
import pathlib
import re
import time
import urllib.request

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
REVIEW = ROOT / "owner-review.json"
SENT = ROOT / "owner-ask-sent.json"
REGISTRY = ROOT / "owner-ask-registry.json"
RECEIPTS = ROOT / "receipts.jsonl"
SECRETS = pathlib.Path("/home/ari/.config/ofn/secrets.env")

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# which channel a card's approval authorizes; the button label says it out loud
CARD_CHANNEL = {"MONEY-BATCH": "email"}


def policy_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def env_val(name):
    try:
        for line in SECRETS.read_text().splitlines():
            m = re.match(r"%s=(.+)" % name, line.strip())
            if m:
                return m.group(1).strip().strip('"')
    except OSError:
        pass
    return ""


def send_card(text, keyboard=None):
    token = env_val("OFN_BOT_TOKEN_OWNER")
    chat = env_val("OFN_OWNER_USER_IDS").split(",")[0].strip()
    if not token or not chat:
        return False, "NO_TOKEN_OR_CHAT"
    body = {"chat_id": chat, "text": text, "disable_web_page_preview": True}
    if keyboard:
        body["reply_markup"] = {"inline_keyboard": keyboard}
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/sendMessage" % token,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200, "http_%s" % r.status
    except Exception as exc:  # noqa: BLE001
        return False, type(exc).__name__


def keyboard_for(item_id, did, channel):
    if channel:
        go_label = "✅ تأیید و ارسال ایمیل"
        go_data = "go:%s:email" % did
    else:
        go_label = "✅ تأیید"
        go_data = "go:%s" % did
    return [[{"text": go_label, "callback_data": go_data},
             {"text": "⛔ رد", "callback_data": "no:%s" % did},
             {"text": "⏸ بعداً", "callback_data": "later:%s" % did}]]


def main():
    review = (json.loads(REVIEW.read_text(encoding="utf-8"))
              if REVIEW.exists() else {"items": []})
    sent = (json.loads(SENT.read_text(encoding="utf-8"))
            if SENT.exists() else {"sent": {}})
    registry = (json.loads(REGISTRY.read_text(encoding="utf-8"))
                if REGISTRY.exists() else {"cards": {}})
    newly = []
    for it in review.get("items", []):
        iid = str(it.get("id", "?"))
        key = "%s@%s" % (iid, str(it.get("at", ""))[:13])
        if sent["sent"].get(key):
            continue
        did = policy_hash("%s|%s" % (iid, it.get("at", "")))
        packets = [str(p) for p in (it.get("packets") or [])]
        channel = CARD_CHANNEL.get(iid)
        lines = ["🐙 کارت تصمیم — %s" % iid, "کد تصمیم: %s" % did]
        why = str(it.get("why", ""))[:280]
        if why:
            lines.append(why)
        for i, ch in enumerate(it.get("owner_one_card", []) or [], 1):
            lines.append("%d) %s" % (i, str(ch)[:240].replace("%d", str(len(packets)))))
        if channel:
            lines.append("— تأیید = ارسال از کانال %s (همین لحظه اجرا می‌شود)"
                         % ("ایمیل" if channel == "email" else channel))
        lines.append("— یا بنویسید: تأیید %s ایمیل" % did)
        ok, detail = send_card("\n".join(lines),
                               keyboard_for(iid, did, channel))
        sent["sent"][key] = {"at": NOW, "ok": ok, "detail": detail, "did": did}
        registry["cards"][did] = {"id": iid, "at": str(it.get("at", "")),
                                  "card_sent_at": NOW, "packets": packets,
                                  "channel": channel, "state": "PENDING",
                                  "sent_ok": ok}
        newly.append({"id": iid, "did": did, "ok": ok, "detail": detail})
        with RECEIPTS.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"schema": "octopus.owner-ask.v2", "at": NOW,
                                 "item": iid, "decision_id": did,
                                 "has_buttons": True, "sent_ok": ok,
                                 "detail": detail}, sort_keys=True) + "\n")

    SENT.write_text(json.dumps(sent, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")
    REGISTRY.write_text(json.dumps(registry, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"at": NOW, "new_cards_sent": newly}))


if __name__ == "__main__":
    main()
