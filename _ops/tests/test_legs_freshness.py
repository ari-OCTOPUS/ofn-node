#!/usr/bin/env python3
"""test_legs_freshness.py — برنامه ۷ (صداقتِ پاها): «live» یعنی داده جریان دارد، نه فایل هست.

اثبات می‌کند (fixtureهای tmp با mtimeِ کنترل‌شده از طریقِ os.utime):
  * leg_freshness.age_days: مسیرِ None/گمشده → None؛ فایلِ ۱۰روزه → ≈۱۰؛ ارزیابیِ
    لحظهٔ فراخوانی (تغییرِ mtime بینِ دو call بدونِ re-import دیده می‌شود).
  * leg_freshness.fresh: تازه → True؛ کهنه → False؛ گمشده → False (fail-closed).
  * crypto: analysisِ تازه → live=True + age_days≈0؛ همان فایل backdate به ۳۰ روز →
    live=False ولی سیگنالِ buy/sell/hold همچنان صادقانه گزارش می‌شود.
  * accounting: workbookِ تازه → live=True؛ backdate به ۶۰ روز → live=False + age_days≈۶۰.
  * mining/knowledge: همیشه live=False (skeletonِ صادق) ولی age_daysِ منبعِ واقعی را
    گزارش می‌کنند؛ noteِ mining منبعِ بعدی (coordinator decisions.jsonl) را نام می‌برد.
  * قراردادِ status دست‌نخورده: کلیدهای هستهٔ {leg,live,signal,note} + age_days (فقط ADD).

صفر نوشتن روی مسیرِ زنده: منابع به tmp مونکی‌پچ می‌شوند. اجرا: python -X utf8 test_legs_freshness.py
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import time

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("legs-freshness")

_LEGS = _HERE.parent / "legs"
if str(_LEGS) not in sys.path:
    sys.path.insert(0, str(_LEGS))

import leg_freshness   # noqa: E402
import crypto_leg      # noqa: E402
import accounting_leg  # noqa: E402
import mining_leg      # noqa: E402
import knowledge_leg   # noqa: E402

_CORE_KEYS = {"leg", "live", "signal", "note"}
_DAY_S = 86400.0


def _tmp() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="legfresh-test-"))


def _backdate(p: pathlib.Path, days: float) -> None:
    """mtimeِ کنترل‌شده: فایل را days روز به عقب می‌برد (os.utime، بدونِ لمسِ محتوا)."""
    ts = time.time() - days * _DAY_S
    os.utime(p, (ts, ts))


def _assert_contract(name: str, d: dict) -> None:
    """قراردادِ هسته + age_days — کلیدها فقط ADD شده‌اند، هرگز rename."""
    assert isinstance(d, dict), f"{name}: dict لازم است"
    assert _CORE_KEYS <= set(d.keys()), f"{name}: کلیدهای هسته ناقص: {set(d.keys())}"
    assert "age_days" in d, f"{name}: کلیدِ age_days لازم است"
    assert d["age_days"] is None or isinstance(d["age_days"], (int, float)), \
        f"{name}: age_days باید عدد یا None باشد"
    assert d["leg"] == name and isinstance(d["live"], bool)
    assert isinstance(d["signal"], str) and d["signal"]
    assert isinstance(d["note"], str) and d["note"]


# ── helper: age_days / fresh ────────────────────────────────────────────────────

def test_age_days_none_and_missing() -> None:
    """مسیرِ None یا ناموجود → None (fail-soft، هرگز exception)."""
    assert leg_freshness.age_days(None) is None
    assert leg_freshness.age_days(_tmp() / "ghost.json") is None


def test_age_days_backdated_file() -> None:
    """فایلِ ۱۰روزه → age ≈ ۱۰ (پنجرهٔ ۰٫۱ روز برای زمانِ اجرا)."""
    p = _tmp() / "old.json"
    p.write_text("{}", encoding="utf-8")
    _backdate(p, 10)
    a = leg_freshness.age_days(p)
    assert a is not None and 9.9 <= a <= 10.1, a


def test_age_days_is_call_time_not_cached() -> None:
    """ارزیابیِ لحظهٔ فراخوانی: تغییرِ mtime بینِ دو call بدونِ re-import دیده می‌شود."""
    p = _tmp() / "flow.json"
    p.write_text("{}", encoding="utf-8")
    _backdate(p, 20)
    a1 = leg_freshness.age_days(p)
    _backdate(p, 1)
    a2 = leg_freshness.age_days(p)
    assert a1 is not None and a2 is not None and a2 < a1, (a1, a2)
    assert 0.9 <= a2 <= 1.1, a2


def test_fresh_true_false_and_fail_closed() -> None:
    """تازه → True؛ کهنه → False؛ گمشده → False (سنِ نامعلوم هرگز «زنده» نیست)."""
    d = _tmp()
    p = d / "f.json"
    p.write_text("{}", encoding="utf-8")
    assert leg_freshness.fresh(p, 7) is True              # تازه (age≈0)
    _backdate(p, 8)
    assert leg_freshness.fresh(p, 7) is False             # کهنه
    assert leg_freshness.fresh(d / "ghost.json", 7) is False   # fail-closed


# ── crypto: آستانهٔ ۷ روز ───────────────────────────────────────────────────────

def _ts_name(days_old: float) -> str:
    """تایم‌استمپِ نامِ فایل به سبکِ ingest_raw (YYYY-MM-DD-HH-MM-SS)، days_old روز پیش."""
    import datetime as _dt
    ts = _dt.datetime.now() - _dt.timedelta(days=days_old)
    return ts.strftime("%Y-%m-%d-%H-%M-%S")


def _crypto_fixture(days_old: float) -> pathlib.Path:
    """دادهٔ crypto با سنِ کنترل‌شده: هم تایم‌استمپِ نام هم mtime هم‌سن (سازگار)."""
    cdir = _tmp() / "crypto"
    cdir.mkdir(parents=True)
    nm = _ts_name(days_old)
    (cdir / f"cryptoquant_{nm}.json").write_text("{}", encoding="utf-8")
    ap = cdir / f"cryptoquant_analysis_{nm}.json"
    ap.write_text('{"summary": {"buy_signals": 3, "sell_signals": 2, "hold_signals": 5}}',
                  encoding="utf-8")
    if days_old > 0:
        for p in cdir.iterdir():
            _backdate(p, days_old)
    return cdir


def test_crypto_fresh_analysis_is_live() -> None:
    """analysisِ تازه (age≈0) → live=True + age_days موجود و ≈0."""
    crypto_leg.CRYPTO_DIR = _crypto_fixture(0)
    r = crypto_leg.crypto_status()
    _assert_contract("crypto", r)
    assert r["live"] is True, r
    assert r["age_days"] is not None and r["age_days"] <= 0.1, r["age_days"]
    assert "buy=3" in r["signal"], r["signal"]


def test_crypto_stale_analysis_not_live_but_honest_signal() -> None:
    """همان داده backdate به ۳۰ روز → live=False + age_days≈۳۰؛ سیگنال همچنان گزارش می‌شود."""
    crypto_leg.CRYPTO_DIR = _crypto_fixture(30)
    r = crypto_leg.crypto_status()
    _assert_contract("crypto", r)
    assert r["live"] is False, "دادهٔ ۳۰روزه نباید live باشد (آستانه ۷ روز)"
    assert r["age_days"] is not None and 29.8 <= r["age_days"] <= 30.2, r["age_days"]
    assert "buy=3" in r["signal"] and "sell=2" in r["signal"], r["signal"]


def test_crypto_boundary_just_inside_threshold() -> None:
    """دقیقاً داخلِ آستانه (۶ روز) → هنوز live=True."""
    crypto_leg.CRYPTO_DIR = _crypto_fixture(6)
    r = crypto_leg.crypto_status()
    assert r["live"] is True, r
    assert 5.8 <= r["age_days"] <= 6.2, r["age_days"]


def test_crypto_name_timestamp_beats_touched_mtime() -> None:
    """دروغِ mtime: analysisِ ۳۰روزه (به نام) که دیروز touch/copy شده → live=False.
    (همان کیسِ درختِ زنده: cryptoquant_analysis_2026-06-15 با mtimeِ تازه.)"""
    cdir = _tmp() / "crypto"
    cdir.mkdir(parents=True)
    ap = cdir / f"cryptoquant_analysis_{_ts_name(30)}.json"
    ap.write_text('{"summary": {"buy_signals": 1, "sell_signals": 1, "hold_signals": 1}}',
                  encoding="utf-8")                       # mtime = الان (touched)
    crypto_leg.CRYPTO_DIR = cdir
    r = crypto_leg.crypto_status()
    _assert_contract("crypto", r)
    assert r["live"] is False, "تایم‌استمپِ نام (سنِ واقعیِ داده) باید بر mtimeِ تازه غالب باشد"
    assert r["age_days"] is not None and 29.8 <= r["age_days"] <= 30.2, r["age_days"]


def test_crypto_missing_dir_age_null() -> None:
    """بدونِ منبع → live=False و age_days=None (نه عددِ جعلی)."""
    crypto_leg.CRYPTO_DIR = _tmp() / "no-crypto"
    r = crypto_leg.crypto_status()
    _assert_contract("crypto", r)
    assert r["live"] is False and r["age_days"] is None, r


# ── accounting: آستانهٔ ۳۵ روز ──────────────────────────────────────────────────

def test_accounting_fresh_workbook_is_live() -> None:
    """workbookِ تازه → live=True + سیگنالِ شمارشیِ بی‌PII دست‌نخورده."""
    adir = _tmp() / "acct"
    adir.mkdir(parents=True)
    for nm in ("a.xlsx", "b.xlsx"):
        (adir / nm).write_bytes(b"never-read")
    accounting_leg.ACCT_DIR = adir
    r = accounting_leg.accounting_status()
    _assert_contract("accounting", r)
    assert r["live"] is True and r["signal"] == "workbooks=2", r
    assert r["age_days"] is not None and r["age_days"] <= 0.1, r["age_days"]


def test_accounting_stale_workbooks_not_live() -> None:
    """workbookها ۶۰ روز دست‌نخورده → live=False + age_days≈۶۰ (دروغِ نوامبر ۲۰۲۴ تمام)."""
    adir = _tmp() / "acct"
    adir.mkdir(parents=True)
    p = adir / "old.xlsx"
    p.write_bytes(b"never-read")
    _backdate(p, 60)
    accounting_leg.ACCT_DIR = adir
    r = accounting_leg.accounting_status()
    _assert_contract("accounting", r)
    assert r["live"] is False, "workbookِ ۶۰روزه نباید live باشد (آستانه ۳۵ روز)"
    assert 59.8 <= r["age_days"] <= 60.2, r["age_days"]
    assert r["signal"] == "workbooks=1", r["signal"]


def test_accounting_newest_workbook_wins() -> None:
    """سن از *تازه‌ترین* workbook می‌آید: یکی کهنه + یکی تازه → live=True."""
    adir = _tmp() / "acct"
    adir.mkdir(parents=True)
    old = adir / "old.xlsx"
    old.write_bytes(b"never-read")
    _backdate(old, 400)
    (adir / "new.xlsx").write_bytes(b"never-read")        # تازه
    accounting_leg.ACCT_DIR = adir
    r = accounting_leg.accounting_status()
    assert r["live"] is True and r["age_days"] <= 0.1, r


# ── mining/knowledge: skeletonِ صادق + سنِ منبعِ واقعی ─────────────────────────

def test_mining_honest_skeleton_reports_source_age() -> None:
    """mining هرگز live نمی‌شود؛ سنِ coordinator/data/decisions.jsonl صادقانه گزارش می‌شود."""
    dpath = _tmp() / "decisions.jsonl"
    dpath.write_text('{"decision": "x"}\n', encoding="utf-8")
    _backdate(dpath, 20)
    mining_leg.DECISIONS_PATH = dpath
    r = mining_leg.mining_status()
    _assert_contract("mining", r)
    assert r["live"] is False and r["signal"] == "skeleton", r
    assert 19.8 <= r["age_days"] <= 20.2, r["age_days"]
    assert "decisions.jsonl" in r["note"], r["note"]      # منبعِ واقعیِ بعدی نام برده می‌شود


def test_mining_missing_source_age_null() -> None:
    """منبعِ گمشده → age_days=None ولی note همچنان منبعِ واقعیِ بعدی را نام می‌برد."""
    mining_leg.DECISIONS_PATH = _tmp() / "ghost.jsonl"
    r = mining_leg.mining_status()
    _assert_contract("mining", r)
    assert r["live"] is False and r["age_days"] is None, r
    assert "decisions.jsonl" in r["note"], r["note"]


def test_knowledge_honest_skeleton_reports_newest_note_age() -> None:
    """knowledge هرگز live نمی‌شود؛ سنِ تازه‌ترین نوت (نه کهنه‌ترین) گزارش می‌شود."""
    kdir = _tmp() / "knowledge"
    (kdir / "sub").mkdir(parents=True)
    old = kdir / "old.md"
    old.write_text("# کهنه\n", encoding="utf-8")
    _backdate(old, 90)
    new = kdir / "sub" / "new.md"
    new.write_text("# تازه\n", encoding="utf-8")
    _backdate(new, 5)
    knowledge_leg.KNOWLEDGE_DIR = kdir
    r = knowledge_leg.knowledge_status()
    _assert_contract("knowledge", r)
    assert r["live"] is False and r["signal"] == "skeleton", r
    assert 4.8 <= r["age_days"] <= 5.2, r["age_days"]


def test_knowledge_missing_dir_age_null() -> None:
    knowledge_leg.KNOWLEDGE_DIR = _tmp() / "no-knowledge"
    r = knowledge_leg.knowledge_status()
    _assert_contract("knowledge", r)
    assert r["live"] is False and r["age_days"] is None, r


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    _failed = 0
    for _t in _tests:
        try:
            _t()
            print(f"  ✓ {_t.__name__}")
        except AssertionError as _e:
            _failed += 1
            print(f"  ✗ {_t.__name__}: {_e}")
    if _failed:
        print(f"❌ test_legs_freshness: {_failed}/{len(_tests)} قرمز")
        sys.exit(1)
    print(f"✅ test_legs_freshness: {len(_tests)}/{len(_tests)} سبز")
