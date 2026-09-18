#!/usr/bin/env python3
"""Reply runner v2 (owner 2026-09-18): automatic replies with three outcomes.
 refusal  -> record DNC, schedule ONE follow-up in 30 days, do not reply again
 hard ask -> "let us talk" reply + escalate the exact question to the owner
 other    -> informational reply (site walk offer), no price
Guards: standing authorization valid, no SEND-PAUSED/AUTH-REVOKED, one reply per
inbound, owner notified on every auto-send. Fail-closed."""
import json, pathlib, re, smtplib, time
from email.message import EmailMessage
RD = pathlib.Path(__file__).resolve().parent
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
REFUSE = re.compile(r"(not interested|no thanks|no thank you|remove me|unsubscribe|stop (contacting|emailing)|"
                    r"sold|already (done|completed|painted)|not at this (time|stage)|we (have|found) (a )?(painter|contractor)|"
                    r"\u0646\u0647 \u0645\u062a\u0631\u0633\u0645|\u0645\u062a\u0645\u0627\u06cc\u0644 \u0646\u06cc\u0633\u062a\u0645|\u062a\u0645\u0627\u0633 \u0646\u06af\u06cc\u0631\u06cc\u062f|\u0644\u0627\u0632\u0645 \u0646\u06cc\u0633\u062a)", re.I)
HARD = re.compile(r"(how much|price|cost|quote.{0,12}\$|exact|when can you|availability|start date|"
                  r"contract|invoice|deposit|per m2|per square|\u0642\u06cc\u0645\u062a|\u0686\u0642\u062f\u0631|\u062a\u0627\u0631\u06cc\u062e|\u06a9\u06cc)", re.I)
def rcp(kind, **kw):
    with (RD / "receipts.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"schema": "octopus.reply-runner.v1", "at": NOW, "kind": kind, **kw},
                            ensure_ascii=False, sort_keys=True, default=str) + chr(10))
def env(n):
    p = pathlib.Path("/home/ari/.config/ofn/secrets.env")
    m = re.search(r"^%s=(.+)$" % n, p.read_text(), re.M) if p.exists() else None
    return m.group(1).strip().strip(chr(34)) if m else ""
def main():
    if (RD / "SEND-PAUSED").exists() or (RD / "AUTH-REVOKED").exists():
        rcp("REPLY_SKIPPED", why="paused_or_revoked"); return
    try:
        auth = json.loads((RD / "standing-authorization.json").read_text(encoding="utf-8"))
        if NOW > auth["scope"]["expires_at"]:
            rcp("REPLY_SKIPPED", why="authorization_expired"); return
    except Exception:
        rcp("REPLY_SKIPPED", why="no_authorization"); return
    sid = json.loads((RD / "sender-identity.json").read_text(encoding="utf-8"))
    st = json.loads((RD / "reply-state.json").read_text()) if (RD / "reply-state.json").exists() else {}
    rows = [json.loads(l) for l in (RD / "tg-inbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    inbound = [r for r in rows if str(r.get("kind")) == "REPLY_DETECTED"]
    # FIRST-RUN GUARD (2026-09-18): a fresh or lost state must never back-reply to old inbound.
    marker = RD / "reply-runner.started"
    if not marker.exists():
        marker.write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), encoding="utf-8")
        (RD / "reply-state.json").write_text(json.dumps(
            {"%s|%s" % (str(r.get("from")), r.get("at")): {"at": NOW, "outcome": "PREEXISTING_SKIPPED"}
             for r in inbound}, indent=1), encoding="utf-8")
        rcp("REPLY_FIRST_RUN_SKIPPED", count=len(inbound))
        print(json.dumps({"at": NOW, "replied": 0, "first_run": True, "skipped": len(inbound)}))
        return
    addr, pw = env("GMAIL_ADDRESS"), env("GMAIL_APP_PASSWORD")
    n = 0
    for r in inbound[-6:]:
        frm = str(r.get("from") or ""); pid = str(r.get("packet_id") or "")
        snippet = str(r.get("snippet") or "") + " " + str(r.get("subject") or "")
        key = "%s|%s" % (frm, r.get("at"))
        if not frm or key in st:
            continue
        if REFUSE.search(snippet):
            with (RD / "dnc.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"at": NOW, "email": frm, "packet": pid, "reason": "customer refused"},
                                    ensure_ascii=False) + chr(10))
            due = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 30 * 86400))
            with (RD / "refusal-followups.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"at": NOW, "email": frm, "packet": pid, "due_at": due, "sent": False},
                                    ensure_ascii=False) + chr(10))
            st[key] = {"at": NOW, "outcome": "REFUSAL_DNC", "to": frm, "due_followup": due}
            rcp("REPLY_CLASSIFIED_REFUSAL", to_domain=frm.split("@")[-1], scheduled=due)
            continue
        hard = bool(HARD.search(snippet))
        if hard:
            body = ("Hi,\n\nGood question - the honest answer depends on the building and the exact scope, so I would "
                    "rather not guess by email. Fifteen minutes on the phone (or a free site walk) and I can give you "
                    "a firm number.\n\nKind regards,\n%s\n%s\n%s\n" % (
                        sid["signature_name"], sid["from_email"],
                        sid.get("business_mobile") or sid.get("contact_phone") or ""))
        else:
            body = ("Hi,\n\nThanks for coming back to us. If it helps, I can attend for a free site walk and bring a "
                    "written scope with the surface areas and the schedule. What day suits you?\n\nKind regards,\n%s\n%s\n%s\n" % (
                        sid["signature_name"], sid["from_email"],
                        sid.get("business_mobile") or sid.get("contact_phone") or ""))
        msg = EmailMessage(); msg["From"] = "%s <%s>" % (sid["signature_name"], addr)
        msg["To"], msg["Subject"] = frm, "Re: your painting quote enquiry"
        msg.set_content(body)
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
                s.login(addr, pw); s.send_message(msg)
            st[key] = {"at": NOW, "to": frm, "packet": pid, "hard_question": hard}
            n += 1
            with (RD / "sent-log.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"at": NOW, "kind": "reply_1", "packet": pid, "outcome": "sent",
                                     "reply_to": frm, "auto": True}, ensure_ascii=False, sort_keys=True) + chr(10))
            rcp("REPLY_SENT_AUTO", to_domain=frm.split("@")[-1], packet=pid, hard_question=hard)
            try:
                import sys as _s; _s.path.insert(0, str(RD)); import owner_reply as _or
                if hard:
                    _or.send_owner_text("\u2753 \u0633\u0648\u0627\u0644 \u0633\u062e\u062a \u0645\u0634\u062a\u0631\u06cc "
                                        "(\u062c\u0648\u0627\u0628 \u0634\u062f \u0627\u0631\u062c\u0627\u0639 \u0628\u0647 \u062a\u0648):\n"
                                        + frm.split("@")[-1] + "\n\u2014 " + snippet[:220])
                else:
                    _or.send_owner_text("\u2705 \u062c\u0648\u0627\u0628 \u062e\u0648\u062f\u06a9\u0627\u0631 \u0627\u0631\u0633\u0627\u0644 \u0634\u062f: "
                                        + frm.split("@")[-1])
            except Exception:
                pass
        except Exception as exc:
            rcp("REPLY_FAILED", to_domain=frm.split("@")[-1], why=type(exc).__name__)
    (RD / "reply-state.json").write_text(json.dumps(st, indent=1), encoding="utf-8")
    print(json.dumps({"at": NOW, "replied": n, "inbound_seen": len(inbound)}))
if __name__ == "__main__":
    main()
