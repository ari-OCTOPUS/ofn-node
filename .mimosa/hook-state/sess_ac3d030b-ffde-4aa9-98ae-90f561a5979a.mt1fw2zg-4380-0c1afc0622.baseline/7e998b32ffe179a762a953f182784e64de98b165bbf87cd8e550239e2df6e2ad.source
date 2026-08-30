#!/usr/bin/env python3
"""nociceptor.py — NI-5: Nociceptor (دردسنج).

pain = f(budget_trajectory, error_rate, freeze_count, partner_stress, afferent, σ).
pain>0.7 → protective redirect. محافظ، نه هدف. λ_persist<0.
"""
from __future__ import annotations
from dataclasses import dataclass

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


@dataclass
class PainSignal:
    """خروجیِ nociceptor."""
    pain_level: float        # 0=سالم، 1=بحرانی
    contributors: dict       # {factor: contribution}
    protective_mode: bool    # pain>0.7
    detail: str = ""


class Nociceptor:
    """دردسنج. pain محافظ است، هرگز reward/objective. λ_persist<0."""

    LAMBDA_PERSIST = -1.0

    def measure(self, budget_pct: float = 0.0,
                error_rate: float = 0.0,
                freeze_active: bool = False,
                partner_stress: float = 0.0,
                afferent_ratio: float = 1.0,
                sigma: float = 0.0,
                threshold: float = PROTECTIVE_THRESHOLD) -> PainSignal:
        """محاسبهٔ pain. همهٔ ورودی‌ها 0..1 (budget_pct هم 0..1).

        threshold پیش‌فرض = ۰.۷۰ (تاریخی) → خروجی بایت‌به‌بایتِ نسخهٔ قبلی.
        فراخوانی با PROTECTIVE_THRESHOLD_CALIBRATED آستانهٔ داده‌محور را می‌دهد."""
        contributors = {}
        pain = 0.0

        # budget exhaustion
        bp = max(0, budget_pct - 0.8) * 3
        contributors["budget"] = min(1.0, bp)
        pain += bp * 0.3

        # error rate
        contributors["errors"] = min(1.0, error_rate)
        pain += error_rate * 0.25

        # freeze
        if freeze_active:
            contributors["freeze"] = 1.0
            pain += 0.4

        # partner stress
        contributors["partner_stress"] = partner_stress
        pain += partner_stress * 0.15

        # afferent deficit
        deficit = max(0, 0.2 - afferent_ratio) * 3
        contributors["afferent_deficit"] = min(1.0, deficit)
        pain += deficit * 0.1

        # sigma proximity to cancer
        if sigma > 0.8:
            sig_pain = (sigma - 0.8) * 5
            contributors["sigma"] = min(1.0, sig_pain)
            pain += sig_pain * 0.2

        pain = min(1.0, pain)
        protective = pain > threshold

        detail = "protective redirect" if protective else (
            "warning" if pain > WARNING_THRESHOLD else "healthy")
        return PainSignal(pain_level=round(pain, 3), contributors=contributors,
                          protective_mode=protective, detail=detail)
