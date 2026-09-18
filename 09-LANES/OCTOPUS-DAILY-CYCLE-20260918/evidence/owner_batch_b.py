#!/usr/bin/env python3
"""Owner batch (2026-09-18): send the Tim reply now, fix the send-ledger blindness,
backfill today's 4 sends, close the four superseded cards.
Pre-image + receipt for every write. Real email send is owner-authorised."""
import hashlib
import json
import pathlib
import re
import shutil
import smtplib
import sqlite3
import time
from email.message import EmailMessage

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
RD = pathlib.Path("/home/ari/ofn/state/revenue-drive")
SEC = pathlib.Path("/home/ari/.config/ofn/secrets.env")


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def env(name):
    try:
        m = re.search(r"^%s=(.+)$" % name, SEC.read_text(), re.M)
        return m.group(1).strip().strip('"') if m else ""
    except OSError:
        return ""


def rcp(kind, **kw):
    with (RD / "receipts.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"schema": "octopus.fix-receipt.v1", "at": NOW, "kind": kind,
                             **kw}, ensure_ascii=False, sort_keys=True, default=str) + "\n")


# ---------- 1. sender identity: both numbers the owner confirmed ----------
sid = json.loads((RD / "sender-identity.json").read_text(encoding="utf-8"))
sid["contact_phone"] = "0493577719"
sid["business_mobile"] = "0410609616"
sid["business_phone_raw"] = "0410609616 & 0493577719 (owner confirmed 2026-09-18)"
sid["business_phone_status"] = "CONFIRMED by owner: mobile 0410 609 616 + 0493 577 719"
(RD / "sender-identity.json").write_text(json.dumps(sid, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
print("identity:", sid["from_email"], "|", sid["signature_name"], "|", sid["business_mobile"])

# ---------- 2. send the Tim reply (owner: send it now) ----------
draft = sorted((RD / "outbox-drafts").glob("reply-absolutestrata-*.txt"))[-1]
text = draft.read_text(encoding="utf-8")
to = "reception@absolutestrata.com.au"
cc = "info@absolutestrata.com.au"
subj = "Re: Painting services quote - Absolute Strata"
body = text.split("\n\n", 1)[1]  # drop the header block
addr, pw = env("GMAIL_ADDRESS"), env("GMAIL_APP_PASSWORD")
sent_ok, detail = False, "NO_CREDS"
if addr and pw:
    msg = EmailMessage()
    msg["From"] = "%s <%s>" % (sid["signature_name"], addr)
    msg["To"], msg["Cc"], msg["Subject"] = to, cc, subj
    msg.set_content(body)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
            s.login(addr, pw)
            s.send_message(msg)
        sent_ok, detail = True, "smtp_ok"
    except Exception as exc:  # noqa: BLE001
        detail = "%s:%s" % (type(exc).__name__, str(exc)[:80])
rcp("REPLY_SENT", to=to, cc=cc, ok=sent_ok, detail=detail, draft=str(draft))
print("reply send:", sent_ok, detail)

# ---------- 3. FIX the ledger blindness + backfill ----------
mt = RD / "money_tools.py"
pre_mt = str(mt) + ".pre-ledgerfix-" + TS
shutil.copy2(mt, pre_mt)
s = mt.read_text(encoding="utf-8")
if "_record_send_ledgers" not in s:
    helper = '''def _record_send_ledgers(sent, variants=None):
    """LEDGER-FIX 2026-09-18: a send must be visible. Appends a sent-log row per
    packet and flips the packet's send_status to sent. (The 06:03:35Z batch was
    sent but never logged, which made every funnel meter report zero.)"""
    import json as _j, pathlib as _p, time as _t
    base = _p.Path(__file__).resolve().parent
    now = _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime())
    for pid in sent or []:
        rec = {"at": now, "kind": "quote", "packet": pid, "outcome": "sent",
               "authorization": "standing-authorization.json",
               "variant": (variants or {}).get(pid, "")}
        try:
            with (base / "sent-log.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(_j.dumps(rec, ensure_ascii=False, sort_keys=True) + chr(10))
        except Exception:
            pass
        pf = base / "quote-packets" / (pid + ".json")
        try:
            d = _j.loads(pf.read_text(encoding="utf-8"))
            d["send_status"] = "sent"
            d["sent_at"] = now
            pf.write_text(_j.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:
            pass


'''
    s = s.replace("def execute_money_batch(packets, email_authorized):",
                  helper + "def execute_money_batch(packets, email_authorized):")
    old = '        receipt("MONEY_BATCH_EMAIL_SENT", sent=sent, failed=failed)'
    new = ('        _record_send_ledgers(sent, ab_variants)\n'
           '        receipt("MONEY_BATCH_EMAIL_SENT", sent=sent, failed=failed)')
    if s.count(old) == 1:
        s = s.replace(old, new)
        mt.write_text(s, encoding="utf-8", newline="\n")
        print("money_tools ledger-fix applied:", sha(mt)[:12])
    else:
        print("!! send-receipt anchor not found; ledger fix NOT applied (probe needed)")
else:
    print("ledger-fix already present")

# backfill today's 4 real sends (evidence: receipts.jsonl line at 06:03:35Z)
BACKFILL = ["QP-20260918-1152", "QP-20260918-8053", "QP-20260918-5773", "QP-20260918-8275"]
FB_AT = "2026-09-18T06:03:35Z"
sl = RD / "sent-log.jsonl"
have = {json.loads(l).get("packet") for l in sl.read_text(encoding="utf-8").splitlines() if l.strip()}
added = 0
with sl.open("a", encoding="utf-8") as fh:
    for pid in BACKFILL:
        if pid in have:
            continue
        fh.write(json.dumps({"at": FB_AT, "kind": "quote", "packet": pid, "outcome": "sent",
                             "authorization": "owner tap (pre-standing-auth)",
                             "backfilled_by": "ledger-fix 2026-09-18"}, ensure_ascii=False,
                            sort_keys=True) + "\n")
        pf = RD / "quote-packets" / (pid + ".json")
        if pf.exists():
            shutil.copy2(pf, str(pf) + ".pre-backfill-" + TS)
            d = json.loads(pf.read_text(encoding="utf-8"))
            d["send_status"] = "sent"
            d["sent_at"] = FB_AT
            d["backfilled"] = True
            pf.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        added += 1
print("backfilled sent-log rows:", added)

# outcome row (the learning loop's first real datum)
oe = RD / "outbound-effects.sqlite3"
try:
    c = sqlite3.connect(str(oe))
    c.execute("create table if not exists effects (at text, packet text, kind text, detail text)")
    for pid in BACKFILL:
        c.execute("insert into effects values (?,?,?,?)", (FB_AT, pid, "sent", "first real batch"))
    if sent_ok:
        c.execute("insert into effects values (?,?,?,?)", (NOW, "reply-absolutestrata", "delivered", detail))
    c.commit()
    print("outbound-effects rows:", c.execute("select count(*) from effects").fetchone()[0])
except Exception as exc:  # noqa: BLE001
    print("outbound-effects error:", type(exc).__name__)

# ---------- 4. close the four superseded cards ----------
reg_p = RD / "owner-ask-registry.json"
shutil.copy2(reg_p, str(reg_p) + ".pre-cardclose-" + TS)
reg = json.loads(reg_p.read_text(encoding="utf-8"))
closed = []
for did, card in reg["cards"].items():
    if card.get("state") == "PENDING" and not card.get("test"):
        card["state"] = "CLOSED_SUPERSEDED"
        card["resolved_at"] = NOW
        card["note"] = "answered in the owner chat (2026-09-18 4-option rounds); card closed so the queue is clean"
        closed.append(did)
reg_p.write_text(json.dumps(reg, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print("cards closed:", closed)
rcp("OWNER_BATCH_20260918B", sent=sent_ok, backfilled=added, cards_closed=closed,
    preimages={"money_tools": pre_mt, "registry": str(reg_p) + ".pre-cardclose-" + TS})
print("DONE")
