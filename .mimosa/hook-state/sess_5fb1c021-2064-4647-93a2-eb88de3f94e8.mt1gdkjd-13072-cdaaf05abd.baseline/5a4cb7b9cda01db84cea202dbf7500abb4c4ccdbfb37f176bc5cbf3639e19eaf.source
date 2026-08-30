#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tg_traffic.py — ارگانیسم چقدر حرف می‌زند، و به چه شکل؟

چرا این ابزار هست (فاز ۱، ۲۰۲۶-۰۸-۰۴)
──────────────────────────────────────
سنجهٔ پذیرشِ فاز ۱ این است: «پیامِ نو در آن مقصد صفر شد و `message_id` ثابت
ماند». تا امروز جوابِ این سؤال یک اسکریپتِ یک‌بارمصرف بود. حالا یک فرمان است.

⚠️ و مهم‌تر: این ابزار برای جلوگیری از خطایی ساخته شد که **خودم مرتکب شدم**.
روی کلِ لاگ (۵۸ ساعت) شمردم و دیدم «۲۱۶ پیامِ یکسان» — و نزدیک بود آن را یک
باگِ زنده گزارش کنم. ولی توزیعِ ساعتی نشان داد آن رگبار مالِ ۰۸-۰۲ بوده و از
۰۸-۰۳ خودش رفع شده؛ در ۲۴ ساعتِ اخیر نرخِ تکرار **۴٪** است.

    عددِ تجمعی می‌گوید «چقدر»؛ فقط توزیعِ زمانی می‌گوید «هنوز؟»

پس این گزارش **همیشه** هر دو را کنارِ هم می‌گذارد و اگر رگبار تاریخی باشد
صریحاً می‌گوید — تا خواننده‌ای که فقط سرِ جدول را می‌خواند گمراه نشود.
(درسِ خواهر: «اول ok-rate، بعد نام‌گذاریِ حادثه».)

ناوردی‌ها: فقط‌خواندنی · stdlib-only · صفر شبکه · هرگز متن یا secret چاپ
نمی‌کند (لاگِ ارسال اصلاً متن ذخیره نمی‌کند، فقط هش).
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE / "budget"))
import opslib  # noqa: E402

SCHEMA = "tg-traffic.v1"

#: زیرِ این نسبت، «رگبار» یک پدیدهٔ گذشته است نه وضعِ جاری.
_STALE_BURST_RATIO = 0.25


def _rows() -> list:
    p = opslib.STATE_DIR / "tg-send-log.jsonl"
    out = []
    try:
        if not p.exists():
            return []
        for ln in p.read_text("utf-8", errors="replace").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                d = json.loads(ln)
                float(d.get("ts") or 0)
                out.append(d)
            except (ValueError, TypeError):
                continue
    except OSError:
        return []
    return out


def analyse(rows=None, *, hours: float = 24.0, now: "float | None" = None) -> dict:
    rows = _rows() if rows is None else list(rows)
    _now = float(now if now is not None else time.time())
    cutoff = _now - hours * 3600.0

    # ⚠️ گاردِ ردیفِ خراب **این‌جا** لازم است، نه فقط در `_rows()`. این تابع
    # هستهٔ تزریق‌پذیر و عمومی است؛ اگر فقط خواننده گارد داشته باشد، یک `ts` ِ
    # غیرعددی (لاگِ نیمه‌نوشته) کلِ گزارش را با ValueError می‌کشد — یعنی یک
    # بایتِ خراب لایهٔ اندازه‌گیری را خاموش می‌کند. همان باگی که یک بار
    # `tg_send_log.stats()` را کشت. فقط همان ردیف می‌افتد، نه کلِ گزارش.
    def _ts(r):
        try:
            return float(r.get("ts") or 0)
        except (TypeError, ValueError, AttributeError):
            return None

    rows = [r for r in rows if isinstance(r, dict) and _ts(r) is not None]
    win = [r for r in rows if _ts(r) >= cutoff]

    edits = [r for r in win if str(r.get("stream")) == "edit"]
    fresh = [r for r in win if str(r.get("stream")) != "edit"]
    sent = [r for r in fresh if str(r.get("state")) == "sent"]
    held = [r for r in fresh if str(r.get("state")) == "held"]
    blocked = [r for r in fresh if str(r.get("state")) == "blocked"]

    def key(r):
        return (str(r.get("stream")), r.get("chat"), r.get("topic"), r.get("sha"))

    c = collections.Counter(key(r) for r in sent)
    dup = sum(n - 1 for n in c.values())

    dm = [r for r in sent if isinstance(r.get("chat"), int) and r["chat"] > 0]
    grp = [r for r in sent if isinstance(r.get("chat"), int) and r["chat"] < 0]

    # ── گاردِ رگبارِ کهنه ──────────────────────────────────────────────────
    # همان اشتباهی که این ابزار برای جلوگیری از آن ساخته شد: یک خوشهٔ بزرگ
    # در **کلِ** لاگ که در پنجرهٔ اخیر تقریباً غایب است.
    all_c = collections.Counter(key(r) for r in rows
                                if str(r.get("stream")) != "edit"
                                and str(r.get("state")) == "sent")
    stale = []
    for k, n_all in all_c.most_common(5):
        if n_all < 10:
            break
        n_win = c.get(k, 0)
        if n_win <= max(2, n_all * _STALE_BURST_RATIO):
            ts = [_ts(r) for r in rows if key(r) == k]
            stale.append({"stream": k[0], "total": n_all, "in_window": n_win,
                          "first": _dt.datetime.fromtimestamp(min(ts)).strftime("%m-%d %H:%M"),
                          "last": _dt.datetime.fromtimestamp(max(ts)).strftime("%m-%d %H:%M")})

    per_hour = collections.Counter(
        _dt.datetime.fromtimestamp(_ts(r)).strftime("%m-%d %H") for r in sent)

    cards = {}
    try:
        sys.path.insert(0, str(_HERE / "telegram_center"))
        import living_card as _lc  # noqa: PLC0415
        cards = _lc.stats()
    except Exception:  # noqa: BLE001
        cards = {}

    return {
        "schema": SCHEMA, "hours": hours,
        "new_sent": len(sent), "edits": len(edits),
        "held": len(held), "blocked": len(blocked),
        "duplicates": dup,
        "duplicate_pct": round(100.0 * dup / max(1, len(sent)), 1),
        "to_dm": len(dm), "to_group": len(grp),
        "by_stream": dict(collections.Counter(
            str(r.get("stream")) for r in sent).most_common()),
        "top_repeats": [{"stream": k[0], "chat": k[1], "topic": k[2], "n": n}
                        for k, n in c.most_common(5) if n > 1],
        "stale_bursts": stale,
        "per_hour": dict(sorted(per_hour.items())),
        "cards": cards,
    }


_FA = str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫")
_LRI, _PDI = "⁦", "⁩"


def _fa(v):
    return str(v).translate(_FA)


def _ltr(s):
    s = str(s or "")
    return f"{_LRI}{s}{_PDI}" if s and s.isascii() else s


def report(d=None, *, hours: float = 24.0) -> str:
    d = analyse(hours=hours) if d is None else d
    out = [f"📡 ترافیکِ {_fa(f'{d['hours']:g}')} ساعتِ اخیر",
           f"   پیامِ نوِ رفته {_fa(d['new_sent'])} · ویرایش {_fa(d['edits'])}"
           f" · نگه‌داشته {_fa(d['held'])} · مسدود {_fa(d['blocked'])}",
           f"   تکراری {_fa(d['duplicates'])} ({_fa(d['duplicate_pct'])}٪)"
           f" · به DM {_fa(d['to_dm'])} · به گروه {_fa(d['to_group'])}"]

    if d["by_stream"]:
        out.append("\n   پیامِ نو به تفکیکِ جریان:")
        for k, v in list(d["by_stream"].items())[:8]:
            out.append(f"      {_fa(v):>4}  {_ltr(k)}")

    if d["top_repeats"]:
        out.append("\n   پرتکرارترین‌ها در همین پنجره:")
        for t in d["top_repeats"]:
            out.append(f"      ↻ {_fa(t['n'])}×  {_ltr(t['stream'])}")

    # ⚠️ بندِ ضدِ گمراهی — بلندتر از بقیه چون دقیقاً همان‌جایی است که خطا رخ داد
    if d["stale_bursts"]:
        out.append("\n   ⚠️ رگبارِ **کهنه** (در کلِ لاگ بزرگ، در این پنجره تقریباً هیچ):")
        for s in d["stale_bursts"]:
            out.append(f"      {_ltr(s['stream'])}: کل {_fa(s['total'])} ·"
                       f" در این پنجره {_fa(s['in_window'])} ·"
                       f" از {_ltr(s['first'])} تا {_ltr(s['last'])}")
        out.append("      ← اگر فقط عددِ تجمعی را بخوانی، این را «باگِ زنده» "
                   "می‌بینی. نیست. گذشته است.")

    if d.get("cards"):
        c = d["cards"]
        out.append(f"\n   کارت‌های زنده: {_fa(c.get('cards', 0))} کارت ·"
                   f" ساخت {_fa(c.get('sends', 0))} ·"
                   f" ویرایش {_fa(c.get('edits', 0))} ·"
                   f" بازسازی {_fa(c.get('resends', 0))}")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="شکلِ ترافیکِ خروجیِ تلگرام")
    ap.add_argument("--hours", type=float, default=24.0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    d = analyse(hours=a.hours)
    print(json.dumps(d, ensure_ascii=False, indent=2) if a.json
          else report(d, hours=a.hours))
    return 0


if __name__ == "__main__":
    sys.exit(main())
