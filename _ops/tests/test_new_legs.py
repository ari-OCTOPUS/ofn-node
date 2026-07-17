#!/usr/bin/env python3
"""test_new_legs.py — WP-F · LEG-01: چهار پای status صادق (mining/crypto/accounting/knowledge).

اثبات می‌کند:
  * هر چهار ماژول import می‌شوند و helperِ <name>_status() قرارداد را می‌دهد:
    کلیدهای هستهٔ {"leg","live","signal","note"} + کلیدِ افزودهٔ "age_days" (برنامه ۷ —
    صداقتِ پاها؛ float گرد یا None) با نوعِ درست، leg == نامِ درست.
  * هیچ helperی روی دادهٔ گمشده crash نمی‌کند (منبع را به tmp خالی مونکی‌پچ می‌کنیم).
  * crypto/accounting وقتی منبعِ واقعی *تازه* هست → live=True با سیگنالِ واقعی؛ وقتی نیست → live=False.
  * mining/knowledge همیشه live=False (skeletonِ صادق، بدونِ منبعِ ماشینی).
  * accounting هرگز مقدار/عددِ مالی echo نمی‌کند (فقط شمارشِ workbook).

صفر نوشتن روی مسیرِ زنده: منابع به tmp مونکی‌پچ می‌شوند. اجرا: python -X utf8 test_new_legs.py
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
_LEGS = _HERE.parent / "legs"
if str(_LEGS) not in sys.path:
    sys.path.insert(0, str(_LEGS))

import crypto_leg      # noqa: E402
import accounting_leg  # noqa: E402
import mining_leg      # noqa: E402
import knowledge_leg   # noqa: E402

_CONTRACT_KEYS = {"leg", "live", "signal", "note"}
_HELPERS = {
    "mining": mining_leg.mining_status,
    "crypto": crypto_leg.crypto_status,
    "accounting": accounting_leg.accounting_status,
    "knowledge": knowledge_leg.knowledge_status,
}


def _tmp() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="newlegs-test-"))


def _assert_contract(name: str, d: dict) -> None:
    assert isinstance(d, dict), f"{name}: dict لازم است"
    # برنامه ۷ (صداقتِ پاها): قراردادِ هسته دست‌نخورده + کلیدِ افزودهٔ age_days —
    # چکِ قبلی set(d) == هسته بود؛ افزودنِ age_days عمداً آن را superset کرد (فقط ADD).
    assert _CONTRACT_KEYS <= set(d.keys()), f"{name}: کلیدها {set(d.keys())}"
    assert "age_days" in d, f"{name}: کلیدِ age_days (قراردادِ تازگی) لازم است"
    assert d["age_days"] is None or isinstance(d["age_days"], (int, float)), \
        f"{name}: age_days باید عدد یا None باشد، شد {type(d['age_days']).__name__}"
    assert d["leg"] == name, f"{name}: leg == {d['leg']}"
    assert isinstance(d["live"], bool), f"{name}: live باید bool باشد"
    assert isinstance(d["signal"], str) and d["signal"], f"{name}: signal رشتهٔ ناخالی"
    assert isinstance(d["note"], str) and d["note"], f"{name}: note رشتهٔ ناخالی"


def test_all_four_import_and_honor_contract() -> None:
    """هر چهار helper قرارداد {leg,live,signal,note} را با نوعِ درست می‌دهند (روی دادهٔ واقعی)."""
    for name, fn in _HELPERS.items():
        _assert_contract(name, fn())


def test_never_crashes_on_missing_data() -> None:
    """منبع را به tmpِ خالی مونکی‌پچ کن — هیچ helper نباید crash کند؛ live باید False شود."""
    d = _tmp()
    crypto_leg.CRYPTO_DIR = d / "no-crypto"
    accounting_leg.ACCT_DIR = d / "no-acct"
    mining_leg.PROJECT_DIR = d / "no-mining"
    knowledge_leg.KNOWLEDGE_DIR = d / "no-knowledge"
    for name, fn in _HELPERS.items():
        r = fn()
        _assert_contract(name, r)
        assert r["live"] is False, f"{name}: بدونِ منبع باید live=False باشد"


def test_mining_and_knowledge_are_honest_skeletons() -> None:
    """mining/knowledge حتی با پوشهٔ پروژه‌ی موجود، هرگز live=True جعلی نمی‌شوند."""
    for name in ("mining", "knowledge"):
        r = _HELPERS[name]()
        _assert_contract(name, r)
        assert r["live"] is False, f"{name} باید skeleton (live=False) باشد"
        assert r["signal"] == "skeleton", f"{name}: signal == skeleton"


def test_crypto_reports_real_signal_when_source_present() -> None:
    """با یک analysis JSONِ *تازهٔ* ساختگی در tmp، crypto باید live=True و buy/sell/hold بدهد.
    برنامه ۷ (صداقتِ پاها): fixtureِ قبلی نامِ ثابتِ 2026-01-01 داشت و live=True را
    بی‌قیدِ تازگی assert می‌کرد (همان دروغِ قدیمی)؛ حالا تایم‌استمپِ نام = الان (دادهٔ واقعاً تازه)."""
    import datetime as _dt
    _now = _dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    d = _tmp()
    cdir = d / "crypto"
    cdir.mkdir(parents=True)
    (cdir / f"cryptoquant_{_now}.json").write_text("{}", encoding="utf-8")
    analysis = {"summary": {"total_coins": 10, "buy_signals": 3, "sell_signals": 2, "hold_signals": 5}}
    (cdir / f"cryptoquant_analysis_{_now}.json").write_text(
        json.dumps(analysis), encoding="utf-8")
    crypto_leg.CRYPTO_DIR = cdir
    r = crypto_leg.crypto_status()
    _assert_contract("crypto", r)
    assert r["live"] is True, "با داده باید live=True"
    assert "buy=3" in r["signal"] and "sell=2" in r["signal"] and "hold=5" in r["signal"], r["signal"]


def test_accounting_counts_workbooks_without_reading_values() -> None:
    """accounting با workbookهای ساختگی: live=True، سیگنال فقط تعداد (صفر مقدار/عددِ داخلی)."""
    d = _tmp()
    adir = d / "acct"
    adir.mkdir(parents=True)
    for nm in ("a.xlsx", "b.xlsx", "c.xlsx"):
        (adir / nm).write_bytes(b"not-a-real-xlsx-secret-1234")   # هرگز خوانده نمی‌شود
    accounting_leg.ACCT_DIR = adir
    r = accounting_leg.accounting_status()
    _assert_contract("accounting", r)
    assert r["live"] is True, "با workbook باید live=True"
    assert r["signal"] == "workbooks=3", r["signal"]
    # صداقتِ PII: محتوای فایل هرگز در خروجی ظاهر نمی‌شود
    assert "1234" not in json.dumps(r, ensure_ascii=False), "نباید هیچ مقدار/محتوای فایل leak شود"


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for _t in _tests:
        _t()
        print(f"  ✓ {_t.__name__}")
    print(f"✅ test_new_legs: {len(_tests)}/{len(_tests)} سبز")
