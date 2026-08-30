"""freshness.py — staleness و تاریخ منابع.

بند ۷: تاریخ انتشار و تاریخ رویداد را جدا ثبت کن. نبودن تاریخ confidence را
کاهش می‌دهد. snippet موتور جست‌وجو شاهد نهایی نیست.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Iterable, Optional

from .contracts import Freshness, Source

# آستانهٔ staleness: برای حوزهٔ AI (حرکت سریع)، >180 روز = stale
STALE_DAYS_AI = 180
# افق مأموریت ما ۷ روز است؛ ولی staleness بر اساس سن منبع تعریف می‌شود نه افق


_ISO_DATE_RE = re.compile(
    r"(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])"
)
_LOOSE_DATE_RE = re.compile(
    r"(19|20)\d{2}[/\-.](0[1-9]|1[0-2])[/\-.](0[1-9]|[12]\d|3[01])"
)


def extract_date(text: str) -> Optional[str]:
    """استخراج YYYY-MM-DD از متن. فقط اولین تطبیق معتبر."""
    if not text:
        return None
    m = _ISO_DATE_RE.search(text)
    if m:
        return m.group(0)
    m = _LOOSE_DATE_RE.search(text)
    if m:
        raw = m.group(0)
        for sep in ("/", ".", "-"):
            if sep in raw:
                y, mo, d = raw.split(sep)
                return f"{y}-{mo}-{d}"
    return None


def parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def is_future(s: Optional[str], today: Optional[date] = None) -> bool:
    """منبع با تاریخ آینده نامعتبر است (تست adversarial بند ۱۶)."""
    d = parse_date(s)
    if d is None:
        return False
    today = today or datetime.now(timezone.utc).date()
    return d > today


def compute_freshness(
    sources: Iterable[Source | dict],
    *,
    observed_at: Optional[str] = None,
    today: Optional[date] = None,
    stale_days: int = STALE_DAYS_AI,
) -> Freshness:
    """محاسبهٔ Freshness از لیست منابع."""
    today = today or datetime.now(timezone.utc).date()
    observed = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    dates: list[date] = []
    for s in sources:
        sd = _src_date(s)
        d = parse_date(sd)
        if d is not None and not is_future(sd, today):
            dates.append(d)

    oldest = min(dates) if dates else None
    newest = max(dates) if dates else None
    span = (newest - oldest).days if (oldest and newest) else None

    stale = False
    if newest is not None:
        age_days = (today - newest).days
        stale = age_days > stale_days

    return Freshness(
        observed_at=observed,
        oldest_source_date=oldest.isoformat() if oldest else None,
        newest_source_date=newest.isoformat() if newest else None,
        stale=stale,
        days_span=span,
    )


def _src_date(s: Source | dict) -> Optional[str]:
    if isinstance(s, dict):
        return s.get("source_date")
    return s.source_date


def missing_date_penalty(sources: Iterable[Source | dict]) -> float:
    """جریمهٔ confidence برای منابعی که تاریخ ندارند (0..1)."""
    items = list(sources)
    if not items:
        return 1.0
    missing = sum(1 for s in items if not _src_date(s))
    return missing / len(items)
