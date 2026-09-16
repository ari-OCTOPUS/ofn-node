#!/usr/bin/env python3
"""money_tools.py — typed tools the octopus built for its own money loop.

GOV-FREEDOM-V2 section 2 allows generating new typed tools inside the non-TCB
Tool Broker. These are the money tools. Every tool is deterministic, receipts
what it does, and never touches the Telegram bot token.

Honest boundary handled here: the EMAIL channel is RETIRED by owner ruling
(GOV-V7 era; "no email is sent"). So execute_money_batch() does NOT send email
unless the owner's approval explicitly named email/ایمیل. Without that, packets
are staged in a ready-to-send queue and one precise follow-up card asks the
owner to re-authorize the email channel. Nothing is silently revived.
"""
import json
import pathlib
import re
import time

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
PACKETS = ROOT / "quote-packets"
SEND_QUEUE = ROOT / "send-queue"
RECEIPTS = ROOT / "receipts.jsonl"
RATE_CARD = pathlib.Path("/home/ari/ofn/data/rate-card.json")

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def receipt(kind, **kw):
    with RECEIPTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(schema="octopus.money-tools.v1", at=NOW,
                                 kind=kind, **kw), sort_keys=True) + "\n")


def record_rate_card(text):
    """RATE_CARD tool: extract the first price-like token and store it."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*(\$|aud|دلار)?\s*(/(?:h|hr|ساعت|m2|متر))?", text, re.I)
    card = {"schema": "octopus.rate-card.v1", "at": NOW,
            "source": "owner telegram reply", "raw_first_price": m.group(0) if m else None}
    RATE_CARD.parent.mkdir(parents=True, exist_ok=True)
    RATE_CARD.write_text(json.dumps(card, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    receipt("RATE_CARD_RECORDED", price=card["raw_first_price"])
    return {"rate_card_written": True, "price": card["raw_first_price"],
            "note": "full line-item rate card can be extended in data/rate-card.json"}


def prepare_channel_assets(channel):
    """TRAFFIC tool: build local campaign assets for the named channel."""
    out = ROOT / "campaign" / re.sub(r"[^a-z0-9_-]+", "_", channel.lower())[:40]
    out.mkdir(parents=True, exist_ok=True)
    leads = json.loads(pathlib.Path("/home/ari/ofn/tools/leads_master.json")
                       .read_text(errors="replace")).get("accounts", [])
    top = [a.get("business_name") for a in leads
           if str(a.get("priority", "")).lower() == "high"][:10]
    (out / "plan.json").write_text(json.dumps({
        "schema": "octopus.campaign.v1", "at": NOW, "channel": channel,
        "target_leads_top": top, "status": "ASSETS_PREPARED_LOCALLY",
        "paid_spend": 0.0}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    receipt("CAMPAIGN_ASSETS_PREPARED", channel=channel[:60], leads=len(top))
    return {"channel": channel[:60], "assets": str(out), "top_leads": len(top)}


def execute_money_batch(packets, email_authorized):
    """MONEY-BATCH tool: send the quote packets.

    Email is a retired channel; sending revives it ONLY on explicit owner words
    naming email/ایمیل in the approval. Otherwise packets move to a ready
    send-queue and the follow-up card asks exactly that one question.
    """
    SEND_QUEUE.mkdir(parents=True, exist_ok=True)
    staged = []
    for pid in packets:
        src = PACKETS / (pid + ".json")
        if src.exists():
            (SEND_QUEUE / src.name).write_text(src.read_text(encoding="utf-8"),
                                               encoding="utf-8")
            staged.append(pid)
    if email_authorized:
        # send via the retired-but-reauthorized channel (Gmail SMTP, in-process creds)
        import smtplib
        from email.message import EmailMessage
        import os
        addr = os.environ.get("GMAIL_ADDRESS", "")
        pw = os.environ.get("GMAIL_APP_PASSWORD", "")
        sent, failed = [], []
        for pid in staged:
            pkt = json.loads((SEND_QUEUE / (pid + ".json")).read_text(encoding="utf-8"))
            to = (pkt.get("lead") or {}).get("contact_channel") or ""
            em = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", to)
            if not (addr and pw and em):
                failed.append({"packet": pid, "reason": "NO_EMAIL_ADDRESS_OR_CREDS"})
                continue
            msg = EmailMessage()
            msg["From"], msg["To"] = addr, em.group(0)
            msg["Subject"] = "Painting services quote — %s" % (pkt.get("market", ""))
            msg.set_content(json.dumps(pkt.get("lead", {}), indent=1, default=str)[:1500])
            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
                    s.login(addr, pw)
                    s.send_message(msg)
                sent.append(pid)
            except Exception as exc:  # noqa: BLE001
                failed.append({"packet": pid, "reason": type(exc).__name__})
        receipt("MONEY_BATCH_EMAIL_SENT", sent=sent, failed=failed)
        return {"email_sent": sent, "failed": failed, "staged": staged}
    receipt("MONEY_BATCH_STAGED", staged=staged,
            email_channel="retired — needs explicit owner re-authorization")
    return {"staged": staged, "email_sent": [],
            "blocked_on": "EMAIL_CHANNEL_RETIRED — reply must name ایمیل/email "
                          "explicitly to authorize sending"}
