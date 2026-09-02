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


# ─── فالوآپ (Lane E5، رأی Q4) ────────────────────────────────────────────────

_FU_SUBJECTS = (
    "Following up — painting availability",
    "Re: painting works — still keen",
    "Quick follow-up on my last note",
    "Painting quote — following up once more",
)

_FU_1 = (
    "Just floating my earlier note to the top of your inbox in case it got "
    "buried. Still happy to put a number on any painting works {short} has "
    "coming up — a rough scope is enough to start.",

    "Following up on my note from last week. If there is a repaint or "
    "maintenance package in the pipeline for {short}, I would be glad to "
    "price it. One line with the scope gets you a figure.",

    "Bumping this once. {short} has real painting cycles in its programme "
    "(we both know the numbers), and I would like to be on the list when "
    "the next one goes out.",
)

_FU_2 = (
    "Last note from me, promise. If painting works are on {short}'s horizon "
    "this year, keep my details on file — a scope of any size gets a "
    "straight price back.",

    "I will leave it here so I am not cluttering your inbox. If a painting "
    "tender or repaint comes up at {short}, my details are below — happy to "
    "quote at any stage.",
)

_FU_SIGN = "Kind regards,\n{sign}\n{city}"


def write_followup(lead_id: str, buyer: str, nth: int = 1,
                   total_awarded_aud=None) -> dict:
    """یادآوریِ ۱ یا ۲ — کوتاه از معرفی، قطعی از seed. بدونِ دادهٔ OCP هم
    می‌شود (برخلافِ intro) ولی اگر عدد بود طبیعی‌تر است."""
    import hashlib
    digest = hashlib.sha256(("fu:" + str(lead_id) + ":" + str(nth)).encode()).digest()
    short = _short_name(buyer)
    pool = _FU_1 if int(nth) == 1 else _FU_2
    si, oi = digest[0] % len(_FU_SUBJECTS), digest[1] % len(pool)
    amount = _amount_text(total_awarded_aud)
    body_para = pool[oi].format(short=short, amount=amount or "recent work")
    subject = _FU_SUBJECTS[si]
    # سوژهٔ «Re:» را فقط وقتی نگذار که پیام اول همان ترد بود — اینجا ایمیلِ
    # نو است، پس Re: حذف می‌شود تا صادقانه باشد (نه جعلِ ترد).
    subject = subject.replace("Re: ", "").strip()
    body = body_para + "\n\n" + _FU_SIGN.format(sign=SIGN_NAME, city=SIGN_CITY)
    return {"subject": subject, "body": body}


def check_followup(draft: dict) -> list[str]:
    """گیت سبکِ فالوآپ — مثل check ولی بدونِ الزامِ عدد (R1 فقط برای intro)."""
    errs = []
    text = ((draft.get("subject") or "") + "\n" +
            (draft.get("body") or "")).lower()
    for bad in FORBIDDEN:
        if bad in text:
            errs.append(f"forbidden-phrase:{bad}")
    words = len((draft.get("body") or "").split())
    if words > 90:
        errs.append(f"body-too-long:{words}")
    return errs
