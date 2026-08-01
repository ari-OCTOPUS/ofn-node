#!/usr/bin/env python3
"""lead_outbound_transport.py — Lane G (منشور TG-UI ۲۰۲۶-۰۷-۳۱، رأی ۱۷): آداپترِ ایمیلِ واقعی.

اولین transportِ غیرِ-stub ِ قوسِ ارسالِ لید. مرزها (خطوطِ قرمزِ LEAD-SAFETY-C1 حفظ):
  · این ماژول **هرگز خودش تصمیمِ ارسال نمی‌گیرد** — تنها صداکنندهٔ مجازش
    outbound_worker.send_one است که قبلش گیتِ per-effect (consent/authz/idempotency/cap)
    را گذرانده. صدا زدنِ مستقیم = دورزدنِ گیت = ممنوع.
  · credential از `mail_credentials.resolve()` می‌آید (تقدم: `OCTOPUS_SMTP_*` ِ
    صریح، سپس fallback ِ Gmail پشتِ فلگِ `OCTOPUS_SMTP_USE_GMAIL`). حل‌نشدن =
    NOT_ARMED ِ صادق با **دلیلِ دقیق** — نه استثنا، نه ارسال، نه سکوت.
  · پسورد هرگز از مرزِ `mail_credentials` رد نمی‌شود: آن ماژول فقط **نامِ**
    متغیرِ env را می‌دهد و همین‌جا لحظهٔ ارسال خوانده می‌شود (§۱۰ قانونِ اساسی).
  · secret (پسورد/کاربر) و گیرندهٔ کامل **هرگز** در رسید/لاگ نمی‌نشیند —
    local-part ِ ایمیل ماسک می‌شود (درسِ §۱۰ قانونِ اساسی).

⛔ مرزِ سختِ ارسالِ واقعی (رأیِ مالک، شبِ ۰۷-۳۱): هیچ مسیری در این ماژول به
   ایمیلِ یک لیدِ **واقعی** نمی‌فرستد مگر از دلِ `outbound_worker.send_one` —
   یعنی بعدِ consent/authz/idempotency/سقف. تنها مسیرِ دیگری که واقعاً به SMTP
   می‌رسد `self_test()` است و آن **فقط** به آدرسِ خودِ مالک
   (`mail_credentials.owner_address()`) می‌فرستد؛ هر گیرندهٔ دیگری را رد می‌کند،
   شمارندهٔ سقفِ روزانه را دست نمی‌زند و در دفترِ funnel چیزی نمی‌نویسد.
  · قفلِ test_effector_gate_bridge: settle ≠ sent. `communication.sent` در funnel.db
    فقط با ارسالِ **تأییدشدهٔ** transport نوشته می‌شود؛ شکست = communication.failed؛
    NOT_ARMED/SUPPRESSED = فقط رسیدِ events.jsonl، هیچ رویدادِ communication.*.
  · STOP/unsubscribe: کاندیدِ نشان‌دارِ opt_out هرگز فرستاده نمی‌شود (SUPPRESSED) و
    suppression دفاعی به consent_store تغذیه می‌شود (exception-safe — آن ماژول امروز
    صفر صداکنندهٔ تولیدی دارد؛ این‌جا دفاعی سیم می‌شود).
  · یک تلاش، بدونِ retry، timeout ثابت ۲۰s. شمارندهٔ سقفِ روزانه فقط با sent=True
    (outbound_worker.record_send) بالا می‌رود.

📣 اعلانِ ارسال به مالک (GAP-1، ۲۰۲۶-۰۸-۰۱ — پشتِ `OCTOPUS_WIRE_LEAD_SEND_NOTIFY`):
   تا امروز یک ایمیلِ **موفق** به لید هیچ صدایی در تلگرام نداشت — فقط یک رسید در
   events.jsonl، یک ردیف در funnel.db و یک ++ روی شمارنده. تنها هشدارِ این قوس
   (`outbound_worker.py:193`) وقتی می‌خواند که گیت باز شد ولی transport **نفرستاد**؛
   یعنی اولین ایمیلِ واقعی به یک مشتریِ واقعی در سکوتِ کامل می‌رفت.
   مرزها:
     · سیستمِ اعلانِ دومی ساخته نمی‌شود. تحویل از همان کانالِ اثبات‌شده‌ای می‌رود که
       `organism`/`c6_trigger`/`instant_alert_bridge` استفاده می‌کنند:
       `wiring.make_telegram_channel()` → `send_text(text, None, stream="lead")`.
       پس ساعتِ سکوت، HOLD، redaction، رسیدِ tg-send-log و مسیریابیِ تاپیک همه
       همان‌هایی‌اند که مالک قبلاً تصویب کرده.
     · **هرگز** ارسال را برنمی‌گرداند و هرگز نمی‌کُشد: ایمیل رفته است؛ اعلانِ گم‌شده
       ضررِ کوچک‌تری از ایمیلِ تکراری دارد. کلِ مسیر بعد از ثبتِ funnel و شمارنده
       می‌آید و در یک try/except مطلق است.
     · انضباطِ PII: فقط **دامنهٔ** گیرنده (نه آدرس، نه local-part ِ ماسک‌شده).
     · فلگ خاموش (پیش‌فرض) = بایت‌به‌بایتِ امروز؛ صفر خواندن، صفر رسید، صفر import.
       فلگ روشن = «ثبت همیشه، گیت فقط روی تحویل»: هر نتیجه (تحویل/ناموفق/بی‌کانال)
       یک رسیدِ `communication.notified` می‌گذارد تا سه سکوتِ متفاوت یکی نشوند.

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
import mail_credentials   # noqa: E402 — هم‌پوشه؛ حلِ نام، بدونِ I/O شبکه

SMTP_TIMEOUT_S = 20.0

# ── اعلانِ ارسال (GAP-1) ──────────────────────────────────────────────────────
# فلگِ نو، پیش‌فرض **خاموش** و عمداً بیرونِ wiring.PAPER_FULL_FLAGS: مسلح‌کردنش
# تصمیمِ مالک است، نه پروفایل، نه ایجنت.
NOTIFY_FLAG = "OCTOPUS_WIRE_LEAD_SEND_NOTIFY"
# جریانِ مسیریابی: همان «lead» که `lead_pipeline` کارتِ لیدش را با آن می‌فرستد و
# `approval_channel._STREAM_TOPIC` می‌شناسدش. نامِ تازه نمی‌سازیم — جریانِ ناشناخته
# یعنی مسیرِ ناشناخته.
NOTIFY_STREAM = "lead"
# ایزولهٔ bidi برای تکه‌های LTR (شناسه/دامنه/شمارهٔ کوت) داخلِ متنِ فارسی — منشور UX-9.
_LRI, _PDI = "\u2066", "\u2069"
_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


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


def recipient_domain(addr: str) -> str:
    """**فقط** دامنهٔ گیرنده — local-part هرگز از این تابع بیرون نمی‌آید.

    `mask_recipient` برای رسیدِ فنی است و دو حرفِ اولِ local-part را نگه می‌دارد؛
    اعلانِ تلگرام سخت‌گیرتر است چون در یک چت می‌نشیند و برای همیشه آن‌جا می‌ماند.
    ورودیِ بی‌`@` (یا دامنهٔ خالی) ⇒ «unknown» — نه خودِ رشته. اگر این‌جا به
    rpartition ِ لخت تکیه شود، «hunter2» بی‌`@` عیناً به‌عنوان «دامنه» چاپ می‌شود."""
    a = str(addr or "").strip()
    _local, sep, dom = a.rpartition("@")
    dom = dom.strip().lower()
    if not sep or not dom:
        return "unknown"
    return dom


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
    """credential ِ حل‌شده (بدونِ پسورد) یا None اگر مسلح نیست.

    نگه‌داشتنِ نامِ تاریخیِ `creds` عمدی است (صداکننده‌های موجود نشکنند)، ولی
    محتوا عوض شده: دیگر پسورد داخلش نیست — فقط `secret_env` (نامِ متغیر)."""
    cr = mail_credentials.resolve()
    return cr if cr.get("ok") else None


def armed_reason() -> str:
    """دلیلِ صادقِ «چرا مسلح نیست» (رشتهٔ خالی = مسلح است). هرگز مقدارِ secret."""
    cr = mail_credentials.resolve()
    return "" if cr.get("ok") else str(cr.get("reason") or "smtp-creds-missing")


def _read_secret(cr: dict) -> str:
    """پسورد را **لحظهٔ ارسال** از env می‌خوانَد (با نامی که resolve داده).
    این تنها نقطه‌ای است که مقدارِ پسورد در حافظه ظاهر می‌شود و هرگز از این
    تابع بیرون نمی‌رود مگر مستقیم به داخلِ `send_impl`."""
    return str(os.environ.get(str(cr.get("secret_env") or ""), "") or "")


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


def _bump_send_counter(now=None) -> "int | None":
    """شمارندهٔ سقفِ روزانه فقط با ارسالِ تأییدشده بالا می‌رود (رأی مالک ۲۰۲۶-۰۷-۳۱: ۱۰).
    منبعِ شمارنده outbound_worker است (کنارِ LEAD_DAILY_SEND_CAP). fail-soft + alert.

    خروجی (نو، ۰۸-۰۱): شمارِ **جدیدِ** امروز، یا None اگر ثبت نشد. فقط اعلان از آن
    استفاده می‌کند؛ هیچ تصمیمی به آن وابسته نیست، پس مسیرِ ارسال دست‌نخورده است."""
    try:
        import outbound_worker as _ow   # noqa: WPS433 — lazy، هم‌پوشه
        _n = _ow.record_send(now=now)
    except Exception:  # noqa: BLE001
        try:
            opslib.alert(["lead transport: sent ولی شمارندهٔ سقف ثبت نشد — بررسی کن"])
        except Exception:  # noqa: BLE001
            pass
        return None
    try:
        return int(_n)
    except (TypeError, ValueError):
        return None


# ── اعلانِ «ایمیل واقعاً رفت» به مالک (GAP-1) ───────────────────────────────────
def notify_enabled() -> bool:
    """فلگِ اعلان — پیش‌فرض خاموش. خاموش = بایت‌به‌بایتِ رفتارِ امروز."""
    return str(os.environ.get(NOTIFY_FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def _esc(s) -> str:
    """گریزِ HTML — کانالِ تلگرام با parse_mode=HTML می‌فرستد؛ `<` ِ خام پیام را می‌شکند."""
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _ltr(s) -> str:
    """تکهٔ LTR داخلِ متنِ فارسی — بدونِ ایزوله، `QT-20260801-003` وارونه دیده می‌شود."""
    return _LRI + str(s if s is not None else "") + _PDI


def _fa(n) -> str:
    """رقمِ فارسی برای عددهای متن (نه برای شناسه‌ها). None ⇒ «؟» — نه صفر."""
    return "؟" if n is None else str(n).translate(_FA_DIGITS)


def _qt_number(draft) -> str:
    """شمارهٔ کوت از draft. ترتیب: کلیدِ صریحِ `qt_number` → الگویِ
    `QT-YYYYMMDD-NNN` ِ lead_quote داخلِ سوژه (چیزی که
    `outbound_worker._draft_for` می‌سازد) → «unknown». هرگز حدس، هرگز استثنا."""
    try:
        import re as _re   # noqa: WPS433 — stdlib، lazy
        if isinstance(draft, dict):
            qt = str(draft.get("qt_number") or "").strip()
            if qt:
                return qt[:40]
            text = str(draft.get("subject") or "")
        else:
            text = str(draft or "")
        m = _re.search(r"QT-\d{8}-\d+", text)
        if m:
            return m.group(0)
        m = _re.search(r"Quote\s+(\S+)", text)
        if m:
            return m.group(1)[:40]
    except Exception:  # noqa: BLE001
        pass
    return "unknown"


def _daily_cap() -> "int | None":
    """سقفِ روزانه از خودِ outbound_worker (تک‌منبع). نبود ⇒ None، نه عددِ حدسی —
    عددِ حدسی یعنی گزارشِ «۳ از ۱۰» وقتی سقف واقعاً چیزِ دیگری است."""
    try:
        import outbound_worker as _ow   # noqa: WPS433 — lazy، هم‌پوشه
        return int(_ow.LEAD_DAILY_SEND_CAP)
    except Exception:  # noqa: BLE001
        return None


def notify_text(lead_id: str, domain: str, qt: str, sent_today, cap) -> str:
    """متنِ اعلان. چهار چیزی که مالک لازم دارد و **نه بیشتر**: کدام لید، دامنهٔ
    گیرنده (نه آدرس)، شمارهٔ کوت، و شمارِ امروز در برابرِ سقف."""
    return ("📤 <b>ایمیلِ لید فرستاده شد</b> — اطلاع است، نه درخواستِ رأی\n"
            f"🆔 لید: <code>{_ltr(_esc(lead_id))}</code>\n"
            f"✉️ دامنهٔ گیرنده: <code>{_ltr(_esc(domain))}</code> "
            "(آدرسِ کامل عمداً نوشته نمی‌شود)\n"
            f"📄 کوت: <code>{_ltr(_esc(qt))}</code>\n"
            f"📊 امروز: {_fa(sent_today)} از {_fa(cap)}")


def _owner_channel():
    """کانالِ اثبات‌شدهٔ تحویل به مالک — همان کارخانهٔ `wiring.make_telegram_channel`
    که organism/c6_trigger/deep_think استفاده می‌کنند. بدونِ توکن None می‌دهد.

    عمداً یک لوله‌ی تازه ساخته نمی‌شود: سیستمِ اعلانِ دوم یعنی دو مسیرِ ارسال که
    یکی‌شان همیشه از سیاستِ مالک (ساعتِ سکوت/HOLD/redaction) عقب می‌ماند."""
    try:
        _p = str(_HERE.parent)
        if _p not in sys.path:
            sys.path.insert(0, _p)
        import wiring as _w   # noqa: WPS433 — lazy؛ فقط وقتی فلگ روشن است
        return _w.make_telegram_channel()
    except Exception:  # noqa: BLE001
        return None


def _deliver(text: str) -> str:
    """تحویلِ واقعی. خروجی: DELIVERED | UNDELIVERED | NO_CHANNEL. هرگز raise."""
    ch = _owner_channel()
    if ch is None or not hasattr(ch, "send_text"):
        return "NO_CHANNEL"
    try:
        ok = bool(ch.send_text(text, None, stream=NOTIFY_STREAM))
    except TypeError:
        # کانالِ قدیمی بدونِ `stream` — به DM برو، نه به سکوت (الگوی instant_alert_bridge).
        ok = bool(ch.send_text(text))
    return "DELIVERED" if ok else "UNDELIVERED"


def notify_sent(lead_id: str, to_addr: str, draft, *, sent_today=None) -> dict:
    """اعلانِ یک ارسالِ **تأییدشده** به مالک. همیشه dict، هرگز استثنا.

    قاعدهٔ «ثبت همیشه، گیت فقط روی تحویل»: با فلگِ روشن، هر خروجی — حتی نبودِ
    کانال — یک رسیدِ `communication.notified` می‌گذارد. بدونِ آن، «نرفت چون
    کانال نبود» و «نرفت چون تلگرام ۴۰۰ داد» یک شکل می‌شوند: هیچ.

    خروجی: {"notified": bool, "status": str}
    statusها: DELIVERED | UNDELIVERED | NO_CHANNEL | FLAG_OFF | NOTIFY_ERROR
    """
    if not notify_enabled():
        return {"notified": False, "status": "FLAG_OFF"}
    domain = qt = "unknown"
    try:
        domain = recipient_domain(to_addr)
        qt = _qt_number(draft)
        cap = _daily_cap()
        status = _deliver(notify_text(str(lead_id or "unknown"), domain, qt,
                                      sent_today, cap))
    except Exception as e:  # noqa: BLE001 — اعلان هرگز صداکننده را نمی‌کشد
        status = f"NOTIFY_ERROR:{type(e).__name__}"
    _receipt("communication.notified", lead_id,
             {"status": status, "channel": "telegram", "stream": NOTIFY_STREAM,
              "to_domain": domain, "qt_number": qt, "sent_today": sent_today})
    return {"notified": status == "DELIVERED", "status": status}


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

        # ۲) creds — حلِ نام. غایب/ناقص → NOT_ARMED صادقانه با دلیلِ دقیق.
        cr = mail_credentials.resolve()
        if not cr.get("ok"):
            reason = str(cr.get("reason") or "smtp-creds-missing")
            _receipt("communication.not_armed", lead_id,
                     {"status": "NOT_ARMED", "reason": reason})
            return {"sent": False, "status": "NOT_ARMED", "detail": reason}
        password = _read_secret(cr)
        if not password:
            # resolve حضور را دیده بود ولی env بینِ حل و ارسال خالی شد — نامِ
            # متغیر را بگو (نه مقدار) و ساکت نمان.
            reason = "secret-env-empty:" + str(cr.get("secret_env") or "?")
            _receipt("communication.not_armed", lead_id,
                     {"status": "NOT_ARMED", "reason": reason})
            return {"sent": False, "status": "NOT_ARMED", "detail": reason}

        # ۳) گیرنده الزامی.
        if not to_addr:
            _receipt("communication.no_recipient", lead_id,
                     {"status": "NO_RECIPIENT"})
            return {"sent": False, "status": "NO_RECIPIENT", "detail": "no-contact-email"}

        # ۴) یک تلاشِ واقعی — بدونِ retry، timeout ۲۰s.
        message = _build_message(cr["from_addr"], to_addr, draft)
        impl = send_impl if callable(send_impl) else _default_send_impl
        try:
            impl(cr["host"], int(cr["port"]), cr["user"], password,
                 cr["from_addr"], to_addr, message)
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
        _sent_today = _bump_send_counter(now=now)
        # ── اعلانِ مالک (GAP-1) — **آخرین** کارِ مسیر، بعد از هر ثبتِ پایدار ────
        # ترتیب عمدی است: شمارنده اول بالا می‌رود تا عددِ اعلان شاملِ همین ارسال
        # باشد. try/except مطلق است چون ایمیل همین حالا رفته — هیچ خطای اعلانی
        # حق ندارد status را عوض کند یا استثنا بدهد (اعلانِ گم‌شده < ایمیلِ تکراری).
        try:
            notify_sent(lead_id, to_addr, draft, sent_today=_sent_today)
        except Exception:  # noqa: BLE001
            pass
        return {"sent": True, "status": "SENT", "detail": f"to={mask_recipient(to_addr)}"}
    except Exception as e:  # noqa: BLE001 — transport هرگز caller را نمی‌کشد
        return {"sent": False, "status": "FAILED", "detail": f"transport-error:{type(e).__name__}"}


def _self_test_message(owner_addr: str) -> str:
    """پیامِ آشکارا-برچسب‌خوردهٔ خودآزمون — کسی نباید با ایمیلِ لید اشتباهش بگیرد."""
    from email.mime.text import MIMEText   # noqa: WPS433 — stdlib
    body = ("This is an automated SELF-TEST from the Octopus outbound transport.\n"
            "It proves the SMTP pipe works end-to-end. It was sent to the owner's\n"
            "own address only. No lead was contacted. No quota was consumed.\n\n"
            "این یک خودآزمونِ خودکارِ لولهٔ ارسال است — به هیچ لیدی چیزی نرفت.\n")
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "[SELF-TEST] Octopus outbound transport"
    msg["From"] = owner_addr
    msg["To"] = owner_addr
    return msg.as_string()


def self_test(to_addr=None, *, now=None, send_impl=None) -> dict:
    """اثباتِ end-to-end ِ لوله — **فقط** به آدرسِ خودِ مالک. همیشه dict، هرگز استثنا.

    این تنها مسیرِ این ماژول است که بدونِ گذر از گیتِ لید واقعاً به SMTP می‌رسد،
    و دقیقاً به همین دلیل سه قفل دارد:
      ۱. گیرنده باید **برابرِ** `from_addr` ِ حل‌شده باشد (آدرسِ خودِ مالک).
         هر چیزِ دیگر ⇒ REFUSED، صفر تلاش. (پیش‌فرضِ None = خودِ همان آدرس.)
      ۲. شمارندهٔ سقفِ روزانه **لمس نمی‌شود** — خودآزمون سهمیهٔ لید را نمی‌خورد.
      ۳. در دفترِ funnel (`communication.sent/failed`) چیزی نمی‌نویسد — این
         ارسال یک «ارتباط با لید» نیست و نباید در قیفِ فروش دیده شود.
    فقط یک رسیدِ `communication.self_test` در events.jsonl می‌نشیند (با آدرسِ ماسک‌شده).

    خروجی: {"sent": bool, "status": str, "detail": str}
    statusها: SENT | FAILED | NOT_ARMED | REFUSED
    """
    try:
        cr = mail_credentials.resolve()
        if not cr.get("ok"):
            reason = str(cr.get("reason") or "smtp-creds-missing")
            _receipt("communication.self_test", "self-test",
                     {"status": "NOT_ARMED", "reason": reason})
            return {"sent": False, "status": "NOT_ARMED", "detail": reason}
        owner = _norm_email(cr.get("from_addr") or "")
        target = _norm_email(to_addr) if to_addr is not None else owner
        if not owner:
            return {"sent": False, "status": "NOT_ARMED", "detail": "no-owner-address"}
        if target != owner:
            # قفلِ ۱ — خودآزمون هرگز به کسی جز مالک نمی‌رود.
            _receipt("communication.self_test", "self-test",
                     {"status": "REFUSED", "reason": "recipient-is-not-owner",
                      "requested": mask_recipient(target)})
            return {"sent": False, "status": "REFUSED",
                    "detail": "self-test may only target the owner address"}
        password = _read_secret(cr)
        if not password:
            reason = "secret-env-empty:" + str(cr.get("secret_env") or "?")
            _receipt("communication.self_test", "self-test",
                     {"status": "NOT_ARMED", "reason": reason})
            return {"sent": False, "status": "NOT_ARMED", "detail": reason}
        impl = send_impl if callable(send_impl) else _default_send_impl
        try:
            impl(cr["host"], int(cr["port"]), cr["user"], password,
                 owner, owner, _self_test_message(owner))
        except Exception as e:  # noqa: BLE001 — شکست = FAILED صادق
            detail = f"smtp-error:{type(e).__name__}"
            _receipt("communication.self_test", "self-test",
                     {"status": "FAILED", "detail": detail,
                      "to": mask_recipient(owner), "how": cr.get("how")})
            return {"sent": False, "status": "FAILED", "detail": detail}
        # قفلِ ۲ و ۳: نه _bump_send_counter، نه _funnel_record — عمداً.
        _receipt("communication.self_test", "self-test",
                 {"status": "SENT", "to": mask_recipient(owner),
                  "how": cr.get("how")})
        return {"sent": True, "status": "SENT",
                "detail": f"self-test to={mask_recipient(owner)} via {cr.get('how')}"}
    except Exception as e:  # noqa: BLE001
        return {"sent": False, "status": "FAILED",
                "detail": f"self-test-error:{type(e).__name__}"}


if __name__ == "__main__":
    _st = mail_credentials.status()
    print(json.dumps({"armed": bool(_st.get("ok")), "how": _st.get("how"),
                      "reason": _st.get("reason"),
                      "from_masked": _st.get("from_masked"),
                      "secret_env": _st.get("secret_env"),
                      "secret_present": _st.get("secret_present"),
                      "note": "مسیرِ مجازِ ارسالِ لید فقط outbound_worker.send_one؛ "
                              "self_test فقط به آدرسِ خودِ مالک."},
                     ensure_ascii=False))
