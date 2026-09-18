#!/usr/bin/env python3
"""reply_alert.py — SEASON-CORRECTION 1.2: <3min reply alert (closes F-019).

Polls the funnel Gmail inbox via IMAP every 2 minutes (systemd timer). For each
new message: if the sender is one of our SENT lead domains — or any non-self
sender whose subject looks like a reply — emit REPLY_DETECTED into tg-inbox.jsonl
and push an owner Telegram card (same pattern as owner_ask.send_card).
Self-sent mail is ignored EXCEPT subject starting with TEST-REPLY (test contract).
Idempotent via UID cursor (reply-alert-cursor.txt). Never raises; JSON to stdout.
"""
import email, email.policy, imaplib, json, os, pathlib, re, sys, time, urllib.request

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
INBOX_LOG = ROOT / "tg-inbox.jsonl"
CURSOR = ROOT / "reply-alert-cursor.txt"
RECEIPTS = ROOT / "receipts.jsonl"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def env(name):
    return os.environ.get(name, "")

def log_inbox(row):
    with INBOX_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

def rcpt(kind, **kw):
    with RECEIPTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(dict(schema="octopus.reply-alert.v1", at=NOW, kind=kind, **kw),
                           sort_keys=True, ensure_ascii=False) + "\n")

_tg_last_err = [""]

def send_card(text):
    token, chat = env("OFN_BOT_TOKEN_OWNER"), env("OFN_OWNER_USER_IDS").split(",")[0].strip()
    if not (token and chat):
        _tg_last_err[0] = "no-token-or-chat"
        return False
    for attempt in (1, 2):  # one retry — transient network tolerance
        try:
            req = urllib.request.Request(
                "https://api.telegram.org/bot%s/sendMessage" % token,
                data=json.dumps({"chat_id": chat, "text": text}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                if r.status == 200:
                    return True
        except Exception as exc:
            _tg_last_err[0] = "%s:%s" % (type(exc).__name__, str(exc)[:120])
            time.sleep(2)
    return False

# lead domains we have ever emailed (sent-log followups + packet recipients)
lead_domains = set()
try:
    for line in (ROOT / "sent-log.jsonl").read_text(errors="replace").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        d = r.get("to_domain")
        if d:
            lead_domains.add(d.lower())
except OSError:
    pass
lead_domains.update({"absolutestrata.com.au", "bcssm.com.au", "alldiscox.com.au"})

addr, pw = env("GMAIL_ADDRESS"), env("GMAIL_APP_PASSWORD")
if not (addr and pw):
    print(json.dumps({"error": "NO_CREDS"})); sys.exit(2)

last_uid = 0
if CURSOR.exists():
    try:
        last_uid = int(CURSOR.read_text().strip() or 0)
    except ValueError:
        last_uid = 0

alerts = []
try:
    with imaplib.IMAP4_SSL("imap.gmail.com", 993) as m:
        m.login(addr, pw)
        m.select("INBOX", readonly=True)
        typ, data = m.uid("SEARCH", None, "UID", "%d:*" % (last_uid + 1))
        uids = [int(u) for u in (data[0].split() if data and data[0] else []) if int(u) > last_uid]
        for uid in uids[:20]:  # bounded per poll
            typ, msgdata = m.uid("FETCH", str(uid), "(BODY.PEEK[])")
            if typ != "OK" or not msgdata or not msgdata[0]:
                continue
            raw = msgdata[0][1]
            msg = email.message_from_bytes(raw, policy=email.policy.default)
            frm = str(msg.get("From", ""))
            subj = str(msg.get("Subject", ""))
            mfrom = email.utils.parseaddr(frm)[1].lower()
            domain = mfrom.split("@")[-1] if "@" in mfrom else ""
            is_self = mfrom == addr.lower()
            is_test = subj.upper().startswith("TEST-REPLY")
            is_reply = subj.lower().startswith("re:")
            if is_self and not is_test:
                alerts.append({"uid": uid, "action": "ignored_self"})
                continue
            if not (is_test or is_reply or domain in lead_domains):
                alerts.append({"uid": uid, "action": "ignored_other"})
                continue
            body_snip = ""
            try:
                part = msg.get_body(preferencelist=("plain",))
                body_snip = (part.get_content() if part else "")[:220].replace("\n", " ")
            except Exception:
                pass
            packet = next((p for p, d in (("QP-20260913-3991", "absolutestrata.com.au"),
                                          ("QP-20260913-5195", "bcssm.com.au"),
                                          ("QP-20260913-951", "alldiscox.com.au")) if d == domain), "")
            row = {"kind": "REPLY_DETECTED", "at": NOW, "from": mfrom, "subject": subj[:120],
                   "packet_id": packet, "snippet": body_snip, "uid": uid}
            log_inbox(row)
            ok = send_card("📩 جواب لید رسید (%s)\n%s\n\n%s" % (mfrom, subj[:100], body_snip[:150]))
            alerts.append({"uid": uid, "action": "alerted", "tg_ok": ok, "packet": packet})
            rcpt("REPLY_ALERT", from_addr=mfrom, subject=subj[:100], packet_id=packet, tg_sent=ok, tg_err=_tg_last_err[0])
        # advance cursor to max seen (or current UIDNEXT when nothing new)
        if uids:
            last_uid = max(uids)
        else:
            typ, d2 = m.status("INBOX", "(UIDNEXT)")
            try:
                last_uid = max(last_uid, int(re.search(rb"UIDNEXT (\d+)", d2[0]).group(1)) - 1)
            except Exception:
                pass
except Exception as exc:
    rcpt("REPLY_ALERT_POLL_ERROR", error=type(exc).__name__)
    print(json.dumps({"error": type(exc).__name__})); sys.exit(0)  # never block the timer

CURSOR.write_text(str(last_uid))
# 2026-09-15: poll receipt ONLY on alerts/errors — a receipt every 2min flooded the ledger
if any(a.get("action") == "alerted" for a in alerts):
    rcpt("REPLY_ALERT_POLL", alerts=alerts[:10])
print(json.dumps({"checked": len(alerts), "alerts": alerts}, ensure_ascii=False))
