#!/usr/bin/env python3
"""lead_scorer.py — موتورِ امتیازدهیِ لیدِ نقاشی (مرحلهٔ ۱ نقشهٔ لید، 2026-07-15).

پورتِ وفادارِ `_launchpad/second-brain-live/painting-bot/lead_scorer.py` به داخلِ
ارگانیسم: همان ریاضی (فیلترِ سخت → مسیریابیِ دسته → سیگنال‌های جمع‌پذیر → ارزش →
جغرافیا → آستانه‌ها)، ولی stdlib-فقط — وابستگیِ pyyaml حذف و کلِ
`painter_lead_scoring.yaml` عیناً به‌صورت DEFAULT_CONFIG این‌جا inline شد.
⚠️ هر تغییرِ وزن این‌جا باید آگاهانه باشد؛ تستِ test_lead_scorer.py مقادیر را به
مقادیرِ yamlِ اصلی پین کرده تا driftِ خاموش لو برود.

تابعِ خالص: dict-ورودی → ScoredLead-خروجی. هیچ I/O، هیچ شبکه، هیچ effector —
تصمیمِ نهایی (draft/save/skip) فقط یک «پیشنهاد» است؛ مصرف‌کننده (lead_discovery_beat)
propose-only است و ارسال همیشه human-gated می‌ماند.
"""
from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field


# ─── VQ-SCORER-001 (2026-07-25): دستهٔ مسکونیِ مستقیم — additive، flag-gated ────
# کارِ واقعیِ مالک (رنگ‌آمیزیِ مستقیمِ خانه، $715–$15k) در هیچ‌یک از ۴ دستهٔ
# DA-محورِ اصلی جا نمی‌گرفت: base=0 + سقفِ سیگنال‌ها 36 < save_threshold=45 → همیشه
# skip. این دسته آن لوله را باز می‌کند. پیش‌فرض خاموش؛ با
# OCTOPUS_LEAD_DIRECT_RESIDENTIAL=1 روشن می‌شود. چهار دستهٔ اصلی و آستانه‌ها
# دست‌نخورده‌اند؛ rollback = حذفِ فلگ یا set 0.
_DIRECT_FLAG = "OCTOPUS_LEAD_DIRECT_RESIDENTIAL"


def _flag_on(name: str) -> bool:
    return str(os.environ.get(name, "")).strip().lower() in ("1", "true", "yes", "on")


def _direct_residential_on() -> bool:
    return _flag_on(_DIRECT_FLAG)


# ─── LANE-3 / VQ-SCORER-FA-001 (2026-08-01، گزارشِ WHY-NO-REAL-LEADS ردیف ۹) ─────
# طبقه‌بندِ ورودی فارسی می‌فهمد (`lead_email_intake._SERVICE_TERMS` شاملِ «نقاشی»،
# «رنگ‌آمیزی»، «نقاش») ولی این scorer که خروجی‌اش را قضاوت می‌کند ۱۰۰٪ انگلیسی بود:
# شمارشِ کاراکترِ غیر-ASCII در کلِ DEFAULT_CONFIG برابرِ صفر بود. یک استعلامِ فارسی از
# در پذیرفته می‌شد، امتیازِ **صفر** می‌گرفت، و در `lead_pipeline._process_one` پشتِ
# `if sc.action == "skip"` — که **بالای** شاخهٔ `is_stuck` است — به یک شمارنده تبدیل
# می‌شد: نه کارت، نه سؤال، نه هیچ ردی به مالک.
#
# دو فلگِ کاملاً مستقل، هر دو پیش‌فرض خاموش (rollback = حذفِ فلگ یا =0):
#   OCTOPUS_LEAD_FA_VOCAB             → واژگانِ فارسی (hard_skip + مسیریابی + سیگنال‌ها)
#   OCTOPUS_LEAD_ASK_WHEN_UNSCOREABLE → لیدِ بی‌دسته به‌جای skip، action=ACTION_ASK می‌گیرد
# با هر دو خاموش، خروجی برای هر ورودی (انگلیسی یا فارسی) بایت‌به‌بایت همان امروز است.
_FA_FLAG = "OCTOPUS_LEAD_FA_VOCAB"
_ASK_FLAG = "OCTOPUS_LEAD_ASK_WHEN_UNSCOREABLE"

# action ِ نو — «ماشین قضاوتی ندارد»؛ نه skip (نمی‌خواهم) و نه draft (می‌خواهم).
# مصرف‌کنندهٔ تولیدیِ واقعی: `lead_pipeline._process_one` — چون != "skip" است از
# early-return عبور می‌کند و به شاخهٔ `lead_research.is_stuck` می‌رسد ⇒ کارِ BLOCKED با
# سؤالِ فارسی در 🎨 (همان مسیرِ «از مالک بپرس»). یعنی اثرِ «چکِ is_stuck بالای
# early-return» بدونِ دست‌زدن به فایلِ لِینِ دیگر به دست می‌آید.
# ⚠️ هیچ مسیرِ خروجی‌ای باز نمی‌کند: هر پنج مصرف‌کنندهٔ تولیدیِ action روی == "draft"
# شرط دارند (lead_pipeline:274/316، wiring:2841، acceptance_journey:1836؛
# lead_outcome_recorder فقط draft↔save را جابه‌جا می‌کند).
ACTION_ASK = "ask"

# نامِ env ِ آستانه‌ها — مستند در DEFAULT_CONFIG["actions"]. ست‌نشده = پیش‌فرضِ کانفیگ.
_DRAFT_TH_ENV = "OCTOPUS_LEAD_DRAFT_THRESHOLD"
_SAVE_TH_ENV = "OCTOPUS_LEAD_SAVE_THRESHOLD"


def _fa_on() -> bool:
    return _flag_on(_FA_FLAG)


def _ask_when_unscoreable_on() -> bool:
    return _flag_on(_ASK_FLAG)


# عباراتِ رنگ‌آمیزیِ مستقیم — برای معافیت از hard-skipِ single-dwelling.
# فقط وقتی فلگ روشن است اثر دارد. hard-skipهای any_phrase (demolition و…)
# همیشه برقرارند.
_DIRECT_REPAINT_PHRASES = [
    "repaint", "repainting", "painting works", "paint work",
    "interior painting", "exterior painting", "house painting",
    "fence painting", "deck painting", "roof painting",
    "touch up", "touch-up", "maintenance painting",
    "re-paint", "re-coat", "recoat",
]


# ─── کانفیگ — inlineِ عیناً painter_lead_scoring.yaml (فلسفه: فیلترِ سخت + مسیریابی
# بر اساسِ «نوعِ خریدار»؛ strata اول = رابطهٔ تکرارشونده) ───────────────────────────
DEFAULT_CONFIG: dict = {
    "meta": {
        "operator": "Sydney painter",
        "base_lat": -33.8688,          # مرکزِ سرویس (CBD سیدنی)
        "base_lng": 151.2093,
        "max_service_radius_km": 40,
    },
    # ── آستانه‌ها — مقدارِ کانفیگ، با override ِ اختیاریِ env (ست‌نشده = همین اعداد) ──
    # OCTOPUS_LEAD_DRAFT_THRESHOLD / OCTOPUS_LEAD_SAVE_THRESHOLD
    #
    # چه شاهدی جابه‌جاییِ ۷۰ را توجیه می‌کند (و چه چیزی نمی‌کند):
    #   ✅ ≥۲۰ لیدِ **واقعیِ** امتیازخورده که در سطلِ save (۴۵–۶۹) نشسته‌اند، و مالک
    #      روی ≥۶۰٪شان دکمهٔ ✅ زده باشد. منبعِ شمارش: رأی‌های ثبت‌شدهٔ مالک در
    #      outcome/receipt store (نه حدس، نه حسِ جلسه). آن‌وقت ۷۰ ثابت می‌کند که
    #      خط‌کش سخت‌گیرتر از بازار است و پایین‌آوردنش داده دارد.
    #   ✅ یا: نشان‌دادنِ این‌که ۸ امتیازِ geo برای کانالِ مربوطه **ساختاراً**
    #      دست‌نیافتنی است (lat/lng هرگز capture نمی‌شود) — یعنی سقفِ واقعیِ آن
    #      کانال ۶۸ است، نه ۷۶. آن یک نقصِ pipeline است؛ درستش capture کردنِ
    #      suburb/postcode است، و پایین‌آوردنِ آستانه فقط مسکّنِ آن.
    #   ❌ «یک لیدِ نمونه ۶۸ گرفت و می‌خواهم سبز شود» — این تنظیمِ خط‌کش روی نتیجه
    #      است، نه اندازه‌گیری. عمداً این‌جا انجام **نشده**: پیش‌فرض ۷۰ دست‌نخورده.
    "actions": {
        "draft_threshold": 70,          # ≥70 → draft (کاندیدِ propose)
        "save_threshold": 45,           # 45–69 → save؛ <45 → skip
    },
    "category_priority": [
        "strata_remedial",
        "residential_repaint_direct",   # VQ-SCORER-001 — بعد از strata، قبل از بقیه
        "government_education",
        "new_residential_multi",
        "commercial_fitout",
    ],
    "hard_skip": {
        "any_phrase": [
            "demolition only", "tree removal", "subdivision of land",
            "strata subdivision", "boundary adjustment",
            "torrens title subdivision", "swimming pool", "signage only",
        ],
        # LANE-3 — قرینهٔ فارسیِ any_phrase (فقط با OCTOPUS_LEAD_FA_VOCAB).
        # عمداً «فقط تخریب» و نه «تخریب»: «تخریب و بازسازی و رنگ» کارِ ماست.
        # بودجهٔ سؤالِ مالک با همین لیست محافظت می‌شود — آشغالِ شناخته‌شده باید
        # skip بماند، نه این‌که به سؤال تبدیل شود.
        "fa_any_phrase": [
            "فقط تخریب", "تخریب بنا", "تخریب کامل", "قطع درخت", "استخر شنا",
            "تفکیک ملک", "تابلو تبلیغاتی", "بنر تبلیغاتی",
        ],
        "single_dwelling_phrases": [
            "dwelling house", "single dwelling", "detached dwelling",
            "secondary dwelling", "granny flat",
        ],
        "single_dwelling_value_floor": 250000,
    },
    "categories": {
        "strata_remedial": {
            "base": 55,
            "label": "Strata remedial / common-property repaint",
            "required_any": [
                "common property", "owners corporation", "remedial",
                "render and paint", "render & paint", "balustrade", "balcony",
            ],
            "context_any": [
                "strata", "units", "apartments", "flat building",
                "multi dwelling", "multi-dwelling", "common property",
                "owners corporation",
            ],
        },
        "government_education": {
            "base": 35,
            "label": "Government / education / social housing (route to tenders)",
            "required_any": [
                "school", "tafe", "hospital", "health facility",
                "social housing", "community facility", "public building",
            ],
        },
        "new_residential_multi": {
            "base": 30,
            "label": "New multi-residential build (future client + builder relationship)",
            "required_any": [
                "residential flat building", "multi dwelling housing",
                "multi-dwelling housing", "apartment building", "townhouses",
                "shop top housing", "boarding house",
            ],
        },
        "commercial_fitout": {
            "base": 40,
            "label": "Commercial fitout / change of use (builder is the buyer)",
            "required_any": [
                "fitout", "fit out", "fit-out", "change of use",
                "retail premises", "office", "tenancy", "shopfront",
                "refurbishment",
            ],
        },
        # ── VQ-SCORER-001: کارِ واقعیِ مالک (رنگ‌آمیزیِ مستقیمِ مسکونی) ──────────
        # base=50: با paint_scope(+18) و geo(+8) → 76 = draft. بدونِ geo → 68 = save.
        # value_tiers اختصاصی ندارد (بازهٔ $715–$15k زیرِ کفِ ۱۰۰kِ tiersِ اصلی است
        # و تغییرِ tiersِ سراسری رفتارِ ۴ دستهٔ دیگر را عوض می‌کرد — additive نیست).
        "residential_repaint_direct": {
            "base": 50,
            "label": "Direct residential repaint / maintenance (owner's real work)",
            "required_any": [
                "repaint", "repainting", "painting works", "paint work",
                "interior painting", "exterior painting", "house painting",
                "fence painting", "deck painting", "roof painting",
                "touch up", "touch-up", "maintenance painting",
                "re-paint", "re-coat", "recoat",
            ],
            "context_any": [
                "dwelling", "house", "residential", "home", "property",
                "apartment", "unit", "townhouse", "villa", "duplex",
            ],
            # ── LANE-3: قرینهٔ فارسیِ همین دسته (فقط با OCTOPUS_LEAD_FA_VOCAB) ──
            # چرا فقط همین دسته و نه strata/دولتی/تجاری: آن سه از اسکرپِ **انگلیسیِ**
            # planning-alerts/AusTender تغذیه می‌شوند و هیچ کانالِ فارسی‌ای ندارند؛
            # کانالِ فارسیِ امروز پیامِ مستقیمِ خودِ مشتری است و آن دقیقاً همین دسته
            # است. افزودنِ واژهٔ فارسی به آن سه بدونِ کانالِ متناظر فقط ریسکِ
            # مسیریابیِ غلط می‌سازد (strata اولِ صفِ اولویت است).
            # «رنگ» تنهاست چون در «رنگ‌آمیزی»، «رنگ‌کاری»، «رنگ زدن» و «رنگش» هم
            # با مرزِ چپ مچ می‌شود — یعنی سه املای رایج را یک عبارت پوشش می‌دهد.
            "fa_required_any": [
                "رنگ", "نقاشی", "نقاش", "رنگ‌آمیزی", "رنگ آمیزی", "رنگ کردن",
                "رنگ زدن", "رنگ‌کاری", "کناف", "بتونه", "بتونه کاری", "سیلر",
                "آستر", "پتینه", "رنگ روغنی", "رنگ پلاستیک", "اکرولیک",
            ],
            "fa_context_any": [
                "خانه", "منزل", "آپارتمان", "واحد", "ویلا", "ساختمان", "ملک",
                "اتاق", "سقف", "دیوار", "نما", "حیاط", "پذیرایی", "آشپزخانه",
                "راه پله", "راه‌پله", "کابینت", "نرده", "درب", "پنجره",
            ],
        },
    },
    "signals": {
        "paint_scope": {
            "weight": 18,
            "any_phrase": [
                "paint", "repaint", "render", "coating", "external alteration",
                "internal alteration", "facade", "fitout", "fit out", "fit-out",
                "refurbishment",
            ],
            "fa_any_phrase": [
                "رنگ", "نقاشی", "نقاش", "رنگ‌آمیزی", "رنگ آمیزی", "رنگ‌کاری",
                "کناف", "بتونه", "سیلر", "آستر", "نما", "سقف", "دیوار",
                "بازسازی", "ترمیم", "زیرسازی",
            ],
        },
        "recurring_buyer": {
            "weight": 10,
            "any_phrase": [
                "common property", "owners corporation", "strata", "maintenance",
            ],
            "fa_any_phrase": [
                "مشاع", "مشاعات", "نگهداری", "قرارداد سالانه", "دوره‌ای",
            ],
        },
        "red_flags": {
            "weight": -15,
            "any_phrase": [
                "business identification signage", "advertising",
                "illuminated sign", "awning", "heritage",
            ],
            # «تابلو» تنها عمداً نیست — «تابلو نقاشی» کارِ هنری است نه علامتِ تبلیغاتی.
            "fa_any_phrase": [
                "تابلو تبلیغاتی", "بنر تبلیغاتی", "تبلیغات محیطی", "میراث فرهنگی",
            ],
        },
        # ── LANE-3: سیگنالِ «قصدِ خرید» — عمداً فقط فارسی، و این عمد قابلِ دفاع است:
        # زبانِ قصد («قیمت می‌خواهم»، «کِی می‌توانید بیایید») فقط در پیامِ **مستقیمِ**
        # مشتری وجود دارد، و تنها کانالِ مستقیمِ امروز فارسی است. لیدهای انگلیسی از
        # اسکرپِ planning-alerts می‌آیند و هیچ‌وقت زبانِ قصد ندارند؛ افزودنِ قرینهٔ
        # انگلیسی الان فقط امتیازِ لیدهای اسکرپ‌شده را جابه‌جا می‌کند بدونِ شاهد.
        # وقتی کانالِ ایمیلِ مستقیمِ انگلیسی producer پیدا کرد، `any_phrase` همین
        # سیگنال پر می‌شود (quote/estimate/how much/when can you) — نه زودتر.
        # وزن ۸: هم‌اندازهٔ bonus ِ جغرافیا، چون هر دو یک چیز می‌گویند —
        # «این لید واقعاً مالِ ماست» — و هیچ‌کدام به‌تنهایی از سطلی به سطلِ دیگر
        # نمی‌برد (۵۰ base ِ دستهٔ مسکونی + ۱۸ رنگ = ۶۸ که هنوز save است).
        "fa_intent": {
            "weight": 8,
            "any_phrase": [],
            "fa_any_phrase": [
                "قیمت", "هزینه", "برآورد", "تخمین", "چقدر", "استعلام",
                "مشاوره", "کی ", "چه زمانی", "چه موقع", "پیشنهاد قیمت",
            ],
        },
    },
    "value_tiers": [
        {"min": 1000000, "bonus": 15},
        {"min": 300000, "bonus": 10},
        {"min": 100000, "bonus": 5},
        {"min": 0, "bonus": 0},
    ],
    "geo": {
        "in_radius_bonus": 8,
        "out_of_radius_penalty": -20,
    },
}


# ─── helpers ────────────────────────────────────────────────────────────────────
def _haystack(lead: dict) -> str:
    """متنِ lowercase که کلیدواژه‌ها در آن جستجو می‌شوند."""
    parts = [str(lead.get("description", "")), str(lead.get("address", ""))]
    return " ".join(parts).lower()


def _matches(haystack: str, phrases) -> list[str]:
    """عبارت‌هایی که به‌صورتِ substring در haystack هستند."""
    return [p for p in (phrases or []) if p.lower() in haystack]


# ─── لایهٔ فارسی (LANE-3) — بدونِ نرمال‌سازی، مچ روی ورودیِ واقعی شکست می‌خورد ────────
# چهار چیزی که واقعاً از گوشیِ یک مشتریِ فارسی‌زبان می‌آید و مچِ ساده را می‌کُشد:
#   ۱) ZWNJ (U+200C) داخلِ «رنگ‌آمیزی» — بایتِ نامرئی بینِ «رنگ» و «آمیزی»
#   ۲) ارقامِ فارسی/عربی: «۲۱۱۸» و «٢١١٨» در برابرِ «2118»
#   ۳) حروفِ هم‌شکلِ کیبوردِ عربی: ي/ك/ة/ۀ/أ/إ به‌جای ی/ک/ه/ه/ا/ا
#   ۴) اعراب: «کِی» (کسره) در برابرِ «کی»
# «آ» عمداً به «ا» نگاشت **نمی‌شود** — حرفِ مستقلِ فارسی است و «آمیزی» را می‌کُشد.
_FA_ZWNJ = "‌"
_FA_TRANS = {ord(c): str(i % 10) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩")}
_FA_TRANS.update({ord("ي"): "ی", ord("ك"): "ک", ord("ة"): "ه",
                  ord("ۀ"): "ه", ord("أ"): "ا", ord("إ"): "ا"})
# اعراب (U+064B..U+0655، U+0670) + نشانه‌های جهت/BOM که در copy-paste می‌آیند.
_FA_DROP = frozenset(chr(c) for c in range(0x064B, 0x0656)) | frozenset(
    ("ٰ", "‍", "‎", "‏", "﻿"))
_FA_LETTER_CLASS = "؀-ۿ‌"
_FA_RX_CACHE: dict = {}


def _fa_norm(text: str) -> str:
    """نرمال‌سازیِ فارسی: ارقام → ASCII، حروفِ عربی → فارسی، اعراب حذف،
    ZWNJ → فاصله، فاصله‌های تکراری جمع. برای متنِ انگلیسی تقریباً no-op است، ولی
    مسیرِ انگلیسی هرگز صدایش نمی‌زند (فلگ‌محور) — پس درزِ رفتاری وجود ندارد."""
    s = str(text or "").translate(_FA_TRANS)
    if _FA_DROP.intersection(s):
        s = "".join(ch for ch in s if ch not in _FA_DROP)
    return " ".join(s.replace(_FA_ZWNJ, " ").split()).lower()


def _fa_rx(phrase: str):
    """رجکسِ کش‌شدهٔ یک عبارتِ فارسی.

    قرارداد: مرزِ **چپ** همیشه لازم است (وگرنه «کی» داخلِ «نزدیکی» می‌افتد)؛ مرزِ
    **راست** عمداً باز است تا پسوندهای چسبانِ فارسی مچ شوند («دیوارها»، «اتاقم»،
    «قیمتش»). عبارتی که در کانفیگ با یک فاصلهٔ انتهایی نوشته شود («کی ») یعنی
    «کلمهٔ کامل» — هر دو مرز — که برای واژه‌های کوتاهِ پرتصادم لازم است."""
    rx = _FA_RX_CACHE.get(phrase)
    if rx is None:
        body = _fa_norm(phrase)
        tail = "(?![" + _FA_LETTER_CLASS + "])" if str(phrase).endswith(" ") else ""
        rx = re.compile("(?<![" + _FA_LETTER_CLASS + "])" + re.escape(body) + tail)
        _FA_RX_CACHE[phrase] = rx
    return rx


def _fa_matches(hay_fa: str, phrases) -> list[str]:
    """اصابت‌های فارسی روی haystack ِ از-قبل-نرمال‌شده. عبارتِ تهی هرگز مچ نمی‌کند."""
    if not hay_fa:
        return []
    return [p for p in (phrases or []) if _fa_norm(p) and _fa_rx(p).search(hay_fa)]


def _hits(hay: str, hay_fa: str, en_phrases, fa_phrases) -> list[str]:
    """اصابت‌های انگلیسی + (فقط با فلگِ فارسی) اصابت‌های فارسی.
    فلگ خاموش ⇒ خروجی دقیقاً همان `_matches(hay, en_phrases)` ِ قبل است."""
    out = _matches(hay, en_phrases)
    if _fa_on():
        out = out + _fa_matches(hay_fa, fa_phrases)
    return out


def _threshold(actions: dict, key: str, env_name: str) -> int:
    """آستانه از کانفیگ، با override ِ اختیاریِ env. env ِ ست‌نشده یا خراب ⇒ پیش‌فرضِ
    کانفیگ (هیچ‌وقت استثنا، هیچ‌وقت آستانهٔ ناخواسته)."""
    raw = os.environ.get(env_name)
    if raw is not None and str(raw).strip():
        try:
            return int(float(str(raw).strip()))
        except (TypeError, ValueError):
            pass
    return int(actions[key])


def _haversine_km(lat1, lng1, lat2, lng2) -> float | None:
    if None in (lat1, lng1, lat2, lng2):
        return None
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ─── VQ-LEAD-CARD-011: پلِ کارتِ قابلِ‌عمل (additive، flag-gated، پیش‌فرض خاموش) ──
def _contact_card(scored) -> "str | None":
    """کارتِ غنی از `legs/lead_card.py` — یا None، که یعنی «بدنهٔ قدیمی را اجرا کن».

    None در سه حالت: فلگ خاموش (پیش‌فرض)، ماژول در دسترس نیست، یا رندر متنِ تهی
    داد. هیچ‌کدام نباید کارت را بکشد — این ماژول تابعِ خالصِ بی‌I/O است و همان
    می‌ماند (`lead_card` هم stdlib-only و بدونِ I/O ِ نوشتنی است).
    """
    try:
        import lead_card  # noqa: WPS433 — lazy: هم‌پوشه، تا env ِ تست اثر کند
        if not lead_card.enabled():
            return None
        return lead_card.card_text(scored.lead, scored=scored) or None
    except Exception:  # noqa: BLE001 — کارتِ غنی هرگز کارتِ پایه را قربانی نمی‌کند
        return None


# ─── نتیجه ──────────────────────────────────────────────────────────────────────
@dataclass
class ScoredLead:
    category: str
    category_label: str
    score: int
    action: str                                   # "draft" | "save" | "skip"
    reasons: list[str] = field(default_factory=list)
    lead: dict = field(default_factory=dict)

    def card(self) -> str:
        """کارتِ تلگرامی — برای نمایشِ کاندیدا به مالک (مرحلهٔ ۷).

        VQ-LEAD-CARD-011 (2026-08-01، گزارشِ WHY-NO-REAL-LEADS ردیف ۱۱): بدنهٔ زیر
        **نه تلفن دارد، نه ایمیل، نه نامِ مشتری** — مالک روی نردبان نمی‌تواند با
        این لید تماس بگیرد. `legs/lead_card.py` نسخهٔ قابلِ‌عملِ کارت را می‌سازد.
        additive و flag-gated: `OCTOPUS_WIRE_LEAD_CARD_CONTACT` خاموش (پیش‌فرض) ⇒
        `_contact_card()` مقدارِ None می‌دهد ⇒ بدنهٔ زیر بایت‌به‌بایت همان امروز.
        """
        _rich = _contact_card(self)
        if _rich:
            return _rich
        L = self.lead
        emoji = {"draft": "🟢", "save": "🟡", "skip": "⚪️",
                 ACTION_ASK: "❓"}.get(self.action, "🏢")
        lines = [
            f"{emoji} {L.get('source', 'lead')} | score: {self.score} | {self.category}",
            f"📌 {str(L.get('description', '')).strip()}",
            f"📍 {L.get('address', 'n/a')}",
        ]
        if L.get("url"):
            lines.append(f"🔗 {L['url']}")
        lines.append("🧠 " + "; ".join(self.reasons))
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {"category": self.category, "category_label": self.category_label,
                "score": self.score, "action": self.action, "reasons": self.reasons}


# ─── امتیازدهنده ────────────────────────────────────────────────────────────────
class LeadScorer:
    """قطعی، $0، بدونِ I/O. کانفیگِ سفارشی فقط برای تست/تنظیم — پیش‌فرض همان yaml."""

    def __init__(self, config: dict | None = None):
        self.cfg = config or DEFAULT_CONFIG

    # -- فیلترهای سخت: اصابت = skip بی‌قیدوشرط --------------------------------------
    def _hard_skip(self, hay: str, lead: dict, hay_fa: str = "") -> str | None:
        hs = self.cfg["hard_skip"]
        hit = _hits(hay, hay_fa, hs.get("any_phrase"), hs.get("fa_any_phrase"))
        if hit:
            return f"hard-skip ({hit[0]})"
        sd = _matches(hay, hs.get("single_dwelling_phrases"))
        if sd:
            # VQ-SCORER-001: رنگ‌آمیزیِ مستقیمِ مسکونی کارِ واقعیِ مالک است؛
            # وقتی فلگ روشن است و لید عبارتِ رنگ‌آمیزی دارد، از hard-skipِ
            # single-dwelling معاف می‌شود. hard-skipهای any_phrase (demolition،
            # tree removal و…) همیشه برقرارند — آن‌ها واقعاً کارِ ما نیستند.
            if _direct_residential_on() and _matches(hay, _DIRECT_REPAINT_PHRASES):
                pass  # fall through to routing — این لید رنگ‌آمیزی است، نه ساخت‌وساز
            else:
                cost = lead.get("cost_of_development")
                floor = hs.get("single_dwelling_value_floor", 0)
                if cost is not None and cost < floor:
                    return f"single dwelling under ${floor:,} ({sd[0]})"
        return None

    # -- مسیریابیِ دسته (اولین اصابت برنده — strata عمداً اول) -----------------------
    def _route(self, hay: str, hay_fa: str = "") -> tuple[str, dict]:
        cats = self.cfg["categories"]
        for name in self.cfg["category_priority"]:
            # VQ-SCORER-001: دستهٔ مسکونیِ مستقیم فقط با فلگ فعال است.
            # بدونِ فلگ، رفتار بایت‌به‌بایت identical با نسخهٔ قبل است.
            if name == "residential_repaint_direct" and not _direct_residential_on():
                continue
            c = cats[name]
            if not _hits(hay, hay_fa, c.get("required_any"), c.get("fa_required_any")):
                continue
            ctx, fa_ctx = c.get("context_any"), c.get("fa_context_any")
            # LANE-3: با فلگِ فارسیِ خاموش `_hits` دقیقاً `_matches(hay, ctx)` است؛
            # و دسته‌ای که هیچ‌کدام از دو لیستِ context را ندارد مثلِ قبل چک نمی‌شود.
            if (ctx or fa_ctx) and not _hits(hay, hay_fa, ctx, fa_ctx):
                continue
            return name, c
        return "uncategorised", {"base": 0, "label": "No clear paint-relevant scope"}

    # -- ارزش + جغرافیا -------------------------------------------------------------
    def _value_bonus(self, lead: dict) -> tuple[int, str | None]:
        cost = lead.get("cost_of_development")
        if cost is None:
            return 0, None
        for tier in self.cfg["value_tiers"]:
            if cost >= tier["min"]:
                if tier["bonus"]:
                    return tier["bonus"], f"value ${cost:,} (+{tier['bonus']})"
                return 0, None
        return 0, None

    def _geo_adjust(self, lead: dict) -> tuple[int, str | None]:
        m, g = self.cfg["meta"], self.cfg["geo"]
        d = _haversine_km(lead.get("lat"), lead.get("lng"), m["base_lat"], m["base_lng"])
        if d is None:
            return 0, None
        if d <= m["max_service_radius_km"]:
            return g["in_radius_bonus"], f"{d:.0f}km away (+{g['in_radius_bonus']})"
        return g["out_of_radius_penalty"], f"{d:.0f}km away ({g['out_of_radius_penalty']})"

    # -- اصلی ------------------------------------------------------------------------
    def score(self, lead: dict) -> ScoredLead:
        hay = _haystack(lead)
        # LANE-3: haystack ِ فارسی فقط وقتی ساخته می‌شود که فلگ روشن باشد — با فلگِ
        # خاموش هیچ محاسبهٔ اضافه‌ای هم انجام نمی‌شود، چه رسد به تغییرِ رفتار.
        hay_fa = _fa_norm(hay) if _fa_on() else ""
        reasons: list[str] = []

        skip_reason = self._hard_skip(hay, lead, hay_fa)
        if skip_reason:
            return ScoredLead("filtered", "Hard filter", 0, "skip", [skip_reason], lead)

        cat_name, cat = self._route(hay, hay_fa)
        total = cat.get("base", 0)
        reasons.append(f"{cat.get('label', cat_name)} (base {cat.get('base', 0)})")

        for sig_name, sig in self.cfg["signals"].items():
            hits = _hits(hay, hay_fa, sig.get("any_phrase"), sig.get("fa_any_phrase"))
            if hits:
                total += sig["weight"]
                sign = "+" if sig["weight"] >= 0 else ""
                reasons.append(f"{sig_name}: {', '.join(hits[:3])} ({sign}{sig['weight']})")

        vb, vr = self._value_bonus(lead)
        total += vb
        if vr:
            reasons.append(vr)
        elif lead.get("cost_of_development") is None:
            reasons.append("value unknown (no bonus)")

        gb, gr = self._geo_adjust(lead)
        total += gb
        if gr:
            reasons.append(gr)

        score = max(0, min(100, total))

        a = self.cfg["actions"]
        if score >= _threshold(a, "draft_threshold", _DRAFT_TH_ENV):
            action = "draft"
        elif score >= _threshold(a, "save_threshold", _SAVE_TH_ENV):
            action = "save"
        else:
            action = "skip"

        # ── LANE-3: «نمی‌فهمم» ≠ «نمی‌خواهم» ───────────────────────────────────────
        # uncategorised یعنی هیچ دسته‌ای اصابت نکرده — ماشین **قضاوتی ندارد**. چنین
        # لیدی باید به انسان برسد، نه به شمارنده. عمداً فقط uncategorised:
        # دستهٔ "filtered" (hard-skip) بالاتر return شده و هرگز به این‌جا نمی‌رسد، و
        # لیدِ دسته‌دارِ کم‌امتیاز هم قضاوت **شده** است — پس بودجهٔ سؤالِ مالک صرفِ
        # آشغالِ شناخته‌شده نمی‌شود، فقط صرفِ چیزی که نفهمیدیم.
        if action == "skip" and cat_name == "uncategorised" and _ask_when_unscoreable_on():
            action = ACTION_ASK
            reasons.append("هیچ دسته‌ای اصابت نکرد — قضاوتِ ماشین وجود ندارد؛ سؤال از مالک")

        return ScoredLead(cat_name, cat.get("label", cat_name), score, action, reasons, lead)


def score_lead(lead: dict) -> ScoredLead:
    """میان‌بُرِ ماژول‌سطح — امتیازدهیِ یک لید با کانفیگِ پیش‌فرض."""
    return LeadScorer().score(lead)
