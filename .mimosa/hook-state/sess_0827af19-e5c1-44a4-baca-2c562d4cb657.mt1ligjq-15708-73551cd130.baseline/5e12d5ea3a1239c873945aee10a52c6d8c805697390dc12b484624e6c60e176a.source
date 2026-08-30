"""test_standards_s.py — بک‌لاگِ ۲۰۲۷ «S batch» (رأی مالک: قلب + برچسب).

#۲ precision-weighting در control_law.heart_step (active-inference؛ π≤۱ فقط gain را کم می‌کند،
پیش‌فرض خاموش = byte-identical). #۳ برچسبِ fact/emerging/hype + گاردِ access-only در
epistemics/contracts.py (هرگز ادعای phenomenal).
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "heart"))
sys.path.insert(0, str(_HERE.parent / "epistemics"))

import harness
ENV = harness.setup("standards_s")

import control_law as cl   # noqa: E402
import contracts as ct     # noqa: E402


def _inputs(v_per_hr=2.0, sample_size=6, confirmed_ts=None):
    """ورودیِ heart_step که همهٔ گیت‌های σ را پاس می‌کند (σ=0.5=۱/۲ سازگار)."""
    return {
        "beat": 1,
        "velocity": {"velocity_per_hr": v_per_hr, "sample_size": sample_size,
                     "confirmed_ts": confirmed_ts or []},
        "cpi": {}, "delta": {},
        "sigma": {"sigma": 0.5, "zone": "ok", "stale": False,
                  "spawn_approved": 1, "parents": 2, "producer": "replication"},
        "budget_remaining": 200, "lock": {}, "prev": {},
    }


# ── #۲ precision-weighting ──────────────────────────────────────────────────
def t_precision_weight_defaults_and_bounds():
    assert cl.precision_weight(None) == 1.0
    assert cl.precision_weight({"sample_size": 1}) == 1.0            # n<۲ → ۱ (byte-identical)
    regular = cl.precision_weight({"sample_size": 6, "confirmed_ts": [0, 1, 2, 3, 4, 5]})
    assert regular == 1.0                                           # منظم/Poisson → ۱
    bursty = cl.precision_weight({"sample_size": 6, "confirmed_ts": [0, 1, 2, 3, 100]})
    assert 0.0 <= bursty < 1.0                                      # بورست‌دار → π<۱
    assert bursty < regular


def t_precision_off_is_byte_identical():
    os.environ.pop("HEART_PRECISION_WEIGHT", None)
    sig, tel = cl.heart_step(_inputs(confirmed_ts=[0, 1, 2, 3, 100]))
    assert "precision" not in tel["gates"] and "err_eff" not in tel["gates"]
    assert tel["gates"]["fail_closed_reason"] is None               # گیت‌ها پاس شد
    assert sig.period_s is not None


def t_precision_on_shrinks_gain_only():
    ts = [0, 1, 2, 3, 100]                                          # بورست → π<۱
    os.environ.pop("HEART_PRECISION_WEIGHT", None)
    off, _ = cl.heart_step(_inputs(confirmed_ts=ts))
    os.environ["HEART_PRECISION_WEIGHT"] = "1"
    on, tel = cl.heart_step(_inputs(confirmed_ts=ts))
    os.environ.pop("HEART_PRECISION_WEIGHT", None)
    assert tel["gates"]["precision"] < 1.0
    # π<۱ → err_eff کوچکتر → period به BASE نزدیک‌تر: gain فقط کم می‌شود، هرگز بیشتر
    assert abs(on.period_s - cl.BASE_PERIOD_S) < abs(off.period_s - cl.BASE_PERIOD_S)


def t_precision_on_regular_signal_unchanged():
    """سیگنالِ منظم → π=۱ → period دقیقاً مثلِ خاموش (فقط نویز را نرم می‌کند، نه سالم را)."""
    ts = [0, 1, 2, 3, 4, 5]
    os.environ.pop("HEART_PRECISION_WEIGHT", None)
    off, _ = cl.heart_step(_inputs(confirmed_ts=ts))
    os.environ["HEART_PRECISION_WEIGHT"] = "1"
    on, tel = cl.heart_step(_inputs(confirmed_ts=ts))
    os.environ.pop("HEART_PRECISION_WEIGHT", None)
    assert tel["gates"]["precision"] == 1.0
    assert abs(on.period_s - off.period_s) < 1e-6


# ── #۳ epistemic label + access-only guard ──────────────────────────────────
def t_epi_label_valid_and_backward_compatible():
    r = ct.make_metric("channel", 0.5, sample_size=500, notes="ok", epistemic_label="fact")
    assert r["epistemic_label"] == "fact" and r["authoritative"] is True
    plain = ct.make_metric("levels", [1, 2, 3], sample_size=8)      # بدونِ برچسب = سازگارِ عقب
    assert plain["epistemic_label"] == "" and plain["type"] == "EPI_METRIC"


def t_epi_label_invalid_raises():
    try:
        ct.make_metric("channel", 0.5, 500, epistemic_label="proven")
        assert False, "برچسبِ نامعتبر باید raise کند"
    except ValueError:
        pass


def t_epi_access_only_guard_blocks_phenomenal():
    for bad in ("qualia detected", "the model is sentient", "phenomenal experience", "it feels"):
        try:
            ct.make_metric("self_reference", 1.0, 100, notes=bad)
            assert False, f"ادعای phenomenal باید raise کند: {bad}"
        except ValueError:
            pass
    # access-only تمیز = عبور
    ok = ct.make_metric("self_reference", 1.0, 100,
                        notes="functional self-model verdict", epistemic_label="emerging")
    assert ok["epistemic_label"] == "emerging"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_standards_s: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
