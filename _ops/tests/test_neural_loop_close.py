#!/usr/bin/env python3
"""test_neural_loop_close.py — تست‌های فیکسِ #214 + #310 (بستنِ حلقهٔ هوش).

۲ فیکس:
  #214 — BCM sync-delete guard: لیستِ known_keys خالی نباید وزن‌ها را پاک کنه.
  #310 — neural_driver.evaluatebcm را fold می‌کنه (learned_pressure)، با shadow log
          و مسیرِ apply پشتِ flag جداگانه (default-off).

$0 آفلاین: همهٔ persistها tmpdir. هیچ لمسِ state واقعی.
"""
import os
import sys
import json
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness
ENV = harness.setup("neural-loop-close")   # ایزولاسیون

from neural.bcm import BCMStabilizer


def _tmp(name="bcm.json"):
    return Path(tempfile.mkdtemp()) / name


def _make_bcm(**kw):
    kw.setdefault("persist_path", _tmp())
    return BCMStabilizer(**kw)


# ═══ #214: BCM sync-delete guard ══════════════════════════════════════════════

def t_bcm_empty_known_preserves_weights():
    """#214: known_keys=[] نباید وزن‌های موجود را پاک کنه.

    ریشهٔ خالی‌بودنِ BCM: قبل از فیکس، این وزن‌ها را پاک می‌کرد.
    """
    b = _make_bcm(beta=0.01)
    b.step({"a": 0.5, "b": 0.8}, known_keys=["a", "b"])
    assert b.weight("a") is not None
    assert b.weight("b") is not None
    # حالا یک step با known_keys خالی — نباید چیزی پاک بشه
    r = b.step({"a": 0.5}, known_keys=[])
    assert b.weight("a") is not None, "a نباید پاک بشه با known_keys=[]"
    assert b.weight("b") is not None, "b نباید پاک بشه با known_keys=[]"
    assert "a" not in r.pruned and "b" not in r.pruned, \
        f"هیچ‌کدوم نباید در pruned باشن: {r.pruned}"


def t_bcm_none_known_preserves_weights():
    """#214: known_keys=None هنوز هم کار می‌کنه (هیچ sync ای انجام نمیشه)."""
    b = _make_bcm(beta=0.01)
    b.step({"a": 0.5}, known_keys=["a"])
    assert b.weight("a") is not None
    r = b.step({"a": 0.5}, known_keys=None)
    assert b.weight("a") is not None


def t_bcm_nonempty_sync_still_removes():
    """regression: known_keys غیرخالی هنوز کلیدهای حذف‌شده را پاک می‌کنه.

    این همان رفتارِ قبل از فیکس است — فقط لیست خالی استثنا شده.
    """
    b = _make_bcm(beta=0.01)
    b.step({"a": 0.5, "b": 0.5}, known_keys=["a", "b"])
    assert set(b.keys()) == {"a", "b"}
    b.step({"a": 0.5}, known_keys=["a"])   # b دیگر در ایندکس نیست
    assert b.weight("b") is None, "b باید پاک بشه چون از known_keys حذف شد"
    assert b.weight("a") is not None


def t_bcm_recovery_from_empty_then_feed():
    """#214: بعد از یک لیست خالی، تغذیهٔ واقعی هنوز کلیدها را اضافه/تقویت می‌کنه."""
    b = _make_bcm(beta=0.05)
    b.step({"a": 0.8}, known_keys=["a"])
    b.step({"a": 0.5}, known_keys=[])   # startup/empty — حفظ
    assert b.weight("a") is not None
    # حالا تغذیهٔ واقعی
    b.step({"a": 0.8, "c": 0.9}, known_keys=["a", "c"])
    assert b.weight("a") is not None
    assert b.weight("c") is not None, "کلید تازه باید اضافه بشه"


# ═══ #310: neural_driver.evaluatebcm fold ════════════════════════════════════

def _make_driver():
    from neural.neural_driver import NeuralDriver
    return NeuralDriver()


def t_evaluate_no_bcm_backward_compat():
    """#310: bcm=None → learned_pressure=0، صفر تغییر رفتار."""
    d = _make_driver()
    result = d.evaluate(beat=1)
    bi = result["brain_inputs"]
    assert bi["learned_pressure"] == 0.0, \
        f"بدون bcm باید 0 باشه، شد {bi['learned_pressure']}"
    assert bi["learned_top_signal"] == ""
    assert bi["learned_n_keys"] == 0
    # backward compat: فیلدهای قدیمی هنوز موجوده
    assert "partner_stress" in bi
    assert "throttle_brain" in bi


def t_evaluate_with_bcm_folds_weights():
    """#310: bcm با وزن‌های معلوم → learned_pressure متناسب."""
    d = _make_driver()
    b = _make_bcm(beta=0.01)
    # سه کلید را تقویت کن
    for _ in range(5):
        b.step({"k1": 0.9, "k2": 0.8, "k3": 0.7}, known_keys=["k1", "k2", "k3"])
    result = d.evaluate(beat=1, bcm=b)
    bi = result["brain_inputs"]
    assert bi["learned_pressure"] > 0.0, \
        f"با وزنِ یادگرفته‌شده باید >0 باشه، شد {bi['learned_pressure']}"
    assert bi["learned_n_keys"] == 3
    assert bi["learned_top_signal"] in ("k1", "k2", "k3"), \
        f"top_signal باید یکی از کلیدها باشه: {bi['learned_top_signal']}"


def t_evaluate_empty_bcm_zero_pressure():
    """#310: bcm بدون وزن → learned_pressure=0 (نه crash)."""
    d = _make_driver()
    b = _make_bcm()   # خالی، هیچ step ای اجرا نشده
    result = d.evaluate(beat=1, bcm=b)
    bi = result["brain_inputs"]
    assert bi["learned_pressure"] == 0.0
    assert bi["learned_n_keys"] == 0


def t_evaluate_learned_pressure_bounded():
    """#310: learned_pressure هرگز از 1.0 بیشتر نشه حتی با وزن‌های max."""
    d = _make_driver()
    b = _make_bcm(beta=0.0, eta=0.5, w_cap=4.0)   # beta=0 → بدون زوال
    # وزن‌ها را به cap برسون
    for _ in range(20):
        b.step({"k1": 1.0, "k2": 1.0, "k3": 1.0}, known_keys=["k1", "k2", "k3"])
    result = d.evaluate(beat=1, bcm=b)
    bi = result["brain_inputs"]
    assert 0.0 <= bi["learned_pressure"] <= 1.0, \
        f"باید در [0,1] باشه: {bi['learned_pressure']}"


def t_evaluate_bcm_crash_safe():
    """#310: bcm خراب (weight() raise می‌کنه) → evaluate crash نمی‌کنه، pressure=0."""
    d = _make_driver()

    class BrokenBCM:
        def keys(self):
            return ["k1"]
        def weight(self, k):
            raise RuntimeError("boom")

    result = d.evaluate(beat=1, bcm=BrokenBCM())
    bi = result["brain_inputs"]
    assert bi["learned_pressure"] == 0.0, "bcm خراب باید safe-fail بشه به 0"


# ═══ #310: protective_override apply path ════════════════════════════════════

def t_apply_flag_default_off():
    """#310: بدون flag OCTOPUS_NEURAL_LEARNED_APPLY، learned_pressure اثر نداره.

    این تضمین می‌کنه که فیکس byte-identical با قبل است تا مالک flag را روشن نکنه.
    """
    import wiring
    # flag خاموش (پیش‌فرض)
    old = os.environ.pop("OCTOPUS_NEURAL_LEARNED_APPLY", None)
    try:
        neural_result = {
            "pain": {"level": 0.3},   # زیر 0.7
            "reflexes": [],
            "brain_inputs": {"learned_pressure": 0.9, "learned_top_signal": "k1"},
        }
        r = wiring.protective_override(neural_result)
        assert r["override"] is False, "با flag خاموش، learned_pressure نباید override کنه"
        assert "all clear" in r["reason"] or "+learned" not in r["reason"], \
            "نباید یادگیری را note کنه"
    finally:
        if old is not None:
            os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = old


def t_apply_flag_on_combines_learned():
    """#310: با flag روشن، learned_pressure به pain اضافه می‌شه.

    pain=0.3 + learned=0.9*0.5=0.45 → 0.75 > 0.7 → protective_halt.
    این اولین مسیری است که یک وزنِ آموخته‌شده یک تصمیم را عوض می‌کنه.
    """
    import wiring
    old = os.environ.get("OCTOPUS_NEURAL_LEARNED_APPLY")
    os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "1"
    try:
        neural_result = {
            "pain": {"level": 0.3},
            "reflexes": [],
            "brain_inputs": {"learned_pressure": 0.9, "learned_top_signal": "k1"},
        }
        r = wiring.protective_override(neural_result)
        assert r["override"] is True, "با flag+learned باید override بشه"
        assert r["action"] == "protective_halt"
        assert "+learned=0.90:k1" in r["reason"], \
            f"باید یادگیری را note کنه: {r['reason']}"
    finally:
        if old is None:
            os.environ.pop("OCTOPUS_NEURAL_LEARNED_APPLY", None)
        else:
            os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = old


def t_apply_flag_on_low_learned_no_override():
    """#310: با flag روشن ولی learned پایین، نباید override بشه (pain زیر 0.7)."""
    import wiring
    old = os.environ.get("OCTOPUS_NEURAL_LEARNED_APPLY")
    os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "1"
    try:
        neural_result = {
            "pain": {"level": 0.3},
            "reflexes": [],
            "brain_inputs": {"learned_pressure": 0.1, "learned_top_signal": "k1"},
        }
        r = wiring.protective_override(neural_result)
        # pain=0.3 + 0.1*0.5=0.05 → 0.35 < 0.7 → no override
        assert r["override"] is False
    finally:
        if old is None:
            os.environ.pop("OCTOPUS_NEURAL_LEARNED_APPLY", None)
        else:
            os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = old


if __name__ == "__main__":
    failed = harness.run([
        # #214
        ("#214: known_keys=[] وزن‌ها را حفظ می‌کنه", t_bcm_empty_known_preserves_weights),
        ("#214: known_keys=None وزن‌ها را حفظ می‌کنه", t_bcm_none_known_preserves_weights),
        ("#214 regression: known_keys غیرخالی هنوز sync می‌کنه", t_bcm_nonempty_sync_still_removes),
        ("#214: recovery بعد از empty، feed واقعی کار می‌کنه", t_bcm_recovery_from_empty_then_feed),
        # #310 evaluate
        ("#310: bcm=None → learned_pressure=0 (backward compat)", t_evaluate_no_bcm_backward_compat),
        ("#310: bcm با وزن → learned_pressure>0", t_evaluate_with_bcm_folds_weights),
        ("#310: bcm خالی → learned_pressure=0", t_evaluate_empty_bcm_zero_pressure),
        ("#310: learned_pressure در [0,1] کران‌دار", t_evaluate_learned_pressure_bounded),
        ("#310: bcm خراب → safe-fail به 0", t_evaluate_bcm_crash_safe),
        # #310 apply
        ("#310 apply: flag default-off → بدون اثر", t_apply_flag_default_off),
        ("#310 apply: flag on → learned به pain اضافه می‌شه", t_apply_flag_on_combines_learned),
        ("#310 apply: flag on ولی learned پایین → no override", t_apply_flag_on_low_learned_no_override),
    ])
    sys.exit(1 if failed else 0)
