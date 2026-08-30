#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_card_render_profile.py — قیدهای شناختیِ کارتِ تصمیم، به‌عنوان assertion.

بریفِ مالک ۲۰۲۶-۰۷-۲۵: تلگرام برای ADHD + ماریجوانا + IQ 140 بهینه شود.
این تست آن بریف را از «توصیهٔ در سند» به «قیدِ اجراشدنی» تبدیل می‌کند — تا کارتی که
قید را می‌شکند ساختاراً ساخته نشود، نه اینکه فقط زشت باشد.

گلوگاهی که این طراحی هدف گرفته: `rfc_decision` صفر ردیف دارد. در کلِ تاریخِ سیستم
هیچ رأیی داده نشده. پس معیار «تصمیم به‌ازای واحدِ توجه» است، نه زیبایی.

⚠️ این تست هرگز `OWNER-PROFILE*` را نمی‌خواند (فایلِ محرمانهٔ مالک، طبقه‌بندی‌شده در
cockpit_readmodel.py و export_status.py) — و یک assertion هم دارد که مطمئن شود
ماژولِ رندر هم آن را نمی‌خواند.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent / "tg"), str(_HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import card_render as cr  # noqa: E402

FAILURES: list[str] = []
CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILURES.append(msg)


def rejects(msg, **kw):
    """کارتی که باید ساختاراً رد شود."""
    base = dict(headline="س", what_happens="کاری می‌شود",
                if_ignored="چیزی نمی‌شود", callback_yes="y", callback_no="n")
    base.update(kw)
    global CHECKS
    CHECKS += 1
    try:
        cr.render_decision_card(**base)
        FAILURES.append(f"{msg} — پذیرفته شد در حالی که باید رد شود")
    except cr.CardDesignError:
        pass
    except Exception as e:  # noqa: BLE001
        FAILURES.append(f"{msg} — استثنای غلط {type(e).__name__}: {e}")


def accepts(msg, **kw):
    base = dict(headline="س", what_happens="کاری می‌شود",
                if_ignored="چیزی نمی‌شود", callback_yes="y", callback_no="n")
    base.update(kw)
    global CHECKS
    CHECKS += 1
    try:
        return cr.render_decision_card(**base)
    except Exception as e:  # noqa: BLE001
        FAILURES.append(f"{msg} — رد شد: {type(e).__name__}: {e}")
        return None


# ── T1 · ADHD: پیامدِ بی‌عملی اجباری است ────────────────────────────────────
def t1_stake_required():
    for bad in ("", "   ", None):
        rejects(f"T1 if_ignored={bad!r}", if_ignored=bad)
    c = accepts("T1 با پیامد")
    ck(c and "نکنی:" in c["text"], "T1: خطِ «نکنی» در متن نیست")
    # و «چه می‌شود» هم اجباری است
    for bad in ("", "  ", None):
        rejects(f"T1 what_happens={bad!r}", what_happens=bad)
    # سرخط اجباری
    for bad in ("", "   ", None):
        rejects(f"T1 headline={bad!r}", headline=bad)


# ── T2 · کوریِ زمان: مهلتِ مدت‌محور رد می‌شود ───────────────────────────────
def t2_no_duration_deadline():
    for bad in ("۴۸ ساعت", "48 hours", "2 روز", "3 days", "30 min", "فردا", "tomorrow", "6h"):
        rejects(f"T2 مهلتِ {bad!r}", deadline_human=bad)
    for good in ("تا یکشنبه", "تا شنبه شب", "۲۸ جولای", "پایانِ هفته", "دوشنبه"):
        c = accepts(f"T2 مهلتِ {good!r}", deadline_human=good)
        ck(c and good in c["text"], f"T2: مهلتِ {good!r} در متن نیامد")
    # «بعداً» بی‌تاریخِ پرسشِ دوباره = صفِ نامرئی
    rejects("T2 بعداً بی‌تاریخ", callback_later="l", later_when="")
    rejects("T2 بعداً با مدت", callback_later="l", later_when="۲ روز")
    c = accepts("T2 بعداً با روز", callback_later="l", later_when="شنبه")
    kb = (c or {}).get("reply_markup", {}).get("inline_keyboard") or []
    ck(any("شنبه" in b["text"] for row in kb for b in row),
       "T2: تاریخِ پرسشِ دوباره روی دکمه نیست")


# ── T3 · بارِ حافظهٔ کاری: سقفِ طول و شناسهٔ ماشینی ─────────────────────────
def t3_working_memory_load():
    ck(cr.MAX_TEXT_CHARS <= 800, f"T3: سقفِ طول ({cr.MAX_TEXT_CHARS}) خیلی بالاست")
    rejects("T3 متنِ بلند", what_happens="ب" * (cr.MAX_TEXT_CHARS + 50))
    rejects("T3 سرخطِ بلند", headline="س" * (cr.MAX_HEADLINE + 1))
    rejects("T3 شاهدِ زیاد", evidence=["a", "b", "c", "d"])
    rejects("T3 خطِ شاهدِ بلند", evidence=["x" * (cr.MAX_EVIDENCE_LINE + 1)])
    # شناسهٔ ماشینی در متنِ انسانی ممنوع (در callback آزاد)
    for bad in ("RFC-aa01e8ff", "520858a2d257e2a8", "76d7df19832c1071"):
        rejects(f"T3 شناسهٔ {bad!r}", what_happens=f"پیشنهادِ {bad} اعمال می‌شود")
    c = accepts("T3 شناسه فقط در callback", callback_yes="rfc:merge:aa01e8ff:76d7df19")
    ck(c, "T3: شناسه در callback_data باید مجاز باشد")
    plain = re.sub(r"<[^>]+>", "", (c or {}).get("text", ""))
    ck("aa01e8ff" not in plain, "T3: شناسه به متنِ انسانی نشت کرد")


# ── T4 · IQ 140: ژارگون بی‌ترجمه ممنوع، ولی محتوا ساده نمی‌شود ─────────────
def t4_no_unglossed_jargon():
    for bad in ("merge پشتِ flag انجام می‌شود", "RFC ثبت می‌شود",
                "dedupe اجرا می‌شود", "rollback دارد"):
        rejects(f"T4 ژارگونِ {bad!r}", what_happens=bad)
    # با ترجمه مجاز می‌شود — یعنی متن بگوید *واقعاً* چه می‌شود
    accepts("T4 merge با ترجمه",
            what_happens="چه چیزی عوض می‌شود: عددِ آهنگ از خالی به ۷۸۰ می‌رود")
    accepts("T4 flag با ترجمه", what_happens="این قابلیت روشن/خاموش می‌شود")
    accepts("T4 rollback با ترجمه", what_happens="برگشت: یک خط پاک می‌شود")
    # allow_jargon=True فقط برای مصرف‌کنندهٔ ماشینی
    accepts("T4 با allow_jargon", what_happens="merge می‌شود", allow_jargon=True)
    # و عدد/چگالی هرگز جریمه نمی‌شود — ساده‌سازیِ محتوا هدف نیست
    c = accepts("T4 چگالِ عددی",
                evidence=["۱۵ از ۳۰ فراخوان روی سقفِ سوکت مرد؛ صفر خطای فروشنده",
                          "نرخ ≈ ۴۰ توکن/ثانیه + ۳.۸ ثانیه سرِ ثابت"])
    ck(c and "۴۰ توکن" in c["text"], "T4: شاهدِ عددی حذف شد")


# ── T5 · خستگیِ تصمیم: «نه» به‌همان‌اندازه ارزان ────────────────────────────
def t5_symmetric_cost():
    rejects("T5 دکمهٔ نامتقارن", yes_label="merge پشتِ flag", no_label="رد")
    c = accepts("T5 متقارن", yes_label="آره", no_label="نه")
    kb = (c or {}).get("reply_markup", {}).get("inline_keyboard") or []
    ck(len(kb) >= 1 and len(kb[0]) == 2, "T5: دو دکمهٔ اصلی در یک ردیف نیست")
    if kb and len(kb[0]) == 2:
        a, b = (len(x["text"]) for x in kb[0])
        ck(abs(a - b) <= 8, f"T5: طولِ دکمه‌ها نامتقارن ({a} vs {b})")
    # توصیه اجازه دارد، ولی بی‌دلیل = فشار
    rejects("T5 توصیهٔ بی‌دلیل", recommendation="yes", why_recommend="")
    rejects("T5 توصیهٔ نامعتبر", recommendation="maybe", why_recommend="چون")
    c = accepts("T5 توصیهٔ با دلیل", recommendation="no", why_recommend="ریسکش سنجیده نشده")
    ck(c and "پیشنهادِ من" in c["text"], "T5: توصیه در متن نیست")
    # و توصیه دکمهٔ مخالف را حذف نمی‌کند
    kb2 = (c or {}).get("reply_markup", {}).get("inline_keyboard") or []
    ck(kb2 and len(kb2[0]) == 2, "T5: توصیه گزینهٔ دیگر را حذف کرد")


# ── T6 · خودبسندگی: ارجاع به پیامِ قبلی معنا ندارد ─────────────────────────
def t6_self_contained():
    c = accepts("T6 پایه", reversible=False)
    ck(c and "برگشت‌پذیر" in c["text"], "T6: برگشت‌پذیری اعلام نشد")
    ck(c and "<b>نه</b>" in c["text"], "T6: غیرِبرگشت‌پذیر باید برجسته باشد")
    # هر کارت مستقلاً کامل است: سرخط + می‌شود + نکنی، بی‌هیچ ارجاع
    plain = re.sub(r"<[^>]+>", "", (c or {}).get("text", ""))
    for lead in ("می‌شود:", "نکنی:"):
        ck(lead in plain, f"T6: «{lead}» در کارت نیست")


# ── T7 · دسته: تعویضِ زمینه گران‌ترین چیز است ──────────────────────────────
def t7_batch():
    items = [{"label": f"تنظیمِ {i}", "callback_yes": f"y{i}", "callback_no": f"n{i}"}
             for i in range(1, 4)]
    b = cr.render_batch(headline="۳ تنظیمِ کم‌ریسک", items=items,
                        if_ignored="همه به حالِ فعلی می‌مانند", deadline_human="تا دوشنبه")
    ck(b["plain_len"] <= cr.MAX_TEXT_CHARS, "T7: دسته از سقفِ طول رد شد")
    ck(len(b["reply_markup"]["inline_keyboard"]) == 3, "T7: ردیفِ دکمه به‌ازای هر آیتم نیست")
    ck("نکنی:" in b["text"], "T7: دسته پیامدِ بی‌عملی ندارد")
    for bad, why in (([], "دستهٔ خالی"),
                     ([{"label": ""}], "آیتمِ بی‌برچسب"),
                     ([{"label": f"x{i}"} for i in range(6)], "بیش از ۵ آیتم")):
        CHECKS_before = None
        try:
            cr.render_batch(headline="h", items=bad, if_ignored="i")
            FAILURES.append(f"T7: {why} پذیرفته شد")
        except cr.CardDesignError:
            pass
        globals()["CHECKS"] = CHECKS + 1
    # مهلتِ مدت‌محور در دسته هم رد می‌شود
    try:
        cr.render_batch(headline="h", items=items, if_ignored="i", deadline_human="۲ روز")
        FAILURES.append("T7: مهلتِ مدت‌محور در دسته پذیرفته شد")
    except cr.CardDesignError:
        pass


# ── T8 · مرزِ خصوصی: رندر هرگز پروفایلِ محرمانه را نمی‌خواند ────────────────
def t8_never_reads_owner_profile():
    src = (_HERE.parent / "tg" / "card_render.py").read_text("utf-8")
    for forbidden in ("OWNER-PROFILE", "owner_profile", "OWNER_PROFILE"):
        # ذکرش در توضیحِ «نمی‌خوانم» مجاز است؛ استفادهٔ واقعی نه.
        for m in re.finditer(re.escape(forbidden), src):
            line = src[:m.start()].count("\n")
            txt = src.split("\n")[line]
            is_comment = txt.lstrip().startswith("#") or txt.lstrip().startswith("·")
            in_docstring = line < 40
            ck(is_comment or in_docstring,
               f"T8: ارجاعِ اجراییِ {forbidden} در خطِ {line + 1}: {txt.strip()[:70]}")
    for io_call in ("open(", "read_text", "Path(", "requests", "urllib", "sqlite3"):
        ck(io_call not in src.replace("read_text(\"utf-8\")", ""),
           f"T8: رندر باید pure باشد ولی {io_call} دارد")
    # نمونه‌ها باید بی‌استثنا رندر شوند (پیش‌نمایشِ امروز، بی‌راز و بی‌ارسال)
    try:
        s = cr.samples()
        ck(len(s) >= 2, "T8: نمونهٔ کافی نیست")
        for title, card in s:
            ck(card["plain_len"] <= cr.MAX_TEXT_CHARS, f"T8: نمونهٔ «{title}» بلند است")
            ck(card["reply_markup"], f"T8: نمونهٔ «{title}» دکمه ندارد")
    except Exception as e:  # noqa: BLE001
        FAILURES.append(f"T8: samples() شکست: {type(e).__name__}: {e}")


def main() -> int:
    for fn in (t1_stake_required, t2_no_duration_deadline, t3_working_memory_load,
               t4_no_unglossed_jargon, t5_symmetric_cost, t6_self_contained,
               t7_batch, t8_never_reads_owner_profile):
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            FAILURES.append(f"{fn.__name__}: EXCEPTION {type(e).__name__}: {e}")
    if FAILURES:
        print(f"FAIL {len(FAILURES)}/{CHECKS} — card render profile")
        for f in FAILURES:
            print("  ✗", f)
        return 1
    print(f"PASS {CHECKS}/{CHECKS} — قیدهای شناختیِ کارت به assertion تبدیل شدند")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
