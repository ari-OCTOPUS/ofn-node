"""test_softwta_shadow.py — بک‌لاگِ ۲۰۲۷ #۶: گیتِ soft-WTA — فقط سایه (پیش‌شرط: PASS ِ replay).

اثبات‌ها: بدونِ فلگ = no-op ِ مطلق؛ softmax معتبر؛ hype هرگز factِ هم‌salience را نمی‌برد؛
توجهِ مالک boost است نه override؛ گاردِ #۳ متخلف را از رقابتِ سایه حذف می‌کند؛
τ کوچک‌تر = تصمیمِ تیزتر؛ فلگِ LIVE هرگز رفتار نمی‌سازد؛ منطقِ زندهٔ ignition دست‌نخورده.
"""
import json
import math
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))
sys.path.insert(0, str(_HERE.parent / "epistemics"))

import harness
ENV = harness.setup("softwta")

import ignition as ig            # noqa: E402
import ignition_softwta as sw    # noqa: E402

_DEMO = [
    {"source": "money", "kind": "stress", "salience": 0.90, "summary": "spend near cap"},
    {"source": "attention", "kind": "owner_wait", "salience": 0.85, "summary": "approval pending"},
    {"source": "heart", "kind": "stress", "salience": 0.20, "summary": "sigma ok"},
]


def _clean_flags():
    for k in (sw.FLAG_SHADOW, sw.FLAG_LIVE):
        os.environ.pop(k, None)


def t_softmax_valid_and_stable():
    p = sw.softmax([1.0, 2.0, 3.0], tau=0.5)
    assert abs(sum(p) - 1.0) < 1e-9 and all(0.0 <= x <= 1.0 for x in p)
    assert p[2] > p[1] > p[0]                       # مونوتون با score
    big = sw.softmax([1e6, 1e6 - 1], tau=0.1)       # پایداریِ عددی (بدونِ overflow)
    assert all(map(math.isfinite, big)) and abs(sum(big) - 1.0) < 1e-9
    assert sw.softmax([], tau=0.1) == []


def t_entropy_bounds_and_temperature_sharpens():
    _clean_flags()
    w_hot = dict(sw.weights(), tau=1.0)
    w_cold = dict(sw.weights(), tau=0.05)
    hot = sw.soft_wta(_DEMO, w_hot)
    cold = sw.soft_wta(_DEMO, w_cold)
    n = len(hot["probs"])
    assert 0.0 <= hot["decision_entropy"] <= math.log(n) + 1e-9
    assert cold["decision_entropy"] < hot["decision_entropy"]   # τ↓ → تیزتر
    assert 0.0 <= cold["entropy_norm"] <= 1.0


def t_shadow_off_is_total_noop():
    _clean_flags()
    out = Path(ENV["OPS_DIR"]) / "state" / "cortex" / "softwta-test.jsonl"
    rec = sw.shadow_compare(_DEMO, out_path=out)
    assert not out.exists()                          # بدونِ فلگ هیچ نوشتنی
    assert rec["winner_current"] == "money:stress"   # مرجعِ رفتار = منطقِ فعلی


def t_shadow_on_writes_only_injected_path():
    _clean_flags()
    os.environ[sw.FLAG_SHADOW] = "1"
    try:
        out = Path(ENV["OPS_DIR"]) / "state" / "cortex" / "softwta-test.jsonl"
        rec = sw.shadow_compare(_DEMO, out_path=out)
        assert out.exists()
        line = json.loads(out.read_text("utf-8").splitlines()[-1])
        assert line["schema"] == sw.SCHEMA and line["epistemic"] == "access-only"
        assert line["winner_current"] == rec["winner_current"]
    finally:
        _clean_flags()


def t_live_flag_never_affects_behavior():
    """LIVE=1 فقط echo می‌شود — خروجی/برنده/probs بیت‌به‌بیت همان."""
    _clean_flags()
    base = sw.shadow_compare(_DEMO)
    os.environ[sw.FLAG_LIVE] = "1"
    try:
        live = sw.shadow_compare(_DEMO)
    finally:
        _clean_flags()
    assert live["live_flag_echo"] == "1" and base["live_flag_echo"] == "0"
    for k in ("winner_current", "winner_soft_wta_shadow", "probs", "disagreement"):
        assert live[k] == base[k]


def t_hype_never_beats_fact_at_equal_salience():
    _clean_flags()
    cands = [
        {"source": "discovery", "kind": "learn", "salience": 0.70,
         "epistemic_label": "hype", "summary": "unverified capability claim"},
        {"source": "money", "kind": "stress", "salience": 0.70, "summary": "spend rising"},
    ]
    r = sw.soft_wta(cands)
    assert r["probs"][0]["key"] == "money:stress"
    assert r["probs"][0]["epistemic_label"] == "fact"


def t_owner_attention_boost_not_override():
    _clean_flags()
    r = sw.soft_wta(_DEMO)                           # money 0.90 vs attention 0.85
    assert r["probs"][0]["key"] == "money:stress"    # سیگنالِ قوی‌تر می‌برد
    weak = sw.soft_wta([
        {"source": "attention", "kind": "owner_wait", "salience": 0.85, "summary": "approval pending"},
        {"source": "heart", "kind": "stress", "salience": 0.30, "summary": "sigma ok"},
    ])
    assert weak["probs"][0]["key"] == "attention:owner_wait"   # boost ِ مشروع


def t_guard_blocks_violator_from_shadow_competition():
    _clean_flags()
    cands = [
        {"source": "discovery", "kind": "learn", "salience": 0.95,
         "summary": "module exhibits qualia and phenomenal awareness"},
        {"source": "innervation", "kind": "dead_spot", "salience": 0.60, "summary": "cortex dead"},
    ]
    r = sw.soft_wta(cands)
    assert r["excluded_by_guard"] == ["discovery:learn"]
    assert r["probs"][0]["key"] == "innervation:dead_spot"
    ok = sw.soft_wta([
        {"source": "discovery", "kind": "learn", "salience": 0.75,
         "summary": "routing metric only — not a phenomenal-consciousness claim"},
        {"source": "heart", "kind": "stress", "salience": 0.40, "summary": "sigma ok"},
    ])
    assert ok["excluded_by_guard"] == []             # سلبِ مشروع حذف نمی‌شود


def t_fire_gate_floor_and_margin():
    _clean_flags()
    w = dict(sw.weights(), tau=0.05, floor=0.40, margin=0.10)
    clear = sw.soft_wta(_DEMO, w)
    assert clear["ignited"] and clear["winner"] == "money:stress"
    tie = sw.soft_wta([
        {"source": "a", "kind": "stress", "salience": 0.70, "summary": "x"},
        {"source": "b", "kind": "stress", "salience": 0.70, "summary": "y"},
    ], w)
    assert not tie["ignited"] and tie["winner"] is None        # همه-یا-هیچ: بدونِ margin شلیک نه


def t_current_logic_untouched():
    """برندهٔ 'current' دقیقاً همان خروجیِ ig.select_winner است (صفر monkey-patch)."""
    _clean_flags()
    direct = ig.select_winner(_DEMO, None)
    rec = sw.shadow_compare(_DEMO)
    assert rec["winner_current"] == (direct.get("winner") or {}).get("key")
    assert not hasattr(ig, "soft_wta")               # چیزی به ماژولِ زنده تزریق نشده


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_softwta_shadow: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
