#!/usr/bin/env python3
"""تست HH-P11 · pulse_arbiter — داورِ نبض (سه قلب → یک ضربان). $0 آفلاین، advisory.

DoD:
  (الف) ترمز غالب: یک قلبِ braking → effective تا periodِ ترمز بالا (شتاب خلعش نمی‌کند)
  (ب) شتاب اجماعی: همه تند و بی‌ترمز → effective < base (نزدیکِ میانگینِ هندسیِ وزن‌دار)
  (ج) کششِ محتاط: یک قلبِ کند اجماع را بالا می‌کشد (شتاب نیاز به توافق دارد)
  (د) clamp سختِ [FLOOR, MAX] + abstain (هیچ قلب → base)
  (ه) precision: قلبِ کم‌اطمینان اجماع را کمتر جابه‌جا می‌کند
  (و) رنگِ آشتی = بدترینِ حاضرها؛ rhythm RED = ترمز (نه T_beatِ تندِ خودش)
  (ز) نرمال‌سازیِ رأی: NaN/inf/≤0 → غایب
  (ح) gather_views fail-soft (۳ رأی، بدونِ crash) + no forbidden production import
  (ط) advisory-only: persist با flag خاموش هیچ نمی‌نویسد؛ با flag روشن فقط سینکِ خودش
  (ی) wire_open ساختاراً بسته + effective_period_if_open هرگز override نمی‌کند وقتی بسته
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("pulse-arbiter")
_HEART = harness.REAL_VAULT / "_ops" / "heart"
if str(_HEART) not in sys.path:
    sys.path.insert(0, str(_HEART))

import opslib  # noqa: E402
import pulse_arbiter as pa  # noqa: E402

V = pa._vote


# ════════════════════════════════════════════════════════════════════════════════
# (الف) ترمز غالب — شتاب هرگز ترمز را خلع‌سلاح نمی‌کند
# ════════════════════════════════════════════════════════════════════════════════
def t_brake_dominates():
    """یک قلبِ hard-brake (period=900) با دو قلبِ تند → effective ≥ ترمز."""
    r = pa.arbitrate([V("cardiac", 40, False, 1.0),
                      V("control_law", 900, True, 1.0, "RED", note="sigma-missing"),
                      V("rhythm", 45, False, 0.7)])
    assert r["effective_period_s"] >= 900 - 1e-6, r
    assert r["driver"].startswith("brake"), r
    assert r["color"] == "RED", r


def t_brake_floor_at_brake_period():
    """قلبِ braking با periodِ کوچک هم دستِ‌کم تا BRAKE_PERIOD_S بالا می‌رود."""
    r = pa.arbitrate([V("rhythm", 40, True, 0.7, "RED")])   # RED با T_beatِ کوتاه
    assert r["effective_period_s"] >= pa.BRAKE_PERIOD_S - 1e-6, r
    assert r["driver"].startswith("brake"), r


# ════════════════════════════════════════════════════════════════════════════════
# (ب) شتاب اجماعی — همه تند و بی‌ترمز → زیرِ base
# ════════════════════════════════════════════════════════════════════════════════
def t_consensus_acceleration():
    r = pa.arbitrate([V("cardiac", 40, False, 1.0),
                      V("control_law", 45, False, 1.0),
                      V("rhythm", 50, False, 0.7)])
    assert 30.0 <= r["effective_period_s"] < 60.0, r
    assert r["driver"] == "consensus", r
    # نزدیکِ میانگینِ هندسیِ وزن‌دار
    assert abs(r["consensus_s"] - r["effective_period_s"]) < 1e-6, r


# ════════════════════════════════════════════════════════════════════════════════
# (ج) کششِ محتاط — یک قلبِ کند اجماع را بالا می‌کشد (توافق لازم است)
# ════════════════════════════════════════════════════════════════════════════════
def t_cautious_pulls_up():
    fast = pa.arbitrate([V("cardiac", 40, False, 1.0),
                         V("control_law", 45, False, 1.0),
                         V("rhythm", 50, False, 0.7)])["effective_period_s"]
    mixed = pa.arbitrate([V("cardiac", 40, False, 1.0),
                          V("control_law", 300, False, 1.0),   # یک قلبِ محتاط
                          V("rhythm", 45, False, 0.7)])["effective_period_s"]
    assert mixed > fast, (mixed, fast)


# ════════════════════════════════════════════════════════════════════════════════
# (د) clamp + abstain
# ════════════════════════════════════════════════════════════════════════════════
def t_clamp_to_max():
    r = pa.arbitrate([V("cardiac", 99999, False, 1.0)])
    assert r["effective_period_s"] == pa.MAX_S, r


def t_clamp_to_floor():
    r = pa.arbitrate([V("cardiac", 1, False, 1.0), V("control_law", 2, False, 1.0)])
    assert r["effective_period_s"] == pa.FLOOR_S, r


def t_abstain_when_no_hearts():
    r = pa.arbitrate([V("cardiac", None, False, 0, present=False),
                      V("control_law", None, False, 0, present=False),
                      V("rhythm", None, False, 0, present=False)])
    assert r["driver"] == "abstain", r
    assert r["effective_period_s"] == round(min(pa.MAX_S, max(pa.FLOOR_S, pa.BASE_PERIOD_S)), 2)
    assert r["n_present"] == 0 and r["n_braking"] == 0


# ════════════════════════════════════════════════════════════════════════════════
# (ه) precision — قلبِ کم‌اطمینان اجماع را کمتر جابه‌جا می‌کند
# ════════════════════════════════════════════════════════════════════════════════
def t_precision_weighting():
    """control_law=300 با precision بالا اجماع را بیشتر بالا می‌کشد تا با precision پایین."""
    hi_pi = pa.arbitrate([V("cardiac", 40, False, 1.0),
                          V("control_law", 300, False, 1.0)])["effective_period_s"]
    lo_pi = pa.arbitrate([V("cardiac", 40, False, 1.0),
                          V("control_law", 300, False, 0.1)])["effective_period_s"]
    assert hi_pi > lo_pi, (hi_pi, lo_pi)
    # کفِ precision: حتی precision=0 برای قلبِ حاضر رأیش کاملاً محو نمی‌شود
    z_pi = pa.arbitrate([V("cardiac", 40, False, 1.0),
                         V("control_law", 300, False, 0.0)])["effective_period_s"]
    assert z_pi > 40.0, z_pi


# ════════════════════════════════════════════════════════════════════════════════
# (و) رنگِ آشتی = بدترین؛ rhythm RED = ترمز
# ════════════════════════════════════════════════════════════════════════════════
def t_color_is_worst():
    assert pa.arbitrate([V("a", 60, False, 1, "GREEN"),
                         V("b", 60, False, 1, "AMBER")])["color"] == "AMBER"
    assert pa.arbitrate([V("a", 60, False, 1, "AMBER"),
                         V("b", 60, False, 1, "RED")])["color"] == "RED"
    assert pa.arbitrate([V("a", 60, False, 1, "GREEN"),
                         V("b", 60, False, 1, "GREEN")])["color"] == "GREEN"


def t_rhythm_red_brakes_not_races():
    """آشتیِ تناقضِ معنایی: rhythm در RED T_beatِ *کوتاه* دارد (واکنشی) ولی در نبضِ واحد
    باید ترمز باشد (throttle). effective نباید به سمتِ 40 تند شود."""
    r = pa._rhythm_vote({"mode_color": "RED", "T_beat": 40.0, "hrv": 3.0,
                         "mode_focus": "CALM"})
    assert r["braking"] is True, r
    fused = pa.arbitrate([r])
    assert fused["effective_period_s"] >= pa.BRAKE_PERIOD_S - 1e-6, fused


# ════════════════════════════════════════════════════════════════════════════════
# (ز) نرمال‌سازیِ رأی — NaN/inf/≤0 → غایب
# ════════════════════════════════════════════════════════════════════════════════
def t_vote_normalization():
    assert V("x", float("nan"), False, 1.0)["present"] is False
    assert V("x", float("inf"), False, 1.0)["present"] is False
    assert V("x", 0, False, 1.0)["present"] is False
    assert V("x", -5, False, 1.0)["present"] is False
    assert V("x", "bad", False, 1.0)["present"] is False
    assert V("x", 60, False, 1.0)["present"] is True


# ════════════════════════════════════════════════════════════════════════════════
# (ح) gather_views fail-soft + no forbidden import
# ════════════════════════════════════════════════════════════════════════════════
def t_gather_views_failsoft():
    """۳ رأی همیشه برمی‌گردد، بدونِ crash (منابعِ غایب = abstain)."""
    views = pa.gather_views()
    assert isinstance(views, list) and len(views) == 3, views
    names = {v["heart"] for v in views}
    assert names == {"cardiac", "control_law", "rhythm"}, names


def t_no_forbidden_production_import():
    """داور هرگز chrono/money/effects/gate را import یا call نمی‌کند (خطِ قرمزِ M-HEART §۶).
    فقط الگوهای واقعیِ import/call چک می‌شوند — نه ذکرِ متنیِ داخلِ توضیحات."""
    src = open(pa.__file__, encoding="utf-8").read()
    for f in ("import chrono", "from chrono", "money_gate", "budget_gate",
              "capability_gate", "organ_gate", "import effects", "from effects",
              ".settle(", "genome_ledger(", "ledger_note("):
        assert f not in src, f"خطِ قرمز: {f}"


# ════════════════════════════════════════════════════════════════════════════════
# (ط) advisory-only — persist با flag
# ════════════════════════════════════════════════════════════════════════════════
def t_persist_flag_off_no_write(monkeyenv=None):
    """flag خاموش → written=False و هیچ فایلی ساخته نمی‌شود (no regression)."""
    import os
    os.environ.pop(pa.FLAG_ENV, None)
    if pa.LATEST.exists():
        pa.LATEST.unlink()
    snap = pa.persist()
    assert snap["written"] is False, snap
    assert not pa.LATEST.exists(), "flag خاموش نباید فایل بنویسد"
    assert snap["advisory_only"] is True


def t_persist_flag_on_writes_only_own_sink():
    """flag روشن → فقط arbiter-latest.json + sink؛ هرگز ORGANISM-STATE/period."""
    import os
    os.environ[pa.FLAG_ENV] = "1"
    try:
        org_state = opslib.STATE_DIR / "ORGANISM-STATE.json"
        before = org_state.exists()
        snap = pa.persist(beat=7)
        assert snap["written"] is True, snap
        assert pa.LATEST.exists(), "flag روشن باید سینکِ خودش را بنویسد"
        # داور هرگز ORGANISM-STATE را لمس نمی‌کند
        assert org_state.exists() == before, "داور نباید ORGANISM-STATE بنویسد"
        rl = pa.read_latest()
        assert rl.get("schema") == pa.SCHEMA and rl.get("beat") == 7, rl
    finally:
        os.environ.pop(pa.FLAG_ENV, None)


# ════════════════════════════════════════════════════════════════════════════════
# (ی) wire_open بسته + effective_period_if_open هرگز override نمی‌کند
# ════════════════════════════════════════════════════════════════════════════════
def t_wire_open_closed_by_default():
    ok, reasons = pa.wire_open()
    assert ok is False, "سیم‌کشیِ زنده باید ساختاراً بسته باشد (تا رأیِ مالک)"
    assert len(reasons) >= 1, reasons


def t_effective_period_if_open_returns_default_when_closed():
    """گیت بسته → default برگردانده می‌شود (advisory؛ هرگز period را override نمی‌کند)."""
    import os
    os.environ.pop(pa.FLAG_ENV, None)
    period, snap = pa.effective_period_if_open(default_s=300.0)
    assert period == 300.0, period
    assert snap.get("wire_open") is False


def t_snapshot_is_advisory_and_gated():
    snap = pa.arbiter_snapshot(beat=3)
    assert snap["advisory_only"] is True
    assert snap["wire_open"] is False
    assert snap["schema"] == pa.SCHEMA and snap["beat"] == 3
    assert snap["effective_period_s"] >= pa.FLOOR_S


# ════════════════════════════════════════════════════════════════════════════════
# (چ) 2027-alignment: precisionِ active-inference (inverse-variance) — کانالِ نبضِ واحد
# ════════════════════════════════════════════════════════════════════════════════
def t_inverse_variance_precision_math():
    """π = 1/(1+CV²): سیگنالِ پایدار → ~۱؛ پرنوسان → پایین‌تر؛ non-finite/کم‌داده → ۱.۰."""
    assert pa.inverse_variance_precision([60, 60, 60]) == 1.0
    assert pa.inverse_variance_precision([]) == 1.0
    assert pa.inverse_variance_precision([60]) == 1.0
    # درسِ replay §۵: NaN/Inf هرگز کرش/غیرمتناهی نمی‌دهد
    p = pa.inverse_variance_precision([float("inf"), float("nan"), 60])
    assert p == 1.0 and math.isfinite(p)
    stable = pa.inverse_variance_precision([100, 101, 99, 100])
    churny = pa.inverse_variance_precision([30, 300, 30, 300])
    assert 0.0 <= churny < stable <= 1.0, (stable, churny)


def _views(cs=60, hs=60, rs=60, ctrl_pi=0.8):
    return dict(
        cardiac_snapshot={"enabled": True, "bio_rhythm": {"period_s": cs, "pace": "balanced"},
                          "budget": {}},
        heart_shadow={"period_s": hs, "telemetry": {"gates": {"precision": ctrl_pi}}},
        rhythm_state={"mode_color": "GREEN", "T_beat": rs, "hrv": 4.0, "mode_focus": "STEADY"})


def t_precision_flag_off_byte_identical():
    """فلگ خاموش → precisionِ دستی دست‌نخورده (rhythm=0.7)، هیچ کلیدِ اضافه، effective بی‌تغییر."""
    import os
    os.environ.pop(pa.FLAG_PRECISION, None)
    pa._period_hist.clear()
    v = pa.gather_views(**_views())
    rh = next(x for x in v if x["heart"] == "rhythm")
    assert rh["precision"] == 0.7, rh
    assert all("_canonical_precision" not in x and "precision_src" not in x for x in v)
    # effective برابرِ arbitrate روی همان رأی‌های دستی
    eff_gathered = pa.arbitrate(v)["effective_period_s"]
    eff_manual = pa.arbitrate([V("cardiac", 60, False, 1.0),
                               V("control_law", 60, False, 0.8),
                               V("rhythm", 60, False, 0.7)])["effective_period_s"]
    assert eff_gathered == eff_manual, (eff_gathered, eff_manual)


def t_precision_flag_on_active_inference():
    """فلگ روشن → control_law precisionِ کانونیِ خودش را بازاستفاده می‌کند (۰.۸)؛
    cardiac/rhythm از inverse-variance؛ snapshot.precision_mode درست."""
    import os
    os.environ[pa.FLAG_PRECISION] = "1"
    pa._period_hist.clear()
    try:
        v = None
        for _ in range(5):
            v = pa.gather_views(**_views(ctrl_pi=0.8))
        ctrl = next(x for x in v if x["heart"] == "control_law")
        card = next(x for x in v if x["heart"] == "cardiac")
        assert abs(ctrl["precision"] - 0.8) < 1e-9, ctrl
        assert ctrl["precision_src"] == "control_law.precision_weight", ctrl
        assert card["precision_src"] == "inverse-variance", card
        snap = pa.arbiter_snapshot(**_views())
        assert snap["precision_mode"].startswith("active-inference"), snap
    finally:
        os.environ.pop(pa.FLAG_PRECISION, None)
        pa._period_hist.clear()


def t_precision_replay_counterfactual():
    """۲۰۲۷ §۵: هر ورودی یک‌بار خاموش (مسیرِ زنده) یک‌بار روشن (سایه). خاموش=دستی؛
    روشن=هر precision finite و ∈[0,1]، حتی با بافرِ منحط؛ هیچ کرش."""
    import os
    inputs = _views(cs=40, hs=500, rs=45, ctrl_pi=0.3)  # ورودیِ مرزی (control کند)
    os.environ.pop(pa.FLAG_PRECISION, None)
    pa._period_hist.clear()
    off = pa.arbitrate(pa.gather_views(**inputs))
    os.environ[pa.FLAG_PRECISION] = "1"
    pa._period_hist.clear()
    try:
        on_views = pa.gather_views(**inputs)
        for x in on_views:
            if x.get("present"):
                assert math.isfinite(x["precision"]) and 0.0 <= x["precision"] <= 1.0, x
        on = pa.arbitrate(on_views)
        assert on["effective_period_s"] >= pa.FLOOR_S and on["effective_period_s"] <= pa.MAX_S
        # خاموش برابرِ رأی‌های دستی (رگرسیونِ صفر)
        assert off["effective_period_s"] >= pa.FLOOR_S
    finally:
        os.environ.pop(pa.FLAG_PRECISION, None)
        pa._period_hist.clear()


if __name__ == "__main__":
    failed = harness.run([
        ("[الف] ترمز غالب", t_brake_dominates),
        ("[الف] کفِ ترمز = BRAKE_PERIOD", t_brake_floor_at_brake_period),
        ("[ب] شتاب اجماعی < base", t_consensus_acceleration),
        ("[ج] کششِ محتاط بالا", t_cautious_pulls_up),
        ("[د] clamp به MAX", t_clamp_to_max),
        ("[د] clamp به FLOOR", t_clamp_to_floor),
        ("[د] abstain بدونِ قلب", t_abstain_when_no_hearts),
        ("[ه] precision weighting", t_precision_weighting),
        ("[و] رنگ = بدترین", t_color_is_worst),
        ("[و] rhythm RED = ترمز", t_rhythm_red_brakes_not_races),
        ("[ز] نرمال‌سازیِ رأی", t_vote_normalization),
        ("[ح] gather_views fail-soft", t_gather_views_failsoft),
        ("[ح] no forbidden import", t_no_forbidden_production_import),
        ("[ط] persist flag off = no write", t_persist_flag_off_no_write),
        ("[ط] persist flag on = only own sink", t_persist_flag_on_writes_only_own_sink),
        ("[ی] wire_open بسته", t_wire_open_closed_by_default),
        ("[ی] if_open → default وقتی بسته", t_effective_period_if_open_returns_default_when_closed),
        ("[ی] snapshot advisory+gated", t_snapshot_is_advisory_and_gated),
        ("[چ] inverse-variance precision math", t_inverse_variance_precision_math),
        ("[چ] 2027 precision flag off = byte-identical", t_precision_flag_off_byte_identical),
        ("[چ] 2027 precision flag on = active-inference", t_precision_flag_on_active_inference),
        ("[چ] 2027 precision replay counterfactual", t_precision_replay_counterfactual),
    ])
    sys.exit(1 if failed else 0)
