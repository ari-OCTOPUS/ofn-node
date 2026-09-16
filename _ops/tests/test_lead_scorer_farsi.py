#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_scorer_farsi — LANE-3 (گزارشِ WHY-NO-REAL-LEADS-2026-08-01، ردیف ۹).

بیماری: طبقه‌بندِ ورودی فارسی می‌فهمد، ولی scorer ای که خروجی‌اش را قضاوت می‌کند
نمی‌فهمید. استعلامِ فارسی از در پذیرفته می‌شد، امتیازِ **صفر** می‌گرفت، و در
`lead_pipeline._process_one` پشتِ `if sc.action == "skip"` — که **بالای** شاخهٔ
`lead_research.is_stuck` است — به یک شمارنده تبدیل می‌شد: نه کارت، نه سؤال، نه هیچ ردی.

این فایل شش چیز را اثبات می‌کند:
  A) با فلگ‌های خاموش، خروجی برای انگلیسی **و** فارسی عینِ امروز است.
  B) با فلگِ فارسی، استعلامِ واقعیِ فارسی امتیازِ **بالای صفر** می‌گیرد.
  C) نرمال‌سازی واقعی است: ZWNJ، ارقامِ فارسی/عربی، ي/ك ِ عربی، و اعرابِ «کِی».
  D) مثبتِ کاذب ندارد: «نزدیکی»/«کیفیت» سیگنالِ «کِی» را نمی‌اندازد، «نیرنگ» رنگ را نه.
  E) لیدی که ماشین **نمی‌فهمد** به‌جای skip، `ACTION_ASK` می‌گیرد — و آشغالِ
     hard-skip ِ شناخته‌شده هنوز skip می‌ماند (بودجهٔ سؤالِ مالک هدر نمی‌رود).
  F) **دندان (مصرف‌کنندهٔ تولیدی):** همان لید از `lead_pipeline._process_one` رد
     می‌شود و به کارِ BLOCKED با سؤالِ فارسی می‌رسد؛ با فلگِ خاموش (= رفتارِ پیش از
     این پچ) همان لید «skip» می‌گیرد در حالی که `is_stuck` صریحاً True است —
     یعنی ماشین می‌دانست گیر است و باز هم دورش ریخت.

$0، آفلاین، stdlib-only، بدونِ شبکه و بدونِ هیچ ارسالی.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("lead-scorer-farsi")

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget"),
           str(_OPS / "telegram_center"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ماشینِ میزبان فلگ‌های زنده دارد (در snapshot ِ ۲۰۲۶-۰۸-۰۱ حتی OUTBOUND مسلح است) —
# تست باید قطعی باشد و از حالتِ محیط ارث نبرد.
_LANE3_FLAGS = ("OCTOPUS_LEAD_FA_VOCAB", "OCTOPUS_LEAD_ASK_WHEN_UNSCOREABLE",
                "OCTOPUS_LEAD_DRAFT_THRESHOLD", "OCTOPUS_LEAD_SAVE_THRESHOLD",
                "OCTOPUS_LEAD_DIRECT_RESIDENTIAL", "OCTOPUS_WIRE_LEAD_CARD_CONTACT",
                "OCTOPUS_WIRE_LEAD_OUTBOUND", "OCTOPUS_SMTP_USE_GMAIL")

import lead_pipeline as lp      # noqa: E402
import lead_research            # noqa: E402
import lead_scorer              # noqa: E402
import leg_tasks as lt          # noqa: E402

NOW = 1_785_400_000.0

# استعلامِ واقعیِ فارسی — عیناً همان جمله‌ای که در گزارش امتیازِ صفر گرفت.
FA_ENQUIRY = "سلام، برای رنگ‌آمیزی داخل خانه‌ام در Carlingford قیمت می‌خواهم"

# سه فیکسچرِ انگلیسیِ پین‌شده به yaml ِ اصلی (هم‌ارزِ test_lead_scorer).
EN_STRATA = {
    "source": "planning_alerts",
    "description": ("Remedial works to common property including rendering and "
                    "repainting of external facade and balcony balustrade "
                    "replacement to residential flat building of 24 units."),
    "address": "12 Wattle Crescent, Pyrmont NSW 2009",
    "cost_of_development": 820000, "lat": -33.8700, "lng": 151.1950,
}
EN_FITOUT = {
    "source": "planning_alerts",
    "description": ("Change of use to a retail premises, including internal "
                    "fitout, external facade works, lighting and business "
                    "identification signage."),
    "address": "106 King Street Sydney NSW 2000",
    "cost_of_development": None, "lat": -33.8675, "lng": 151.2070,
}
EN_DEMOLITION = {
    "source": "planning_alerts",
    "description": "Demolition only of existing dwelling house.",
    "address": "5 Quiet St, Sydney NSW 2000",
    "cost_of_development": 60000, "lat": -33.87, "lng": 151.21,
}


def _clear_flags() -> None:
    for k in _LANE3_FLAGS:
        os.environ.pop(k, None)


def _fa_lead(text: str = FA_ENQUIRY, **extra) -> dict:
    """لیدِ فارسی با کانالِ رضایت‌دار — وگرنه consent_firewall آن را market_signal
    می‌داند و pipeline قبل از امتیازدهی ردش می‌کند (یعنی این تست چیزی را نمی‌سنجید)."""
    lead = {"source": "telegram_manual", "description": text}
    lead.update(extra)
    return lead


def _snap(lead: dict) -> tuple:
    sc = lead_scorer.score_lead(lead)
    return (sc.category, sc.score, sc.action, tuple(sc.reasons))


# ─── A) فلگ خاموش = امروز، بایت‌به‌بایت ────────────────────────────────────────
def t_a_flags_off_is_todays_behaviour_for_english_and_farsi():
    _clear_flags()
    # فارسی: دقیقاً همان بیماریِ گزارش — دستهٔ uncategorised، امتیازِ صفر، skip.
    cat, score, action, _ = _snap(_fa_lead())
    assert (cat, score, action) == ("uncategorised", 0, "skip"), \
        f"فلگ خاموش باید رفتارِ امروز را بدهد، گرفتم: {(cat, score, action)}"
    # انگلیسی: هر سه عددِ پین‌شدهٔ yaml دست‌نخورده.
    assert _snap(EN_STRATA)[1:3] == (100, "draft"), _snap(EN_STRATA)
    assert _snap(EN_FITOUT)[1:3] == (51, "save"), _snap(EN_FITOUT)
    assert _snap(EN_DEMOLITION)[0:3] == ("filtered", 0, "skip"), _snap(EN_DEMOLITION)


def t_b_english_path_is_identical_even_with_the_farsi_flag_on():
    """گاردِ درزِ زبانی: روشن‌کردنِ واژگانِ فارسی نباید هیچ عددِ انگلیسی را تکان دهد."""
    _clear_flags()
    before = [_snap(EN_STRATA), _snap(EN_FITOUT), _snap(EN_DEMOLITION)]
    os.environ["OCTOPUS_LEAD_FA_VOCAB"] = "1"
    after = [_snap(EN_STRATA), _snap(EN_FITOUT), _snap(EN_DEMOLITION)]
    assert before == after, f"مسیرِ انگلیسی با فلگِ فارسی تغییر کرد:\n{before}\n{after}"


# ─── B) فارسی دیگر صفر نمی‌گیرد ────────────────────────────────────────────────
def t_c_a_real_farsi_enquiry_now_scores_above_zero():
    _clear_flags()
    os.environ["OCTOPUS_LEAD_FA_VOCAB"] = "1"
    cat, score, action, reasons = _snap(_fa_lead())
    assert score > 0, f"استعلامِ فارسی هنوز صفر می‌گیرد: {(cat, score, action)}"
    assert score == 26, f"۱۸ (paint_scope) + ۸ (fa_intent) = ۲۶؛ گرفتم {score}: {reasons}"
    assert any(r.startswith("paint_scope") for r in reasons), reasons
    assert any(r.startswith("fa_intent") for r in reasons), reasons


def t_d_farsi_enquiry_routes_to_the_owners_real_category():
    """با دستهٔ مسکونیِ مستقیم (همان فلگی که در snapshot ِ زنده =۱ است) لیدِ فارسی
    دیگر بی‌دسته نیست: ۵۰ base + ۱۸ رنگ + ۸ قصد = ۷۶ → draft."""
    _clear_flags()
    os.environ["OCTOPUS_LEAD_FA_VOCAB"] = "1"
    os.environ["OCTOPUS_LEAD_DIRECT_RESIDENTIAL"] = "1"
    cat, score, action, reasons = _snap(_fa_lead())
    assert cat == "residential_repaint_direct", f"{cat} / {reasons}"
    assert score == 76 and action == "draft", f"{score} {action} / {reasons}"


# ─── C) نرمال‌سازی ─────────────────────────────────────────────────────────────
def t_e_normalisation_zwnj_digits_arabic_letters_and_harakat():
    """چهار املای واقعیِ همان جمله باید **دقیقاً** یک امتیاز بدهند."""
    _clear_flags()
    os.environ["OCTOPUS_LEAD_FA_VOCAB"] = "1"
    os.environ["OCTOPUS_LEAD_DIRECT_RESIDENTIAL"] = "1"
    canonical = _snap(_fa_lead())[1]
    variants = {
        # ۱) ZWNJ با فاصلهٔ ساده جایگزین شده (تایپِ گوشی)
        "zwnj→space": "سلام، برای رنگ آمیزی داخل خانه ام در Carlingford قیمت می خواهم",
        # ۲) کیبوردِ عربی: ي به‌جای ی و ك به‌جای ک
        "arabic ي/ك": "سلام، براي رنگ‌آميزي داخل خانه‌ام در Carlingford قيمت مي‌خواهم",
    }
    for name, text in variants.items():
        got = _snap(_fa_lead(text))[1]
        assert got == canonical, f"{name}: {got} ≠ {canonical}"
    # ۳) ارقامِ فارسی و عربی نباید مچ را بشکنند
    fa_digits = _snap(_fa_lead("رنگ‌آمیزی ۲ اتاق و سقف خانه، کد پستی ۲۱۱۸، قیمت چقدر است؟"))
    ar_digits = _snap(_fa_lead("رنگ‌آمیزی ٢ اتاق و سقف خانه، کد پستی ٢١١٨، قیمت چقدر است؟"))
    assert fa_digits == ar_digits, f"ارقام: {fa_digits} ≠ {ar_digits}"
    assert fa_digits[1] == 76, fa_digits
    assert lead_scorer._fa_norm("۲۱۱۸ و ٢١١٨") == "2118 و 2118"
    # ZWNJ خودش — نه از راهِ املای دومِ کانفیگ، بلکه مستقیم روی نرمال‌ساز، و بعد
    # روی عبارتی که در کانفیگ **فقط** شکلِ فاصله‌دار دارد («قرارداد سالانه»).
    assert lead_scorer._fa_norm("رنگ‌آمیزی") == "رنگ آمیزی"
    zwnj_only = _snap(_fa_lead("قرارداد‌سالانه نگهداری"))
    assert any(r.startswith("recurring_buyer") for r in zwnj_only[3]), zwnj_only[3]
    # ۴) اعرابِ «کِی» (کسره) — بدونِ حذفِ اعراب این مچ نمی‌شود
    kasra = _snap(_fa_lead("نقاشی ساختمان و کناف اتاق — کِی می‌توانید بیایید؟"))
    plain = _snap(_fa_lead("نقاشی ساختمان و کناف اتاق — کی می‌توانید بیایید؟"))
    assert kasra == plain, f"اعراب: {kasra} ≠ {plain}"
    assert any(r.startswith("fa_intent") for r in kasra[3]), kasra[3]


# ─── D) مثبتِ کاذب ─────────────────────────────────────────────────────────────
def t_f_farsi_matching_has_word_boundaries_not_blind_substrings():
    """«کی» داخلِ «نزدیکی»/«کیفیت» و «رنگ» داخلِ «نیرنگ» نباید سیگنال بیندازد —
    وگرنه هر پیامِ فارسی امتیازِ الکی می‌گیرد و خط‌کش بی‌معنا می‌شود."""
    _clear_flags()
    os.environ["OCTOPUS_LEAD_FA_VOCAB"] = "1"
    os.environ["OCTOPUS_LEAD_DIRECT_RESIDENTIAL"] = "1"
    for text, prefix in (("نزدیکی محل کار من", "fa_intent"),
                         ("کیفیت کار شما چطور است؟", "fa_intent"),
                         ("نیرنگ و کلاهبرداری", "paint_scope")):
        cat, score, action, reasons = _snap(_fa_lead(text))
        assert not [r for r in reasons if r.startswith(prefix)], \
            f"مثبتِ کاذب روی {text!r}: {reasons}"
        assert score == 0, f"{text!r} باید صفر بماند، گرفتم {score}"
    # ولی شکلِ درست باید بیفتد (وگرنه گارد فقط همه‌چیز را خاموش کرده)
    ok_reasons = _snap(_fa_lead("کی می‌توانید بیایید؟"))[3]
    assert any(r.startswith("fa_intent") for r in ok_reasons), ok_reasons
    # پسوندِ چسبانِ فارسی باید مچ شود («دیوارها» ⇒ «دیوار»)
    assert _snap(_fa_lead("دیوارهای اتاقم را رنگ بزنید"))[0] == "residential_repaint_direct"
    # «تابلو نقاشی» علامتِ تبلیغاتی نیست — نباید red_flags بخورد
    assert not [r for r in _snap(_fa_lead("تابلو نقاشی برای دیوار"))[3]
                if r.startswith("red_flags")]


# ─── E) «نمی‌فهمم» ≠ «نمی‌خواهم» ───────────────────────────────────────────────
def t_g_unscoreable_becomes_ask_and_known_garbage_stays_skip():
    _clear_flags()
    os.environ["OCTOPUS_LEAD_FA_VOCAB"] = "1"
    assert _snap(_fa_lead())[2] == "skip", "پیش‌شرط: بدونِ فلگِ ASK هنوز skip است"
    os.environ["OCTOPUS_LEAD_ASK_WHEN_UNSCOREABLE"] = "1"
    cat, score, action, reasons = _snap(_fa_lead())
    assert cat == "uncategorised" and action == lead_scorer.ACTION_ASK, \
        f"لیدِ بی‌دسته باید سؤال شود نه skip: {(cat, score, action)}"
    assert any("سؤال از مالک" in r for r in reasons), reasons
    # بودجهٔ سؤال: آشغالِ hard-skip ِ شناخته‌شده هرگز سؤال نمی‌شود
    assert _snap(EN_DEMOLITION)[0:3] == ("filtered", 0, "skip"), _snap(EN_DEMOLITION)
    assert _snap(_fa_lead("فقط تخریب بنا و قطع درخت"))[2] == "skip", \
        "تخریبِ فارسی هم باید skip بماند، نه سؤال"
    # لیدِ دسته‌دارِ کم‌امتیاز هم قضاوت **شده** است ⇒ ask نمی‌شود.
    # (این مورد مرزِ دقیقِ قاعده را می‌سنجد: ۳۵ < ۴۵ یعنی skip، ولی چون دسته
    # اصابت کرده ماشین **قضاوت دارد** و نباید بودجهٔ سؤالِ مالک را خرج کند.)
    low_but_understood = {"source": "planning_alerts",
                          "description": "Construction of a new school hall at a TAFE campus."}
    cat2, score2, action2, _ = _snap(low_but_understood)
    assert (cat2, score2, action2) == ("government_education", 35, "skip"), \
        f"لیدِ دسته‌دارِ کم‌امتیاز نباید سؤال شود: {(cat2, score2, action2)}"
    assert _snap(EN_FITOUT)[2] == "save", _snap(EN_FITOUT)


# ─── F) دندان: مصرف‌کنندهٔ تولیدی ─────────────────────────────────────────────
def _process(lead: dict) -> tuple:
    """یک لید را از خودِ `lead_pipeline._process_one` (تابعِ تولیدی) رد می‌کند.
    headless: بدونِ send_fn هیچ کارتی نمی‌رود و هیچ ارسالی وجود ندارد."""
    st = {"stuck": {}, "followups": {}}
    out = {"ok": True, "sensed": 0, "ready": 0, "stuck": 0, "cards_sent": 0,
           "followups": 0, "revived": 0, "signals": 0, "duplicates": 0}
    label = lp._process_one("LEAD-FA-PROBE", lead, {}, st, out, NOW)
    return label, out, st


def _blocked():
    return [t for t in lt.queue("lead") if t.get("state") == lt.BLOCKED]


def t_h_teeth_pre_fix_the_pipeline_drops_a_lead_it_knows_is_stuck():
    """بازسازیِ رفتارِ **پیش از پچ** (فلگ‌ها خاموش = همان کدِ دیروز):
    ماشین می‌داند لید گیر است (`is_stuck` صریحاً True) و باز هم به‌عنوان skip
    دورش می‌ریزد — چون `if sc.action == "skip"` بالای شاخهٔ is_stuck است."""
    _clear_flags()
    lead = _fa_lead()
    research = lead_research.enrich(lead)
    assert lead_research.is_stuck(research) is True, \
        "پیش‌شرطِ سناریو: این لید باید از نظرِ تحقیق «گیر» باشد"
    before = len(_blocked())
    label, out, st = _process(lead)
    assert label == "skip", f"رفتارِ پیش از پچ باید skip باشد، گرفتم {label}"
    assert out.get("skip") == 1 and out["stuck"] == 0, out
    assert st["stuck"] == {}, st
    assert len(_blocked()) == before, "پیش از پچ نباید هیچ سؤالی برای مالک ساخته شود"


def t_i_an_unscoreable_lead_now_reaches_the_owner_as_a_question():
    """همان لید، با فلگ‌ها روشن: `ACTION_ASK` از early-return ِ skip عبور می‌کند و
    به شاخهٔ is_stuck می‌رسد ⇒ کارِ BLOCKED با سؤالِ فارسی در 🎨."""
    _clear_flags()
    os.environ["OCTOPUS_LEAD_FA_VOCAB"] = "1"
    os.environ["OCTOPUS_LEAD_ASK_WHEN_UNSCOREABLE"] = "1"
    before = len(_blocked())
    label, out, st = _process(_fa_lead())
    assert label == "stuck", f"لیدِ نافهمیده باید سؤال شود، گرفتم {label}"
    assert out["stuck"] == 1 and out.get("skip") is None, out
    assert st["stuck"], "لیدِ گیر باید در state ِ pipeline ثبت شود"
    blocked = _blocked()
    assert len(blocked) == before + 1, f"کارِ BLOCKED ساخته نشد: {blocked}"
    newest = blocked[-1]
    assert "🎨 لیدِ" in str(newest.get("text")), newest
    assert "آدرس" in str(newest.get("question")), \
        f"سؤالِ فارسی روی کارِ BLOCKED نیست: {newest.get('question')}"


def t_j_known_garbage_still_never_becomes_an_owner_question():
    """قرینهٔ تستِ بالا: با همان فلگ‌های روشن، آشغالِ hard-skip هنوز skip است —
    یعنی پچ درِ سؤال را برای همه باز نکرده، فقط برای «نفهمیدم»."""
    _clear_flags()
    os.environ["OCTOPUS_LEAD_FA_VOCAB"] = "1"
    os.environ["OCTOPUS_LEAD_ASK_WHEN_UNSCOREABLE"] = "1"
    before = len(_blocked())
    label, out, _st = _process(_fa_lead("فقط تخریب بنا و قطع درخت، بدون آدرس"))
    assert label == "skip", f"آشغالِ شناخته‌شده باید skip بماند، گرفتم {label}"
    assert len(_blocked()) == before, "بودجهٔ سؤالِ مالک نباید خرجِ آشغال شود"


# ─── آستانه به‌عنوان مقدارِ کانفیگ ─────────────────────────────────────────────
def t_k_thresholds_are_config_values_with_documented_defaults():
    _clear_flags()
    a = lead_scorer.DEFAULT_CONFIG["actions"]
    # پیش‌فرض عمداً دست‌نخورده مانده — خط‌کش روی نتیجه تنظیم نشده.
    assert a["draft_threshold"] == 70 and a["save_threshold"] == 45, a
    assert lead_scorer._threshold(a, "draft_threshold", "OCTOPUS_LEAD_DRAFT_THRESHOLD") == 70
    # override ِ صریحِ مالک محترم است…
    os.environ["OCTOPUS_LEAD_DRAFT_THRESHOLD"] = "65"
    assert lead_scorer._threshold(a, "draft_threshold", "OCTOPUS_LEAD_DRAFT_THRESHOLD") == 65
    os.environ["OCTOPUS_LEAD_DIRECT_RESIDENTIAL"] = "1"
    no_geo = {"source": "direct_enquiry", "cost_of_development": 4200,
              "description": "Exterior repainting of residential property, fence and deck."}
    assert _snap(no_geo)[1:3] == (68, "draft"), _snap(no_geo)   # ۶۸ ≥ ۶۵
    # …ولی مقدارِ خراب هرگز آستانه را نمی‌شکند (fail-safe به پیش‌فرضِ کانفیگ)
    os.environ["OCTOPUS_LEAD_DRAFT_THRESHOLD"] = "شصت‌وپنج"
    assert lead_scorer._threshold(a, "draft_threshold", "OCTOPUS_LEAD_DRAFT_THRESHOLD") == 70
    assert _snap(no_geo)[1:3] == (68, "save"), _snap(no_geo)
    _clear_flags()


CHECKS = [
    ("A فلگ خاموش = رفتارِ امروز (انگلیسی و فارسی)",
     t_a_flags_off_is_todays_behaviour_for_english_and_farsi),
    ("A مسیرِ انگلیسی با فلگِ فارسی هم دست‌نخورده",
     t_b_english_path_is_identical_even_with_the_farsi_flag_on),
    ("B استعلامِ فارسی دیگر صفر نمی‌گیرد", t_c_a_real_farsi_enquiry_now_scores_above_zero),
    ("B فارسی به دستهٔ کارِ واقعیِ مالک می‌رسد",
     t_d_farsi_enquiry_routes_to_the_owners_real_category),
    ("C نرمال‌سازی: ZWNJ/ارقام/ي‌ك/اعراب", t_e_normalisation_zwnj_digits_arabic_letters_and_harakat),
    ("D مرزِ کلمه — بدونِ مثبتِ کاذب", t_f_farsi_matching_has_word_boundaries_not_blind_substrings),
    ("E نافهمیده ⇒ ask، آشغال ⇒ skip", t_g_unscoreable_becomes_ask_and_known_garbage_stays_skip),
    ("F دندان: پیش از پچ، لیدِ گیر بی‌صدا دور ریخته می‌شد",
     t_h_teeth_pre_fix_the_pipeline_drops_a_lead_it_knows_is_stuck),
    ("F حالا همان لید به مالک می‌رسد (کارِ BLOCKED + سؤالِ فارسی)",
     t_i_an_unscoreable_lead_now_reaches_the_owner_as_a_question),
    ("F آشغال هنوز سؤال نمی‌شود", t_j_known_garbage_still_never_becomes_an_owner_question),
    ("G آستانه = مقدارِ کانفیگ با پیش‌فرضِ مستند",
     t_k_thresholds_are_config_values_with_documented_defaults),
]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} pass، {failed} fail — "
          "test_lead_scorer_farsi")
    sys.exit(1 if failed else 0)
