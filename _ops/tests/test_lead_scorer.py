#!/usr/bin/env python3
"""تستِ مرحلهٔ ۱ نقشهٔ لید (2026-07-15): پورتِ موتورِ امتیازدهیِ لیدِ نقاشی.

مقادیرِ انتظاری عمداً به painter_lead_scoring.yamlِ اصلی پین شده‌اند
(_launchpad/second-brain-live/painting-bot) — driftِ خاموشِ کانفیگِ inline لو می‌رود:
  strata dream lead → 55+18+10+10+8 = 101 → clamp 100 → draft
  commercial fitout → 40+18−15+8 = 51 → save
  demolition only   → hard filter → 0 → skip
$0 آفلاین، stdlib-only، بدونِ I/O.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("lead-scorer")

_LEGS = harness.REAL_VAULT / "_ops" / "legs"
if str(_LEGS) not in sys.path:
    sys.path.insert(0, str(_LEGS))
import lead_scorer  # noqa: E402

STRATA_DREAM = {
    "source": "planning_alerts",
    "description": ("Remedial works to common property including rendering and "
                    "repainting of external facade and balcony balustrade "
                    "replacement to residential flat building of 24 units."),
    "address": "12 Wattle Crescent, Pyrmont NSW 2009",
    "cost_of_development": 820000,
    "lat": -33.8700, "lng": 151.1950,
}
COMMERCIAL_FITOUT = {
    "source": "planning_alerts",
    "description": ("Change of use to a retail premises, including internal "
                    "fitout, external facade works, lighting and business "
                    "identification signage."),
    "address": "106 King Street Sydney NSW 2000",
    "cost_of_development": None,
    "lat": -33.8675, "lng": 151.2070,
}
DEMOLITION_NOISE = {
    "source": "planning_alerts",
    "description": "Demolition only of existing dwelling house.",
    "address": "5 Quiet St, Sydney NSW 2000",
    "cost_of_development": 60000,
    "lat": -33.87, "lng": 151.21,
}


def t_a_strata_dream_is_draft():
    """لیدِ رویاییِ strata → دستهٔ strata_remedial، امتیازِ سقف‌خورده ۱۰۰، action=draft."""
    sc = lead_scorer.score_lead(STRATA_DREAM)
    assert sc.category == "strata_remedial", sc
    assert sc.score == 100, sc                       # 55+18+10+10+8=101 → clamp 100
    assert sc.action == "draft", sc
    assert any("base 55" in r for r in sc.reasons), sc.reasons


def t_b_commercial_fitout_is_save():
    """fitout با پرچمِ قرمزِ signage → 40+18−15+8=51 → save (بینِ آستانه‌ها)."""
    sc = lead_scorer.score_lead(COMMERCIAL_FITOUT)
    assert sc.category == "commercial_fitout", sc
    assert sc.score == 51, sc
    assert sc.action == "save", sc
    assert any("red_flags" in r for r in sc.reasons), sc.reasons
    assert any("value unknown" in r for r in sc.reasons), sc.reasons


def t_c_demolition_hard_skip():
    """فیلترِ سخت: «demolition only» → امتیاز ۰، action=skip، دستهٔ filtered."""
    sc = lead_scorer.score_lead(DEMOLITION_NOISE)
    assert sc.category == "filtered" and sc.score == 0 and sc.action == "skip", sc
    assert "hard-skip" in sc.reasons[0], sc.reasons


def t_d_thresholds_pinned_to_yaml():
    """پینِ ضدِ drift: آستانه‌ها/وزن‌های کلیدی باید عینِ yamlِ اصلی بمانند."""
    c = lead_scorer.DEFAULT_CONFIG
    assert c["actions"]["draft_threshold"] == 70
    assert c["actions"]["save_threshold"] == 45
    assert c["categories"]["strata_remedial"]["base"] == 55
    assert c["signals"]["paint_scope"]["weight"] == 18
    assert c["signals"]["red_flags"]["weight"] == -15
    assert c["geo"] == {"in_radius_bonus": 8, "out_of_radius_penalty": -20}
    assert c["hard_skip"]["single_dwelling_value_floor"] == 250000
    assert c["category_priority"][0] == "strata_remedial"   # strata عمداً اول


def t_e_out_of_radius_penalised():
    """خارج از شعاعِ ۴۰km → جریمهٔ −۲۰ (نیوکاسل ~۱۱۵km)."""
    far = dict(STRATA_DREAM, lat=-32.9283, lng=151.7817,
               address="1 Hunter St, Newcastle NSW 2300")
    sc = lead_scorer.score_lead(far)
    assert sc.score == 73, sc                        # 55+18+10+10−20=73 (هنوز draft)
    assert any("-20" in r for r in sc.reasons), sc.reasons


def t_f_single_dwelling_value_floor():
    """خانهٔ تک‌واحدیِ زیرِ کف ۲۵۰k با هزینهٔ معلوم → skip؛ هزینهٔ نامعلوم → skip نمی‌شود."""
    cheap = {"description": "Alterations to existing dwelling house including repaint.",
             "cost_of_development": 80000}
    sc = lead_scorer.score_lead(cheap)
    assert sc.action == "skip" and "single dwelling" in sc.reasons[0], sc
    unknown = dict(cheap, cost_of_development=None)
    sc2 = lead_scorer.score_lead(unknown)
    assert sc2.category != "filtered", sc2           # کفِ ارزش فقط با هزینهٔ KNOWN


if __name__ == "__main__":
    for f in (t_a_strata_dream_is_draft, t_b_commercial_fitout_is_save,
              t_c_demolition_hard_skip, t_d_thresholds_pinned_to_yaml,
              t_e_out_of_radius_penalised, t_f_single_dwelling_value_floor):
        f()
        print("ok", f.__name__)
    print("PASS test_lead_scorer")
