"""test_cardiac_allometry.py — تستِ لایهٔ ضربانِ آلوستاتیک (cardiac.py).

سه قانونِ بیولوژیک (نظریه: CARDIAC-ALLOMETRY-v1):
  ۱) bio_rhythm(mass) → period تابعِ حجم (M^(−۱/۴))
  ۲) BeatBudget: بودجهٔ روزانه، مجبور به انتخاب
  ۳) baroreflex: پاسخِ فوریِ محیط

خطوطِ قرمز: flag off = no regression؛ TINVها دست‌نخورده؛ $0/offline؛ fail-soft.
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))           # _ops/
sys.path.insert(0, str(_HERE.parent / "budget"))

import cardiac


def _setbio(on: bool):
    if on:
        os.environ["OCTOPUS_WIRE_BIO"] = "1"
    else:
        os.environ.pop("OCTOPUS_WIRE_BIO", None)


# ── قانونِ ۱: flag off = no regression ────────────────────────────────────────────
def test_bio_rhythm_flag_off_is_base():
    """وقتی OCTOPUS_WIRE_BIO خاموز است، period باید عیناً BASE باشد (no regression)."""
    _setbio(False)
    r = cardiac.bio_rhythm()
    assert r["period_s"] == cardiac.BASE_PERIOD_S
    assert r["pace"] == "static"
    assert "off" in r["reason"]


def test_bio_rhythm_mass_monotonic():
    """جرمِ بیشتر → period بیشتر (ضربانِ کندتر، نهنگ). allometric، نه ثابت."""
    _setbio(True)
    try:
        small = cardiac.bio_rhythm(mass=1.0)
        big = cardiac.bio_rhythm(mass=100.0)
        assert small["period_s"] < big["period_s"], \
            f"جرمِ بیشتر باید period بیشتر بدهد: {small['period_s']} vs {big['period_s']}"
        # pace classification
        assert small["pace"] in ("mice", "balanced")
        assert big["pace"] in ("whale", "balanced")
    finally:
        _setbio(False)


def test_bio_rhythm_floor_and_ceiling():
    """period هرگز از کف/سقف رد نمی‌کند (ایمنی)."""
    _setbio(True)
    try:
        tiny = cardiac.bio_rhythm(mass=0.001)   # باید به کف برسد
        huge = cardiac.bio_rhythm(mass=1e9)      # باید به سقف برسد
        assert tiny["period_s"] >= cardiac.BIO_RESTING_FLOOR_S
        assert huge["period_s"] <= cardiac.BIO_MAX_PERIOD_S
        assert tiny["period_s"] > 0
        assert huge["period_s"] > 0
    finally:
        _setbio(False)


def test_bio_rhythm_mass_minimum():
    """جرمِ صفر/منفی باید به کف (۱.۰) رسیدگی شود — هیچ‌وقت crash."""
    _setbio(True)
    try:
        r = cardiac.bio_rhythm(mass=0)
        assert r["period_s"] > 0
        r2 = cardiac.bio_rhythm(mass=-5)
        assert r2["period_s"] > 0
    finally:
        _setbio(False)


# ── قانونِ ۲: BeatBudget ─────────────────────────────────────────────────────────
def test_budget_flag_off_unlimited():
    _setbio(False)
    b = cardiac.BeatBudget(daily_cap=5)
    r = b.spend("active")
    assert r["mode"] == "unlimited"
    assert r["depleted"] is False


def test_budget_spends_and_depletes():
    _setbio(True)
    with tempfile.TemporaryDirectory() as td:
        b = cardiac.BeatBudget(daily_cap=3, path=Path(td) / "bud.json")
        try:
            r1 = b.spend("active"); assert r1["remaining"] == 2 and not r1["depleted"]
            r2 = b.spend("active"); assert r2["remaining"] == 1 and not r2["depleted"]
            r3 = b.spend("active"); assert r3["remaining"] == 0 and r3["depleted"]
            r4 = b.spend("active"); assert r4["depleted"]  # بعد از depletion همچنان depleted
            assert r4["mode"] == "resting-only"
        finally:
            _setbio(False)


def test_budget_resets_on_new_day():
    _setbio(True)
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "bud.json"
        b = cardiac.BeatBudget(daily_cap=2, path=p)
        try:
            # شبیه‌سازیِ روزِ قبل
            b._save({"date": "2020-01-01", "spent": 2, "resting": 0})
            d = b._load()
            assert d["spent"] == 2
            # spend امروز باید reset کند
            r = b.spend("active")
            assert r["remaining"] >= 1, "باید در روزِ جدید reset شود"
        finally:
            _setbio(False)


def test_budget_resting_free():
    """ضربانِ resting نباید از بودجه بخورد (مجانی)."""
    _setbio(True)
    with tempfile.TemporaryDirectory() as td:
        b = cardiac.BeatBudget(daily_cap=1, path=Path(td) / "bud.json")
        try:
            for _ in range(10):
                b.spend("resting")
            s = b.status()
            assert s["spent"] == 0   # resting خرج نمی‌کند
            assert s["resting"] == 10
            assert not s["depleted"]
        finally:
            _setbio(False)


def test_budget_thread_safety():
    """spend هم‌زمان از چند نخ نباید race کند."""
    import threading
    _setbio(True)
    with tempfile.TemporaryDirectory() as td:
        b = cardiac.BeatBudget(daily_cap=100, path=Path(td) / "bud.json")
        try:
            def worker():
                for _ in range(50):
                    b.spend("active")
            threads = [threading.Thread(target=worker) for _ in range(4)]
            for t in threads: t.start()
            for t in threads: t.join()
            s = b.status()
            assert s["spent"] == 200, f"باید دقیقاً ۲۰۰ باشد، نه {s['spent']}"
        finally:
            _setbio(False)


# ── قانونِ ۳: baroreflex ─────────────────────────────────────────────────────────
def test_baroreflex_flag_off_noop():
    _setbio(False)
    br = cardiac.Baroreflex()
    br.stimulate(0.5)   # نباید اثر بگذارد
    assert br.current_factor() == 1.0


def test_baroreflex_acceleration():
    """factor < ۱ → شتاب → ضریبِ فعّال < ۱."""
    _setbio(True)
    try:
        br = cardiac.Baroreflex(ttl_s=60)
        br.stimulate(0.5)   # فروش/تعامل → شتاب ۵۰٪
        f = br.current_factor()
        assert f < 1.0, f"شتاب باید factor<۱ بدهد: {f}"
        assert f >= 0.2      # کفِ ایمن
    finally:
        _setbio(False)


def test_baroreflex_pressure_slowdown():
    """factor > ۱ → فشار → ضریبِ فعّال > ۱ (کُندی)."""
    _setbio(True)
    try:
        br = cardiac.Baroreflex(ttl_s=60)
        br.stimulate(2.0)   # CONFLICT → کُندی
        f = br.current_factor()
        assert f > 1.0
    finally:
        _setbio(False)


def test_baroreflex_decay():
    """محرک بعد از TTL محو می‌شود."""
    _setbio(True)
    try:
        br = cardiac.Baroreflex(ttl_s=0.05)   # ۵۰ms
        br.stimulate(0.5)
        assert br.current_factor() < 1.0
        time.sleep(0.1)   # عبور از TTL
        assert br.current_factor() == 1.0   # محو شد
    finally:
        _setbio(False)


def test_baroreflex_factor_clamped():
    """factorهایِ افراطی نباید کف/سقف را رد کنند."""
    _setbio(True)
    try:
        br = cardiac.Baroreflex(ttl_s=60)
        br.stimulate(0.001)   # خیلی شدید
        assert br.current_factor() >= 0.2
        br2 = cardiac.Baroreflex(ttl_s=60)
        br2.stimulate(100.0)  # خیلی شدید
        assert br2.current_factor() <= 3.0
    finally:
        _setbio(False)


# ── ترکیب: effective_period ──────────────────────────────────────────────────────
def test_effective_period_flag_off():
    _setbio(False)
    r = cardiac.effective_period(base_period_s=300)
    assert r["period_s"] == 300
    assert not r["effective"]


def test_effective_period_combines_all():
    _setbio(True)
    try:
        with tempfile.TemporaryDirectory() as td:
            b = cardiac.BeatBudget(daily_cap=10, path=Path(td) / "bud.json")
            br = cardiac.Baroreflex(ttl_s=60)
            br.stimulate(0.7)   # شتاب
            r = cardiac.effective_period(base_period_s=300, budget=b, baro=br)
            assert r["effective"]
            assert r["period_s"] > 0
            assert r["bio"] is not None
            assert r["budget"] is not None
            assert r["baro_factor"] < 1.0   # شتاب
    finally:
        _setbio(False)


def test_effective_period_depleted_forces_resting():
    """وقتی بودجه تمام است، period به سمتِ سقف (whale-mode عمیق) می‌رود."""
    _setbio(True)
    try:
        with tempfile.TemporaryDirectory() as td:
            b = cardiac.BeatBudget(daily_cap=1, path=Path(td) / "bud.json")
            b.spend("active")   # تمام
            b.spend("active")   # depleted
            r = cardiac.effective_period(base_period_s=300, budget=b, baro=cardiac.Baroreflex())
            assert r["period_s"] >= cardiac.BIO_MAX_PERIOD_S * 0.5   # به سمتِ سقف
    finally:
        _setbio(False)


# ── snapshot (برای UI) ────────────────────────────────────────────────────────────
def test_status_snapshot_flag_off():
    _setbio(False)
    s = cardiac.status_snapshot()
    assert s["enabled"] is False


def test_status_snapshot_flag_on():
    _setbio(True)
    try:
        s = cardiac.status_snapshot()
        assert s["enabled"] is True
        assert "bio_rhythm" in s
        assert "budget" in s
    finally:
        _setbio(False)


# ── TINVها دست‌نخورده ───────────────────────────────────────────────────────────
def test_cardiac_does_not_import_chrono_internals():
    """cardiac نباید به داخلِ HLC/phi/effector-gate دست بزند (TINV حفظ)."""
    src = (_HERE.parent / "cardiac.py").read_text("utf-8")
    forbidden = ["hlc_tick", "hlc_merge", "PhiAccrual", "EffectorGate", "beat_once",
                 "leg_clock", "gated_effect"]
    found = [f for f in forbidden if f in src]
    assert not found, f"cardiac نباید به chrono internals دست بزند: {found}"
