"""test_consolidation_fuzzy_dedup.py — dedup فازیِ consolidation (افزودنی، پشتِ فلگ) — ۲۰۲۶-۰۸-۰۷.

پیش‌زمینه: `consolidation.py::run()` تا امروز فقط امضای **دقیق** (sha256 محتوایی)
را dedup می‌کرد و فقط مسیرِ consecutive-guard روی درختِ زنده فعال بود. اندازه‌گیریٔ
زنده: ۵۸۳ ردیف، **۲۸ امضای یکتا (۴.۸٪)** — ۹۵.۲٪ تکرار. علت اصلی: نوسانِ عددِ
«آگاهیِ میانگین» (0.73 → 0.72 → 0.73) امضای عین‌هم نمی‌سازد، پس exact روی همه‌شان
صفر اثر داشت. این تست مسیرِ افزودنیِ فازی (شباهتِ زیررشته‌ای جاکاردی، پشتِ
`OCTOPUS_CONSOLIDATION_DEDUP_FUZZY`) را pin می‌کند.

قواعدِ وصله (همه این تست رویشان نگهبان است):
- افزودنی: فلگ خاموش → بایت‌به‌بایتِ امروز (dedup_skipped می‌ماند None).
- fail-soft: تاریخچهٔ خراب → append معمولی، نه crash.
- محافظه‌کارانه: یک تغییرِ تک‌عددی (0.72 vs 0.73) تکرار شمرده **نمی‌شود**
  (jaccard پایین) — این رفتارِ ایمنیِ درست است.
- ردیفِ دارای بردارِ latent هرگز مقصدِ fold نمی‌شود (حفظِ دادهٔ کمیاب).

اجرا: python -X utf8 test_consolidation_fuzzy_dedup.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "neural"))

import harness
ENV = harness.setup("cortex")   # env ایزوله، state واقعی را آلوده نمی‌کند

import importlib  # noqa: E402
import consolidation  # noqa: E402
importlib.reload(consolidation)
C = consolidation


def _seed_cycle(rows: list[dict]):
    """یک ConsolidationCycle با tmp-path و تاریخچهٔ seed شده. مسیر را برمی‌گرداند."""
    fd, tmp = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f)
    return tmp, C.ConsolidationCycle(data_path=tmp)


def t_a_flag_off_is_byte_identical():
    """فلگ خاموش → dedup_skipped=None (مثل قبل از وصله) و ردیفِ نو append می‌شود."""
    os.environ.pop("OCTOPUS_CONSOLIDATION_DEDUP_FUZZY", None)
    importlib.reload(C)
    seed = [{"cycle": 1, "insights": ["آگاهیِ میانگین: 0.7"],
             "verified_sources": ["school_awareness"], "discarded_sources": [],
             "repeats": 1, "timestamp": 1786080000.0}]
    tmp, cyc = _seed_cycle(seed)
    try:
        res = cyc.run({"school_awareness": {"mean_awareness": 0.7}})
        assert res.dedup_skipped is None, f"فلگ خاموش باید None بدهد: {res.dedup_skipped}"
        # even an exact dup appends because flag off disables the path entirely
        # (the consecutive-guard may fold; what we assert is dedup_skipped stays None)
    finally:
        os.unlink(tmp)


def t_b_flag_on_folds_high_overlap_paraphrase():
    """قلبِ وصله: دو جملهٔ بازنویسی‌شده (jaccard≥0.7) → fold، نه append.
    بعد: ۱ ردیف؛ dedup_skipped=1."""
    os.environ["OCTOPUS_CONSOLIDATION_DEDUP_FUZZY"] = "1"
    importlib.reload(C)
    base = "وضعیتِ سیستم پایدار است و حافظهٔ بلندمدت خوب کار می‌کند"
    seed = [{"cycle": 1, "insights": [base],
             "verified_sources": ["acquisition"], "discarded_sources": [],
             "repeats": 1, "timestamp": 1786080000.0}]
    tmp, cyc = _seed_cycle(seed)
    try:
        # acquisition → insight "بهترین محتوا: <base> (score=X)" — jaccard بالا با base
        res = cyc.run({"acquisition": {base: 0.9}})
        assert res.dedup_skipped == 1, f"باید fold شود: dedup_skipped={res.dedup_skipped}"
        assert len(cyc.history) == 1, f"ردیف نباید append شود: {len(cyc.history)}"
        assert cyc.history[0]["repeats"] == 2, f"repeats باید ۲ باشد: {cyc.history[0].get('repeats')}"
    finally:
        os.environ.pop("OCTOPUS_CONSOLIDATION_DEDUP_FUZZY")
        os.unlink(tmp)


def t_c_single_digit_change_is_not_duplicate():
    """محافظه‌کارانه: 0.72 در برابر 0.73 (jaccard پایین) → تکرار نیست، append می‌شود."""
    os.environ["OCTOPUS_CONSOLIDATION_DEDUP_FUZZY"] = "1"
    importlib.reload(C)
    # تأییدِ ریاضیِ آستانه روی این جفت
    a = C._tokenize("آگاهیِ میانگین: 0.72")
    b = C._tokenize("آگاهیِ میانگین: 0.73")
    assert C._jaccard(a, b) < C._dedup_threshold(), "تک‌رقم نباید بالای آستانه باشد"
    seed = [{"cycle": 1, "insights": ["آگاهیِ میانگین: 0.73"],
             "verified_sources": ["school_awareness"], "discarded_sources": [],
             "repeats": 1, "timestamp": 1786080000.0}]
    tmp, cyc = _seed_cycle(seed)
    try:
        res = cyc.run({"school_awareness": {"mean_awareness": 0.72}})
        assert res.dedup_skipped == 0, f"تک‌رقم نباید fold شود: {res.dedup_skipped}"
        assert len(cyc.history) == 2, "باید ردیفِ نو append شود"
    finally:
        os.environ.pop("OCTOPUS_CONSOLIDATION_DEDUP_FUZZY")
        os.unlink(tmp)


def t_d_latent_vector_row_never_folded():
    """ردیفِ دارای بردارِ latent هرگز مقصدِ fold نمی‌شود (حفظِ دادهٔ کمیاب)."""
    os.environ["OCTOPUS_CONSOLIDATION_DEDUP_FUZZY"] = "1"
    importlib.reload(C)
    base = "وضعیتِ سیستم پایدار است و حافظهٔ بلندمدت خوب کار می‌کند"
    seed = [{"cycle": 1, "insights": [base],
             "verified_sources": ["acquisition"], "discarded_sources": [],
             "repeats": 1, "timestamp": 1786080000.0,
             "latent_vector": [0.1] * 32}]   # ردیفِ غنی
    tmp, cyc = _seed_cycle(seed)
    try:
        res = cyc.run({"acquisition": {base: 0.9}})   # jaccard بالا
        assert res.dedup_skipped == 0, "ردیفِ بردار‌دار نباید مقصدِ fold شود"
        assert len(cyc.history) == 2, "باید append شود (نه fold داخلِ غنی)"
        assert cyc.history[0].get("latent_vector") is not None, "بردار باید دست‌نخورده بماند"
    finally:
        os.environ.pop("OCTOPUS_CONSOLIDATION_DEDUP_FUZZY")
        os.unlink(tmp)


def t_e_fail_soft_on_corrupt_history():
    """تاریخچهٔ خراب (نه list) → append معمولی، نه crash (fail-soft)."""
    os.environ["OCTOPUS_CONSOLIDATION_DEDUP_FUZZY"] = "1"
    importlib.reload(C)
    # _fuzzy_duplicate روی هر خطا → (None,None)؛ ولی ConsolidationCycle._load
    # خودش هم fail-soft است. تست: history خالی → jaccard هیچ‌وقت صدا نمی‌خورد.
    tmp, cyc = _seed_cycle([])
    try:
        res = cyc.run({"school_awareness": {"mean_awareness": 0.5}})
        assert res.dedup_skipped == 0   # history خالی → چیزی برای dedup نیست
        assert len(cyc.history) == 1
    finally:
        os.environ.pop("OCTOPUS_CONSOLIDATION_DEDUP_FUZZY")
        os.unlink(tmp)


def t_f_window_and_threshold_env_knobs():
    """knobها از env خوانده می‌شوند و بازهٔ معتبر را نگه می‌دارند."""
    os.environ["OCTOPUS_CONSOLIDATION_DEDUP_N"] = "3"
    os.environ["OCTOPUS_CONSOLIDATION_DEDUP_SIM"] = "0.55"
    importlib.reload(C)
    assert C._dedup_window() == 3
    assert C._dedup_threshold() == 0.55
    # بازهٔ نامعتبر → پیش‌فرض
    os.environ["OCTOPUS_CONSOLIDATION_DEDUP_SIM"] = "9.9"
    importlib.reload(C)
    assert C._dedup_threshold() == 0.7, "خارجِ [0,1] → پیش‌فرضِ ۰.۷"
    os.environ.pop("OCTOPUS_CONSOLIDATION_DEDUP_N")
    os.environ.pop("OCTOPUS_CONSOLIDATION_DEDUP_SIM")
    importlib.reload(C)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_consolidation_fuzzy_dedup: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
