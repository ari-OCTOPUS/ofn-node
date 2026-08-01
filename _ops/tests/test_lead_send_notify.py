#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_send_notify — ایمیلی که به مشتریِ واقعی می‌رود نباید بی‌صدا برود.

شکافی که این تست می‌بندد (GAP-1، ۲۰۲۶-۰۸-۰۱، پیش از مسلح‌شدنِ ایمیلِ واقعی):

  یک ارسالِ **موفقِ** لید سه اثر داشت — یک رسید در `events.jsonl`، یک ردیف در
  `funnel.db`، و یک ++ روی شمارندهٔ سقف — و **صفر** اطلاع در تلگرام. تنها
  هشدارِ کلِ این قوس (`outbound_worker.py:193`) دقیقاً برعکس شلیک می‌کند: وقتی
  گیت باز شد ولی transport **نفرستاد**. یعنی «نرفت» صدا داشت و «رفت» نداشت؛
  اولین ایمیل به یک مشتریِ واقعی در سکوتِ کامل می‌رفت.

قواعدی که این‌جا گارد می‌شوند:
  · اعلان فقط روی مسیرِ **تأییدشده** می‌آید. FAILED / NOT_ARMED / SUPPRESSED /
    NO_RECIPIENT هیچ‌کدام «ایمیل رفت» نیستند — اعلان روی آن‌ها یعنی دروغ.
  · شکستِ اعلان هرگز ارسال را برنمی‌گرداند. ایمیل قبلاً رفته؛ استثنای اعلان
    نباید status را از SENT به FAILED ببرد (وگرنه لایهٔ بالادست دوباره می‌فرستد
    — و ایمیلِ تکراری ضررِ بزرگ‌تری از اعلانِ گم‌شده دارد).
  · انضباطِ PII: فقط **دامنه**. نه آدرسِ کامل، نه حتی local-part ِ ماسک‌شده‌ای
    که `mask_recipient` برای رسیدِ فنی نگه می‌دارد.
  · فلگ خاموش = بایت‌به‌بایتِ دیروز: صفر کانال، صفر رسیدِ تازه.
  · «ثبت همیشه، گیت فقط روی تحویل»: نبودِ کانال هم رسید می‌گذارد، وگرنه
    «کانال نبود» و «تلگرام رد کرد» یک شکل می‌شوند: هیچ.

صفر شبکه · صفر توکن · صفر لمسِ درختِ زنده (SMTP و تلگرام هر دو جاسوسِ تزریقی‌اند).
"""
import json
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("lead-send-notify")

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                          # noqa: E402
import outbound_worker as ow           # noqa: E402
import lead_outbound_transport as lot  # noqa: E402
import mail_credentials as mc          # noqa: E402

NOW_S = 1_785_400_000.0

_SMTP_ENV = {"OCTOPUS_SMTP_HOST": "localhost", "OCTOPUS_SMTP_PORT": "2525",
             "OCTOPUS_SMTP_USER": "smtp-test-user",
             "OCTOPUS_SMTP_PASS": "hunter2-super-secret",
             "OCTOPUS_SMTP_FROM": "quotes@example.com"}

# همان خطرِ واقعیِ کشف‌شدهٔ ۰۷-۳۱ (رجوع به test_lead_outbound_transport): اگر
# ماشینِ میزبان `GMAIL_*` ِ زنده در env داشته باشد، تستِ «بی-creds» مسلح می‌شود و
# `_default_send_impl` ِ واقعی به یک آدرسِ نمونه ایمیل می‌زند. هر مسیرِ credential
# این‌جا صریحاً کنترل می‌شود و هیچ `.env` ِ واقعی‌ای وسطِ تست کلید تزریق نمی‌کند.
_CRED_KEYS = tuple(_SMTP_ENV) + (mc.GMAIL_ADDR_ENV, mc.GMAIL_SECRET_ENV,
                                 mc.GMAIL_FALLBACK_FLAG)
mc._ensure_env_loaded = lambda: None

_REAL_OWNER_CHANNEL = lot._owner_channel

# آدرسِ کاملِ گیرنده — هیچ‌جای متنِ اعلان و هیچ رسیدی نباید ببیندش.
_FULL_ADDR = "jane.doe@acme-painting.com.au"
_LOCAL_PART = "jane.doe"
_DOMAIN = "acme-painting.com.au"


# ── جاسوس‌ها ───────────────────────────────────────────────────────────────────
class SpySmtp:
    """جای smtplib. fail=True ⇒ ارسالِ ناموفق (بدونِ هیچ شبکه‌ای)."""

    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def __call__(self, host, port, user, pw, from_addr, to_addr, message):
        self.calls.append(to_addr)
        if self.fail:
            raise ConnectionError("boom")


class SpyChannel:
    """کانالِ تلگرامِ ساختگی با همان امضایِ `approval_channel.send_text`."""

    def __init__(self, ok=True):
        self.sent = []
        self.ok = ok

    def send_text(self, text, reply_markup=None, chat_id=None, stream=None,
                  topic_id=None):
        self.sent.append({"text": text, "reply_markup": reply_markup,
                          "stream": stream, "chat_id": chat_id})
        return self.ok


class ChannelFactory:
    """جای `lot._owner_channel` — می‌شمارد که اصلاً **صدا زده شد یا نه**.

    شمارنده مهم است: «بایت‌به‌بایتِ دیروز» یعنی با فلگِ خاموش حتی کانال هم ساخته
    نمی‌شود (نه اینکه ساخته شود و پیام نرود)."""

    def __init__(self, channel=None, raises=False):
        self.channel = channel
        self.raises = raises
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.raises:
            raise RuntimeError("notifier is broken")
        return self.channel


# ── کمکی‌ها ────────────────────────────────────────────────────────────────────
def _events_path():
    return opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"


def _events() -> list:
    try:
        raw = _events_path().read_text("utf-8")
    except OSError:
        return []
    out = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


def _event_types_since(n: int) -> list:
    return [e.get("event_type") for e in _events()[n:]]


def _notified_since(n: int) -> list:
    return [e for e in _events()[n:] if e.get("event_type") == "communication.notified"]


def _set_creds(on: bool):
    for k in _CRED_KEYS:
        os.environ.pop(k, None)
    if on:
        os.environ.update(_SMTP_ENV)


def _set_flag(on: bool):
    if on:
        os.environ[lot.NOTIFY_FLAG] = "1"
    else:
        os.environ.pop(lot.NOTIFY_FLAG, None)


def _fresh_counter():
    try:
        ow._counter_path().unlink()
    except OSError:
        pass


def _cand(lead_id, email=_FULL_ADDR, **extra):
    c = {"lead_id": lead_id, "contact": {"email": email},
         "source": {"channel": "telegram_manual"}}
    c.update(extra)
    return c


def _draft(qt="QT-20260801-007"):
    """همان شکلی که `outbound_worker._draft_for` می‌سازد: شماره فقط در سوژه."""
    return {"subject": f"Quote {qt} — painting works",
            "body": "Two coats, interior.\n\nTotal price: A$4,200–5,100"}


def _arm(channel=None, raises=False, flag=True, creds=True):
    """محیطِ یک ارسالِ مسلح + جاسوسِ کانال. خروجی: کارخانهٔ کانال."""
    _set_creds(creds)
    _set_flag(flag)
    _fresh_counter()
    factory = ChannelFactory(channel=channel, raises=raises)
    lot._owner_channel = factory
    return factory


# ── ۱) اعلان روی ارسالِ موفق ────────────────────────────────────────────────────
def t_a_a_confirmed_send_reaches_the_owner_in_telegram():
    """قلبِ شکاف: ایمیل رفت ⇒ مالک در تلگرام می‌فهمد.

    و پیام باید هر چهار چیزی را بگوید که تصمیمِ بعدی به آن وابسته است: کدام
    لید، دامنهٔ گیرنده، شمارهٔ کوت، و شمارِ امروز در برابرِ سقف. پیامی که فقط
    «یک ایمیل رفت» بگوید همان سکوت است با صدای بیشتر."""
    ch = SpyChannel()
    _arm(channel=ch)
    smtp = SpySmtp()
    r = lot.send(_cand("L-notify-1"), _draft(), now=NOW_S, send_impl=smtp)
    assert r["sent"] is True and r["status"] == "SENT", r
    assert len(smtp.calls) == 1, "ایمیل اصلاً نرفت"
    assert len(ch.sent) == 1, f"ارسالِ موفق باید دقیقاً یک اعلان بدهد: {ch.sent!r}"
    text = ch.sent[0]["text"]
    assert "L-notify-1" in text, text
    assert _DOMAIN in text, text
    assert "QT-20260801-007" in text, text
    # شمارِ امروز = ۱ (رقمِ فارسی) از سقفِ ۱۰ — و شمارنده قبل از اعلان بالا رفته.
    assert "۱ از ۱۰" in text, f"شمار/سقف در متن نیست: {text!r}"
    assert ow.sends_today(now=NOW_S) == 1, "شمارنده باید بالا رفته باشد"


def t_a_b_the_notification_goes_through_the_proven_owner_channel():
    """تحویل از همان قراردادی می‌رود که کانالِ تأییدشده می‌فهمد.

    `stream="lead"` تنها جریانی است که `approval_channel._STREAM_TOPIC` برای لید
    می‌شناسد؛ نامِ تازه یعنی جریانِ ناشناخته، و جریانِ ناشناخته یعنی مسیرِ
    ناشناخته. و `reply_markup=None` عمدی است: این اطلاع است نه کارتِ رأی —
    دکمهٔ بی‌هندلر همان «۳۵ کارتِ مرده» را بازتولید می‌کند."""
    ch = SpyChannel()
    _arm(channel=ch)
    lot.send(_cand("L-notify-stream"), _draft(), now=NOW_S, send_impl=SpySmtp())
    assert len(ch.sent) == 1, ch.sent
    assert ch.sent[0]["stream"] == "lead", ch.sent[0]
    assert ch.sent[0]["reply_markup"] is None, "اعلان نباید دکمه داشته باشد"
    assert ch.sent[0]["chat_id"] is None, "مقصد را سیاستِ کانال تعیین می‌کند، نه این ماژول"


def t_a_c_the_receipt_records_the_delivery():
    """«ثبت همیشه»: تحویلِ موفق هم رسیدِ خودش را می‌گذارد، نه فقط تحویلِ ناموفق."""
    n = len(_events())
    ch = SpyChannel()
    _arm(channel=ch)
    lot.send(_cand("L-notify-receipt"), _draft(), now=NOW_S, send_impl=SpySmtp())
    rec = _notified_since(n)
    assert len(rec) == 1, f"رسیدِ اعلان نیست: {_event_types_since(n)}"
    p = rec[0].get("payload") or {}
    assert p.get("status") == "DELIVERED", p
    assert p.get("to_domain") == _DOMAIN, p
    assert p.get("sent_today") == 1, p


# ── ۲) روی ارسالِ ناموفق شلیک نمی‌کند ────────────────────────────────────────────
def t_b_a_a_failed_send_notifies_nothing():
    """SMTP ترکید ⇒ هیچ ایمیلی نرفته ⇒ گفتنِ «ایمیل رفت» دروغ است."""
    ch = SpyChannel()
    f = _arm(channel=ch)
    r = lot.send(_cand("L-fail"), _draft(), now=NOW_S, send_impl=SpySmtp(fail=True))
    assert r["status"] == "FAILED", r
    assert not ch.sent, f"شکست نباید اعلان بدهد: {ch.sent!r}"
    assert f.calls == 0, "شکست حتی نباید کانال بسازد"


def t_b_b_the_three_other_non_send_outcomes_are_silent_too():
    """NOT_ARMED / SUPPRESSED / NO_RECIPIENT هم «ارسال» نیستند.

    این سه شاخه از خطِ اعلان **قبل‌تر** return می‌کنند؛ اگر روزی کسی اعلان را
    بالاتر ببرد (مثلاً برای «ثبتِ بیشتر»)، همین‌جا قرمز می‌شود."""
    ch = SpyChannel()
    f = _arm(channel=ch)

    _set_creds(False)                                     # NOT_ARMED
    assert lot.send(_cand("L-noarm"), _draft(), now=NOW_S)["status"] == "NOT_ARMED"

    _set_creds(True)                                      # SUPPRESSED
    r = lot.send(_cand("L-stop", email="stop@" + _DOMAIN, opt_out=True),
                 _draft(), now=NOW_S, send_impl=SpySmtp())
    assert r["status"] == "SUPPRESSED", r

    r = lot.send({"lead_id": "L-noaddr", "contact": {}}, _draft(),   # NO_RECIPIENT
                 now=NOW_S, send_impl=SpySmtp())
    assert r["status"] == "NO_RECIPIENT", r

    assert not ch.sent, f"هیچ‌کدام از این سه نباید اعلان بدهد: {ch.sent!r}"
    assert f.calls == 0, "هیچ‌کدام نباید کانال بسازد"


# ── ۳) اعلانِ خراب ارسال را نمی‌شکند ────────────────────────────────────────────
def t_c_a_a_broken_notifier_never_breaks_the_send():
    """کانال استثنا می‌دهد ⇒ ایمیل همچنان SENT است و شمارنده بالا رفته.

    این مهم‌ترین ناوردایِ این فایل است: اگر اعلان بتواند status را خراب کند،
    لایهٔ بالادست ارسالِ رفته را «نرفته» می‌بیند و **دوباره می‌فرستد**. ایمیلِ
    تکراری به مشتریِ واقعی ضررِ بزرگ‌تری از اعلانِ گم‌شده دارد."""
    n = len(_events())
    f = _arm(raises=True)
    smtp = SpySmtp()
    r = lot.send(_cand("L-broken"), _draft(), now=NOW_S, send_impl=smtp)
    assert r == {"sent": True, "status": "SENT",
                 "detail": "to=" + lot.mask_recipient(_FULL_ADDR)}, r
    assert len(smtp.calls) == 1, "ایمیل باید رفته باشد"
    assert f.calls == 1, "کانال باید تلاش شده باشد"
    assert ow.sends_today(now=NOW_S) == 1, "شمارندهٔ سقف نباید قربانیِ اعلان شود"
    rec = _notified_since(n)
    assert len(rec) == 1 and str((rec[0].get("payload") or {}).get("status")
                                 ).startswith("NOTIFY_ERROR"), rec
    # و ردیفِ funnel هم سرِ جایش است (اعلان چیزی را rollback نمی‌کند).
    assert "communication.sent" in _event_types_since(n), _event_types_since(n)


def t_c_b_a_channel_that_refuses_is_recorded_not_swallowed():
    """کانال هست ولی False داد (تلگرام رد کرد / ساعتِ سکوت HOLD کرد) ⇒
    ارسال SENT می‌مانَد ولی رسید صادقانه UNDELIVERED می‌گوید."""
    n = len(_events())
    _arm(channel=SpyChannel(ok=False))
    r = lot.send(_cand("L-refused"), _draft(), now=NOW_S, send_impl=SpySmtp())
    assert r["status"] == "SENT", r
    rec = _notified_since(n)
    assert len(rec) == 1 and (rec[0].get("payload") or {}).get("status") == "UNDELIVERED", rec


def t_c_c_no_channel_still_leaves_a_receipt():
    """«ثبت همیشه، گیت فقط روی تحویل»: بی‌کانال هم رد می‌گذارد.

    بدونِ این رسید، «توکن نبود» و «تلگرام ۴۰۰ داد» هر دو یک شکل می‌شوند: هیچ —
    و همان‌جاست که یک شکافِ تحویل ماه‌ها نامرئی می‌مانَد."""
    n = len(_events())
    _arm(channel=None)
    r = lot.send(_cand("L-nochannel"), _draft(), now=NOW_S, send_impl=SpySmtp())
    assert r["status"] == "SENT", r
    rec = _notified_since(n)
    assert len(rec) == 1 and (rec[0].get("payload") or {}).get("status") == "NO_CHANNEL", rec


# ── ۴) فلگِ خاموش = بایت‌به‌بایتِ دیروز ─────────────────────────────────────────
def t_d_a_flag_off_is_byte_identical_to_today():
    """با فلگِ خاموش: نه کانالی ساخته می‌شود، نه رسیدِ تازه‌ای می‌نشیند.

    «کانال ساخته شود ولی پیام نرود» کافی نیست — ساختِ کانال خودش I/O و
    ChronoDB باز می‌کند. سنجهٔ درست شمارِ **فراخوانیِ کارخانه** است."""
    n = len(_events())
    ch = SpyChannel()
    f = _arm(channel=ch, flag=False)
    smtp = SpySmtp()
    r = lot.send(_cand("L-flagoff"), _draft(), now=NOW_S, send_impl=smtp)
    assert r["sent"] is True and r["status"] == "SENT", r
    assert len(smtp.calls) == 1, "ایمیل باید مثلِ دیروز رفته باشد"
    assert ow.sends_today(now=NOW_S) == 1, "شمارنده باید مثلِ دیروز بالا رفته باشد"
    assert f.calls == 0, "فلگِ خاموش نباید حتی کانال بسازد"
    assert not ch.sent, ch.sent
    # مجموعهٔ رویدادهای این ارسال دقیقاً همان چیزی است که قبل از GAP-1 بود.
    assert _event_types_since(n) == ["communication.sent"], _event_types_since(n)


def t_d_b_notify_sent_alone_is_a_noop_when_the_flag_is_off():
    """همان گارد روی خودِ تابع (نه فقط از مسیرِ send) — تا اگر روزی صداکنندهٔ
    دومی پیدا کرد، فلگ همچنان تنها کلیدِ مسلح‌کردن باشد."""
    n = len(_events())
    f = _arm(channel=SpyChannel(), flag=False)
    out = lot.notify_sent("L-direct", _FULL_ADDR, _draft(), sent_today=3)
    assert out == {"notified": False, "status": "FLAG_OFF"}, out
    assert f.calls == 0 and _event_types_since(n) == [], _event_types_since(n)


# ── ۵) انضباطِ PII ──────────────────────────────────────────────────────────────
def t_e_a_the_notification_carries_the_domain_and_never_the_address():
    """چت برای همیشه می‌ماند؛ آدرسِ مشتری نباید در آن بنشیند.

    حتی ماسکِ `mask_recipient` (که دو حرفِ اولِ local-part را نگه می‌دارد و برای
    رسیدِ فنی کافی است) این‌جا زیادی است."""
    ch = SpyChannel()
    _arm(channel=ch)
    lot.send(_cand("L-pii"), _draft(), now=NOW_S, send_impl=SpySmtp())
    text = ch.sent[0]["text"]
    assert _FULL_ADDR not in text, text
    assert _LOCAL_PART not in text, text
    assert lot.mask_recipient(_FULL_ADDR) not in text, text
    assert _DOMAIN in text, text
    # و هیچ secret ِ SMTP هم در متن نیست.
    assert "hunter2-super-secret" not in text and "smtp-test-user" not in text, text


def t_e_b_the_notify_receipt_carries_no_address_either():
    """رسیدِ اعلان هم فقط دامنه دارد — رسیدها append-only اند و پاک نمی‌شوند."""
    n = len(_events())
    _arm(channel=SpyChannel())
    lot.send(_cand("L-pii-receipt"), _draft(), now=NOW_S, send_impl=SpySmtp())
    blob = json.dumps(_notified_since(n), ensure_ascii=False)
    assert _FULL_ADDR not in blob and _LOCAL_PART not in blob, blob
    assert _DOMAIN in blob, blob


def t_e_c_recipient_domain_never_leaks_a_local_part():
    """ورودیِ بی‌`@` نباید عیناً به‌عنوان «دامنه» چاپ شود.

    `"x".rpartition("@")` سه‌تاییِ `('', '', 'x')` می‌دهد — یعنی پیاده‌سازیِ
    ساده‌دلانه خودِ local-part را دامنه می‌نامد. دقیقاً همان نشتی که این تابع
    برای جلوگیری از آن نوشته شده."""
    assert lot.recipient_domain(_FULL_ADDR) == _DOMAIN
    assert lot.recipient_domain("Jane.Doe@ACME.example") == "acme.example"
    assert lot.recipient_domain("no-at-sign-here") == "unknown"
    assert lot.recipient_domain("trailing@") == "unknown"
    assert lot.recipient_domain("") == "unknown"
    assert lot.recipient_domain(None) == "unknown"


# ── ۶) شمارهٔ کوت ───────────────────────────────────────────────────────────────
def t_f_a_the_quote_number_survives_both_draft_shapes():
    """امروز `outbound_worker._draft_for` شماره را فقط در **سوژه** می‌گذارد؛
    کلیدِ صریح مسیرِ فرداست. هر دو باید کار کنند، و نبودش «unknown» است نه حدس."""
    assert lot._qt_number(_draft()) == "QT-20260801-007"
    assert lot._qt_number({"qt_number": "QT-20260801-011"}) == "QT-20260801-011"
    # attribution_id به‌جای شماره (شاخهٔ `rec.get("qt_number") or aid` ِ درایور)
    assert lot._qt_number({"subject": "Quote attr-9f3 — painting works"}) == "attr-9f3"
    assert lot._qt_number({"subject": "no number at all"}) == "unknown"
    assert lot._qt_number(None) == "unknown"


def t_f_b_the_count_reflects_this_send_not_the_previous_one():
    """اعلان **بعد از** ++ شمارنده می‌آید. اگر ترتیب برگردد، دومین ایمیلِ روز
    «۱ از ۱۰» گزارش می‌شود و مالک همیشه یک قدم عقب است."""
    ch = SpyChannel()
    _arm(channel=ch)
    for _ in range(3):
        lot.send(_cand("L-count"), _draft(), now=NOW_S, send_impl=SpySmtp())
    assert len(ch.sent) == 3, ch.sent
    assert "۱ از ۱۰" in ch.sent[0]["text"], ch.sent[0]["text"]
    assert "۲ از ۱۰" in ch.sent[1]["text"], ch.sent[1]["text"]
    assert "۳ از ۱۰" in ch.sent[2]["text"], ch.sent[2]["text"]


def t_f_c_the_cap_comes_from_the_worker_not_a_local_guess():
    """سقف تک‌منبع است. عددِ هاردکد این‌جا یعنی روزی که مالک رأیش را عوض کند،
    اعلان با اطمینانِ کامل عددِ اشتباه می‌گوید."""
    text = lot.notify_text("L-x", "example.com", "QT-1", 4, lot._daily_cap())
    assert lot._daily_cap() == ow.LEAD_DAILY_SEND_CAP
    assert "۴ از " + str(ow.LEAD_DAILY_SEND_CAP).translate(lot._FA_DIGITS) in text, text


def t_f_d_unknown_numbers_are_reported_as_unknown_not_zero():
    """ندانستن هرگز «۰» گزارش نمی‌شود — «۰ از ۱۰» یعنی «هیچ ارسالی نشده»،
    که دقیقاً برعکسِ چیزی است که همین لحظه اتفاق افتاده."""
    text = lot.notify_text("L-x", "example.com", "QT-1", None, None)
    assert "؟ از ؟" in text, text
    assert "۰" not in text, text


# ── ۷) HTML و bidi ─────────────────────────────────────────────────────────────
def t_g_a_hostile_values_cannot_break_the_html_message():
    """کانال با parse_mode=HTML می‌فرستد؛ `<` ِ خام کلِ پیام را از تلگرام برمی‌گرداند
    (۴۰۰) — یعنی همان سکوتی که این لِین دارد می‌بندد، با یک راهِ تازه."""
    text = lot.notify_text("<b>L", "a<b>.com", "QT<script>", 1, 10)
    assert "<b>L" not in text and "&lt;b&gt;L" in text, text
    assert "<script>" not in text, text


def t_g_b_latin_identifiers_are_bidi_isolated():
    """بدونِ ایزوله، `QT-20260801-007` در متنِ فارسی وارونه دیده می‌شود و مالک
    شمارهٔ کوت را اشتباه می‌خواند (درسِ «کارتِ فارسی و bidi»)."""
    text = lot.notify_text("L-1", "example.com", "QT-20260801-007", 1, 10)
    lri, pdi = "\u2066", "\u2069"          # LRI … PDI — همان ثابت‌های ماژول
    assert (lri, pdi) == (lot._LRI, lot._PDI), (lot._LRI, lot._PDI)
    assert lri + "QT-20260801-007" + pdi in text, repr(text)
    assert lri + "example.com" + pdi in text, repr(text)


if __name__ == "__main__":
    try:
        checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
        failed = harness.run(checks)
    finally:
        lot._owner_channel = _REAL_OWNER_CHANNEL
    print(f"\n{'✅' if not failed else '❌'} test_lead_send_notify: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
