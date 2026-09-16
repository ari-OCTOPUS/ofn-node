#!/usr/bin/env python3
"""send_reply_3991.py — FIRST CUSTOMER REPLY RESPONSE (2026-09-16).

Absolute Strata (reception@absolutestrata.com.au, QP-20260913-3991) replied to our
follow-up_1 asking: "which building address/strata plan number is this referring to?"
This answers honestly: portfolio outreach, per-building quotes, ask what they manage.
Idempotent on (packet, kind=reply_1). Same authorized channel + receipts as funnel.
"""
import json, os, pathlib, smtplib, sys, time
from email.message import EmailMessage

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
SENTLOG = ROOT / "sent-log.jsonl"
RECEIPTS = ROOT / "receipts.jsonl"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
TO = "reception@absolutestrata.com.au"
PACKET = "QP-20260913-3991"

if SENTLOG.exists():
    for line in SENTLOG.read_text(errors="replace").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("kind") == "reply_1" and r.get("packet") == PACKET and r.get("outcome") == "sent":
            print(json.dumps({"status": "ALREADY_SENT"})); sys.exit(0)

addr = os.environ.get("GMAIL_ADDRESS", "")
pw = os.environ.get("GMAIL_APP_PASSWORD", "")
if not (addr and pw):
    print(json.dumps({"error": "NO_CREDS"})); sys.exit(2)

msg = EmailMessage()
msg["From"], msg["To"] = addr, TO
msg["Subject"] = "Re: Painting services quote — quick question"
msg.set_content(
    "Hi,\n\n"
    "Thanks for getting back to me.\n\n"
    "To answer your question: this isn't tied to one specific building — I reached out "
    "about our strata repaint work generally. We repaint and maintain common areas and "
    "exteriors for strata-managed properties across Sydney Metro (stairwells, foyers, "
    "balconies, external walls), working to AGRR-compliant schedules so committees get "
    "proper scope documents.\n\n"
    "So the easiest next step from your side: if you send me one building you manage "
    "(address is enough, strata plan number if handy), I'll put together a specific "
    "quote for it — no obligation. If it's easier, just tell me which suburbs your "
    "Sydney properties are in and I'll flag what a typical repainting cycle looks like "
    "for that area.\n\n"
    "Either way, happy to forward scope samples if that helps the correct manager.\n\n"
    "Thanks again,\n"
    "Armin — Painting & Maintenance Services, Sydney\n")

outcome, err = "sent", ""
try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
        s.login(addr, pw)
        s.send_message(msg)
except Exception as exc:
    outcome, err = "failed:%s" % type(exc).__name__, str(exc)[:200]

row = {"at": NOW, "packet": PACKET, "kind": "reply_1", "reply_to": "reception@absolutestrata.com.au",
       "outcome": outcome, "to_domain": "absolutestrata.com.au",
       "authorization": "channel-authorization.json", "trigger": "REPLY_DETECTED 2026-09-16T00:22:06Z uid57121"}
with SENTLOG.open("a", encoding="utf-8") as f:
    f.write(json.dumps(row, sort_keys=True) + "\n")
with RECEIPTS.open("a", encoding="utf-8") as f:
    f.write(json.dumps({"schema": "octopus.send-queue.v1", "at": NOW, "kind": "CUSTOMER_REPLY_SENT",
                        "packet": PACKET, "outcome": outcome, "err": err}, sort_keys=True,
                       ensure_ascii=False) + "\n")
print(json.dumps({"status": outcome, "err": err}, ensure_ascii=False))
