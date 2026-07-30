#!/usr/bin/env python3
"""discoveries.py — «چی یاد گرفتم / چی کشف کردم» به زبانِ آدمیزاد (جلسه ۴۶).

رأی مالک: «الان یادگیری نداره ... کشف و نوتیف به من نداره.» این ماژول کشف/یادگیری
را دیدنی می‌کند: هر بار سیستم چیزی از وب یاد گرفت یا مغز ایده‌ای ساخت، یک جملهٔ
سادهٔ فارسی در `state/discoveries.jsonl` ثبت می‌شود؛ خانهٔ ساده و نوتیف آن را نشان می‌دهند.

$0، stdlib-only، fail-soft، بی‌محتوا (فقط خلاصهٔ عمومی؛ هیچ secret/محتوای خصوصی).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

LOG = opslib.STATE_DIR / "discoveries.jsonl"
SEEN = opslib.STATE_DIR / "discoveries-seen.json"
MAX_KEEP = 200


def record(kind: str, summary: str) -> None:
    """یک کشف/یادگیریِ تازه ثبت کن. kind: research|idea|learn. summary: جملهٔ کوتاهِ فارسی."""
    summary = str(summary or "").strip()[:160]
    if not summary:
        return
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "kind": str(kind)[:20],
                                "summary": summary}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _all() -> list[dict]:
    try:
        if not LOG.exists():
            return []
        rows = []
        for ln in LOG.read_text("utf-8").splitlines()[-MAX_KEEP:]:
            try:
                rows.append(json.loads(ln))
            except ValueError:
                continue
        return rows
    except OSError:
        return []


def recent(n: int = 5, within_h: float = 72) -> list[dict]:
    cutoff = time.time() - within_h * 3600
    return [r for r in _all() if float(r.get("ts", 0)) >= cutoff][-n:][::-1]


def unseen_count() -> int:
    """چند کشفِ تازه از آخرین باری که مالک دید."""
    try:
        seen_ts = float((json.loads(SEEN.read_text("utf-8")) if SEEN.exists() else {})
                        .get("ts", 0))
    except (OSError, ValueError):
        seen_ts = 0.0
    return sum(1 for r in _all() if float(r.get("ts", 0)) > seen_ts)


def mark_seen() -> None:
    try:
        SEEN.parent.mkdir(parents=True, exist_ok=True)
        SEEN.write_text(json.dumps({"ts": time.time()}), "utf-8")
    except OSError:
        pass


# ── «به تو گفتم» ≠ «تو نگاه کردی» (۲۰۲۶-۰۷-۲۶) ──────────────────────────────
# `SEEN` فقط با کلیکِ مالک روی دکمهٔ «ببین چی یاد گرفتم» جلو می‌رود
# (`approval_channel` تنها فراخوانِ `mark_seen` است). پس اگر مالک کلیک نکند،
# `unseen_count` بی‌نهایت رشد می‌کند و نوتیف **همان انبارِ کامل را دوباره و
# دوباره اعلام می‌کند** — ۲۰۲۶-۰۷-۲۶ اندازه‌گیری شد: نشانگر از ۲۰۲۶-۰۷-۱۹ تکان
# نخورده بود و شمارنده روی ۱۰ بود.
# راه‌حل: دو نشانگرِ جدا. `NUDGED` می‌گوید «دربارهٔ این‌ها خبر دادم» و `SEEN`
# می‌ماند برای «مالک واقعاً نگاه کرد» — تا معنیِ دکمه از بین نرود.
NUDGED = opslib.STATE_DIR / "discoveries-nudged.json"


def unseen_since_nudge() -> int:
    """چند کشف از آخرین باری که *خبر دادم*. کلیکِ مالک اینجا بی‌ربط است."""
    try:
        ts = float((json.loads(NUDGED.read_text("utf-8")) if NUDGED.exists() else {})
                   .get("ts", 0))
    except (OSError, ValueError):
        ts = 0.0
    return sum(1 for r in _all() if float(r.get("ts", 0)) > ts)


def mark_nudged() -> None:
    """فقط بعد از ارسالِ **موفق** صدا زده شود — وگرنه یک نوتیفِ ازدست‌رفته
    برای همیشه دفن می‌شود (همان الگویی که کارتِ C6 را یک شبانه‌روز پنهان کرد)."""
    try:
        NUDGED.parent.mkdir(parents=True, exist_ok=True)
        NUDGED.write_text(json.dumps({"ts": time.time()}), "utf-8")
    except OSError:
        pass


def lines(n: int = 5) -> list[str]:
    """خطوطِ سادهٔ فارسی برای نمایش (بی‌محتوا).

    ۲۰۲۶-۰۷-۲۷ — `summary` از **متنِ خامِ صفحاتِ اینترنت** می‌آید و مصرف‌کننده‌هایش
    با `parse_mode=HTML` می‌فرستند. یک عنوانِ صفحه با `<` کافی بود تا تلگرام کلِ
    پیام را ۴۰۰ کند — و بدتر: دکمهٔ «ببین چی یاد گرفتم» رکوردها را **قبل از**
    ارسال «دیده‌شده» علامت می‌زند، یعنی یک عنوانِ مسموم می‌توانست کلِ صفِ کشف‌ها
    را برای همیشه دفن کند. escape اینجا هر دو مصرف‌کننده را پوشش می‌دهد."""
    import html
    icons = {"research": "🔍", "idea": "💡", "learn": "🧠"}
    return [f"{icons.get(r.get('kind'), '•')} {html.escape(str(r.get('summary', '')))}"
            for r in recent(n)]
