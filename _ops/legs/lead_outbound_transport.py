#!/usr/bin/env python3
"""lead_outbound_transport.py — Lane G (منشور TG-UI ۲۰۲۶-۰۷-۳۱، رأی ۱۷): آداپترِ ایمیلِ واقعی.

اولین transportِ غیرِ-stub ِ قوسِ ارسالِ لید. مرزها (خطوطِ قرمزِ LEAD-SAFETY-C1 حفظ):
  · این ماژول **هرگز خودش تصمیمِ ارسال نمی‌گیرد** — تنها صداکنندهٔ مجازش
    outbound_worker.send_one است که قبلش گیتِ per-effect (consent/authz/idempotency/cap)
    را گذرانده. صدا زدنِ مستقیم = دورزدنِ گیت = ممنوع.
  · بدونِ ۵ متغیرِ env (OCTOPUS_SMTP_HOST/PORT/USER/PASS/FROM) صادقانه NOT_ARMED
    برمی‌گرداند — نه استثنا، نه ارسال. arming = رأیِ deploy ِ مالک (env ست می‌شود).
  · secret (پسورد/کاربر) و گیرندهٔ کامل **هرگز** در رسید/لاگ نمی‌نشیند —
    local-part ِ ایمیل ماسک می‌شود (درسِ §۱۰ قانونِ اساسی).
  · قفلِ test_effector_gate_bridge: settle ≠ sent. `communication.sent` در funnel.db
    فقط با ارسالِ **تأییدشدهٔ** transport نوشته می‌شود؛ شکست = communication.failed؛
    NOT_ARMED/SUPPRESSED = فقط رسیدِ events.jsonl، هیچ رویدادِ communication.*.
  · STOP/unsubscribe: کاندیدِ نشان‌دارِ opt_out هرگز فرستاده نمی‌شود (SUPPRESSED) و
    suppression دفاعی به consent_store تغذیه می‌شود (exception-safe — آن ماژول امروز
    صفر صداکنندهٔ تولیدی دارد؛ این‌جا دفاعی سیم می‌شود).
  · یک تلاش، بدونِ retry، timeout ثابت ۲۰s. شمارندهٔ سقفِ روزانه فقط با sent=True
    (outbound_worker.record_send) بالا می‌رود.

تزریق‌پذیر: send_impl (برای تست، جای smtplib) و now. stdlib-only.
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib   # noqa: E402

REQUIRED_ENV = ("OCTOPUS_SMTP_HOST", "OCTOPUS_SMTP_PORT", "OCTOPUS_SMTP_USER",
                "OCTOPUS_SMTP_PASS", "OCTOPUS_SMTP_FROM")
SMTP_TIMEOUT_S = 20.0


def _events() -> Path:
    return opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"


def _receipt(event_type: str, corr: str, payload: dict) -> None:
    """رسیدِ append-only در events.jsonl — هم‌الگوی lead_effect_gate._emit. هرگز raise."""
    try:
        opslib.append_jsonl(_events(), {
            "event_id": uuid.uuid4().hex, "event_type": event_type,
            "occurred_at": opslib.now_iso(), "correlation_id": str(corr or ""),
            "source_component": "LeadOutboundTransport", "schema_version": "1.0",
            "payload": payload})
    except Exception:  # noqa: BLE001
        pass


def _funnel_record(event_type: str, lead_id: str, payload: dict) -> None:
    """رویدادِ funnel.db (فقط communication.sent/failed — نتیجهٔ واقعیِ transport).
    fail-soft: ثبتِ ناموفق هرگز مسیرِ ارسال را نمی‌کشد."""
    store = None
    try:
        _oc = str(_HERE.parent / "outcomes")
        if _oc not in sys.path:
            sys.path.insert(0, _oc)
        import funnel_store as _fs   # noqa: WPS433 — lazy
        store = _fs.FunnelStore()
        store.record({"event_type": event_type, "lead_id": str(lead_id or "unknown"),
                      "source_component": "LeadOutboundTransport", "payload": payload})
    except Exception:  # noqa: BLE001
        pass
    finally:
        try:
            if store is not None:
                store.close()
        except Exception:  # noqa: BLE001
            pass


def mask_recipient(addr: str) -> str:
    """ماسکِ local-part: «ab***@domain» — گیرندهٔ کامل هرگز در رسید/لاگ نمی‌نشیند."""
    a = str(addr or "").strip()
    local, _, dom = a.partition("@")
    if not dom:
        return "***"
    return (local[:2] + "***@" + dom) if local else ("***@" + dom)


def _norm_email(addr: str) -> str:
    return str(addr or "").strip().lower()


def _recipient(candidate: dict) -> str | None:
    """ایمیلِ گیرنده از رکوردِ کاندید — contact.email (یا email ِ top-level). نبود → None."""
    c = candidate if isinstance(candidate, dict) else {}
    contact = c.get("contact") if isinstance(c.get("contact"), dict) else {}
    em = _norm_email(contact.get("email") or c.get("email") or "")
    return em if ("@" in em and "." in em.rsplit("@", 1)[-1]) else None


def _opted_out(candidate: dict) -> str | None:
    """نشانِ STOP/opt-out روی خودِ رکورد (لایهٔ اول، بدونِ I/O). دلیل یا None."""
    c = candidate if isinstance(candidate, dict) else {}
    contact = c.get("contact") if isinstance(c.get("contact"), dict) else {}
    for holder, key in ((c, "opt_out"), (c, "stop"), (c, "unsubscribed"),
                        (contact, "opt_out"), (contact, "stop"), (contact, "unsubscribed")):
        if holder.get(key):
            return f"candidate-marker:{key}"
    return None


def _feed_suppression(email_norm: str, reason: str) -> None:
    """تغذیهٔ دفاعیِ consent_store.suppression (D2a، امروز بدونِ صداکنندهٔ تولیدی).
    exception-safe مطلق — نبود/خطای store هرگز رد کردنِ ارسال را لغو نمی‌کند."""
    store = None
    try:
        import consent_store as _cs   # noqa: WPS433 — lazy، هم‌پوشه
        # واژگانِ reason در schema بسته است (CHECK) — نگاشتِ نشانِ آزاد به enum:
        r = str(reason or "").casefold()
        if "unsub" in r:
            canon = "unsubscribe"
        elif "stop" in r:
            canon = "stop_reply"
        else:
            canon = "manual_dnc"
        store = _cs.ConsentStore()
        store.insert_suppression(email_norm, "email", canon)
    except Exception:  # noqa: BLE001
        pass
    finally:
        try:
            if store is not None:
                store.close()
        except Exception:  # noqa: BLE001
            pass


def _store_suppressed(email_norm: str) -> str | None:
    """لایهٔ دوم: اگر consent_store در دسترس است، suppression فعال را بپرس.
    نبودِ store = None (نه fail-closed — لایهٔ اول و گیتِ بالادست سرِ جایشان‌اند)."""
    store = None
    try:
        import consent_store as _cs   # noqa: WPS433 — lazy
        store = _cs.ConsentStore()
        return store.suppression_active(email_norm)
    except Exception:  # noqa: BLE001
        return None
    finally:
        try:
            if store is not None:
                store.close()
        except Exception:  # noqa: BLE001
            pass


def creds() -> dict | None:
    """۵ متغیرِ env — همه الزامی. یکی هم غایب → None (NOT_ARMED). مقدارها هرگز لاگ نمی‌شوند."""
    vals = {name: str(os.environ.get(name, "") or "").strip() for name in REQUIRED_ENV}
    if not all(vals.values()):
        return None
    return vals


def _default_send_impl(host: str, port: int, user: str, password: str,
                       from_addr: str, to_addr: str, message: str) -> None:
    """ارسالِ واقعیِ SMTP — یک تلاش، بدونِ retry. استثنا = شکست (caller ترجمه می‌کند).
    پورت ۴۶۵ → SMTP_SSL؛ وگرنه STARTTLS."""
    import smtplib   # noqa: WPS433 — فقط این‌جا؛ ماژول‌های گیت شبکه import نمی‌کنند
    if int(port) == 465:
        with smtplib.SMTP_SSL(host, int(port), timeout=SMTP_TIMEOUT_S) as srv:
            srv.login(user, password)
            srv.sendmail(from_addr, [to_addr], message)
    else:
        with smtplib.SMTP(host, int(port), timeout=SMTP_TIMEOUT_S) as srv:
            srv.starttls()
            srv.login(user, password)
            srv.sendmail(from_addr, [to_addr], message)


def _build_message(from_addr: str, to_addr: str, draft) -> str:
    """پیامِ RFC822 از draft (str یا dict با subject/body)."""
    from email.mime.text import MIMEText   # noqa: WPS433 — stdlib
    if isinstance(draft, dict):
        subject = str(draft.get("subject") or "Quote — painting works")
        body = str(draft.get("body") or draft.get("text") or "")
    else:
        subject = "Quote — painting works"
        body = str(draft or "")
    if "reply stop" not in body.lower() and "STOP" not in body:
        body = body.rstrip() + "\n\nReply STOP to opt out."
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    return msg.as_string()


def _bump_send_counter(now=None) -> None:
    """شمارندهٔ سقفِ روزانه فقط با ارسالِ تأییدشده بالا می‌رود (رأی مالک ۲۰۲۶-۰۷-۳۱: ۱۰).
    منبعِ شمارنده outbound_worker است (کنارِ LEAD_DAILY_SEND_CAP). fail-soft + alert."""
    try:
        import outbound_worker as _ow   # noqa: WPS433 — lazy، هم‌پوشه
        _ow.record_send(now=now)
    except Exception:  # noqa: BLE001
        try:
            opslib.alert(["lead transport: sent ولی شمارندهٔ سقف ثبت نشد — بررسی کن"])
        except Exception:  # noqa: BLE001
            pass


def send(candidate: dict, draft, *, now=None, send_impl=None) -> dict:
    """ارسالِ ایمیلِ یک لید — همیشه dict، هرگز استثنا، هرگز credential در خروجی.

    خروجی: {"sent": bool, "status": str, "detail": str}
    statusها: SENT | FAILED | NOT_ARMED | SUPPRESSED | NO_RECIPIENT
    هر تلاش (هر status) یک رسیدِ append-only در events.jsonl می‌گذارد؛
    communication.sent/failed در funnel.db فقط برای نتیجهٔ واقعیِ transport.
    """
    lead_id = str((candidate or {}).get("lead_id")
                  or (candidate or {}).get("attribution_id") or "unknown")
    try:
        # ۱) STOP/opt-out — قبل از هر چیز؛ لایهٔ اول رویِ خودِ رکورد.
        marker = _opted_out(candidate)
        to_addr = _recipient(candidate)
        if marker is None and to_addr:
            marker = _store_suppressed(to_addr)      # لایهٔ دوم: جدولِ suppression
            marker = f"suppression-store:{marker}" if marker else None
        if marker:
            if to_addr:
                _feed_suppression(to_addr, marker)
            _receipt("communication.suppressed", lead_id,
                     {"status": "SUPPRESSED", "reason": marker,
                      "to": mask_recipient(to_addr or "")})
            return {"sent": False, "status": "SUPPRESSED", "detail": marker}

        # ۲) creds — همه یا هیچ. غایب → NOT_ARMED صادقانه (بدونِ استثنا).
        cr = creds()
        if cr is None:
            _receipt("communication.not_armed", lead_id,
                     {"status": "NOT_ARMED", "reason": "smtp-creds-missing"})
            return {"sent": False, "status": "NOT_ARMED", "detail": "smtp-creds-missing"}

        # ۳) گیرنده الزامی.
        if not to_addr:
            _receipt("communication.no_recipient", lead_id,
                     {"status": "NO_RECIPIENT"})
            return {"sent": False, "status": "NO_RECIPIENT", "detail": "no-contact-email"}

        # ۴) یک تلاشِ واقعی — بدونِ retry، timeout ۲۰s.
        message = _build_message(cr["OCTOPUS_SMTP_FROM"], to_addr, draft)
        impl = send_impl if callable(send_impl) else _default_send_impl
        try:
            impl(cr["OCTOPUS_SMTP_HOST"], int(cr["OCTOPUS_SMTP_PORT"]),
                 cr["OCTOPUS_SMTP_USER"], cr["OCTOPUS_SMTP_PASS"],
                 cr["OCTOPUS_SMTP_FROM"], to_addr, message)
        except Exception as e:  # noqa: BLE001 — شکستِ ارسال = FAILED صادقانه
            detail = f"smtp-error:{type(e).__name__}"
            _receipt("communication.failed", lead_id,
                     {"status": "FAILED", "detail": detail,
                      "to": mask_recipient(to_addr)})
            _funnel_record("communication.failed", lead_id,
                           {"channel": "email", "detail": detail,
                            "to": mask_recipient(to_addr)})
            return {"sent": False, "status": "FAILED", "detail": detail}

        # ۵) ارسالِ تأییدشده — تنها جایی که communication.sent و شمارندهٔ سقف می‌نشیند.
        _receipt("communication.sent", lead_id,
                 {"status": "SENT", "channel": "email", "to": mask_recipient(to_addr)})
        _funnel_record("communication.sent", lead_id,
                       {"channel": "email", "to": mask_recipient(to_addr)})
        _bump_send_counter(now=now)
        return {"sent": True, "status": "SENT", "detail": f"to={mask_recipient(to_addr)}"}
    except Exception as e:  # noqa: BLE001 — transport هرگز caller را نمی‌کشد
        return {"sent": False, "status": "FAILED", "detail": f"transport-error:{type(e).__name__}"}


if __name__ == "__main__":
    print(json.dumps({"armed": creds() is not None,
                      "note": "بدونِ ۵ envِ SMTP = NOT_ARMED؛ مسیرِ مجاز فقط outbound_worker.send_one."},
                     ensure_ascii=False))
