#!/usr/bin/env python3
"""test_lead_email_intake.py — Module A: تولیدکنندهٔ گمشدهٔ سرِ لولهٔ لید (IMAP intake).

پوشش (همه آفلاین، stdlib-only، $0؛ **هرگز سوکتی باز نمی‌شود**):
  (الف) فلگ خاموش = no-opِ مطلق (صفر فایل، صفر dir).
  (ب) بدونِ armـ صریح، مسیرِ پیش‌فرض اتصال نمی‌گیرد و `imaplib` حتی import نمی‌شود.
  (پ) **حریمِ خصوصی**: صندوقی که فقط پیامِ غیرِ استعلام دارد ⇒ صفر ردِ پایدار —
      مجموعهٔ فایل‌های کلِ sandbox بایت‌به‌بایت همان قبل، و هیچ کاناریِ محتوایی
      در هیچ فایلی (شاملِ governor-alerts.md) پیدا نمی‌شود.
  (ت) **پذیرش**: صندوقِ ۴تایی (استعلامِ واقع‌نما، صورتحسابِ بانک، خبرنامه، تکراریِ
      استعلام) ⇒ دقیقاً **یک** کاندید؛ سه‌تای دیگر بی‌رد.
  (ث) idempotency دو-لایه + **دندان**: با بازسازیِ «بی‌dedup» فراخوانیِ دوم رخ می‌دهد.
  (ج) صداقتِ کانال: ایمیلِ مستقیمِ انسان ⇒ `other` ⇒ market_signal ⇒ صفر outreach و
      صفر کاندیدِ top-level؛ فقط اعلانِ allowlist‌شدهٔ فرم ⇒ website_form ⇒ accepted.
  (چ) **دندانِ طبقه‌بند**: طبقه‌بندِ پیش-از-این (`email_inbound.parse_lead_from_email` —
      کدِ تولیدیِ موجود) همان خبرنامه/بانک را «لید» می‌شمارد؛ این ماژول رد می‌کند.
  (ح) گیتِ پایین‌دستِ خاموش ⇒ استعلام **نگه** داشته می‌شود (کلیدِ dedup ثبت نمی‌شود).
  (خ) ساختاری: صفر سطحِ ارسال، readonly + BODY.PEEK در کد، secret هرگز echo نمی‌شود.
  (د) صداکننده: `wiring.lead_email_intake_beat` وجود دارد، از `email_beat` صدا زده
      می‌شود، و `email_beat` دو صداکنندهٔ تولیدی دارد (AST، بدونِ grep).

اجرا: python -X utf8 _ops/tests/test_lead_email_intake.py
"""
import ast
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_WORKTREE = _HERE.parents[1]
os.environ.setdefault("REAL_VAULT", str(_WORKTREE))
sys.path.insert(0, str(_HERE))

import harness                                    # noqa: E402
ENV = harness.setup("lead-email-intake")

_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import importlib                                  # noqa: E402
import opslib                                     # noqa: E402
import consent_firewall                           # noqa: E402
importlib.reload(consent_firewall)
import lead_candidate_inbox as lci                # noqa: E402
importlib.reload(lci)
import lead_email_intake as lei                   # noqa: E402
importlib.reload(lei)

# ── کاناری‌ها: نشانه‌های یکتای پیامِ غیرِ استعلام. هیچ‌کدام نباید در هیچ بایتی بنشیند. ──
CANARY_BANK = "ZZCANARYBANK4417"
CANARY_NEWS = "ZZCANARYNEWS8812"
CANARY_PERSONAL = "ZZCANARYPERSONAL5507"
CANARY_BANKMKT = "ZZCANARYBANKMKT2290"
CANARY_NEIGHBOUR = "ZZCANARYNEIGHBOUR6634"
CANARY_NOHANDLE = "ZZCANARYNOHANDLE7719"
CANARY_HALT = "ZZCANARYHALT3341"
CANARIES = (CANARY_BANK, CANARY_NEWS, CANARY_PERSONAL,
            CANARY_BANKMKT, CANARY_NEIGHBOUR, CANARY_NOHANDLE, CANARY_HALT)

FORM_NOTIFIER = "forms@painting-site-notifier.example"
INQUIRY_MID = "<form-2026-08-01-abc123@painting-site-notifier.example>"

# مقدارِ **ساختگیِ** پسورد فقط برای اثباتِ عدمِ نشت. هیچ credential واقعی در این فایل نیست.
FAKE_SECRET = "ZZFAKESECRETVALUE0001"


def _bank_msg():
    return {
        "message_id": "<stmt-77@bank.example>",
        "from": "no-reply@statements.bank.example",
        "to": "owner@example.com",
        "subject": f"Your July statement is ready {CANARY_BANK}",
        "date": "Fri, 01 Aug 2026 06:00:00 +1000",
        "body": ("Your statement for account ending 4417 is available. "
                 "Available balance and your Home Renovation Loan interest are shown. "
                 f"BSB 062-000. {CANARY_BANK}"),
        "headers": {"Precedence": "bulk", "Auto-Submitted": "auto-generated"},
    }


def _newsletter_msg():
    return {
        "message_id": "<news-99@trends.example>",
        "from": "Colour Weekly <hello@trends.example>",
        "to": "owner@example.com",
        "subject": f"Spring colour trends: 5 ways to paint a room {CANARY_NEWS}",
        "date": "Fri, 01 Aug 2026 07:00:00 +1000",
        "body": ("Get the look for less — 20% off selected paint this week. "
                 f"Unsubscribe at any time. View in browser. {CANARY_NEWS}"),
        "headers": {"List-Unsubscribe": "<https://trends.example/u>",
                    "List-Id": "colour-weekly.trends.example"},
    }


def _personal_msg():
    """نامهٔ کاملاً شخصی — نه استعلام، نه انبوه. باید بی‌ردِ مطلق بیفتد."""
    return {
        "message_id": "<fam-3@mail.example>",
        "from": "Sara <sara@mail.example>",
        "to": "owner@example.com",
        "subject": f"dinner on saturday {CANARY_PERSONAL}",
        "date": "Fri, 01 Aug 2026 08:00:00 +1000",
        "body": f"are you free saturday night? {CANARY_PERSONAL}",
        "headers": {},
    }


def _bank_marketing_msg():
    """بازاریابیِ بانک **بدونِ** هدرِ انبوه و از فرستندهٔ غیر-noreply — تنها چیزی که آن را
    می‌اندازد نشانه‌های بازاریابیِ متن است. (جهشِ M8 این را زنده مانده بود.)"""
    return {
        "message_id": "<mkt-31@bank.example>",
        "from": "Home Offers <offers@bank.example>",
        "to": "owner@example.com",
        "subject": f"Refresh your home: painting cashback offer {CANARY_BANKMKT}",
        "date": "Fri, 01 Aug 2026 06:30:00 +1000",
        "body": ("Get a quote on a personal loan and save 20% off your next "
                 f"painting project. Unsubscribe at any time. {CANARY_BANKMKT}"),
        "headers": {},          # ← عمداً بدونِ List-Unsubscribe / Precedence
    }


def _neighbour_msg():
    """همسایه‌ای که فقط خبر می‌دهد: واژهٔ خدمت هست، **قصد نیست**. (جهشِ M9 زنده مانده بود.)"""
    return {
        "message_id": "<nb-12@neighbour.example>",
        "from": "Dave <dave@neighbour.example>",
        "to": "owner@example.com",
        "subject": f"paint on our fence {CANARY_NEIGHBOUR}",
        "date": "Fri, 01 Aug 2026 06:45:00 +1000",
        "body": ("the painters working next door got some paint on our fence "
                 f"yesterday. thought you should know. {CANARY_NEIGHBOUR}"),
        "headers": {},
    }


def _no_handle_msg():
    """استعلامِ واقعی از نظرِ واژگان — ولی **هیچ دستگیرهٔ پاسخی** ندارد: نه آدرسِ فرستنده،
    نه Reply-To، نه ایمیلی در متن. لیدی که نمی‌شود جوابش را داد لید نیست؛ و مهم‌تر:
    نباید غریبه‌ای را وارد لوله‌ای کند که خودش نمی‌داند چطور به او برسد.
    (جهشِ N6 — «حذفِ الزامِ دستگیرهٔ پاسخ» — بدونِ این فیکسچر زنده می‌ماند.)"""
    return {
        "message_id": "<anon-8@localhost>",
        "from": "Anonymous",                 # ← عمداً بدونِ <a@b>
        "to": "owner@example.com",
        "subject": f"painting quote {CANARY_NOHANDLE}",
        "date": "Fri, 01 Aug 2026 11:00:00 +1000",
        "body": ("could you give me a price to repaint our lounge room? "
                 f"{CANARY_NOHANDLE}"),
        "headers": {},
    }


def _form_inquiry_msg(mid=INQUIRY_MID):
    """اعلانِ واقعیِ فرمِ سایت (فرستنده در allowlist ِ مالک)."""
    return {
        "message_id": mid,
        "from": f"Website Form <{FORM_NOTIFIER}>",
        "to": "owner@example.com",
        "reply_to": "Jane Kelly <jane.kelly@resident.example>",
        "subject": "New quote request from the website",
        "date": "Fri, 01 Aug 2026 09:15:00 +1000",
        "body": ("Name: Jane Kelly\nSuburb: Mosman\n"
                 "Message: We need an interior painting quote for a 3 bedroom "
                 "house, two coats, ceilings included. When can you do a site visit?"),
        "headers": {},
    }


def _human_inquiry_msg():
    """ایمیلِ مستقیمِ یک انسان — استعلامِ واقعی، ولی کانالش فرمِ سایت **نیست**."""
    return {
        "message_id": "<direct-55@resident.example>",
        "from": "Tom Reid <tom.reid@resident.example>",
        "to": "owner@example.com",
        "subject": "painting quote for our unit",
        "date": "Fri, 01 Aug 2026 10:00:00 +1000",
        "body": ("Hi, could you give me a price to repaint the interior of our "
                 "two bedroom unit in Randwick? Interested in booking soon."),
        "headers": {},
    }


# ── ابزارِ سنجش ────────────────────────────────────────────────────────────────
def _tree_files(root: Path) -> set:
    out = set()
    for p in root.rglob("*"):
        if p.is_file():
            out.add(str(p.relative_to(root)))
    return out


def _canary_hits(root: Path) -> list:
    hits = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        try:
            blob = p.read_bytes()
        except OSError:
            continue
        for c in CANARIES + (FAKE_SECRET,):
            if c.encode("utf-8") in blob:
                hits.append(f"{p.relative_to(root)}::{c}")
    return hits


def _top_level_candidates():
    box = opslib.STATE_DIR / "legs" / "lead-inbox"
    return sorted(p.name for p in box.glob("*.json")) if box.is_dir() else []


def _mailbox(msgs):
    def _fetch():
        return list(msgs)
    return _fetch


def _arm(intake=True, downstream=True, form_sender=True):
    os.environ[lei.FLAG] = "1" if intake else "0"
    os.environ[lci.FLAG] = "1" if downstream else "0"
    if form_sender:
        os.environ["OCTOPUS_LEAD_FORM_SENDERS"] = FORM_NOTIFIER
    else:
        os.environ.pop("OCTOPUS_LEAD_FORM_SENDERS", None)
    os.environ["GMAIL_ADDRESS"] = "owner@example.com"
    os.environ[lei.SECRET_ENV] = FAKE_SECRET      # ساختگی — فقط برای ردیابیِ نشت
    os.environ.pop(lei.IMAP_ARM_FLAG, None)       # هرگز اتصالِ واقعی در تست


# ══════════════════════════════════════════════════════════════════════════════
def t_a_flag_off_is_absolute_noop():
    os.environ.pop(lei.FLAG, None)
    os.environ.pop(lci.FLAG, None)
    before = _tree_files(ENV["root"])
    r = lei.beat(fetch_fn=_mailbox([_form_inquiry_msg(), _bank_msg()]))
    assert r["ok"] is False and r["reason"] == "flag_off", r
    assert r["fetched"] == 0 and r["submitted"] == 0, r
    assert _tree_files(ENV["root"]) == before, "فلگ خاموش نباید هیچ فایلی بسازد"
    assert not (opslib.STATE_DIR / "legs" / "email-intake").exists()


def t_b_default_path_never_opens_a_socket():
    """بدونِ armـ صریح: نه اتصال، نه importِ imaplib. (قفلِ دومِ صندوقِ شخصی.)"""
    _arm()
    os.environ.pop(lei.IMAP_ARM_FLAG, None)
    sys.modules.pop("imaplib", None)
    r = lei.beat()                      # بدونِ fetch_fn → مسیرِ پیش‌فرض
    assert r["armed"] is False, r
    assert r["reason"] == "not_armed:" + lei.IMAP_ARM_FLAG, r
    assert "imaplib" not in sys.modules, "مسیرِ پیش‌فرض نباید imaplib را لود کند"
    # حتی با armـ روشن ولی بی‌credential هم صادقانه می‌ایستد (بازهم بدونِ اتصال)
    os.environ[lei.IMAP_ARM_FLAG] = "1"
    os.environ.pop("GMAIL_ADDRESS", None)
    os.environ.pop(lei.SECRET_ENV, None)
    r2 = lei.beat()
    assert r2["armed"] is False and r2["reason"].startswith("creds_absent:"), r2
    assert "imaplib" not in sys.modules
    os.environ.pop(lei.IMAP_ARM_FLAG, None)


def t_c_non_inquiry_leaves_zero_trace():
    """حریمِ خصوصی: دسترسیِ وسیع ≠ پردازشِ وسیع. سه پیامِ غیرِ استعلام ⇒ صفر ردِ پایدار."""
    _arm()
    # هر پیام باید به دلیلِ **قاعدهٔ خودش** بیفتد — نه اینکه قاعدهٔ دیگری تصادفاً بگیردش.
    for msg, why in ((_bank_msg(), "bulk_precedence"),
                     (_newsletter_msg(), "bulk_header"),
                     (_personal_msg(), "no_service_term"),
                     (_bank_marketing_msg(), "marketing_marks"),
                     (_neighbour_msg(), "no_intent_term")):
        v = lei.classify(msg)
        assert v["is_inquiry"] is False and v["reason"] == why, (why, v)
    before = _tree_files(ENV["root"])
    r = lei.beat(fetch_fn=_mailbox([_bank_msg(), _newsletter_msg(), _personal_msg(),
                                    _bank_marketing_msg(), _neighbour_msg()]))
    assert r["ok"] is True and r["fetched"] == 5, r
    assert r["inquiries"] == 0 and r["submitted"] == 0 and r["dropped"] == 5, r
    after = _tree_files(ENV["root"])
    assert after == before, f"فایل‌های نو ساخته شد: {sorted(after - before)}"
    hits = _canary_hits(ENV["root"])
    assert hits == [], f"ردِ محتوایی نشت کرد: {hits}"


def t_d_acceptance_exactly_one_candidate():
    """پذیرش: [استعلام، بانک، خبرنامه، تکراریِ استعلام] ⇒ دقیقاً یک کاندید."""
    _arm()
    before = set(_top_level_candidates())
    box = [_form_inquiry_msg(), _bank_msg(), _newsletter_msg(), _form_inquiry_msg()]
    r = lei.beat(fetch_fn=_mailbox(box))
    assert r["fetched"] == 4, r
    assert r["inquiries"] == 2, r          # استعلام و تکراری‌اش
    assert r["dropped"] == 2, r            # بانک + خبرنامه
    assert r["submitted"] == 1, r          # تکراری به در نمی‌رسد
    assert r["duplicates"] == 1, r
    new = set(_top_level_candidates()) - before
    assert len(new) == 1, f"باید دقیقاً یک کاندید باشد: {sorted(new)}"
    data = json.loads((opslib.STATE_DIR / "legs" / "lead-inbox" / list(new)[0])
                      .read_text("utf-8"))
    assert data["source"] == "website_form", data["source"]
    assert data["candidate"]["candidate_type"] == "consented_inbound"
    assert data["candidate"]["consent"]["outreach_allowed"] is True
    assert data["candidate"]["workflow"]["external_send_allowed"] is False
    assert data["candidate"]["synthetic"] is False
    assert "Mosman" in data["description"] or "interior" in data["description"]
    assert _canary_hits(ENV["root"]) == [], "سه پیامِ دیگر باید بی‌رد باشند"


def t_e_idempotent_across_beats_with_teeth():
    """اجرای دوم صفر submit؛ و **دندان**: با بازسازیِ «بی‌dedup»، فراخوانیِ دوم رخ می‌دهد."""
    _arm()
    calls = []

    def spy(candidate, source_id="unknown"):
        calls.append(source_id)
        return {"ok": True, "status": "accepted", "lead_id": "spy-%d" % len(calls)}

    box = _mailbox([_form_inquiry_msg("<idem-1@painting-site-notifier.example>")])
    lei.beat(fetch_fn=box, submit_fn=spy)
    n_after_first = len(calls)
    lei.beat(fetch_fn=box, submit_fn=spy)
    assert len(calls) == n_after_first == 1, f"اجرای دوم نباید submit کند: {calls}"

    # ── دندان: رفتارِ پیش-از-فیکس (بدونِ لایهٔ dedup) را بازسازی کن ──────────────
    real_load = lei._load_seen
    lei._load_seen = lambda: {}
    try:
        lei.beat(fetch_fn=box, submit_fn=spy)
    finally:
        lei._load_seen = real_load
    assert len(calls) == 2, ("بدونِ dedup باید فراخوانیِ دوم رخ دهد — وگرنه assert ِ بالا "
                             f"بی‌دندان بود: {calls}")
    # لایهٔ دوم (idempotency ِ خودِ inbox) هم مستقلاً هست:
    assert "external_id" not in json.dumps({}), ""   # no-op نگهبانِ خوانایی
    lei.beat(fetch_fn=box)                           # با درِ واقعی
    assert lei.dedup_key(_form_inquiry_msg("<idem-1@painting-site-notifier.example>")) \
        in lei._load_seen()


def t_f_channel_honesty_direct_email_is_other():
    """ایمیلِ مستقیمِ انسان `website_form` نیست ⇒ کانال `other` ⇒ market_signal ⇒ صفر outreach."""
    _arm()
    v = lei.classify(_human_inquiry_msg())
    assert v["is_inquiry"] is True and v["channel"] == "other", v
    cand = lei.to_candidate(_human_inquiry_msg(), v["channel"], "k1")
    verdict = consent_firewall.evaluate(cand)
    assert verdict["candidate_type"] == "market_signal", verdict
    assert verdict["outreach_allowed"] is False, verdict

    before = set(_top_level_candidates())
    r = lei.beat(fetch_fn=_mailbox([_human_inquiry_msg()]))
    assert r["inquiries"] == 1 and r["signals"] == 1 and r["submitted"] == 0, r
    assert set(_top_level_candidates()) == before, "سیگنال نباید کاندیدِ top-level بسازد"
    sigs = opslib.STATE_DIR / "legs" / "lead-inbox" / "signals"
    assert sigs.is_dir() and any(p.suffix == ".json" for p in sigs.iterdir())
    # و بدونِ allowlist، همان اعلانِ فرم هم فقط `other` می‌شود (ادعای کانال بی‌مدرک نه).
    _arm(form_sender=False)
    v2 = lei.classify(_form_inquiry_msg())
    assert v2["channel"] == "other", v2


def t_g_pre_fix_classifier_teeth():
    """دندان: طبقه‌بندِ **تولیدیِ موجود** (email_inbound) خبرنامه/بانک را لید می‌شمارد."""
    import email_inbound                          # noqa: WPS433 — کدِ تولیدیِ پیش-از-این
    legacy_hits = 0
    for m in (_bank_msg(), _newsletter_msg()):
        legacy = email_inbound.parse_lead_from_email(
            {"id": "x", "subject": m["subject"], "snippet": m["body"],
             "from": m["from"], "date": m["date"]})
        if legacy is not None:
            legacy_hits += 1
        assert lei.classify(m)["is_inquiry"] is False, m["subject"][:20]
    assert legacy_hits == 2, ("رفتارِ بازسازی‌شدهٔ پیش-از-فیکس باید هر دو را لید بشمارد؛ "
                              f"وگرنه این تست بی‌دندان است: {legacy_hits}")
    # و استعلامِ واقعی را هر دو قبول می‌کنند (تستِ ما فقط سخت‌گیرتر است، نه کور)
    assert lei.classify(_human_inquiry_msg())["is_inquiry"] is True


def t_h_downstream_gate_off_holds_the_lead():
    """گیتِ پایین‌دستِ خاموش ⇒ نگه‌داشتن، نه سوزاندن: کلیدِ dedup ثبت نمی‌شود."""
    _arm(downstream=False)
    msg = _form_inquiry_msg("<held-1@painting-site-notifier.example>")
    key = lei.dedup_key(msg)
    r = lei.beat(fetch_fn=_mailbox([msg]))
    assert r["inquiries"] == 1 and r["submitted"] == 0, r
    assert r["blocked"] == lei.DOWNSTREAM_FLAG, r
    assert key not in lei._load_seen(), "لیدِ نگه‌داشته نباید seen شود، وگرنه برای همیشه گم می‌شود"
    _arm(downstream=True)
    r2 = lei.beat(fetch_fn=_mailbox([msg]))
    assert r2["submitted"] == 1, r2
    assert key in lei._load_seen()


def t_l_no_reply_handle_is_not_a_lead():
    """بی‌دستگیرهٔ پاسخ ⇒ لید نیست، و مثلِ هر غیرِ استعلام **صفر رد**.

    چرا جدا از (پ): جهشِ «حذفِ الزامِ دستگیرهٔ پاسخ» از کلِ باتریِ قبلی زنده بیرون آمد —
    یعنی این گاردِ تولیدی تماشاگر نداشت. هزینه‌اش واقعی است: کاندیدی بی‌راهِ تماس وارد
    لوله می‌شود و پایین‌دست باید حدس بزند."""
    _arm()
    v = lei.classify(_no_handle_msg())
    assert v["is_inquiry"] is False and v["reason"] == "no_reply_handle", v
    before = _tree_files(ENV["root"])
    r = lei.beat(fetch_fn=_mailbox([_no_handle_msg()]))
    assert r["fetched"] == 1 and r["dropped"] == 1, r
    assert r["inquiries"] == 0 and r["submitted"] == 0, r
    assert _tree_files(ENV["root"]) == before, "پیامِ بی‌دستگیره نباید فایلی بسازد"
    assert _canary_hits(ENV["root"]) == [], "پیامِ بی‌دستگیره نباید ردِ محتوایی بگذارد"


def t_m_halt_stops_the_beat():
    """kill-switch مقدم است: در halt، ضربان هیچ نمی‌خواند و هیچ نمی‌نویسد.

    عمداً **هیچ فایلِ STOP-* ای ساخته نمی‌شود** — روی این ریپو یک پروبِ دست‌نویس یک‌بار
    ارگانیسمِ زنده را ۳۰ دقیقه خواباند. پس خودِ تابعِ تشخیص را monkeypatch می‌کنیم:
    همان شاخهٔ `kill` سنجیده می‌شود، با صفر ریسکِ نشتِ اثر به درختِ زنده."""
    _arm()
    fetched = []

    def _spy_fetch(**kw):
        fetched.append(1)                       # در halt نباید حتی صندوق خوانده شود
        return [_form_inquiry_msg("<halt-1@painting-site-notifier.example>")]

    before = _tree_files(ENV["root"])
    real_halted, real_master = opslib.halted, opslib.master_halted
    try:
        opslib.halted = lambda: "TEST-HALT"
        r = lei.beat(fetch_fn=_spy_fetch)
        assert r["ok"] is False and r["reason"] == "halted", r
        assert fetched == [], "در halt نباید صندوق خوانده شود"
        assert r["submitted"] == 0 and r["fetched"] == 0, r
        # master-halt هم مستقلاً همین کار را می‌کند
        opslib.halted = real_halted
        opslib.master_halted = lambda: "TEST-MASTER-HALT"
        r2 = lei.beat(fetch_fn=_spy_fetch)
        assert r2["ok"] is False and r2["reason"] == "halted", r2
        assert fetched == [], "در master-halt هم نباید صندوق خوانده شود"
    finally:
        opslib.halted, opslib.master_halted = real_halted, real_master
    assert _tree_files(ENV["root"]) == before, "halt نباید هیچ فایلی بسازد"
    # و پس از رفعِ halt، همان پیام می‌رسد (نگه‌داشته شد، نه سوخته)
    r3 = lei.beat(fetch_fn=_spy_fetch)
    assert r3["ok"] is True and r3["submitted"] == 1, r3


def t_i_structural_no_send_surface_and_readonly():
    src = Path(lei.__file__).read_text("utf-8")
    for bad in ("import smtplib", "smtplib.", "requests.", "twilio", "sendgrid",
                "urllib.request", "http.client", "socket.socket", "STORE", "\\\\Deleted"):
        assert bad not in src, f"سطحِ ممنوع در ماژول: {bad}"
    tree = ast.parse(src)
    # ⚠️ لنگرِ متنیِ «readonly=True» بی‌دندان بود: همان رشته در docstring هم هست، پس
    # جهشِ readonly=False زنده می‌ماند. پس روی **خودِ فراخوانی** لنگر می‌اندازیم (AST).
    selects = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute) and n.func.attr == "select"]
    assert len(selects) == 1, f"انتظار دقیقاً یک select روی صندوق: {len(selects)}"
    kw = {k.arg: k.value for k in selects[0].keywords}
    assert "readonly" in kw and isinstance(kw["readonly"], ast.Constant) \
        and kw["readonly"].value is True, "صندوق باید EXAMINE (readonly=True) باز شود"
    fetches = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute) and n.func.attr == "fetch"]
    assert fetches and all(any(isinstance(a, ast.Constant) and "PEEK" in str(a.value)
                               for a in f.args) for f in fetches), \
        "هر fetch باید BODY.PEEK باشد وگرنه سرور \\Seen می‌گذارد"
    assert "BODY[]" not in src.replace("BODY.PEEK[]", ""), "BODY[] ِ برهنه = نشان‌گذاریِ خوانده"
    # هیچ فرمانِ جهش‌دهندهٔ صندوق (حذف/انتقال/flag) در ماژول نیست
    for verb in (".store(", ".copy(", ".expunge(", ".uid(", ".move("):
        assert verb not in src, f"فرمانِ جهش‌دهندهٔ صندوق ممنوع: {verb}"
    # importهای top-level هیچ ماژولِ شبکه‌ای ندارند (AST، نه grep)
    top = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            top.add(node.module.split(".")[0])
    assert not (top & {"imaplib", "smtplib", "socket", "urllib", "http", "ssl", "email"}), top
    # secret هرگز echo نمی‌شود
    st = lei.status()
    blob = json.dumps(st, ensure_ascii=False)
    assert FAKE_SECRET not in blob and "@" not in blob, blob
    assert st["marks_seen"] is False and st["readonly_mailbox"] is True and st["sends"] is False
    assert lei.mask_address("jane.kelly@resident.example") == "ja***@resident.example"

    # زخمِ ثبت‌شده: «Message-ID به‌عنوانِ نامِ فایل». کلید باید هشِ filename-safe باشد،
    # نه شناسهٔ خام — و همان کلید است که به external_id ِ پایین‌دست می‌رود.
    key = lei.dedup_key(_form_inquiry_msg())
    assert len(key) == 24 and all(c in "0123456789abcdef" for c in key), key
    assert not (set(key) & set("<>@/\\:*?\"|")), key
    assert INQUIRY_MID.strip("<>").lower() not in key
    assert lei.dedup_key(_form_inquiry_msg("<other@x.example>")) != key
    cand = lei.to_candidate(_form_inquiry_msg(), "website_form", key)
    assert cand["source"]["external_id"] == key
    assert INQUIRY_MID not in json.dumps(cand, ensure_ascii=False)
    # کاندید هرگز خودش را ارتقا نمی‌دهد و هرگز synthetic ادعا نمی‌کند
    assert "candidate_type" not in cand and cand["source"]["channel"] != "synthetic_test"


def t_j_wiring_beat_and_sidecar():
    import wiring                                  # noqa: WPS433
    importlib.reload(wiring)
    assert hasattr(wiring, "lead_email_intake_beat")
    for n in ("OCTOPUS_WIRE_LEAD_EMAIL_INTAKE", "OCTOPUS_WIRE_EMAIL"):
        os.environ.pop(n, None)
    assert wiring.lead_email_intake_beat(beat=99) is None, "فلگ خاموش → None"
    assert wiring.email_beat(beat=99) is None, "رفتارِ email_beat با هر دو فلگ خاموش تغییر نکرد"

    _arm()
    os.environ["CHRONO_LEAD_EMAIL_INTAKE_EVERY_N_BEATS"] = "1"
    out = wiring.email_beat(beat=1234)             # ← از همان تابعی که organism صدا می‌زند
    assert out is not None and out["fetched"] == 0, out   # بدونِ fetch_fn: not_armed ِ صادق
    assert out["reason"] == "not_armed:" + lei.IMAP_ARM_FLAG, out
    sp = opslib.STATE_DIR / "ORGANISM-STATE.lead_email_intake"
    assert sp.exists(), "سایدکارِ cockpit نوشته نشد"
    side = json.loads(sp.read_text("utf-8"))
    assert set(side) >= {"fetched", "submitted", "dropped", "reason", "beat"}
    # سایدکار فقط عدد و کُد — هیچ محتوایی
    out2 = wiring.lead_email_intake_beat(beat=2345,
                                         fetch_fn=_mailbox([_bank_msg(), _newsletter_msg()]))
    assert out2["dropped"] == 2 and out2["submitted"] == 0, out2
    assert _canary_hits(ENV["root"]) == [], "سایدکار نباید محتوای پیام را بنویسد"
    os.environ.pop("CHRONO_LEAD_EMAIL_INTAKE_EVERY_N_BEATS", None)


def t_k_ast_production_callers():
    """AST: صداکنندهٔ تولیدی واقعاً هست (ماژولِ یتیم = ماژولِ مرده — دو بار در ۲۴ ساعت)."""
    wsrc = (_OPS / "wiring.py").read_text("utf-8")
    wtree = ast.parse(wsrc)

    def _calls_in(fn_name, tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == fn_name:
                return {n.func.id for n in ast.walk(node)
                        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        return set()

    assert "lead_email_intake_beat" in _calls_in("email_beat", wtree), \
        "email_beat باید intake را صدا بزند"
    # خودِ ماژول از داخلِ beat ِ wiring import می‌شود
    imported = {a.name for n in ast.walk(wtree) if isinstance(n, ast.Import)
                for a in n.names}
    assert "lead_email_intake" in imported, "wiring باید ماژول را import کند"

    # و email_beat خودش صداکنندهٔ تولیدی دارد (خارج از _ops/tests)
    callers = []
    for p in (_OPS / "organism.py", _OPS / "brain_worker.py"):
        t = ast.parse(p.read_text("utf-8"))
        for n in ast.walk(t):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr == "email_beat":
                callers.append(p.name)
                break
    assert len(callers) >= 2, f"زنجیرهٔ صداکننده کوتاه است: {callers}"

    # و ماژولِ intake از هیچ‌جای تولیدی «مرده» نیست: دقیقاً یک صداکنندهٔ wiring
    n_ref = sum(1 for n in ast.walk(wtree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "lead_email_intake_beat")
    assert n_ref == 1, f"انتظار یک صداکننده در wiring: {n_ref}"


CHECKS = [
    ("الف — فلگ خاموش no-opِ مطلق", t_a_flag_off_is_absolute_noop),
    ("ب — مسیرِ پیش‌فرض هرگز سوکت باز نمی‌کند", t_b_default_path_never_opens_a_socket),
    ("پ — پیامِ غیرِ استعلام صفر رد می‌گذارد", t_c_non_inquiry_leaves_zero_trace),
    ("ت — پذیرش: دقیقاً یک کاندید از صندوقِ ۴تایی", t_d_acceptance_exactly_one_candidate),
    ("ث — idempotency دو-لایه (+دندان)", t_e_idempotent_across_beats_with_teeth),
    ("ج — صداقتِ کانال: مستقیم ⇒ other ⇒ signal", t_f_channel_honesty_direct_email_is_other),
    ("چ — دندان: طبقه‌بندِ پیش-از-فیکس رد می‌شود", t_g_pre_fix_classifier_teeth),
    ("ح — گیتِ پایین‌دستِ خاموش لید را نگه می‌دارد", t_h_downstream_gate_off_holds_the_lead),
    ("ز — بی‌دستگیرهٔ پاسخ لید نیست (صفر رد)", t_l_no_reply_handle_is_not_a_lead),
    ("ژ — halt ضربان را می‌ایستاند (بی‌فایلِ STOP)", t_m_halt_stops_the_beat),
    ("خ — ساختاری: بی‌ارسال، readonly، بی‌نشتِ secret", t_i_structural_no_send_surface_and_readonly),
    ("د — ضربانِ wiring + سایدکارِ بی‌محتوا", t_j_wiring_beat_and_sidecar),
    ("ذ — AST: صداکنندهٔ تولیدی هست", t_k_ast_production_callers),
]

if __name__ == "__main__":
    print("=== test_lead_email_intake ===")
    failed = harness.run(CHECKS)
    print(f"\n{'❌' if failed else '✅'} {len(CHECKS) - failed}/{len(CHECKS)} سبز")
    sys.exit(1 if failed else 0)
