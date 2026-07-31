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
# ریشهٔ باگِ «prune هرگز اجرا نمی‌شود» (یافتهٔ اسکنِ عمیق ۲۰۲۶-۰۷-۳۱):
# `_since_prune` state ِ per-process بود و روی هر ری‌استارت صفر می‌شد. یک
# پروسهٔ بلندمدت که ۲۰۰ بار record صدا نمی‌زد، prune را هرگز اجرا نمی‌کرد.
# حل: در کنارِ شمارنده، timestamp ِ آخرین prune را هم در یک فایل کوچک نگه
# می‌داریم تا across-restart هم کار کند. اگر فایل بگوید RETAIN_S گذشته، prune
# می‌زند حتی اگر شمارنده کم باشد.
_PRUNE_STATE = opslib.STATE_DIR / "tg-send-log-prune.json"


def _since_last_prune_s() -> float:
    """ثانیه از آخرین prune — across restartها (از فایل، نه memory)."""
    try:
        d = json.loads(_PRUNE_STATE.read_text("utf-8"))
        return time.time() - float(d.get("last_prune_ts", 0))
    except Exception:  # noqa: BLE001
        return float("inf")   # هرگز prune نشده ⇒ اجرا شود


def _mark_pruned() -> None:
    try:
        _PRUNE_STATE.parent.mkdir(parents=True, exist_ok=True)
        _PRUNE_STATE.write_text(json.dumps({"last_prune_ts": time.time()}),
                                encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


_since_prune = 0


def _path() -> Path:
    return opslib.STATE_DIR / "tg-send-log.jsonl"


def enabled() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def digest(text: str) -> str:
    """اثرِ انگشتِ محتوا. متن هرگز ذخیره نمی‌شود — فقط این."""
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:16]


# حالتِ سه‌گانهٔ رسید (یافتهٔ boundary-13): تا امروز فقط `ok: bool` بود، پس
# یک پیامِ HELD یا DENIED از یک پیامِ هرگز-ساخته‌شده غیرقابل‌تمایز بود. حالا
# هر رویداد یک ردیف می‌گیرد:
#   sent    — واقعاً فرستاده شد (ok قدیمی)
#   held    — سیاستِ سطح نگه‌اش داشت (HOLD/DIGEST)
#   blocked — سیاستِ ورودی ردش کرد (DENY)
STATES = frozenset({"sent", "held", "blocked"})


def record(*, chat_id=None, topic_id=None, text: str = "", stream=None,
           ok: bool = True, bot_role: str | None = None,
           surface: str | None = None,
           state: str | None = None,
           disposition: str | None = None) -> bool:
    """یک رویدادِ ارسال/نگه‌داشت/رد را ثبت کن. خروجی: ثبت شد؟ هر خطا → False.

    رسیدِ سه‌حالتی (منشور UX-8 + رفعِ gate 8، وحدتِ دو لِین ۲۰۲۶-۰۷-۳۱):
      - state: sent/held/blocked — «HOLD شد» و «هرگز تولید نشد» دیگر یک شکل
        نیستند. sent = واقعاً POST شد (ok موفق/ناموفق را می‌گوید)؛ held =
        ماشینِ hold/سکوت نگهش داشت (گم نشد)؛ blocked = ساختاراً نمی‌توانست
        برود (not-wired / سیاستِ ورودی).
      - disposition: نامِ مستعارِ همان پارامتر از لِینِ خواهر (attempted≡sent)
        — هر دو واژگان یک ردیف می‌سازند؛ state اگر هر دو داده شوند برنده است.
      - bot_role: outer|inner — بدونش «به DM ِ inner رفت» ابطال‌ناپذیر بود
        (هر دو بات به یک chat می‌فرستند). surface: dm/group/held/None.
    صداکنندهٔ قدیمی بی‌تغییر: پیش‌فرض‌ها همان ردیفِ دیروز را می‌سازند."""
    global _since_prune
    if not enabled():
        return False
    _raw = state or ("sent" if disposition == "attempted" else disposition)
    _state = _raw if _raw in STATES else "sent"
    try:
        row = {"ts": round(time.time(), 3),
               "chat": chat_id, "topic": topic_id,
               "stream": str(stream) if stream else None,
               "sha": digest(text), "chars": len(str(text or "")),
               "ok": bool(ok),
               "state": _state}
        if bot_role:
            row["bot_role"] = str(bot_role)
        if surface:
            row["surface"] = str(surface)
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        _since_prune += 1
        # prune هم روی شمارنده و هم روی زمان (across-restart) — هر کدام زودتر
        if _since_prune >= _PRUNE_EVERY or _since_last_prune_s() > RETAIN_S:
            _since_prune = 0
            _mark_pruned()
            prune()
        return True
    except Exception:  # noqa: BLE001 — لاگ هرگز نباید ارسال را بکشد
        return False


def _rows(window_s: float | None = None, now: float | None = None) -> list:
    p = _path()
    if not p.exists():
        return []
    # ساعتِ تزریقی — درسِ «ساعتِ نیمه‌تزریقی»: اگر فقط بعضی شاخه‌ها `now` را
    # بگیرند و بقیه `time.time()` بخوانند، پنجرهٔ تست با پنجرهٔ واقعی فرق
    # می‌کند و تست چیزی را می‌سنجد که وجود ندارد. تنها ساعتِ این تابع همین است.
    _now = float(now) if now is not None else time.time()
    cutoff = (_now - window_s) if window_s else 0.0
    out = []
    try:
        for ln in p.read_text("utf-8", errors="replace").splitlines():
            if not ln.strip():
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            # ⚠️ ۲۰۲۶-۰۷-۳۱: این خط قبلاً `float(d.get("ts") or 0)` بی‌محافظ
            # بود. یک ردیف با `ts` ِ غیرعددی (لاگِ نیمه‌نوشته/دستکاری‌شده)
            # کلِ `stats()` را با ValueError می‌کشت — یعنی یک بایتِ خراب کلِ
            # لایهٔ اندازه‌گیری را خاموش می‌کرد. حالا فقط همان ردیف می‌افتد.
            try:
                ts = float(d.get("ts") or 0)
            except (TypeError, ValueError):
                continue
            if ts >= cutoff:
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


def stats(window_h: float = 24.0, now: float | None = None) -> dict:
    """تصویرِ واقعیِ حجم و تکرار در پنجرهٔ داده‌شده.

    `duplicates` = ارسال‌هایی که دقیقاً همان محتوا در همان مقصد قبلاً رفته بود.
    این عددی است که تصمیمِ ساختنِ dedup باید بر آن سوار شود — نه بر حدس.

    `now` اختیاری است (پیش‌فرض = ساعتِ سیستم) تا تست بتواند پنجره را قطعی
    بسنجد؛ صداکنندهٔ قدیمی بایت‌به‌بایت همان رفتار را می‌گیرد."""
    rows = _rows(window_h * 3600.0, now=now)
    if not rows:
        return {"window_h": window_h, "sends": 0, "unique": 0, "duplicates": 0,
                "by_stream": {}, "top_repeats": [], "note": "هیچ ارسالی ثبت نشده"}
    from collections import Counter
    keys = [f"{r.get('chat')}|{r.get('topic')}|{r.get('sha')}" for r in rows]
    c = Counter(keys)
    dup = sum(n - 1 for n in c.values())
    by_stream = Counter(str(r.get("stream")) for r in rows)
    # کلیدِ `c` سه‌تکه است: chat|topic|sha — پس `[0]` **chat** است نه stream.
    # تا امروز اسمش "stream" بود؛ یک برچسبِ دروغ در خودِ لایهٔ اندازه‌گیری.
    # هیچ صداکننده‌ای این کلید را نمی‌خواند (weekly_review فقط `sends` را
    # می‌گیرد)، پس تغییرِ نام هیچ‌چیزی را نمی‌شکند و یک دروغِ کوچک را می‌بندد.
    top = [{"repeats": n, "chat": k.split("|")[0]} for k, n in c.most_common(5) if n > 1]
    return {"window_h": window_h, "sends": len(rows), "unique": len(c),
            "duplicates": dup,
            "duplicate_pct": round(100.0 * dup / len(rows), 1),
            "by_stream": dict(by_stream), "top_repeats": top}


# ── خطِ نبض: تنها مصرف‌کنندهٔ ساعتیِ همین اندازه‌گیری ────────────────────────
# چرا اضافه شد (۲۰۲۶-۰۷-۳۱): `stats()` از ۲۶ جولای وجود داشت و تنها خواننده‌اش
# مرورِ **هفتگی** بود، آن هم فقط فیلدِ `sends`. یعنی درصدِ تکرار — دقیقاً عددی
# که کلِ این ماژول برای دیدنش ساخته شد — هیچ‌وقت به چشمِ مالک نمی‌رسید. یک
# سنجهٔ خوانده‌نشده با سنجهٔ نبود فرقی ندارد.
_PULSE_MIN_SENDS = 3   # زیرِ این، خبری نیست که ارزشِ یک خط در پالس را داشته باشد
_FA_DIGITS = str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫")
_LRI, _PDI = "⁦", "⁩"   # ایزولهٔ bidi دورِ تکهٔ LTR (منشور UX-۹)


def _fa(v) -> str:
    return str(v).translate(_FA_DIGITS)


def _top_stream(by_stream: dict) -> "str | None":
    """پرحجم‌ترین جریان. مساوی → نامِ الفبایی (قطعی، نه وابسته به ترتیبِ dict)."""
    if not by_stream:
        return None
    name, n = sorted(by_stream.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))[0]
    if not n:
        return None
    # `str(None)` یعنی ارسالِ بی‌جریان — پنهانش نمی‌کنیم؛ اگر بیشترِ ترافیک
    # بی‌جریان است، همان خودش یافته است.
    return "بی‌جریان" if str(name) in ("None", "", "null") else str(name)


def pulse_line(window_h: float = 24.0, now: float | None = None) -> "str | None":
    """یک خطِ فارسی برای پالسِ ساعتیِ لنگر — یا None وقتی حرفی برای گفتن نیست.

    ناوردی‌ها: صفر side-effect (فقط می‌خواند) · fail-soft (هر خطا → None،
    پالس هرگز به‌خاطرِ این خط نمی‌میرد) · هرگز متنِ پیام را لو نمی‌دهد (فقط
    شمار و نامِ جریان).

    None برمی‌گردد وقتی: فلگِ ثبت خاموش است (عدد ناقص را «واقعیت» جا نمی‌زنیم)
    · هیچ ردیفی در پنجره نیست · حجم زیرِ `_PULSE_MIN_SENDS` است."""
    try:
        if not enabled():
            # ثبت خاموش ⇒ هر عددی زیرشمارش است. سکوت صادق‌تر از عددِ ناقص است.
            return None
        s = stats(window_h, now=now)
        sends = int(s.get("sends") or 0)
        if sends < _PULSE_MIN_SENDS:
            return None
        parts = [f"📨 ارسالِ {_fa(f'{float(window_h):g}')} ساعت: {_fa(sends)}",
                 f"یکتا {_fa(int(s.get('unique') or 0))}"]
        dup = float(s.get("duplicate_pct") or 0.0)
        if dup >= 1.0:
            parts.append(f"تکراری {_fa(int(round(dup)))}٪")
        top = _top_stream(s.get("by_stream") or {})
        if top:
            # ایزوله فقط دورِ تکهٔ **لاتین**؛ گذاشتنش دورِ متنِ فارسی جهت را
            # برعکس می‌کند و همان bidi ای را می‌شکند که قرار بود درست کند.
            parts.append("بیشترین: "
                         + (f"{_LRI}{top}{_PDI}" if top.isascii() else top))
        return " · ".join(parts)
    except Exception:  # noqa: BLE001 — سنجه هرگز نباید پالس را بکشد
        return None


if __name__ == "__main__":  # pragma: no cover — گزارشِ دستی، صفر ارسال
    w = float(sys.argv[1]) if len(sys.argv) > 1 else 24.0
    print(json.dumps(stats(w), ensure_ascii=False, indent=2))
    print(pulse_line(w) or "(خطِ نبض: چیزی برای گفتن نیست)")
