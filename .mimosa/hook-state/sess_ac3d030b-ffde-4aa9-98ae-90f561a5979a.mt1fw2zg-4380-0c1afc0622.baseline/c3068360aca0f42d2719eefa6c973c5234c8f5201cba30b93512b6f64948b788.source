# -*- coding: utf-8 -*-
"""تست‌های parser نرخ RBA — موارد الزامی دستور مالک (۲۰۲۶-۰۸-۲۰ ~۱۵:۴۵)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rba_parser import parse_f11

REQ = "20-Aug-2026"


def _csv(rows_str: str) -> bytes:
    return rows_str.encode("utf-8")


BASE = """F11.1  EXCHANGE RATES
Title,Other,A$1=USD
Description,x,AUD/USD Exchange Rate
Frequency,x,Daily
Type,x,Indicative
Units,x,USD

Source,x,WM/Reuters
Publication date,19-Aug-2026,19-Aug-2026
Series ID,FXRTWI,FXRUSD
,,,
17-Aug-2026,,0.7114
18-Aug-2026,,0.7101
19-Aug-2026,,0.7070
"""


def test_bom_and_metadata_pass():
    raw = ("﻿" + BASE + f"{REQ},,0.7080\n").encode("utf-8")   # BOM
    r = parse_f11(raw, REQ)
    assert r.ok and r.rate == 0.7080, r.reasons
    assert r.quote_convention == "USD_per_AUD"
    assert r.raw_sha256  # هش raw قبل از parse


def test_blank_final_row_pass():
    r = parse_f11(_csv(BASE + f"{REQ},,0.7080\n,,,\n\n"), REQ)
    assert r.ok and r.rate == 0.7080


def test_na_latest_blocks():
    r = parse_f11(_csv(BASE + f"{REQ},,NA\n"), REQ)
    assert r.verdict == "BLOCK" and any("na-latest" in x for x in r.reasons)


def test_duplicate_date_blocks():
    r = parse_f11(_csv(BASE + f"{REQ},,0.7080\n{REQ},,0.7090\n"), REQ)
    assert r.verdict == "BLOCK" and any("duplicate" in x for x in r.reasons)


def test_missing_required_row_is_fx_stale():
    r = parse_f11(_csv(BASE), REQ)
    assert r.verdict == "BLOCK_FX_STALE"


def test_wrong_series_blocks():
    bad = BASE.replace("FXRUSD", "FXRCNY")
    r = parse_f11(_csv(bad + f"{REQ},,7.1\n"), REQ)
    assert r.verdict == "BLOCK" and "series-id-unknown" in r.reasons


def test_inverted_convention_fails():
    bad = BASE.replace("A$1=USD", "USD$1=A").replace("Units,x,USD", "Units,x,AUD")
    r = parse_f11(_csv(bad + f"{REQ},,0.7080\n"), REQ)
    assert r.verdict == "FAIL" and "quote-convention" in r.reasons[0]


def test_oversized_rate_inversion_fails():
    r = parse_f11(_csv(BASE + f"{REQ},,1.4124\n"), REQ)      # ≈ 1/0.7071 وارونه
    assert r.verdict == "FAIL" and "inverted" in r.reasons[0]


def test_future_published_date_blocks():
    future = BASE.replace("19-Aug-2026", "31-Dec-2099") + f"{REQ},,0.7080\n"
    r = parse_f11(_csv(future), REQ)
    assert r.verdict == "BLOCK" and "future" in r.reasons[0]


def test_raw_hash_replay_stable():
    raw = _csv(BASE + f"{REQ},,0.7080\n")
    a, b = parse_f11(raw, REQ), parse_f11(raw, REQ)
    assert a.raw_sha256 == b.raw_sha256 and a.ok
    other = _csv(BASE + f"{REQ},,0.7081\n")
    assert parse_f11(other, REQ).raw_sha256 != a.raw_sha256
