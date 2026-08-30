#!/usr/bin/env python3
"""test_bcm_real_sources.py — سیم‌کشیِ محافظه‌کارِ ۲۰۲۶-۰۸-۰۶: acquisition_data/
doctor_archive واقعی برای BCM (بستری که تا امروز فقط school_awareness می‌دید).

پس‌زمینه (تأییدشده روی کد): consolidation_beat هرگز acquisition_data=/doctor_archive=
پاس نمی‌دهد (organism.py:928-929، brain_worker.py:302-303) — هر دو پارامتر همیشه
None بودند، پس canonical_consolidation._enrich_with_latent فقط شاخهٔ school را
می‌دید و bcm-weights.json فقط کلیدِ ":school_awareness" داشت.

این تست دو منبعِ **واقعیِ** موجود را وصل می‌کند (نه ساختنِ داده‌ای نو):
  · acquisition_data ← budget/attribution.py::confirmed_revenue().by_cell
    (همان سطحی که fitness.py می‌خواند — درآمدِ CONFIRMED/ATTRIBUTED).
  · doctor_archive   ← doctor/calibration.py::get_verdict_history (chrono.db،
    جدولِ duration_marker) — ترجمه‌شده به outcome∈{approved,rejected}.

هر دو پشتِ فلگِ **نو و پیش‌فرض‌خاموش**:
  OCTOPUS_WIRE_CONSOLIDATION_ACQUISITION
  OCTOPUS_WIRE_CONSOLIDATION_ARCHIVE

اثباتِ لازم (per مگاپرامپت): (الف) با فلگ خاموش، رفتار بایت‌به‌بایت قبلی —
حتی وقتی دادهٔ واقعیِ بالادست وجود دارد. (ب) با فلگ روشن، همان دادهٔ واقعی تا
bcm.step() می‌رسد و کلیدهایی می‌سازد که در حالتِ فقط-school هرگز نبودند.
$0 آفلاین، stdlib-only.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("bcm-real-sources")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "neural"), str(_OPS / "doctor"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib   # noqa: E402
import wiring   # noqa: E402


ACQ_FLAG = "OCTOPUS_WIRE_CONSOLIDATION_ACQUISITION"
ARCH_FLAG = "OCTOPUS_WIRE_CONSOLIDATION_ARCHIVE"


def _clear_flags():
    for f in (ACQ_FLAG, ARCH_FLAG, "OCTOPUS_WIRE_CONSOLIDATION", "OCTOPUS_WIRE_BCM",
              "OCTOPUS_WIRE_NEURAL"):
        os.environ.pop(f, None)


def _seed_confirmed_revenue(cell="test-cell", amount=123.45):
    """درآمدِ CONFIRMED واقعی در ledgerِ ایزولهٔ harness — از مسیرِ واقعیِ
    propose→claim→confirm (نه نوشتنِ دستیِ فایل)."""
    import attribution
    aid = attribution.mint_id(1, day=opslib.today())
    attribution.propose(cell=cell, expected_aud=amount, lead="test-lead")
    attribution.claim(aid, ref="inv-1", amount_aud=amount)
    attribution.confirm(aid, cell=cell, amount_aud=amount, matched={"ref": "inv-1"})
    return aid


def _seed_verdict_history():
    """chrono.db واقعی (harness-ایزوله) با سه verdict — merged/rejected/ignored —
    از مسیرِ واقعیِ calibration.record_verdict (نه نوشتنِ دستیِ ردیف)."""
    import chrono as _chrono_mod
    from calibration import record_verdict
    db_path = opslib.STATE_DIR / "chrono.db"
    db = _chrono_mod.ChronoDB(str(db_path))
    record_verdict(db, "RFC-merge-1", "merged", bottleneck_key="k1")
    record_verdict(db, "RFC-reject-1", "rejected", bottleneck_key="k1")
    record_verdict(db, "RFC-ignore-1", "ignored", bottleneck_key="k1")
    return db


def _stack():
    os.environ["OCTOPUS_WIRE_NEURAL"] = "1"
    s = wiring.make_neural_stack()
    os.environ.pop("OCTOPUS_WIRE_NEURAL")
    return s


# ════════════════════════════════════════════════════════════════════════════════
# (۱) _real_acquisition_data — واحد
# ════════════════════════════════════════════════════════════════════════════════

def t_acquisition_flag_off_is_none_even_with_real_data():
    """فلگ خاموش (پیش‌فرض) → None، حتی وقتی درآمدِ CONFIRMEDِ واقعی در ledger هست."""
    _clear_flags()
    _seed_confirmed_revenue(cell="off-cell", amount=50.0)
    assert wiring._real_acquisition_data() is None, \
        "فلگ خاموش باید بی‌قیدوشرط None بدهد (no regression)"


def t_acquisition_flag_on_no_data_is_none():
    """فلگ روشن ولی هیچ CONFIRMEDای نیست → None (نه dictِ خالیِ جعلی)."""
    _clear_flags()
    os.environ[ACQ_FLAG] = "1"
    try:
        got = wiring._real_acquisition_data()
    finally:
        os.environ.pop(ACQ_FLAG, None)
    assert got is None, f"بدونِ CONFIRMED باید None باشد، شد {got}"


def t_acquisition_flag_on_reads_real_ledger():
    """فلگ روشن + CONFIRMEDِ واقعی → dictِ per-cell با همان مقدار."""
    _clear_flags()
    _seed_confirmed_revenue(cell="acq-cell-1", amount=77.5)
    os.environ[ACQ_FLAG] = "1"
    try:
        got = wiring._real_acquisition_data()
    finally:
        os.environ.pop(ACQ_FLAG, None)
    assert got is not None, "با دادهٔ CONFIRMEDِ واقعی نباید None باشد"
    assert got.get("acq-cell-1") == 77.5, f"مقدارِ درآمد اشتباه: {got}"


# ════════════════════════════════════════════════════════════════════════════════
# (۲) _real_doctor_archive — واحد
# ════════════════════════════════════════════════════════════════════════════════

def t_archive_flag_off_is_none_even_with_real_data():
    """فلگ خاموش (پیش‌فرض) → None، حتی وقتی chrono.db واقعاً verdict دارد."""
    _clear_flags()
    _seed_verdict_history()
    assert wiring._real_doctor_archive() is None, \
        "فلگ خاموش باید بی‌قیدوشرط None بدهد (no regression)"


def t_archive_flag_on_no_db_is_none():
    """فلگ روشن ولی chrono.db هنوز وجود ندارد → None (نه crash)."""
    _clear_flags()
    os.environ[ARCH_FLAG] = "1"
    try:
        got = wiring._real_doctor_archive()
    finally:
        os.environ.pop(ARCH_FLAG, None)
    assert got is None


def t_archive_flag_on_translates_real_verdicts():
    """فلگ روشن + verdictِ واقعی → outcome ترجمه‌شده؛ ignored حذف می‌شود."""
    _clear_flags()
    _seed_verdict_history()
    os.environ[ARCH_FLAG] = "1"
    try:
        got = wiring._real_doctor_archive()
    finally:
        os.environ.pop(ARCH_FLAG, None)
    assert got is not None, "با verdictِ واقعی نباید None باشد"
    outcomes = sorted(d.get("outcome") for d in got)
    assert outcomes == ["approved", "rejected"], \
        f"ترجمه اشتباه (ignored باید حذف شود): {outcomes}"
    rfc_ids = {d.get("rfc_id") for d in got}
    assert rfc_ids == {"RFC-merge-1", "RFC-reject-1"}, rfc_ids


# ════════════════════════════════════════════════════════════════════════════════
# (۳) consolidation_beat — سرِ خط، اثباتِ جریانِ واقعی تا bcm.step()
# ════════════════════════════════════════════════════════════════════════════════

def t_consolidation_beat_flags_off_matches_baseline():
    """فلگ‌های نو خاموش (پیش‌فرض) → verified_sources فقط چیزی است که همیشه بود
    (بدونِ school_bridge: هیچ‌کدام) — حتی با دادهٔ واقعیِ بالادست."""
    _clear_flags()
    _seed_confirmed_revenue(cell="noop-cell", amount=10.0)
    _seed_verdict_history()
    stack = _stack()
    if stack is None:
        return
    os.environ["OCTOPUS_WIRE_CONSOLIDATION"] = "1"
    try:
        result = wiring.consolidation_beat(stack, beat=720)
    finally:
        os.environ.pop("OCTOPUS_WIRE_CONSOLIDATION", None)
    assert result is not None
    assert "acquisition" not in result.verified_sources, \
        f"فلگ خاموش نباید acquisition بیاورد: {result.verified_sources}"
    assert "doctor_archive" not in result.verified_sources, \
        f"فلگ خاموش نباید doctor_archive بیاورد: {result.verified_sources}"


def t_consolidation_beat_flags_on_reaches_verified_sources():
    """هر دو فلگِ نو روشن + دادهٔ واقعی → هر دو منبع در verified_sources."""
    _clear_flags()
    _seed_confirmed_revenue(cell="on-cell", amount=99.0)
    _seed_verdict_history()
    stack = _stack()
    if stack is None:
        return
    os.environ["OCTOPUS_WIRE_CONSOLIDATION"] = "1"
    os.environ[ACQ_FLAG] = "1"
    os.environ[ARCH_FLAG] = "1"
    try:
        result = wiring.consolidation_beat(stack, beat=720)
    finally:
        os.environ.pop("OCTOPUS_WIRE_CONSOLIDATION", None)
        os.environ.pop(ACQ_FLAG, None)
        os.environ.pop(ARCH_FLAG, None)
    assert result is not None
    assert "acquisition" in result.verified_sources, \
        f"acquisition باید verified باشد: {result.verified_sources}"
    assert "doctor_archive" in result.verified_sources, \
        f"doctor_archive باید verified باشد: {result.verified_sources}"


def t_real_data_produces_different_bcm_weights_than_school_only_baseline():
    """اثباتِ **اثر**: با فلگ روشن، bcm.step() کلیدهایی می‌گیرد که با فلگ خاموش
    (baselineِ فقط-school، رفتارِ امروزِ زنده) اصلاً وجود ندارند."""
    _clear_flags()
    _seed_confirmed_revenue(cell="bcm-proof-cell", amount=250.0)
    _seed_verdict_history()

    # baseline: هر دو فلگِ نو خاموش (فقط OCTOPUS_WIRE_BCM روشن — همان profileِ زنده)
    stack_off = _stack()
    if stack_off is None:
        return
    os.environ["OCTOPUS_WIRE_CONSOLIDATION"] = "1"
    os.environ["OCTOPUS_WIRE_BCM"] = "1"
    try:
        r_off = wiring.consolidation_beat(stack_off, beat=720)
    finally:
        os.environ.pop("OCTOPUS_WIRE_CONSOLIDATION", None)
        os.environ.pop("OCTOPUS_WIRE_BCM", None)
    assert r_off is not None
    bcm_off = stack_off.get("bcm")
    keys_off = set(bcm_off.keys()) if bcm_off is not None else set()
    assert not any(":acquisition:" in k or ":doctor_archive:" in k for k in keys_off), \
        f"baselineِ فقط-school نباید کلیدِ acquisition/doctor_archive بسازد: {keys_off}"

    # armed: هر دو فلگِ نو + BCM روشن — روی stackِ تازه (epoch مستقل)
    stack_on = _stack()
    os.environ["OCTOPUS_WIRE_CONSOLIDATION"] = "1"
    os.environ["OCTOPUS_WIRE_BCM"] = "1"
    os.environ[ACQ_FLAG] = "1"
    os.environ[ARCH_FLAG] = "1"
    try:
        r_on = wiring.consolidation_beat(stack_on, beat=720)
    finally:
        os.environ.pop("OCTOPUS_WIRE_CONSOLIDATION", None)
        os.environ.pop("OCTOPUS_WIRE_BCM", None)
        os.environ.pop(ACQ_FLAG, None)
        os.environ.pop(ARCH_FLAG, None)
    assert r_on is not None
    bcm_on = stack_on.get("bcm")
    assert bcm_on is not None, "با OCTOPUS_WIRE_BCM روشن، bcm باید ساخته شود"
    keys_on = set(bcm_on.keys())
    assert any(":acquisition:" in k for k in keys_on), \
        f"bcm.step باید کلیدِ acquisition واقعی گرفته باشد: {keys_on}"
    assert any(":doctor_archive:" in k for k in keys_on), \
        f"bcm.step باید کلیدِ doctor_archive واقعی گرفته باشد: {keys_on}"
    assert keys_on != keys_off, \
        "وزنِ BCM با دادهٔ واقعی باید از baselineِ فقط-school متفاوت باشد"


if __name__ == "__main__":
    # ترتیب مهم است: تست‌های «بدون داده» باید **قبل از** هر seedِ ledger/chrono.db
    # اجرا شوند — همهٔ توابعِ این فایل روی همان OPS_DIR موقتِ harness (یک پروسه)
    # کار می‌کنند، پس ledger/chrono.db بینِ توابع append-only باقی می‌ماند.
    failed = harness.run([
        ("acquisition: فلگ روشن + بدون داده → None", t_acquisition_flag_on_no_data_is_none),
        ("archive: فلگ روشن + بدون db → None", t_archive_flag_on_no_db_is_none),
        ("acquisition: فلگ خاموش → None حتی با دادهٔ واقعی", t_acquisition_flag_off_is_none_even_with_real_data),
        ("acquisition: فلگ روشن + ledgerِ واقعی", t_acquisition_flag_on_reads_real_ledger),
        ("archive: فلگ خاموش → None حتی با دادهٔ واقعی", t_archive_flag_off_is_none_even_with_real_data),
        ("archive: فلگ روشن + verdictِ واقعی ترجمه می‌شود", t_archive_flag_on_translates_real_verdicts),
        ("consolidation_beat: فلگ‌های نو خاموش = baseline", t_consolidation_beat_flags_off_matches_baseline),
        ("consolidation_beat: فلگ‌های نو روشن → verified_sources", t_consolidation_beat_flags_on_reaches_verified_sources),
        ("اثباتِ اثر: bcm.step با دادهٔ واقعی از baseline متفاوت است", t_real_data_produces_different_bcm_weights_than_school_only_baseline),
    ])
    print(f"\n{'OK' if not failed else 'FAIL'} test_bcm_real_sources: "
          f"{9 - failed}/9 passed, {failed} failed")
    sys.exit(1 if failed else 0)
