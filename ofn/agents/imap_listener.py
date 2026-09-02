r"""imap_listener — گوشِ OCTOPUS (Lane E، نقشهٔ راه ۲۰۲۶-۰۹-۰۱ / رأی Q3).

هر ۱۵ دقیقه inbox همان Gmail را با IMAP می‌خواند و فقط پیام‌هایی را پردازش
می‌کند که مالِ ما هستند؛ به بقیهٔ ایمیل‌های شخصیِ مالک دست نمی‌زند (نه \Seen،
نه حذف). سه طبقه:

  reply    — فرستنده = یکی از ایمیل‌های لیدهای contact/engaged ما
  bounce   — MAILER-DAEMON/postmaster یا multipart/report delivery-status
  optout   — STOP/unsubscribe در متنِ reply

اقدام‌ها (همه idempotent، همه با رسید در events.jsonl):
  reply(quote_request) → status=engaged + next_action='quote requested' + digest
  reply(acceptance)    → status=won_pending + رویداد booked (مبلغ بعد از تأیید مالک)
  reply(general)       → status=engaged + digest
  optout               → suppression در consent_store + status=opted_out
  bounce(wrong_recipient) → کمپین PAINT-L5-001 کِیل (metric خودِ envelope) + آلارم مالک

dry-run (--dry): فقط طبقه‌بندی و لاگ، هیچ نوشتنی. ایمن برای اولین اجرا (درس GAPS-71).
هرگز raise نمی‌کند؛ خروجی JSON برای systemd/journal.
"""
from __future__ import annotations

import email
import email.policy
import imaplib
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))

import opslib  # noqa: E402
import memory_chain  # noqa: E402

HOME = Path.home()
PAINTING_DB = HOME / ".local/share/ofn/painting.sqlite"
STATE_DIR = opslib.STATE_DIR / "imap"
CAMPAIGN = "PAINT-L5-001"
CAMPAIGN_HALT_FLAG = opslib.STATE_DIR / f"campaign-halt-{CAMPAIGN}.flag"

QUOTE_WORDS = ("quote", "pricing", "price", "scope of works", "estimate",
               "pricing schedule", "rfq", "tender documents")
ACCEPT_WORDS = ("we accept", "accepted", "award", "awarded", "proceed",
                "go ahead", "engaged your", "appointment", "site visit",
                "book you")
OPTOUT_RE = re.compile(r"^\s*(stop|unsubscribe|opt[- ]?out|remove me)\s*$",
                       re.IGNORECASE | re.MULTILINE)
BOUNCE_PERM = ("5.1.1", "5.1.10", "user unknown", "no mailbox",
               "address rejected", "does not exist", "recipient rejected",
               "bad destination")


def _receipt(event_type: str, corr: str, payload: dict) -> None:
    opslib.append_jsonl(opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl", {
        "event_id": opslib.now_iso() + "-" + event_type, "event_type": event_type,
        "occurred_at": opslib.now_iso(), "correlation_id": str(corr or ""),
        "source_component": "ImapListener", "schema_version": "1.0",
        "payload": payload})


def _norm(addr: str) -> str:
    return (addr or "").strip().lower()


def _load_state() -> dict:
    p = STATE_DIR / "last_uid.json"
    try:
        return json.loads(p.read_text())
    except Exception:  # noqa: BLE001
        return {"mailbox": "INBOX", "uidvalidity": 0, "last_uid": 0}


def _save_state(st: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / "last_uid.json").write_text(
        json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def lead_emails() -> dict:
    """ایمیل→lead_id برای لیدهای دارای ایمیل (تماس‌گرفته یا engages)."""
    import sqlite3
    out = {}
    try:
        c = sqlite3.connect(PAINTING_DB)
        for em, lid in c.execute(
                "SELECT email, lead_id FROM painting_leads WHERE email != \"\""):
            out[_norm(em)] = lid
        c.close()
    except Exception as e:  # noqa: BLE001
        _receipt("imap.lead_db_error", "imap", {"detail": type(e).__name__})
    return out


AUTOREPLY_SUBJ = ("automatic reply", "auto-reply", "auto reply",
                  "out of office", "out-of-office", "_autoreply",
                  "automatic response")


def classify(msg: email.message.Message, sender: str, known: dict) -> tuple:
    """(kind, intent, detail) — kind در {reply, bounce, noise}."""
    subj = (msg.get("Subject") or "").lower()
    if ("mailer-daemon" in sender or "postmaster" in sender
            or sender.startswith("bounce")):
        ctype = msg.get_content_type() or ""
        if ctype.startswith("multipart/report"):
            return "bounce", "dsn", "delivery-status"
        if any(w in subj for w in ("undeliverable", "delivery status",
                                   "returned mail", "failure notice")):
            return "bounce", "dsn", subj[:60]
        return "noise", "", ""
    if sender in known:
        # پاسخِ خودکارِ اداری ≠ جوابِ انسانی؛ لید نباید engaged شود
        if any(subj.strip().startswith(m) for m in AUTOREPLY_SUBJ):
            return "reply", "autoreply", subj[:60]
        body = _body_text(msg)
        low = body.lower()
        if OPTOUT_RE.search(body) or re.search(
                r"(please\s+)?(unsubscribe|remove)\s+me", low):
            return "reply", "optout", body[:80]
        if any(w in low for w in ACCEPT_WORDS):
            return "reply", "acceptance", body[:120]
        if any(w in low for w in QUOTE_WORDS):
            return "reply", "quote_request", body[:120]
        return "reply", "general", body[:120]
    return "noise", "", ""


def _body_text(msg: email.message.Message) -> str:
    try:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_content()
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    return re.sub(r"<[^>]+>", " ", part.get_content())
            return ""
        return msg.get_content()
    except Exception:  # noqa: BLE001
        return ""


def _bounce_recipient(msg: email.message.Message) -> str:
    """گیرندهٔ اصلی از بدنهٔ DSN (Original-Recipient/Final-Recipient) یا متن."""
    try:
        for part in msg.walk():
            if part.get_content_type() == "message/delivery-status":
                for ds in part.get_payload():
                    for k, v in ds.items():
                        if k.lower() in ("original-recipient", "final-recipient"):
                            return _norm(v.split(";")[-1].strip())
    except Exception:  # noqa: BLE001
        pass
    m = re.search(r"[\w.+-]+@[\w.-]+", _body_text(msg)[:2000])
    return _norm(m.group(0)) if m else ""


def _act(kind: str, intent: str, sender: str, lead_id: str,
         body_snip: str, msg: email.message.Message,
         known: dict, dry: bool) -> dict:
    import sqlite3
    now = opslib.now_iso()
    result = {"kind": kind, "intent": intent, "from": sender[:40]}
    if dry:
        result["dry"] = True
        return result
    if kind == "bounce":
        rcpt = _bounce_recipient(msg)
        perm = any(w in body_snip.lower() or w in _body_text(msg)[:3000].lower()
                   for w in BOUNCE_PERM)
        _receipt("communication.bounce", lead_id or rcpt or "bounce",
                 {"recipient": rcpt, "permanent": perm})
        memory_chain.append("bounce", lead_id or rcpt or "bounce",
                            {"recipient": rcpt, "permanent": perm})
        if perm and rcpt in known:
            CAMPAIGN_HALT_FLAG.write_text(
                f"wrong_recipient bounce for {rcpt} at {now} — kill_metric fired")
            try:
                c = sqlite3.connect(PAINTING_DB)
                c.execute("UPDATE painting_campaigns SET status=?, "
                          "next_step=? WHERE title LIKE ? OR campaign_id LIKE ?",
                          ("killed_by_metric",
                           f"halt: wrong_recipient bounce {rcpt} {now}",
                           "%existing-CRM%", f"%{CAMPAIGN}%"))
                c.execute("UPDATE painting_leads SET status=\"lost\" "
                          "WHERE email COLLATE NOCASE = ?", (rcpt,))
                c.commit()
                c.close()
            except Exception as e:  # noqa: BLE001
                _receipt("imap.campaign_kill_db_error", CAMPAIGN, {"detail": type(e).__name__})
            try:
                import owner_notify
                owner_notify.alert_owner(
                    f"🛑 کمپین {CAMPAIGN} متوقف شد — bounce دائمی برای {rcpt}. "
                    "هیچ ارسال جدیدی تا بررسی تو نمی‌رود.")
            except Exception:  # noqa: BLE001
                pass
            result["campaign_killed"] = True
        return result
    if kind != "reply":
        return result
    c = sqlite3.connect(PAINTING_DB)
    try:
        if intent == "autoreply":
            # ثبتِ رویداد بدونِ تغییرِ وضعیتِ لید — فریبِ خودکارخوان‌ها ممنوع
            _receipt("communication.autoreply", lead_id, {"subject": body_snip})
            result["action"] = "autoreply-logged"
            c.execute("INSERT INTO painting_interactions "
                      "(interaction_id, tenant_id, channel, kind, person, subject, "
                      "body, status, lead_id, created_at, updated_at) VALUES "
                      "(?, \"lead\", \"email\", \"inbound\", ?, ?, ?, \"archived\", ?, ?, ?)",
                      (f"imap:{now}:{sender[:20]}", sender[:60],
                       (msg.get("Subject") or "")[:120], body_snip,
                       lead_id, now, now))
            memory_chain.append("inbound_autoreply", lead_id,
                                {"from": sender[:40]})
            c.commit()
            return result
        if intent == "optout":
            try:
                import consent_store as _cs
                _cs.ConsentStore().insert_suppression(
                    sender, "email", "imap-optout")
            except Exception as e:  # noqa: BLE001
                _receipt("imap.consent_store_error", lead_id,
                         {"detail": f"{type(e).__name__}"})
            c.execute("UPDATE painting_leads SET status=\"archived\", "
                      "next_action=\"do not contact\", "
                      "next_action_at=datetime('now') WHERE lead_id=?",
                      (lead_id,))
            _receipt("communication.opted_out", lead_id, {"to": sender[:40]})
            result["action"] = "suppressed"
        elif intent == "acceptance":
            c.execute("UPDATE painting_leads SET status=\"won\", "
                      "next_action=\"book amount from reply (digest confirm)\", "
                      "next_action_at=datetime('now','+2 days') WHERE lead_id=?",
                      (lead_id,))
            _receipt("communication.acceptance", lead_id, {"snip": body_snip})
            result["action"] = "won_pending"
        elif intent == "quote_request":
            c.execute("UPDATE painting_leads SET status=\"review\", "
                      "next_action=\"quote requested\", "
                      "next_action_at=datetime('now','+1 day') WHERE lead_id=?",
                      (lead_id,))
            _receipt("communication.quote_requested", lead_id, {"snip": body_snip})
            result["action"] = "quote_requested"
        else:
            c.execute("UPDATE painting_leads SET status=\"review\", "
                      "next_action=\"owner reply via digest\", "
                      "next_action_at=datetime('now','+3 days') "
                      "WHERE lead_id=? AND status='contacted'", (lead_id,))
            _receipt("communication.reply", lead_id, {"snip": body_snip})
            result["action"] = "engaged"
        c.execute("INSERT INTO painting_interactions "
                  "(interaction_id, tenant_id, channel, kind, person, subject, "
                  "body, status, lead_id, created_at, updated_at) VALUES "
                  "(?, \"lead\", \"email\", \"inbound\", ?, ?, ?, \"needs_reply\", ?, ?, ?)",
                  (f"imap:{now}:{sender[:20]}", sender[:60],
                   (msg.get("Subject") or "")[:120], body_snip,
                   lead_id, now, now))
        memory_chain.append(f"inbound_{intent}", lead_id,
                            {"from": sender[:40], "subject":
                             (msg.get("Subject") or "")[:80]})
        c.commit()
    finally:
        c.close()
    if intent in ("acceptance", "quote_request", "general"):
        try:
            import owner_notify
            owner_notify.alert_owner(
                f"📥 جواب از {sender[:40]} ({intent}): {body_snip[:120]}")
        except Exception:  # noqa: BLE001
            pass
    return result


def cycle(dry: bool = False, limit: int = 60) -> dict:
    """یک پولِ IMAP. فقط ایمیل‌های مالِ ما؛ بقیه دست‌نخورده."""
    out = {"scanned": 0, "processed": 0, "results": [], "dry": dry}
    st = _load_state()
    known = lead_emails()
    import mail_credentials
    cr = mail_credentials.resolve()
    if not cr.get("ok"):
        out["error"] = "not-armed:" + str(cr.get("reason"))
        _receipt("imap.not_armed", "imap", {"reason": cr.get("reason")})
        return out
    pw = os.environ.get(str(cr.get("secret_env") or "GMAIL_APP_PASSWORD"), "")
    user = cr.get("user") or os.environ.get("GMAIL_ADDRESS", "")
    if not pw:
        out["error"] = "no-password"
        return out
    srv = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    srv.login(user, pw)
    srv.select("INBOX", readonly=False)
    typ, data = srv.status("INBOX", "(UIDNEXT UIDVALIDITY)")
    raw_status = data[0].decode() if data and data[0] else ""
    mu = re.search(r"UIDVALIDITY (\d+)", raw_status)
    mn = re.search(r"UIDNEXT (\d+)", raw_status)
    uidvalidity = int(mu.group(1)) if mu else 0
    uidnext = int(mn.group(1)) if mn else 0
    if st.get("uidvalidity") != uidvalidity:
        st = {"mailbox": "INBOX", "uidvalidity": uidvalidity, "last_uid": 0}
    start = int(st.get("last_uid", 0)) + 1
    end = uidnext - 1
    if start > end:
        srv.logout()
        out["note"] = "no-new"
        return out
    # فقط پنجرهٔ تازه را بکش؛ حداکثر limit تا اولین اجرا انفجار نکند
    if end - start + 1 > limit:
        start = end - limit + 1
    typ, data = srv.uid("SEARCH", None, f"UID {start}:{end}")
    uids = (data[0].split() if typ == "OK" and data and data[0] else [])
    for uid in uids:
        uid_i = int(uid)
        typ, md = srv.uid("FETCH", uid, "(RFC822)")
        if typ != "OK" or not md or not md[0]:
            continue
        raw = md[0][1]
        msg = email.message_from_bytes(raw, policy=email.policy.default)
        sender = _norm(email.utils.parseaddr(msg.get("From", ""))[1])
        out["scanned"] += 1
        kind, intent, snip = classify(msg, sender, known)
        if kind == "noise":
            continue  # ایمیل شخصی مالک: نه می‌خوانیمش، نه seen می‌کنیم
        out["processed"] += 1
        lead_id = known.get(sender, "")
        res = _act(kind, intent, sender, lead_id, snip, msg, known, dry)
        res["uid"] = uid_i
        out["results"].append(res)
        if not dry:
            srv.uid("STORE", uid, "+FLAGS", "(\\Seen)")
        st["last_uid"] = uid_i
    if not dry:
        _save_state(st)
    srv.logout()
    return out


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    try:
        print(json.dumps(cycle(dry=dry), ensure_ascii=False, indent=1))
    except Exception as e:  # noqa: BLE001 — listener هرگز نمی‌میرد بی‌صدا
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
