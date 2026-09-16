#!/usr/bin/env python3
"""nociceptor.py — NI-5: Nociceptor (دردسنج).

pain = f(budget_trajectory, error_rate, freeze_count, partner_stress, afferent, σ).
pain>0.7 → protective redirect. محافظ، نه هدف. λ_persist<0.
"""
from __future__ import annotations
from dataclasses import dataclass, field

# ── کالیبراسیونِ آستانهٔ محافظ (۲۰۲۶-۰۷-۲۸) ─────────────────────────────────────
# توزیعِ *واقعیِ* درد، از ۲۲۱۴ تیکِ ثبت‌شده در
# `_ops/state/neural/effect-shadow.jsonl` (۲۰۲۶-۰۷-۲۷T۱۶:۰۴ → ۲۰۲۶-۰۷-۲۸T۲۱:۴۰):
#
#     min ۰.۱۰۲ · میانه ۰.۱۲۵ · میانگین ۰.۱۲۳۸ · σ ۰.۰۰۸۵۷ · بیشینه ۰.۱۵۰
#     صدکِ۹۵ ۰.۱۳۰ · صدکِ۹۹ ۰.۱۵۰ · صفر تیک از ۲۲۱۴ بالای ۰.۲۰
#     ۱۶۲۹ تیک (۷۳.۶٪) دقیقاً ۰.۱۲۵؛ کلِ توزیع فقط ۱۲ مقدارِ یکتا دارد
#     protective=false روی ۲۲۱۴/۲۲۱۴
#
# و تجزیهٔ همان توزیع (اندازه‌گیری، نه حدس): هر ۱۲ مقدار دقیقاً `۰.۲۵ × error_rate`
# است — یعنی ۵ ورودی از ۶ ورودیِ درد روی ۲۲۱۴/۲۲۱۴ تیک **صفر** بوده‌اند:
#   · budget_pct  بیشینهٔ مشاهده‌شده ۰.۰۰۰۷۲ (شرطِ ترم `>۰.۸`) → صفر
#   · sigma       ساختاراً ۰.۰ (نسبتِ replication؛ ۱۰۴۹ نمونه در ۱۶ روز، همه صفر)
#   · partner_stress  **هیچ‌وقت پاس داده نمی‌شود** — نه organism.py نه brain_worker.py
#     آن را در `sensory` نمی‌گذارند → همیشه روی پیش‌فرضِ ۰.۰
#   · afferent_ratio هرگز زیر ۰.۲ نرفت → deficit صفر
#   · freeze (rhythm=RED) در این پنجره رخ نداد
#
# پس با سیم‌کشیِ امروز، سقفِ *دست‌یافتنیِ* درد ۰.۷۱ است (errors=۱.۰ **و** RED
# **و** afferent=۰.۰ هم‌زمان) و آستانهٔ ۰.۷۰ یعنی ترمز فقط در بالاترین ۱.۴٪ از
# دامنهٔ ممکن باز می‌شود. بزرگ‌ترین ترکیبِ دو-نقصی (RED + خطای ۱۰۰٪) ۰.۶۵ است —
# هنوز زیرِ آستانه. ترمز عملاً به هم‌زمانیِ سه نقصِ حداکثری گره خورده.
#
# آستانهٔ کالیبره از سه قیدِ داده‌محور بیرون می‌آید (پنجرهٔ مجاز: ۰.۲۵ < θ < ۰.۴۰):
#   C1 — پوششِ سالم: θ > بیشینهٔ مشاهده‌شده ۰.۱۵۰ (با ۳σ: ۰.۱۷۶) → صفر halt کاذب
#   C2 — حساسیت:    θ < ۰.۴۰ = بزرگ‌ترین نقصِ ساختاریِ تک‌عاملی (freeze/RED)
#   C3 — ضدِ نویز:  θ > ۰.۲۵ = سقفِ کانالِ error_rate به‌تنهایی. این کانال
#        `organism_stress` است (شمارندهٔ هشدار، پرنویزترین ورودی و تنها ورودیِ
#        همیشه-غیرصفر)؛ یک کانالِ نویزی به‌تنهایی نباید ترمز بکشد.
# θ = ۰.۳۵ → ۲۶σ بالاتر از میانگینِ سالم، ۰.۱۰ حاشیه بالای سقفِ نویز، و RED
# به‌تنهایی ترمز را می‌کشد. چون ۰.۳۵ < ۰.۷۰، مجموعهٔ شلیک‌ها **ابرمجموعهٔ** امروز
# است — این تغییر هرگز کم‌محافظ‌تر نیست (ناوردیِ آزموده‌شده در
# `_ops/tests/test_pain_calibration.py::t_calibrated_never_less_protected`).
#
# پیش‌فرضِ این ماژول همان ۰.۷۰ی تاریخی می‌ماند؛ انتخابِ آستانه در
# `wiring.protective_override` و پشتِ فلگِ OCTOPUS_PAIN_THRESHOLD_CALIBRATED است
# (پیش‌فرض خاموش، رفتار بایت‌به‌بایتِ امروز).
PROTECTIVE_THRESHOLD = 0.70              # تاریخی — پیش‌فرض، بدونِ تغییر
PROTECTIVE_THRESHOLD_CALIBRATED = 0.35   # داده‌محور (C1/C2/C3 بالا)
WARNING_THRESHOLD = 0.40                 # مرزِ «هشدار»ِ خودِ همین ماژول (detail)

# انبارهٔ اعدادِ اندازه‌گیری‌شده — تنها منبعِ حقیقتِ کالیبراسیون (تست به آن pin است)
HEALTHY_ENVELOPE = {
    "n_ticks": 2214,
    "source": "_ops/state/neural/effect-shadow.jsonl",
    "window": "2026-07-27T16:04:35..2026-07-28T21:40:08",
    "min": 0.102, "mean": 0.1238, "median": 0.125, "sd": 0.00857,
    "p95": 0.130, "p99": 0.150, "max": 0.150,
    "n_above_0_20": 0, "n_protective": 0,
    "attainable_max_as_wired": 0.71,     # errors=1.0 + RED + afferent=0.0
    "noisy_channel_ceiling": 0.25,       # error_rate به‌تنهایی
    "structural_single_fault_max": 0.40,  # freeze/RED به‌تنهایی
}

# ── سرشماریِ ورودی‌ها (WS-2، ۲۰۲۶-۰۸-۰۱) ──────────────────────────────────────
# نامِ هر شش ترمِ fusion، به همان کلیدی که `contributors` استفاده می‌کند.
# ترتیب = ترتیبِ جمع‌شدن در `measure`.
PAIN_INPUTS = ("budget", "errors", "freeze",
               "partner_stress", "afferent_deficit", "sigma")

# وزنِ هر ترم (ضریبی که به pain اضافه می‌شود). آینهٔ `measure` — تست drift را می‌گیرد.
PAIN_WEIGHTS = {"budget": 0.30, "errors": 0.25, "freeze": 0.40,
                "partner_stress": 0.15, "afferent_deficit": 0.10, "sigma": 0.20}

# ── چرا این سرشماری لازم شد ───────────────────────────────────────────────────
# `contributors` از روزِ اول دو کلید را **حذف** می‌کند وقتی ترمشان خاموش است
# (`freeze` فقط اگر freeze_active، `sigma` فقط اگر sigma>0.8). یعنی «صفر بود» و
# «اندازه‌گیری نشد» در همان یک dict از هم قابل‌تفکیک نیستند — و `neural_driver`
# هم اصلاً `contributors` را برنمی‌گرداند، پس `effect-shadow.jsonl` فقط اسکالرِ
# fuse‌شده را دارد. نتیجه: کشفِ «۵ ورودی از ۶ صفرند» فقط با بازسازیِ آفلاینِ
# ۸۵۱۱ ردیف (تقسیم بر ۰.۲۵) ممکن شد، نه با خواندنِ لاگ.
#
# اندازه‌گیریِ ۲۰۲۶-۰۸-۰۱ روی `_ops/state/neural/effect-shadow.jsonl`
# (۸۵۱۱ ردیف، ۲۰۲۶-۰۷-۲۷T۱۶:۰۴:۳۵ → ۲۰۲۶-۰۸-۰۱T۱۰:۲۵:۱۸؛ فایل زنده است):
#   · ۴۵ مقدارِ یکتای درد، بازهٔ [۰.۰۴۳ ، ۰.۱۵۲]، protective=false روی ۸۵۱۱/۸۵۱۱
#   · هر ۴۵ مقدار دقیقاً `۰.۲۵ × error_rate` → پنج ترمِ دیگر صفرِ **دقیق**
#   · شاهدِ مستقلِ هم‌زمان (۱۰:۲۶): cortex/stress-latest.json organism_stress=۰.۴۱
#     و تازه‌ترین ردیفِ سایه pain=۰.۱۰۲ = round(۰.۲۵×۰.۴۱, ۳). صفرِ باقی، قطعی.
#   · از واژگانِ ۸تاییِ سیگنال فقط دو نام آتش کرد: errors_high (۶۹۸۸)،
#     rhythm_amber (۲۲۰). `rhythm_red` صفر → ترمِ freeze هرگز فعال نشد.
INPUT_CENSUS = {
    "budget": {
        "source": "organism.py:618 — usd(month.musd) / budgets.yaml:cap_monthly(30 AUD)",
        "observed_max": 0.00072,        # ژوئیه؛ ۰۸-۰۱ ماه چرخید → ۰.۰
        "gate": "budget_pct > 0.8",
        "why_zero": "wired-and-correct — خرجِ واقعی ~۰.۰۷٪ سقف است (LLMِ محلی، $۰). "
                    "ترم درست است ولی «سطح» را می‌سنجد نه «تراژکتوری»ی که docstring "
                    "ادعا می‌کند؛ زیرِ ۸۰٪ سقف دقیقاً صفر است، نه کم.",
        "verdict": "keep — واقعاً خاموش، نه خراب",
    },
    "errors": {
        "source": "organism.py:603 — state/cortex/stress-latest.json:organism_stress",
        "observed_max": 0.608,          # = ۰.۱۵۲ / ۰.۲۵
        "gate": "بدونِ گیت — خطی",
        "why_zero": "صفر نیست. تنها ورودیِ زنده؛ کلِ سیگنالِ درد از همین یکی می‌آید.",
        "verdict": "live",
    },
    "freeze": {
        "source": "organism.py:617 — rhythm.mode_color == 'RED'",
        "observed_max": 0.0,
        "gate": "mode_color == 'RED'",
        "why_zero": "wired-and-correct — در پنجره ۲۲۰ تیک AMBER و صفر تیک RED. "
                    "ترمِ رویدادِ نادر است، نه ترمِ مرده.",
        "verdict": "keep — واقعاً خاموش، نه خراب",
    },
    "partner_stress": {
        "source": "هیچ. `sensory` در organism.py:635 فقط afferent_ratio و error_rate "
                  "دارد؛ NEURAL_PAYLOAD_CONTRACT هم این کلید را ندارد.",
        "observed_max": 0.0,
        "gate": "بدونِ گیت — خطی",
        "why_zero": "no-producer — هیچ حسگری این کمیت را تولید نمی‌کند. تنها هم‌نامش "
                    "`neural_driver.snapshot_to_brain_inputs` است که آن را `pain*0.8` "
                    "می‌سازد — یعنی **خروجیِ** خودِ درد. وصل‌کردنِ آن به ورودی حلقهٔ "
                    "بازخوردِ مثبت روی مسیرِ ترمز می‌سازد (pain += 0.12*pain).",
        "verdict": "REMOVE از fusion — کمیتِ خوداظهارِ انسانی است؛ جایش "
                   "ThinkingBrain.think_risk(partner_stress=...) است که مالک مقدارش را "
                   "می‌دهد، نه یک حلقهٔ تیکِ خودکار.",
    },
    "afferent_deficit": {
        "source": "organism.py:635 ← wiring.afferent_beat ← afferent/sensory_bus.status()",
        "observed_max": 0.0,
        "gate": "afferent_ratio < 0.2",
        "why_zero": "starved-sampler — `_last_afferent_ratio` در organism.py:489 با ۱.۰ "
                    "مقداردهی می‌شود و تنها به‌روزکننده‌اش `afferent_beat` است که "
                    "CHRONO_AFFERENT_EVERY_N_BEATS=1440 (~۲۴h) گیت شده. SensoryBus هم "
                    "in-memory است و هیچ‌جا persist نمی‌شود (صفر تطابق برای "
                    "\"afferent_ratio\" در کلِ _ops/state). یعنی آشکارسازِ گرسنگی خودش "
                    "گرسنه است — ۱.۰ یک پیش‌فرض است، نه یک اندازه‌گیری.",
        "verdict": "SHOULD BE NON-ZERO — ارزان‌ترین و کم‌ریسک‌ترین اصلاح",
    },
    "sigma": {
        "source": "organism.py:632 — state/replication-latest.json:sigma "
                  "(spawn_approved/parents = 0/1)",
        "observed_max": 0.0,
        "gate": "sigma > 0.8",
        "why_zero": "wrong-source — نامش σِ طیفی است ولی مقدارش نسبتِ replication است. "
                    "چون هیچ spawnی تأیید نشده، ساختاراً ۰.۰ می‌ماند و هیچ حالتِ "
                    "واقعیِ ارگانیسم بالای ۰.۸ نمی‌بردش. σِ واقعی در "
                    "doctor/spectral.py::estimate_sigma تولید می‌شود و هرگز وصل نشده.",
        "verdict": "SHOULD BE NON-ZERO — ولی repoint کردنِ منبع تغییرِ رفتارِ ایمنی "
                   "است و رأیِ صریحِ مالک می‌خواهد.",
    },
}


@dataclass
class PainSignal:
    """خروجیِ nociceptor."""
    pain_level: float        # 0=سالم، 1=بحرانی
    contributors: dict       # {factor: contribution}
    protective_mode: bool    # pain>0.7
    detail: str = ""
    # ── WS-2 (۲۰۲۶-۰۸-۰۱): تفکیکِ وزن‌دارِ درد. پیش‌فرض None = مسیرِ امروز.
    # `compare=False, repr=False` تا با breakdown خاموش، حتی == و repr هم
    # بایت‌به‌بایتِ نسخهٔ قبل بمانند.
    contributions: dict | None = field(default=None, compare=False, repr=False)
    zero_terms: tuple = field(default=(), compare=False, repr=False)


class Nociceptor:
    """دردسنج. pain محافظ است، هرگز reward/objective. λ_persist<0."""

    LAMBDA_PERSIST = -1.0

    def measure(self, budget_pct: float = 0.0,
                error_rate: float = 0.0,
                freeze_active: bool = False,
                partner_stress: float = 0.0,
                afferent_ratio: float = 1.0,
                sigma: float = 0.0,
                threshold: float = PROTECTIVE_THRESHOLD,
                breakdown: bool = False) -> PainSignal:
        """محاسبهٔ pain. همهٔ ورودی‌ها 0..1 (budget_pct هم 0..1).

        threshold پیش‌فرض = ۰.۷۰ (تاریخی) → خروجی بایت‌به‌بایتِ نسخهٔ قبلی.
        فراخوانی با PROTECTIVE_THRESHOLD_CALIBRATED آستانهٔ داده‌محور را می‌دهد.

        breakdown=False (پیش‌فرض) → `contributions`/`zero_terms` دست‌نخورده
        (None و ()). هیچ عبارتِ حسابیِ این تابع با breakdown عوض نمی‌شود؛ فقط
        همان مقادیرِ اضافه‌شده در یک dictِ کنارْ ثبت می‌شوند. بنابراین آستانه،
        pain_level، contributors و protective_mode در هر دو حالت یکی‌اند.
        ⚠️ این متد آستانه را **نمی‌خواند و نمی‌نویسد** — مسیرِ ترمز دست‌نخورده."""
        contributors = {}
        # هر شش ترم همیشه حاضر — تفاوتِ «صفر بود» با «کلید نیست» همین‌جا بسته می‌شود.
        added = dict.fromkeys(PAIN_INPUTS, 0.0)
        pain = 0.0

        # budget exhaustion
        bp = max(0, budget_pct - 0.8) * 3
        contributors["budget"] = min(1.0, bp)
        pain += bp * 0.3
        added["budget"] = bp * 0.3

        # error rate
        contributors["errors"] = min(1.0, error_rate)
        pain += error_rate * 0.25
        added["errors"] = error_rate * 0.25

        # freeze
        if freeze_active:
            contributors["freeze"] = 1.0
            pain += 0.4
            added["freeze"] = 0.4

        # partner stress
        contributors["partner_stress"] = partner_stress
        pain += partner_stress * 0.15
        added["partner_stress"] = partner_stress * 0.15

        # afferent deficit
        deficit = max(0, 0.2 - afferent_ratio) * 3
        contributors["afferent_deficit"] = min(1.0, deficit)
        pain += deficit * 0.1
        added["afferent_deficit"] = deficit * 0.1

        # sigma proximity to cancer
        if sigma > 0.8:
            sig_pain = (sigma - 0.8) * 5
            contributors["sigma"] = min(1.0, sig_pain)
            pain += sig_pain * 0.2
            added["sigma"] = sig_pain * 0.2

        pain = min(1.0, pain)
        protective = pain > threshold

        detail = "protective redirect" if protective else (
            "warning" if pain > WARNING_THRESHOLD else "healthy")
        signal = PainSignal(pain_level=round(pain, 3), contributors=contributors,
                            protective_mode=protective, detail=detail)
        if breakdown:
            signal.contributions = {k: round(added[k], 6) for k in PAIN_INPUTS}
            signal.zero_terms = tuple(k for k in PAIN_INPUTS if added[k] == 0.0)
        return signal
