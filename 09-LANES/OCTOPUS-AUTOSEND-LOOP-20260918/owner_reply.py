#!/usr/bin/env python3
"""owner_reply.py — the octopus READS the owner's Telegram answers and acts.

Owner order 2026-09-13: «کامل بساز جوابمو بخونه و عملکرد درست رو تشخیص بده
خودش برای خودش ابزار بسازی و انجام بده».

Loop (every cycle): poll the glass spool (owner bot updates; offset persisted,
owner chat only) -> match each reply to a PENDING card -> recognise the decision
-> dispatch to money_tools -> record receipts -> resolve the card -> confirm back
to the owner in the same Telegram chat. The token stays in-process; nothing is
ever printed.

Owner order 2026-09-18: «ارسالم یک‌کاری کن اختاپوس خودکار هر وقت نیاز دید تایید
بگیره و بفرسته در تلگرام» — so an inline-button tap now counts as the per-item
approval. `go:<did>:email` (button label «تأیید و ارسال ایمیل») carries BOTH the
card identity (8-hex decision id from owner-ask-registry.json) and the channel,
which is exactly what the retired-email ruling demands before a send.

Decision recognition (deterministic keyword intents, Persian + English):
  APPROVE  : بفرست، ارسال، تایید، تأیید، آره، بله، yes, approve, go, ok
  REJECT   : نه، نکن، نمی‌خوام، no, reject, stop
  RATE_CARD: any message containing 'rate' or 'تعرفه' or r'\d+\s*(\$|دلار|aud|/h|هر ساعت)'
  CHANNEL  : any other short text = the named market/channel for TRAFFIC-DECISION
"""
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
OFFSET = ROOT / "tg-offset.txt"
DECISIONS = ROOT / "owner-decisions.jsonl"
SECRETS = pathlib.Path("/home/ari/.config/ofn/secrets.env")

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
APPROVE_PAT = re.compile(r"(بفرست|ارسال|تایید|تأیید|آره|بله|yes|approve|\bgo\b|\bok\b)", re.I)
REJECT_PAT = re.compile(r"(نکن|نه|نمی.?خوام|no|reject|stop)", re.I)
RATE_PAT = re.compile(r"(rate.?card|تعرفه|(\d+(\.\d+)?)\s*(\$|aud|دلار|/(h|hr|ساعت|m2|متر)))", re.I)
CALLBACK_PAT = re.compile(r"^(go|no|later):([0-9a-f]{8})(?::([a-z]+))?$", re.I)
CHANNEL_WORD_PAT = re.compile(r"(ایمیل|email)", re.I)


def env_val(name):
    for line in SECRETS.read_text().splitlines():
        m = re.match(r"%s=(.+)" % name, line.strip())
        if m:
            return m.group(1).strip().strip('"')
    return ""


def send_owner_text(text):
    """Confirm back in the owner chat (sanctioned channel, receipt-only path)."""
    token = env_val("OFN_BOT_TOKEN_OWNER")
    chat = (env_val("OFN_OWNER_USER_IDS") or "").split(",")[0].strip()
    if not token or not chat:
        return False
    body = json.dumps({"chat_id": chat, "text": text[:3800],
                       "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/sendMessage" % token,
        data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


INBOX = ROOT / "tg-inbox.jsonl"
CURSOR = ROOT / "tg-inbox-cursor.txt"


def tg_get(token, chat_allow):
    """Read NEW owner messages from the glass_runner spool (glass holds the
    single getUpdates slot and now persists owner msgs instead of dropping)."""
    if not INBOX.exists():
        return "OK", []
    seen = int(CURSOR.read_text().strip() or 0) if CURSOR.exists() else 0
    lines = INBOX.read_text(errors="replace").strip().splitlines()
    msgs, kept = [], seen
    for i, line in enumerate(lines):
        if i < seen:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            kept = i + 1
            continue
        kept = i + 1
        if str(d.get("chat", "")) in chat_allow.split(","):
            msgs.append({"chat": str(d.get("chat")), "text": str(d.get("text", ""))[:600],
                         "at": str(d.get("at", "")),
                         "kind": str(d.get("kind", "message"))})
    CURSOR.write_text(str(kept), encoding="utf-8")
    return "OK", msgs


def classify(text):
    if RATE_PAT.search(text):
        return "RATE_CARD", text
    if REJECT_PAT.search(text):
        return "REJECT", text
    if APPROVE_PAT.search(text):
        return "APPROVE", text
    return "CHANNEL", text


def review_items():
    if REVIEW.exists():
        return json.loads(REVIEW.read_text(encoding="utf-8")).get("items", [])
    return []


def save_review(items):
    REVIEW.write_text(json.dumps({"at": NOW, "items": items}, indent=1,
                                 sort_keys=True) + "\n", encoding="utf-8")


def load_registry():
    if REGISTRY.exists():
        try:
            return json.loads(REGISTRY.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {"cards": {}}


def save_registry(reg):
    REGISTRY.write_text(json.dumps(reg, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")


def receipt(kind, **kw):
    with RECEIPTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(schema="octopus.owner-reply.v1", at=NOW,
                                 kind=kind, **kw), sort_keys=True) + "\n")


def _dispatch_card(it, kind, raw, channel_from_button=None):
    """Run the typed tool for one identified card. Returns (acted, note)."""
    import money_tools
    iid = str(it.get("id"))
    if kind == "REJECT":
        return {"action": "rejected-by-owner"}, "رد شد — هیچ اقدامی انجام نشد."
    if kind == "RATE_CARD":
        return money_tools.record_rate_card(raw), "نرخ ثبت شد."
    if kind == "APPROVE" and iid == "MONEY-BATCH":
        email_ok = (channel_from_button == "email") or bool(CHANNEL_WORD_PAT.search(raw))
        acted = money_tools.execute_money_batch(packets=it.get("packets") or [],
                                               email_authorized=email_ok)
        n_sent = len(acted.get("email_sent") or [])
        if n_sent:
            note = "✅ %d بسته ارسال شد (رسید ثبت شد)." % n_sent
        else:
            note = ("⚠️ ارسال انجام نشد — دلیل: %s"
                    % str(acted.get("blocked_on") or acted.get("failed") or "?")[:200])
        return acted, note
    if kind == "APPROVE":
        return {"action": "approved-no-typed-tool", "item": iid}, "تأیید ثبت شد."
    if kind == "CHANNEL":
        return {"action": "noted", "item": iid, "text": raw[:80]}, "یادداشت شد."
    if kind == "DEFER":
        return {"action": "deferred"}, "برای بعد نگه داشته شد."
    return None, ""


def main():
    token = env_val("OFN_BOT_TOKEN_OWNER")
    chat_allow = env_val("OFN_OWNER_USER_IDS")
    if not token or not chat_allow:
        print(json.dumps({"at": NOW, "error": "NO_TOKEN_OR_CHAT"}))
        return
    status, msgs = tg_get(token, chat_allow)
    if not msgs:
        print(json.dumps({"at": NOW, "poll": status, "new_owner_messages": len(msgs)}))
        return
    items = review_items()
    reg = load_registry()
    reg_dirty = False
    for m in msgs:
        raw = m["text"]
        cb = CALLBACK_PAT.match(raw.strip())
        channel_from_button = None
        used_registry = False
        target = None
        if cb:
            action, did, channel_from_button = cb.group(1).lower(), cb.group(2).lower(), cb.group(3)
            kind = {"go": "APPROVE", "no": "REJECT", "later": "DEFER"}[action]
            card = reg.get("cards", {}).get(did)
            if card:
                target = next((it for it in items if str(it.get("id")) == str(card["id"])),
                              {"id": card["id"], "packets": card.get("packets") or []})
                used_registry = True
            else:
                receipt("OWNER_CALLBACK_UNKNOWN_CARD", did=did, decision=kind)
                send_owner_text("⚠️ این دکمه مربوط به کارتی است که در فهرست نیست "
                                "(کد %s). هیچ اقدامی انجام نشد." % did)
                with DECISIONS.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"at": m["at"], "read_at": NOW,
                                         "decision": "CALLBACK_UNKNOWN",
                                         "text": raw[:120]}, sort_keys=True) + "\n")
                continue
        else:
            kind, _ = classify(raw)
        with DECISIONS.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": m["at"], "read_at": NOW, "decision": kind,
                                 "text": raw[:200], "kind": m.get("kind")},
                                sort_keys=True) + "\n")
        receipt("OWNER_DECISION_READ", decision=kind, at_msg=m["at"],
                source=m.get("kind"))
        if target is None:
            # a text reply may name a registered decision id — the id is the
            # identity (it resolves to a card we sent), never the wording
            for did, card in (reg.get("cards") or {}).items():
                if did in raw.lower() and str(card.get("state")) == "PENDING":
                    target = next((it for it in items
                                   if str(it.get("id")) == str(card["id"])),
                                  {"id": card["id"], "packets": card.get("packets") or []})
                    used_registry = True
                    break
        if target is None:
            # associate the reply with the card it answers: explicit id/keyword
            # match first, else refuse (no positional guessing — 2026-09-14 rule)
            KEYWORDS = {"MONEY-BATCH": ("پول", "بسته", "quote", "money"),
                        "TRAFFIC-DECISION": ("ترافیک", "تبلیغ", "traffic", "ad")}
            matches = []
            for it in items:
                if it.get("state"):
                    continue
                iid = str(it.get("id", ""))
                if iid.lower() in raw.lower() or any(k in raw.lower()
                                                     for k in KEYWORDS.get(iid, ())):
                    matches.append(it)
            if len(matches) == 1:
                target = matches[0]
            elif len(matches) > 1:
                receipt("OWNER_DECISION_AMBIGUOUS", decision=kind,
                        candidates=[str(x.get("id")) for x in matches][:4])
                continue
        if target is None:
            receipt("OWNER_DECISION_NO_IDENTITY", decision=kind)
            continue
        acted, note = _dispatch_card(target, kind, raw, channel_from_button)
        if acted is None:
            continue
        iid = str(target.get("id"))
        for it in items:
            if str(it.get("id")) == iid:
                it["state"] = ("REJECTED" if kind == "REJECT" else
                               "EXECUTED" if kind == "APPROVE" else
                               "RESOLVED" if kind in ("RATE_CARD", "CHANNEL") else it.get("state"))
                it["result"] = acted
                it["resolved_at"] = NOW
        if used_registry:
            for did, card in (reg.get("cards") or {}).items():
                if str(card.get("id")) == iid and str(card.get("state")) == "PENDING":
                    card["state"] = ("REJECTED" if kind == "REJECT" else
                                     "DEFERRED" if kind == "DEFER" else "EXECUTED")
                    card["resolved_at"] = NOW
                    reg_dirty = True
        receipt("OWNER_DECISION_EXECUTED", item=iid,
                result=json.dumps(acted, default=str)[:300])
        if note:
            send_owner_text(note)
    save_review(items)
    if reg_dirty:
        save_registry(reg)
    print(json.dumps({"at": NOW, "poll": status, "processed": len(msgs)}))


if __name__ == "__main__":
    main()
