#!/usr/bin/env python3
"""owner_reply.py — the octopus READS the owner's Telegram answers and acts.

Owner order 2026-09-13: «کامل بساز جوابمو بخونه و عملکرد درست رو تشخیص بده
خودش برای خودش ابزار بسازی و انجام بده».

Loop (every cycle): poll Telegram getUpdates (owner bot, offset persisted,
owner chat only) -> match each reply to a PENDING card in owner-review.json ->
recognise the decision -> dispatch to money_tools -> record receipts ->
resolve the card. The token stays in-process; nothing is ever printed.

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
RECEIPTS = ROOT / "receipts.jsonl"
OFFSET = ROOT / "tg-offset.txt"
DECISIONS = ROOT / "owner-decisions.jsonl"
SECRETS = pathlib.Path("/home/ari/.config/ofn/secrets.env")

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
APPROVE_PAT = re.compile(r"(بفرست|ارسال|تایید|تأیید|آره|بله|yes|approve|\bgo\b|\bok\b)", re.I)
REJECT_PAT = re.compile(r"(نکن|نه|نمی.?خوام|no|reject|stop)", re.I)
RATE_PAT = re.compile(r"(rate.?card|تعرفه|(\d+(\.\d+)?)\s*(\$|aud|دلار|/(h|hr|ساعت|m2|متر)))", re.I)


def env_val(name):
    for line in SECRETS.read_text().splitlines():
        m = re.match(r"%s=(.+)" % name, line.strip())
        if m:
            return m.group(1).strip().strip('"')
    return ""


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
                         "at": str(d.get("at", ""))})
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


def receipt(kind, **kw):
    with RECEIPTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(schema="octopus.owner-reply.v1", at=NOW,
                                 kind=kind, **kw), sort_keys=True) + "\n")


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
    for m in msgs:
        kind, raw = classify(m["text"])
        with DECISIONS.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": m["at"], "read_at": NOW, "decision": kind,
                                 "text": raw[:200]}, sort_keys=True) + "\n")
        receipt("OWNER_DECISION_READ", decision=kind, at_msg=m["at"])
        # associate the reply with the card it answers: explicit id/keyword
        # match first, else the OLDEST pending card (FIFO matches card order)
        KEYWORDS = {"MONEY-BATCH": ("پول", "بسته", "quote", "money"),
                    "TRAFFIC-DECISION": ("ترافیک", "تبلیغ", "traffic", "ad")}
        target = None
        # OWNER DECISION 2026-09-14 (ambiguity): with more than one unresolved card of the
        # same kind, a keyword match is NOT identity. Picking the first was a silent guess.
        # One match -> that card. Several -> refuse with a clear disposition and no effect.
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
            # OWNER DECISION 2026-09-14: a reply that does not name the card it is about
            # must NOT create a money effect. The old fallback attached a bare approval to
            # the OLDEST unresolved card, so an unidentifiable message could act on money.
            # APPROVE_PAT is NOT widened; this only removes the positional fallback.
            receipt("OWNER_DECISION_NO_IDENTITY", decision=kind)
            continue
        acted = None
        import money_tools
        for it in ([target] if target else []):
            iid = it.get("id")
            if it.get("state") in ("RESOLVED", "RESOLVED_APPROVED", "RESOLVED_NOTED",
                                   "EXECUTED", "REJECTED"):
                continue
            if kind == "REJECT":
                it["state"] = "REJECTED"
                acted = {"action": "rejected-by-owner"}
            elif kind == "RATE_CARD":
                acted = money_tools.record_rate_card(raw)
                it["state"] = "RESOLVED"; it["result"] = acted
            elif kind == "APPROVE" and iid == "MONEY-BATCH":
                acted = money_tools.execute_money_batch(
                    packets=it.get("packets") or [],
                    email_authorized=re.search(r"(ایمیل|email)", raw, re.I) is not None)
                it["state"] = "EXECUTED"; it["result"] = acted
            elif kind == "APPROVE":
                it["state"] = "RESOLVED_APPROVED"
                acted = {"action": "approved-no-typed-tool", "item": iid}
            elif kind == "CHANNEL" and iid == "TRAFFIC-DECISION":
                acted = money_tools.prepare_channel_assets(raw[:200])
                it["state"] = "RESOLVED"; it["result"] = acted
            elif kind == "CHANNEL":
                it["state"] = "RESOLVED_NOTED"
                acted = {"action": "noted", "item": iid, "text": raw[:80]}
            if acted:
                receipt("OWNER_DECISION_EXECUTED", item=iid,
                        result=json.dumps(acted, default=str)[:300])
                break
        save_review(items)
    print(json.dumps({"at": NOW, "poll": status,
                      "processed": len(msgs)}))


if __name__ == "__main__":
    main()
