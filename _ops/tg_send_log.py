#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tg_send_log.py — شمردنِ آنچه واقعاً فرستاده می‌شود، قبل از ساختنِ ضدِاسپم.

چرا این ماژول **قبل از** dedup می‌آید (رأیِ مالک ۲۰۲۶-۰۷-۲۶): سه گزارشِ پیاپی
«اسپم» را علتِ اصلی خواندند و هیچ‌کدام حجمِ واقعیِ پیام‌ها را نشمرده بود. یکی از
آن‌ها digestِ ۲۴ساعته را «اسپم» نامید و یکی دیگر lockِ نبضِ زنده را ردِ نمونهٔ
تکراری خواند. ساختنِ ضدِاسپم بدونِ شمردنِ اسپم یعنی همان اشتباه، این‌بار در کد.

پس این‌جا فقط **اندازه می‌گیرد**. تصمیمِ dedup بعد از دیدنِ عدد گرفته می‌شود.

ناوردی‌ها: append-only · stdlib-only · صفر شبکه · fail-soft (خطای دیسک هرگز
ارسالِ تلگرام را نمی‌کشد) · **هرگز متنِ پیام را ذخیره نمی‌کند** — فقط hash، تا
لاگ به یک کپیِ دومِ محتوای مالک تبدیل نشود.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE / "budget"))
import opslib  # noqa: E402

FLAG = "OCTOPUS_TG_SEND_LOG"
RETAIN_S = 48 * 3600.0          # پنجرهٔ نگه‌داری؛ بیش از این هرس می‌شود
_PRUNE_EVERY = 200              # هر N نوشتن یک‌بار هرس (نه هر بار — I/O بیهوده)
_since_prune = 0


def _path() -> Path:
    return opslib.STATE_DIR / "tg-send-log.jsonl"


def enabled() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def digest(text: str) -> str:
    """اثرِ انگشتِ محتوا. متن هرگز ذخیره نمی‌شود — فقط این."""
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:16]


def record(*, chat_id=None, topic_id=None, text: str = "", stream=None,
           ok: bool = True) -> bool:
    """یک ارسال را ثبت کن. خروجی: ثبت شد؟ هر خطا → False، بی‌سروصدا."""
    global _since_prune
    if not enabled():
        return False
    try:
        row = {"ts": round(time.time(), 3),
               "chat": chat_id, "topic": topic_id,
               "stream": str(stream) if stream else None,
               "sha": digest(text), "chars": len(str(text or "")),
               "ok": bool(ok)}
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        _since_prune += 1
        if _since_prune >= _PRUNE_EVERY:
            _since_prune = 0
            prune()
        return True
    except Exception:  # noqa: BLE001 — لاگ هرگز نباید ارسال را بکشد
        return False


def _rows(window_s: float | None = None) -> list:
    p = _path()
    if not p.exists():
        return []
    cutoff = (time.time() - window_s) if window_s else 0.0
    out = []
    try:
        for ln in p.read_text("utf-8", errors="replace").splitlines():
            if not ln.strip():
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            if float(d.get("ts") or 0) >= cutoff:
                out.append(d)
    except OSError:
        return []
    return out


def prune(retain_s: float = RETAIN_S) -> int:
    """خطوطِ کهنه‌تر از پنجره را دور بریز. خروجی = تعدادِ خطوطِ باقی‌مانده."""
    try:
        keep = _rows(retain_s)
        p = _path()
        if not p.exists():
            return 0
        p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in keep)
                     + ("\n" if keep else ""), encoding="utf-8")
        return len(keep)
    except Exception:  # noqa: BLE001
        return -1


def stats(window_h: float = 24.0) -> dict:
    """تصویرِ واقعیِ حجم و تکرار در پنجرهٔ داده‌شده.

    `duplicates` = ارسال‌هایی که دقیقاً همان محتوا در همان مقصد قبلاً رفته بود.
    این عددی است که تصمیمِ ساختنِ dedup باید بر آن سوار شود — نه بر حدس."""
    rows = _rows(window_h * 3600.0)
    if not rows:
        return {"window_h": window_h, "sends": 0, "unique": 0, "duplicates": 0,
                "by_stream": {}, "top_repeats": [], "note": "هیچ ارسالی ثبت نشده"}
    from collections import Counter
    keys = [f"{r.get('chat')}|{r.get('topic')}|{r.get('sha')}" for r in rows]
    c = Counter(keys)
    dup = sum(n - 1 for n in c.values())
    by_stream = Counter(str(r.get("stream")) for r in rows)
    top = [{"repeats": n, "stream": k.split("|")[0]} for k, n in c.most_common(5) if n > 1]
    return {"window_h": window_h, "sends": len(rows), "unique": len(c),
            "duplicates": dup,
            "duplicate_pct": round(100.0 * dup / len(rows), 1),
            "by_stream": dict(by_stream), "top_repeats": top}


if __name__ == "__main__":  # pragma: no cover — گزارشِ دستی، صفر ارسال
    w = float(sys.argv[1]) if len(sys.argv) > 1 else 24.0
    print(json.dumps(stats(w), ensure_ascii=False, indent=2))
