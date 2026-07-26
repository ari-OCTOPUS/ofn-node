#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""card_render.py — رندرِ واحدِ کارتِ تصمیم، طراحی‌شده برای پروفایلِ شناختیِ اپراتور.

بریفِ مالک ۲۰۲۶-۰۷-۲۵ (به بیانِ خودش، در چت): «محیطِ تلگرام را برای ADHD،
ماریجوانا، IQ 140 بهینه و شخصی‌سازی کن تا بازدهیِ AGI برود بالا.»

⚠️ این ماژول `_ops/state/OWNER-PROFILE*` را **نمی‌خواند و نخواهد خواند** — کدِ خودِ
مخزن آن را جزوِ فایل‌های محرمانه اعلام کرده (cockpit_readmodel.py، export_status.py).
پروفایلِ اینجا فقط همان سه واقعیتِ عملیاتی است که مالک صریحاً گفت، به‌صورتِ قیدِ طراحی.

═══ گلوگاهِ واقعی ═══
کمیاب‌ترین منبعِ کلِ اختاپوس **توجهِ مالک** است، نه CPU و نه توکن. شاهد: جدولِ
`rfc_decision` صفر ردیف دارد — در کلِ تاریخِ سیستم **هیچ رأیی داده نشده**. پس هدفِ
بهینه‌سازی «کارتِ قشنگ‌تر» نیست؛ **تصمیم به‌ازای هر واحد توجه** است.

═══ پروفایل → قیدِ مهندسی (هر کدام در تست assert می‌شود) ═══
ADHD:
  · حافظهٔ کاری گلوگاه است، نه هوش → کارت باید **خودبسنده** باشد؛ ارجاع به پیامِ
    قبلی ممنوع. (`no_backref`)
  · شروعِ کار سخت‌ترین قدم است → **یک** تصمیم در هر کارت، با پیش‌فرضِ توصیه‌شده.
  · بی‌عملی پیامد دارد ولی دیده نمی‌شود → هر کارت **باید** بگوید اگر کاری نکنی چه
    می‌شود. کارتِ بی‌`if_ignored` ساختاراً رد می‌شود. (`stake_required`)
  · کوریِ زمان → «تا یکشنبه» عمل‌پذیر است، «۴۸ ساعت» نه. (`no_duration_deadline`)
ماریجوانا:
  · یادآوریِ کوتاه‌مدت پایین‌تر → سقفِ سختِ طول، مهم‌ترین چیز در خطِ اول.
  · خستگیِ تصمیم بالاتر → «نه» باید **به‌همان‌اندازه ارزان** باشد که «آره».
IQ 140:
  · محتوا **ساده نمی‌شود** — عدد و حقیقتِ کاملِ فنی می‌ماند. تحقیر هزینه دارد.
  · تناقض را فوری می‌بیند → دقت مهم‌تر می‌شود، نه کمتر.
  · نتیجه: **چگالیِ بالای اطلاعات با بارِ صفرِ حافظهٔ کاری.** این دو با هم سازگارند.
  · و ژارگون بی‌ترجمه ممنوع: «merge پشتِ flag» نمی‌گوید *واقعاً* چه اتفاقی می‌افتد.

pure است: صفر I/O، صفر شبکه، صفر state. فقط dict برمی‌گرداند.
"""
from __future__ import annotations

import html
import re

# ── قیدهای عددیِ طراحی (تست‌ها مستقیماً این‌ها را می‌خوانند) ──────────────────
MAX_TEXT_CHARS = 700        # تلگرام ۴۰۹۶ می‌پذیرد؛ توجه نه
MAX_HEADLINE = 64
MAX_EVIDENCE_LINES = 3
MAX_EVIDENCE_LINE = 110
MAX_INFO_ROWS = 6           # گزارشِ بلند = گزارشِ خوانده‌نشده

# ژارگونی که بی‌ترجمه در متنِ انسانی ممنوع است. کلید = واژه، مقدار = چه چیزی باید
# کنارش باشد تا مجاز شود (یعنی متن باید *بگوید* چه اتفاقی می‌افتد، نه اسمِ مکانیزم).
JARGON_NEEDS_GLOSS = {
    "merge": "چه چیزی عوض می‌شود",
    "flag": "روشن/خاموش",
    "rfc": "پیشنهاد",
    "dedupe": "تکراری",
    "hmac": "امضا",
    "rollback": "برگشت",
    "sandbox": "آزمایشی",
}

# دیرکردِ مدت‌محور: ADHD این‌ها را به عمل تبدیل نمی‌کند.
_DURATION_PAT = re.compile(
    r"(\d+\s*(ساعت|دقیقه|روز|hour|hours|min|mins|minute|minutes|day|days|h|d)\b)"
    r"|(\btomorrow\b)|(\bفردا\b)", re.IGNORECASE)

# شناسه‌های ماشینی که در متنِ انسانی فقط توجه می‌خورند (در callback_data آزادند).
_MACHINE_ID_PAT = re.compile(r"\b(?:[0-9a-f]{8,}|RFC-[0-9a-f]{6,}|[0-9a-f]{4}(?:-[0-9a-f]{4}){2,})\b",
                             re.IGNORECASE)


class CardDesignError(ValueError):
    """کارت قیدِ شناختی را می‌شکند — ساختاراً ساخته نمی‌شود، نه اینکه زشت باشد."""


def _has_gloss(text_low: str, word: str, gloss: str) -> bool:
    return gloss.lower() in text_low


def _check(text: str, *, allow_jargon: bool) -> None:
    """قیدها را روی متنِ نهایی اعمال می‌کند. شکست = استثنا، نه هشدارِ بی‌اثر."""
    plain = re.sub(r"<[^>]+>", "", text)
    if len(plain) > MAX_TEXT_CHARS:
        raise CardDesignError(
            f"کارت {len(plain)} کاراکتر است (سقف {MAX_TEXT_CHARS}) — "
            "بارِ حافظهٔ کاری. مهم‌ترین چیز را نگه دار، بقیه را بیرون بگذار.")
    if _MACHINE_ID_PAT.search(plain):
        raise CardDesignError(
            "شناسهٔ ماشینی در متنِ انسانی — توجه می‌خورد و معنایی ندارد. "
            "شناسه فقط در callback_data.")
    if not allow_jargon:
        low = plain.lower()
        for word, gloss in JARGON_NEEDS_GLOSS.items():
            if re.search(rf"\b{re.escape(word)}\b", low) and not _has_gloss(low, word, gloss):
                raise CardDesignError(
                    f"ژارگونِ «{word}» بی‌ترجمه — متن باید بگوید *واقعاً* چه اتفاقی "
                    f"می‌افتد (مثلاً «{gloss}»)، نه اسمِ مکانیزم را.")


def _check_deadline(deadline_human: str) -> None:
    if _DURATION_PAT.search(deadline_human or ""):
        raise CardDesignError(
            f"دیرکردِ مدت‌محور «{deadline_human}» — کوریِ زمان آن را به عمل تبدیل "
            "نمی‌کند. روزِ هفته یا تاریخِ مشخص بده.")


def render_decision_card(*, headline: str, what_happens: str, if_ignored: str,
                         evidence: "list[str] | None" = None,
                         deadline_human: str = "", recommendation: "str | None" = None,
                         why_recommend: str = "", reversible: "bool | None" = None,
                         yes_label: str = "آره", no_label: str = "نه",
                         callback_yes: str = "", callback_no: str = "",
                         callback_later: str = "", later_when: str = "",
                         allow_jargon: bool = False) -> dict:
    """یک تصمیم، خودبسنده، با پیامدِ بی‌عملی. خروجی: {text, reply_markup, plain_len}.

    `recommendation` ∈ {'yes','no',None}. توصیه یعنی تصمیم یک ضربه می‌شود؛
    ولی «نه» همان‌قدر ارزان می‌ماند (دکمه‌های متقارن) — وگرنه توصیه به فشار تبدیل می‌شود."""
    if not headline or not headline.strip():
        raise CardDesignError("کارتِ بی‌سرخط: خطِ اول باید بگوید این چیست.")
    if len(headline) > MAX_HEADLINE:
        raise CardDesignError(f"سرخط {len(headline)} کاراکتر (سقف {MAX_HEADLINE}).")
    if not what_happens or not what_happens.strip():
        raise CardDesignError("کارت نمی‌گوید اگر «آره» بزنی *واقعاً* چه می‌شود.")
    if not if_ignored or not if_ignored.strip():
        raise CardDesignError(
            "کارتِ بی‌پیامدِ بی‌عملی. ADHD بی‌عملی را انتخاب نمی‌بیند — پس هر کارت "
            "باید بگوید اگر هیچ کاری نکنی چه می‌شود. این قید عمدی است.")
    if deadline_human:
        _check_deadline(deadline_human)
    if later_when:
        _check_deadline(later_when)
    if recommendation not in (None, "yes", "no"):
        raise CardDesignError(f"توصیهٔ نامعتبر: {recommendation!r}")
    if recommendation and not why_recommend.strip():
        raise CardDesignError("توصیهٔ بی‌دلیل = فشار. یک بند بگو چرا.")

    ev = [e.strip() for e in (evidence or []) if e and e.strip()]
    if len(ev) > MAX_EVIDENCE_LINES:
        raise CardDesignError(
            f"{len(ev)} خط شاهد (سقف {MAX_EVIDENCE_LINES}) — چگالی خوب است، "
            "دیوارِ متن نه.")
    for e in ev:
        if len(e) > MAX_EVIDENCE_LINE:
            raise CardDesignError(f"خطِ شاهد {len(e)} کاراکتر (سقف {MAX_EVIDENCE_LINE}).")

    esc = html.escape
    parts = [f"<b>{esc(headline.strip())}</b>", ""]
    parts.append(f"▸ می‌شود: {esc(what_happens.strip())}")
    parts.append(f"▸ نکنی: {esc(if_ignored.strip())}")
    if reversible is not None:
        parts.append("▸ برگشت‌پذیر: " + ("بله" if reversible else "<b>نه</b>"))
    if deadline_human:
        parts.append(f"▸ مهلت: {esc(deadline_human.strip())}")
    if ev:
        parts.append("")
        parts.extend(f"· {esc(e)}" for e in ev)
    if recommendation:
        parts.append("")
        arrow = yes_label if recommendation == "yes" else no_label
        parts.append(f"<i>پیشنهادِ من: {esc(arrow)} — {esc(why_recommend.strip())}</i>")

    text = "\n".join(parts)
    _check(text, allow_jargon=allow_jargon)

    # دکمه‌های متقارن: «نه» هرگز گران‌تر از «آره» نیست.
    if abs(len(yes_label) - len(no_label)) > 6:
        raise CardDesignError(
            f"دکمه‌های نامتقارن ({yes_label!r} / {no_label!r}) — خستگیِ تصمیم باعث "
            "می‌شود گزینهٔ ارزان‌تر برنده شود. هر دو را کوتاه نگه دار.")
    row = []
    if callback_yes:
        row.append({"text": f"{yes_label} ✅", "callback_data": callback_yes})
    if callback_no:
        row.append({"text": f"{no_label} ❌", "callback_data": callback_no})
    kb = [row] if row else []
    if callback_later:
        if not later_when:
            raise CardDesignError(
                "«بعداً» بی‌تاریخِ پرسشِ دوباره = صفِ نامرئی. بگو کِی دوباره می‌پرسم.")
        kb.append([{"text": f"بعداً ({later_when}) ⏳", "callback_data": callback_later}])
    return {"text": text, "reply_markup": {"inline_keyboard": kb} if kb else None,
            "plain_len": len(re.sub(r"<[^>]+>", "", text))}


def render_batch(*, headline: str, items: "list[dict]", if_ignored: str,
                 deadline_human: str = "", allow_jargon: bool = False) -> dict:
    """چند تصمیمِ هم‌جنسِ کم‌ریسک در **یک** کارت — هر کارت یک تعویضِ زمینه است،
    و تعویضِ زمینه گران‌ترین چیز برای ADHD است. هر item: {label, callback_yes, callback_no}."""
    if not items:
        raise CardDesignError("دستهٔ خالی.")
    if len(items) > 5:
        raise CardDesignError(f"{len(items)} تصمیم در یک کارت — بیش از ۵ به دیوار تبدیل می‌شود.")
    esc = html.escape
    parts = [f"<b>{esc(headline.strip())}</b>", ""]
    for i, it in enumerate(items, 1):
        lbl = str(it.get("label") or "").strip()
        if not lbl:
            raise CardDesignError(f"آیتمِ {i} برچسب ندارد.")
        parts.append(f"{i}. {esc(lbl)}")
    parts += ["", f"▸ نکنی: {esc(if_ignored.strip())}"]
    if deadline_human:
        _check_deadline(deadline_human)
        parts.append(f"▸ مهلت: {esc(deadline_human.strip())}")
    text = "\n".join(parts)
    _check(text, allow_jargon=allow_jargon)
    kb = []
    for i, it in enumerate(items, 1):
        r = []
        if it.get("callback_yes"):
            r.append({"text": f"{i} آره ✅", "callback_data": it["callback_yes"]})
        if it.get("callback_no"):
            r.append({"text": f"{i} نه ❌", "callback_data": it["callback_no"]})
        if r:
            kb.append(r)
    return {"text": text, "reply_markup": {"inline_keyboard": kb} if kb else None,
            "plain_len": len(re.sub(r"<[^>]+>", "", text))}


def render_info(*, headline: str, lead: str, rows: "list[str] | None" = None,
                next_step: str = "", allow_jargon: bool = False) -> dict:
    """کارتِ اطلاعاتیِ خلوت: بی‌تصمیم، بی‌دکمه — ولی زیرِ همان قیدهای شناختی.

    چرا جدا از `render_decision_card`: آن‌جا `if_ignored` **اجباری** است چون تصمیم
    است و ADHD بی‌عملی را انتخاب نمی‌بیند. یک گزارشِ read-only تصمیم نیست، و اجبارِ
    «اگر کاری نکنی» به آن، پیامدِ ساختگی می‌سازد — و کارتِ دروغ از کارتِ شلوغ بدتر است.
    پس آن قید این‌جا برداشته می‌شود و به‌جایش `lead` اجباری می‌شود.

    قیدهایی که این‌جا هم می‌مانند (هرکدام در `test_card_render_profile` assert می‌شود):
      · سقفِ سختِ طول — دیوارِ متن حافظهٔ کاری را می‌خورد. (`MAX_TEXT_CHARS`)
      · `lead` اجباری: مهم‌ترین حقیقت در خطِ اول، نه تهِ گزارش. (`lead_required`)
      · شناسهٔ ماشینی و ژارگونِ بی‌ترجمه ممنوع (همان `_check`).
      · سقفِ ردیف `MAX_INFO_ROWS`.

    محتوا **ساده نمی‌شود**: عدد و حقیقتِ فنی کامل می‌ماند. چیزی که حذف می‌شود
    تکرار و نویز است، نه اطلاعات.
    """
    if not headline or not headline.strip():
        raise CardDesignError("کارتِ بی‌سرخط: خطِ اول باید بگوید این چیست.")
    if len(headline) > MAX_HEADLINE:
        raise CardDesignError(f"سرخط {len(headline)} کاراکتر (سقف {MAX_HEADLINE}).")
    if not lead or not lead.strip():
        raise CardDesignError(
            "کارتِ بی‌سرنخ: مهم‌ترین حقیقت باید خطِ اول باشد. گزارشی که نتیجه‌اش "
            "ته متن است، خوانده نمی‌شود. این قید عمدی است.")

    rws = [r.strip() for r in (rows or []) if r and r.strip()]
    if len(rws) > MAX_INFO_ROWS:
        raise CardDesignError(
            f"{len(rws)} ردیف (سقف {MAX_INFO_ROWS}) — چگالی خوب است، دیوارِ متن نه.")
    for r in rws:
        if len(r) > MAX_EVIDENCE_LINE:
            raise CardDesignError(f"ردیفِ {len(r)} کاراکتری (سقف {MAX_EVIDENCE_LINE}).")

    esc = html.escape
    parts = [f"<b>{esc(headline.strip())}</b>", "", f"▸ {esc(lead.strip())}"]
    if rws:
        parts.append("")
        parts.extend(f"· {esc(r)}" for r in rws)
    if next_step.strip():
        parts += ["", f"<i>{esc(next_step.strip())}</i>"]

    text = "\n".join(parts)
    _check(text, allow_jargon=allow_jargon)
    return {"text": text, "reply_markup": None,
            "plain_len": len(re.sub(r"<[^>]+>", "", text))}


# ── نمونه‌ها: مالک بتواند **امروز** ببیند، بی‌راز و بی‌ارسال ──────────────────
def samples() -> "list[dict]":
    """کارت‌های واقعیِ رندرشده از دادهٔ واقعیِ امروز — برای پیش‌نمایشِ بی‌ارسال."""
    out = []
    out.append(("پیشنهادِ تنظیمِ آهنگِ کاری", render_decision_card(
        headline="آهنگِ خودتنظیمی: مقدارِ صریح ندارد",
        what_happens="عددِ آهنگ روی ۷۸۰ ضربان تنظیم می‌شود (میانهٔ بازهٔ امنِ ۱۲۰ تا ۱۴۴۰)",
        if_ignored="همین‌طور بی‌مقدار می‌ماند و خودتنظیمیِ نرم خاموش است",
        evidence=["الان: هیچ مقداری ست نشده · بازهٔ امن ۱۲۰–۱۴۴۰",
                  "برگشت: یک خط از فایلِ تنظیماتِ خودکار پاک می‌شود"],
        deadline_human="تا یکشنبه", recommendation="yes",
        why_recommend="کم‌ریسک و یک‌خطی برمی‌گردد", reversible=True,
        callback_yes="rfc:merge:aa01e8ff:tok", callback_no="rfc:deny:aa01e8ff:tok",
        callback_later="rfc:later:aa01e8ff:tok", later_when="شنبه")))
    out.append(("دستهٔ تصمیمِ کم‌ریسک", render_batch(
        headline="۳ تنظیمِ کم‌ریسک، یک‌جا",
        items=[{"label": "سقفِ زمانِ مغزِ پولی: ۲۰ → ۴۵ ثانیه",
                "callback_yes": "k:y:1", "callback_no": "k:n:1"},
               {"label": "اندازهٔ درخواستِ گاورنر: ۱۲۰۰ → ۶۰۰ توکن",
                "callback_yes": "k:y:2", "callback_no": "k:n:2"},
               {"label": "ددلاینِ گذشته دیگر فوریت نسازد",
                "callback_yes": "k:y:3", "callback_no": "k:n:3"}],
        if_ignored="هر سه به حالِ فعلی می‌مانند؛ مغزِ پولی هر ۲۰ دقیقه یک‌بار می‌میرد",
        deadline_human="تا دوشنبه")))
    return out


if __name__ == "__main__":  # pragma: no cover — پیش‌نمایشِ دستی، صفر ارسال
    for title, card in samples():
        print("═" * 58)
        print(f"◆ {title}   ({card['plain_len']} کاراکتر)")
        print("═" * 58)
        print(re.sub(r"<[^>]+>", "", card["text"]))
        kb = (card.get("reply_markup") or {}).get("inline_keyboard") or []
        for row in kb:
            print("   [" + "]  [".join(b["text"] for b in row) + "]")
        print()
