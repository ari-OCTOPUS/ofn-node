#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rba_parser.py — parser مقاوم نرخ روزانهٔ RBA (دستور مالک 2026-08-20 ~15:45).

قواعد: انتخاب ردیف بر اساس «تاریخ + Series ID» (نه آخرین سطر)؛ BOM/metadata/
سطر خالی تحمل می‌شود؛ NA/دودوتاریخ/آینده/سری غلط/قرارداد نقل مبهم → BLOCK؛
raw bytes قبل از parse هش می‌شوند (replay ممکن). تاریخ‌ها بر مبنای سیدنی‌اند."""
from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass, field

SERIES_ID = "FXRUSD"
QUOTE_TITLE = "A$1=USD"
QUOTE_UNITS = "USD"


@dataclass
class ParseResult:
    verdict: str                                   # PASS | BLOCK_* | FAIL_*
    reasons: list = field(default_factory=list)
    raw_sha256: str = ""
    series_col: int = -1
    published_date: str = ""                       # DD-Mon-YYYY سیدنی
    rate: float = 0.0
    rows_seen: int = 0
    quote_convention: str = ""

    @property
    def ok(self) -> bool:
        return self.verdict == "PASS"


def parse_f11(raw: bytes, required_date: str) -> ParseResult:
    """raw = بایت‌های CSV رسمی F11.1 · required_date = تاریخ سیدنی مطلوب."""
    res = ParseResult(verdict="PASS", raw_sha256=hashlib.sha256(raw).hexdigest())
    if not raw:
        return _b(res, "BLOCK", "empty-raw")
    text = raw.decode("utf-8-sig", errors="replace")     # BOM
    rows = [r for r in csv.reader(io.StringIO(text))]
    res.rows_seen = len(rows)
    if len(rows) < 12:
        return _b(res, "BLOCK", "structure-too-short")

    # سطرها را برچسب‌محور پیدا کن — ایندکس ثابت با سطرهای خالی/چندسطری می‌شکند
    def _row_with(label: str):
        return next((r for r in rows[:15] if r and r[0].strip() == label), None)

    sid_row_i, sid_row = next(((i, r) for i, r in enumerate(rows[:15])
                               if SERIES_ID in r), (-1, None))
    if sid_row is None:
        return _b(res, "BLOCK", "series-id-unknown")
    res.series_col = sid_row.index(SERIES_ID)
    title_row, units_row, pub_row = (_row_with("Title"), _row_with("Units"),
                                     _row_with("Publication date"))
    if title_row is None or units_row is None:
        return _b(res, "BLOCK", "header-labels-missing")
    title = title_row[res.series_col] if len(title_row) > res.series_col else ""
    units = units_row[res.series_col] if len(units_row) > res.series_col else ""
    if title.strip() != QUOTE_TITLE or units.strip() != QUOTE_UNITS:
        # مثلاً USD/AUD وارونه یا سری دیگر → قرارداد نقل مبهم
        res.quote_convention = f"{title}|{units}"
        return _b(res, "FAIL", f"quote-convention-ambiguous:{title}/{units}")
    res.quote_convention = "USD_per_AUD"

    if pub_row is None:
        return _b(res, "BLOCK", "missing-published-date")
    published = pub_row[res.series_col].strip() if len(pub_row) > res.series_col else ""
    if not published:
        return _b(res, "BLOCK", "missing-published-date")

    # ردیف‌های داده برای همین سری، بر اساس تاریخِ خواسته‌شده
    matches = []
    for r in rows[sid_row_i + 1:]:
        if len(r) > res.series_col and r[0].strip() == required_date:
            matches.append(r[res.series_col].strip())
    if len(matches) == 0:
        return _b(res, "BLOCK_FX_STALE",
                  f"no-row-for-{required_date};last-published={published}")
    if len(matches) > 1:
        return _b(res, "BLOCK", f"duplicate-date:{len(matches)}")
    v = matches[0]
    if v in ("", "NA", "N/A", "-"):
        return _b(res, "BLOCK", "na-latest-value")
    try:
        rate = float(v)
    except ValueError:
        return _b(res, "BLOCK", f"unparseable-rate:{v!r}")
    if rate <= 0:
        return _b(res, "BLOCK", "rate-nonpositive")
    # وارونگیِ USD/AUD (معکوس) — باند تاریخی معقول FXRUSD؛ خروج از باند = FAIL
    if not (0.40 <= rate <= 1.25):
        return _b(res, "FAIL", f"aud-usd-inverted-suspected:{rate}")

    # تاریخ انتشارِ آینده (نسبت به سیدنیِ الان) → BLOCK
    from datetime import datetime, timezone, timedelta
    syd = timezone(timedelta(hours=10))
    try:
        pub_dt = datetime.strptime(published, "%d-%b-%Y").replace(tzinfo=syd)
    except ValueError:
        return _b(res, "BLOCK", f"unparseable-published-date:{published}")
    if pub_dt.date() > datetime.now(syd).date():
        return _b(res, "BLOCK", "future-published-date")

    res.published_date = published
    res.rate = rate
    return res


def _b(res: ParseResult, verdict: str, reason: str) -> ParseResult:
    res.verdict = verdict
    res.reasons.append(reason)
    return res
