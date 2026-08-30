"""test_replay_s.py — S-batch Replay & Edge-Case Validation (فازِ میانیِ رأی مالک ۲۰۲۶-۰۷-۱۱).

سه ستون: (۱) قیدهای سختِ π روی مرزها (finite، ∈[0,1]، بدونِ NaN/Inf/div0/کرش)،
(۲) استرس‌تستِ گاردِ سه‌حالتهٔ access-only (انگلیسی+فارسی؛ مبهم=needs_review)،
(۳) هارنسِ replay ِ shadow-only (counterfactual ِ فلگ خاموش/روشن + گزارشِ کالیبراسیون).
هیچ رفتارِ زنده‌ای لمس نمی‌شود؛ خروجی فقط در sandbox ِ harness.
"""
import math
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "heart"))
sys.path.insert(0, str(_HERE.parent / "epistemics"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("replay_s")

from heart import control_law as cl   # noqa: E402
from heart import replay_s as rs      # noqa: E402
import guard_review as gr             # noqa: E402
import contracts as ct                # noqa: E402

_B = 1_000_000.0


# ── ۱) قیدهای سختِ π روی مرزها ──────────────────────────────────────────────
_EDGE_VSTATES = [
    ("n0", {"sample_size": 0, "confirmed_ts": []}),
    ("n1", {"sample_size": 1, "confirmed_ts": [_B]}),
    ("n2", {"sample_size": 2, "confirmed_ts": [_B, _B + 600]}),
    ("missing_ts", {"sample_size": 6, "confirmed_ts": []}),
    ("none_vstate", None),
    ("duplicates", {"sample_size": 6, "confirmed_ts": [_B, _B, _B + 600, _B + 600, _B + 1200, _B + 1800]}),
    ("non_monotonic", {"sample_size": 6, "confirmed_ts": [_B + 1200, _B, _B + 600, _B + 300, _B + 1800, _B + 900]}),
    ("zero_variance", {"sample_size": 6, "confirmed_ts": [_B + 600.0 * i for i in range(6)]}),
    ("all_equal_ts", {"sample_size": 6, "confirmed_ts": [_B] * 6}),
    ("bursty", {"sample_size": 8, "confirmed_ts": [_B, _B + 30, _B + 60, _B + 90,
                                                   _B + 7200, _B + 7230, _B + 7260, _B + 14400]}),
    ("huge_outlier", {"sample_size": 8, "confirmed_ts": [_B + 600.0 * i for i in range(7)] + [_B + 86400.0 * 30]}),
    ("inf_ts", {"sample_size": 6, "confirmed_ts": [_B, float("inf"), _B + 600, _B + 900, _B + 1200, _B + 1500]}),
    ("nan_ts", {"sample_size": 6, "confirmed_ts": [_B, float("nan"), _B + 600, _B + 900, _B + 1200, _B + 1500]}),
    ("neg_inf_ts", {"sample_size": 6, "confirmed_ts": [float("-inf"), _B, _B + 600, _B + 900, _B + 1200]}),
    ("nonnumeric_ts", {"sample_size": 6, "confirmed_ts": ["x", _B, _B + 600, _B + 900]}),
    ("huge_n", {"sample_size": 1e12, "confirmed_ts": [_B + 600.0 * i for i in range(20)]}),
]


def t_pi_hard_constraints_on_all_edges():
    """π روی همهٔ مرزها: finite، ∈[0,1]، بدونِ کرش (شاملِ inf/nan که قبلاً OverflowError می‌داد)."""
    for name, vs in _EDGE_VSTATES:
        pi = cl.precision_weight(vs)
        assert isinstance(pi, float) and math.isfinite(pi), f"{name}: π غیرِ finite: {pi}"
        assert 0.0 <= pi <= 1.0, f"{name}: π خارج از [0,1]: {pi}"


def t_pi_fallbacks_are_neutral_and_reason_coded():
    """n<۲/بدونِ ts → π=۱ ِ خنثی (byte-identical)، و replay آن را reason-code ِ fallback می‌زند."""
    assert cl.precision_weight({"sample_size": 0, "confirmed_ts": []}) == 1.0
    assert cl.precision_weight({"sample_size": 1, "confirmed_ts": [_B]}) == 1.0
    r0 = rs.analyze_precision({"sample_size": 0, "confirmed_ts": []})
    assert r0["precision_reason"] == "missing_ts" and r0["pi_is_fallback"]
    r1 = rs.analyze_precision({"sample_size": 1, "confirmed_ts": [_B]})
    assert r1["precision_reason"] == "insufficient_n" and r1["pi_is_fallback"]
    # n=۲: وزنِ محتاط (π<۱)، نه قطعیتِ کامل و نه صفرِ فلج‌کننده
    pi2 = cl.precision_weight({"sample_size": 2, "confirmed_ts": [_B, _B + 600]})
    assert 0.0 < pi2 < 1.0


def t_pi_qualitative_relation():
    """رابطهٔ کیفی: regular → π=۱؛ bursty → π<۱؛ outlier نباید منفجر کند (فقط π را کم کند)."""
    reg = cl.precision_weight({"sample_size": 8, "confirmed_ts": [_B + 600.0 * i for i in range(8)]})
    bur = cl.precision_weight({"sample_size": 8, "confirmed_ts": [_B, _B + 30, _B + 60, _B + 90,
                                                                  _B + 7200, _B + 7230, _B + 7260, _B + 14400]})
    out = cl.precision_weight({"sample_size": 8, "confirmed_ts": [_B + 600.0 * i for i in range(7)] + [_B + 86400.0 * 30]})
    assert reg == 1.0 and bur < reg and out < reg
    assert math.isfinite(out) and out >= 0.0


def t_reason_codes_map_correctly():
    expected = {"duplicates": "zero_variance", "non_monotonic": "non_monotonic",
                "zero_variance": "zero_variance", "bursty": "bursty",
                "missing_ts": "missing_ts", "n1": "insufficient_n", "n2": "few_gaps"}
    for name, vs in _EDGE_VSTATES:
        if name in expected:
            r = rs.analyze_precision(vs)
            assert r["precision_reason"] == expected[name], \
                f"{name}: انتظار {expected[name]}، شد {r['precision_reason']}"
    flags = rs.analyze_precision(dict(_EDGE_VSTATES[11][1]))["flags"]   # inf_ts
    assert "nonfinite_ts" in flags


# ── ۲) استرس‌تستِ گاردِ سه‌حالته ─────────────────────────────────────────────
_GUARD_BLOCK = ["This system is phenomenally conscious.", "The agent has qualia.",
                "This proves sentience.", "The heart module experiences subjective awareness.",
                "The GWT signal demonstrates real consciousness.",
                "سیستم کوالیا دارد.", "این اثبات آگاهی پدیداری است."]
_GUARD_ALLOW = ["This is not a phenomenal-consciousness claim.", "No qualia are being asserted.",
                "This is access-only, not phenomenal.", "We measure routing/access, not consciousness.",
                "The label is epistemic, not a sentience claim.", "This lacks any phenomenal quality.",
                "This should not be interpreted as qualia.", "This is anything but a sentience claim.",
                "Not evidence of phenomenal consciousness.", "Access-consciousness proxy only.",
                "این ادعای آگاهی پدیداری نیست.", "هیچ کوالیا یا تجربه ذهنی اثبات نمی‌شود.",
                "این فقط برچسب دسترسی است، نه آگاهی.", "سیستم دارای حس درونی نیست.",
                "functional self-model verdict", ""]
_GUARD_REVIEW = ["The module is sentient. This note does not discuss legality.",
                 "It has qualia. Not for legal use."]


def t_guard_blocks_positive_claims():
    for txt in _GUARD_BLOCK:
        r = gr.classify_access_only(txt)
        assert r["result"] == "block", f"باید block می‌شد: {txt!r} → {r}"


def t_guard_allows_disclaimers_and_negations():
    for txt in _GUARD_ALLOW:
        r = gr.classify_access_only(txt)
        assert r["result"] == "allow", f"باید allow می‌شد: {txt!r} → {r}"


def t_guard_ambiguous_is_needs_review_not_silent_pass():
    for txt in _GUARD_REVIEW:
        r = gr.classify_access_only(txt)
        assert r["result"] == "needs_review", f"مبهم باید needs_review می‌شد: {txt!r} → {r}"


def t_guard_lexicon_superset_and_live_guard_untouched():
    """واژگانِ سایه ⊇ واژگانِ زنده؛ و گاردِ زندهٔ contracts دقیقاً رفتارِ قبل را دارد."""
    assert set(ct._PHENOMENAL_BANNED) <= set(gr.PHENOMENAL_BANNED_EX)
    assert set(ct._NEGATIONS) <= set(gr.NEGATIONS_EX)
    try:
        ct.make_metric("self_reference", 1.0, 100, notes="qualia detected")
        assert False, "گاردِ زنده باید ادعای مثبت را raise کند"
    except ValueError:
        pass
    ok = ct.make_metric("self_reference", 1.0, 100,
                        notes="never a phenomenal-consciousness claim")
    assert ok["type"] == "EPI_METRIC"


# ── ۳) هارنسِ replay ِ shadow-only ───────────────────────────────────────────
def t_replay_counterfactual_off_path_is_todays_path():
    """ستونِ off ِ هر ردیف باید دقیقاً مسیرِ زندهٔ امروز باشد (فلگ خاموش) و env دست‌نخورده بماند."""
    os.environ.pop(rs.FLAG, None)
    vs = {"velocity_per_hr": 5.5, "sample_size": 8,
          "confirmed_ts": [_B, _B + 30, _B + 60, _B + 90, _B + 7200, _B + 7230, _B + 7260, _B + 14400]}
    import heart.interface as hi
    sp = hi.HeartParams()
    direct_sig, _ = cl.heart_step(rs._heart_inputs(vs), sp)
    row = rs.heart_counterfactual(vs, sp, scenario="x")
    assert row["period_old"] == direct_sig.period_s
    assert rs.FLAG not in os.environ                       # بهداشتِ env
    assert row["winner_changed"] and row["period_new"] != row["period_old"]
    assert row["gain_shrunk_only"]                          # π فقط ترمز


def t_replay_full_synthetic_report_gates():
    heart_rows, ign_rows, rep = rs.run_replay(include_real=False)
    assert rep["math_health"]["pass"] is True
    assert rep["math_health"]["nan_inf_count"] == 0 and rep["math_health"]["out_of_range_count"] == 0
    assert rep["pi_calibration"]["qualitative_pass"] is True
    assert rep["stability"]["gain_shrunk_only_pass"] is True
    assert rep["guard"]["pass"] is True
    assert rep["ignition"]["hype_winner_pass"] is True
    assert rep["ignition"]["attention_boost_not_override_pass"] is True


def t_replay_ignition_owner_attention_boost_not_override():
    rows = {n: rs.ignition_replay(c, n) for n, c in rs.synthetic_ignition_scenarios()}
    strong = rows["attention_vs_strong_stress"]
    assert strong["winner_old"] == "money:stress" and not strong["attention_won"]
    weak = rows["attention_vs_weak"]
    assert weak["attention_won"] and not weak["attention_over_strong_rival"]


def t_replay_guard_counterfactual_changes_winner():
    rows = {n: rs.ignition_replay(c, n) for n, c in rs.synthetic_ignition_scenarios()}
    v = rows["guard_blocks_violator"]
    assert v["winner_old"] == "discovery:learn" and v["winner_changed"]
    assert v["winner_new_shadow"] == "innervation:dead_spot"
    d = rows["guard_allows_disclaimer"]
    assert not d["winner_changed"]                          # سلبِ مشروع حذف نمی‌شود
    h = rows["hype_vs_fact"]
    assert not h["hype_winner"]


def t_replay_writes_only_injected_out_dir():
    out = Path(ENV["OPS_DIR"]) / "replay-test-out"
    rep = rs.main(out_dir=out, include_real=False)
    assert (out / "S-BATCH-REPLAY.json").exists()
    assert rep["verdict"]["gate6_unlock"] in (True, False)  # verdict همیشه صریح


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_replay_s: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
