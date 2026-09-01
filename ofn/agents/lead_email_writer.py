"""lead_email_writer — مهارتِ نویسندگیِ ایمیلِ OCTOPUS (رأیِ مالک ۲۰۲۶-۰۸-۳۱).

هدف: ایمیلی که شبیه آدم باشد، نه шабلورِ هوش مصنوعی. قواعدِ سفتِ این ماژول:

  R1. هر ایمیل باید حداقل یک عددِ واقعی از دادهٔ NSW OCP داشته باشد
      (مجموعِ قراردادهای رنگ‌کاریِ خودِ گیرنده). عددِ ساختگی ممنوع.
  R2. ممنوعاتِ مطلق (کلیشهٔ ربات): "I hope this email finds you well" و
      هم‌خانواده‌ها — فهرستِ _FORBIDDEN. شکستنِ آن‌ها = AssertionError در تست.
  R3. بدنه زیرِ ~۱۲۰ کلمه. سفارش‌دهندهٔ دولتی اسکیم می‌کند؛ کوتاهِ محترمانه.
  R4. فقط یک درخواست: «کارِ رنگی در راه است؟» — نه چند درخواستِ موازی.
  R5. تنوعِ قطعی (deterministic) از seed=lead_id — هر لید متنِ خودش را
      می‌گیرد؛ دو لید هرگز متنِ یکسان نمی‌گیرند (نه قالبِ کپی‌شده).
  R6. فقط ادعاهای راست: ABN، بیمه، سیدنی — همان هویتِ کمپینِ PAINT-L5-001.
      هیچ گواهی/سابقهٔ ساختگی.

خروجیِ write_intro همیشه {"subject","body"} است و برای lead_id ثابت
(همان lead_id بعد، همان متن — idempotent برای بازارسالِ تکراری).
"""
from __future__ import annotations

import hashlib

# هویتِ فرستنده — از کمپینِ موجود؛ تک‌منبعِ راستگویی.
SIGN_NAME = "Master Painting"
SIGN_CITY = "Sydney NSW"

# R2 — هرگز در بدنه/سوژه ظاهر نشوند (lowercase مقایسه می‌شود).
FORBIDDEN = (
    "i hope this email finds you well",
    "i hope you are well",
    "i am reaching out",
    "i am writing to introduce",
    "we are a leading",
    "solutions provider",
    "leverage",
    "delve",
    "at your earliest convenience",
    "king regards",  # تایپوِ رایج — گاردِ املایی
)

# R5 — استخرهای تنوع. انتخاب با seed نه با شانس؛ تا خروجی برای lead_id ثابت بماند.
_SUBJECTS = (
    "Painting contractor for upcoming {short} work",
    "{short} painting packages — availability",
    "Local painter, pricing for {short} projects",
    "Availability for {short} repaint works",
    "Painting quote — {short} sites",
)

_OPENERS = (
    # هر opener به عددِ OCP گیرنده وصل است (R1) — نه سلامِ کلی.
    "Hello, I could not help noticing {short} ran about {amount} of painting "
    "work through NSW contracts recently. That is steady programme, and "
    "programmes need reliable painters.",

    "Hello, the NSW contract data shows around {amount} in painting jobs "
    "through {short} over the past year. I am a Sydney painting contractor "
    "and would like to be on your list of people to call.",

    "Hi there, quick note from a local painter. Public records put "
    "{short}'s recent painting spend near {amount}, so I imagine repaint "
    "cycles keep coming around.",

    "Hello, I work across Sydney on commercial and government repaints. "
    "Saw {short} has committed roughly {amount} to painting contracts "
    "lately — figures like that usually mean more work is coming.",

    "Hi, short and practical: {short} spends real money on painting "
    "(about {amount} on recent NSW contracts) and I would like to quote "
    "the next round.",
)

_MIDDLES = (
    "My crew does internal and external repaints, surface prep and "
    "protective coatings, and scheduled maintenance painting. Fully "
    "insured, ABN on file, and we price from scope quickly — usually "
    "within a few days of getting the details.",

    "What we do day to day: repaint programmes, protective coatings, "
    "prep work done properly. Insured, ABN registered, Sydney based. "
    "Send a scope and you will have a price back fast.",

    "We handle interior and exterior painting, prep and coatings, and "
    "standing maintenance repaints for sites that need them on a cycle. "
    "ABN and insurance documents ready on request. Quotes go out within "
    "days, not weeks.",
)

_CLOSERS = (
    "If there is a painting package on your horizon, I am happy to put a "
    "number on it. What would be the right way to get on the tender or "
    "quote list?",

    "Is there anything in the pipeline I could quote? Even a rough scope "
    "is enough for a first price.",

    "If upcoming works need a painter, I would like to be considered. "
    "Happy to send insurance certificates or price a trial scope first.",
)

_SHORT = (
    ("department", "Education"),
    ("transport", "Transport"),
    ("environment", "DPIE"),
    ("health", "HealthShare"),
    ("education", "Education"),
)


def _short_name(buyer: str) -> str:
    b = (buyer or "").lower()
    for key, short in _SHORT:
        if key in b:
            return short
    return "your organisation"


def _amount_text(total_aud) -> str:
    try:
        n = float(total_aud)
    except (TypeError, ValueError):
        return ""  # R1: بدون دادهٔ واقعی، عدد نمی‌سازیم.
    if n >= 1_000_000:
        return f"${n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"${round(n / 1_000)}K"
    return f"${n:.0f}"


def write_intro(lead_id: str, buyer: str, total_awarded_aud=None,
                contract_count=None) -> dict:
    """متنِ معرفی — قطعی از seed=lead_id. خروجی {"subject","body"}.

    اگر total_awarded_aud واقعی نباشد، ValueError می‌دهد (R1: ایمیلِ بی‌عددِ
    واقعی از این مهارت بیرون نمی‌رود — caller یا داده می‌آورد یا نمی‌فرستد).
    """
    amount = _amount_text(total_awarded_aud)
    if not amount:
        raise ValueError("no-real-ocp-total-for:" + str(lead_id))

    digest = hashlib.sha256(str(lead_id).encode()).digest()
    s0, s1, s2, s3 = digest[0] % len(_SUBJECTS), digest[1] % len(_OPENERS), \
        digest[2] % len(_MIDDLES), digest[3] % len(_CLOSERS)

    short = _short_name(buyer)
    subject = _SUBJECTS[s0].format(short=short)
    body = "\n\n".join((
        _OPENERS[s1].format(short=short, amount=amount),
        _MIDDLES[s2],
        _CLOSERS[s3],
        "Kind regards,\n"
        f"{SIGN_NAME}\n{SIGN_CITY}",
    ))
    return {"subject": subject, "body": body}


def check(draft: dict) -> list[str]:
    """گیتِ سبک — فهرستِ خطاها؛ خالی یعنی پاس. صدازندهٔ production باید
    خروجیِ خالی بگیرد وگرنه ارسال نکند."""
    errs = []
    text = ((draft.get("subject") or "") + "\n" +
            (draft.get("body") or "")).lower()
    for bad in FORBIDDEN:
        if bad in text:
            errs.append(f"forbidden-phrase:{bad}")
    words = len((draft.get("body") or "").split())
    if words > 130:
        errs.append(f"body-too-long:{words}")
    if "$" not in text:
        errs.append("no-concrete-figure")  # R1 به‌صورتِ دفاعِ دوم
    return errs
