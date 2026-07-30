#!/usr/bin/env python3
"""recall_trend — «آیا واقعاً به یاد می‌آورد؟» را به یک سریِ زمانی تبدیل می‌کند.

سنجهٔ سومِ خودآگاهی در آزمونِ ۷ روزه: «یادآوریِ گذشتهٔ خودش». مسئله این بود که
سنجهٔ درست از قبل نوشته شده بود ولی هیچ‌کس صدایش نمی‌زد.

چه چیزی از قبل بود و چه چیزی نبود
─────────────────────────────────
`neural/consolidation.recall_reach(history)` دقیقاً همان تابعی است که لازم داریم، و
داکِ خودش استدلال می‌کند چرا سنجه‌های رقیب غلط‌اند (`proposal_accept_rate` رفتارِ
مالک را می‌سنجد نه سیستم؛ نسبتِ یکتا/کل کیفیتِ *نوشتن* را می‌سنجد نه یادآوری؛
شمارِ ردیف‌ها سنجهٔ *عمر* است نه یادگیری). ولی:

  • صفر صداکنندهٔ تولیدی داشت — یک عکسِ لحظه‌ای که فقط دستی گرفته می‌شد.
  • و بی‌سریِ زمانی، «بهتر شدن» **قابلِ اثبات نیست**. یک عدد روند نیست.

پس این ماژول چیزِ تازه‌ای اختراع نمی‌کند؛ فقط همان سنجه را **مهر می‌زند و نگه
می‌دارد** تا در پایانِ ۷ روز بتوان پرسید «بردِ بازیابی بالا رفت یا نه؟».

خطِ پایه‌ها (روی فایلِ زندهٔ `neural/consolidation.json`)
──────────────────────────────────────────────────────
  ۲۰۲۶-۰۷-۲۸ (داکِ recall_reach، ۵۳۸ ردیف):
      events=2  keys=8   reach_median=1.0  reach_max=2  self_ratio=0.375  coverage=0.0037
  ۲۰۲۶-۰۷-۳۰ (۵۴۰ ردیف، بعد از فیکسِ `similar(vector)` در 294dce5):
      events=4  keys=17  reach_median=2.0  reach_max=3  self_ratio=0.176  coverage=0.0074

یعنی فیکس اثر گذاشت (self_ratio پایین آمد = بازتابِ خود کمتر شد)، ولی ۴ رخداد در
۵۴۰ سیکل یعنی بازیابی هنوز تقریباً خاموش است. آزمون باید این را حرکت بدهد.

مرزها: **فقط‌خواندنی** روی `consolidation.json` (هرگز نمی‌نویسد)، append-only روی
سریِ خودش. $0 · stdlib · fail-soft.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "neural")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_RECALL_TREND"
SCHEMA = "recall_trend.v1"
CARD_TITLE = "🧠 بردِ بازیابی"
TREND = opslib.STATE_DIR / "neural" / "recall-trend.jsonl"

# ردیف‌های سنجه‌ای که «بهتر شدن» را نشان می‌دهند (بالاتر = بهتر)، و آن‌که برعکس است.
_HIGHER_BETTER = ("events", "keys", "reach_median", "reach_max", "coverage")
_LOWER_BETTER = ("self_ratio",)          # بازتابِ همین لحظه، نه یادآوری


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _history() -> list:
    """تاریخِ ادغام — فقط‌خواندنی. ساختارِ فایل یک list است (نه dict)."""
    try:
        import consolidation as _c
        raw = json.loads(_c._DATA_PATH.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — نبودِ فایل/نصب = سریِ خالی، نه کرش
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        h = raw.get("history")
        return h if isinstance(h, list) else []
    return []


def measure() -> dict:
    """عکسِ لحظه‌ای، بدونِ نوشتن. `{}` اگر زیرسیستم در دسترس نباشد."""
    try:
        import consolidation as _c
        hist = _history()
        out = dict(_c.recall_reach(hist) or {})
        out["rows"] = len(hist)
        return out
    except Exception:  # noqa: BLE001
        return {}


def sample(*, cycle: "str | int | None" = None, now: "float | None" = None) -> dict:
    """اندازه بگیر و **مهرزده** در سری ثبت کن. همین کار روند را ممکن می‌کند.

    مهرِ زمان از `opslib.now_iso()` می‌آید (ساعتِ سیستم)، نه از عددی که خودمان
    ساخته باشیم — درسِ «ساعتِ خودساخته در evidence = fabrication»."""
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    m = measure()
    if not m:
        return {"ok": False, "reason": "subsystem-unavailable"}
    rec = {"ts": opslib.now_iso(), "schema": SCHEMA, "cycle": cycle,
           "wall": float(now if now is not None else time.time()), **m}
    try:
        opslib.append_jsonl(TREND, rec)
    except (OSError, ValueError):
        return {"ok": False, "reason": "write-failed", **m}
    return {"ok": True, **rec}


def _rows() -> list:
    out: list = []
    try:
        if not TREND.exists():
            return out
        with open(TREND, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict) and d.get("schema") == SCHEMA:
                    out.append(d)
    except OSError:
        pass
    return out


def trend(window: int = 4) -> dict:
    """نیمهٔ اولِ سری را با نیمهٔ آخر بسنج — «بهتر شد؟» با عدد، نه با صفت.

    `window` = چند نمونهٔ ابتدا و چند نمونهٔ انتها. کمتر از دو نمونه = حکمی نیست
    (و صریح می‌گوید، نه اینکه صفر برگرداند و صفر شبیهِ «بدتر شد» به‌نظر بیاید)."""
    rows = _rows()
    if len(rows) < 2:
        return {"ok": False, "reason": "not-enough-samples", "samples": len(rows)}
    w = max(1, min(int(window), len(rows) // 2))
    first, last = rows[:w], rows[-w:]

    def _med(batch, key):
        vals = [r[key] for r in batch
                if isinstance(r.get(key), (int, float))]
        return statistics.median(vals) if vals else None

    deltas, verdict = {}, {}
    for key in _HIGHER_BETTER + _LOWER_BETTER:
        a, b = _med(first, key), _med(last, key)
        if a is None or b is None:
            continue
        deltas[key] = {"first": a, "last": b, "delta": round(b - a, 6)}
        if b == a:
            verdict[key] = "flat"
        elif key in _LOWER_BETTER:
            verdict[key] = "better" if b < a else "worse"
        else:
            verdict[key] = "better" if b > a else "worse"
    improved = sum(1 for v in verdict.values() if v == "better")
    worsened = sum(1 for v in verdict.values() if v == "worse")
    return {"ok": True, "samples": len(rows), "window": w,
            "deltas": deltas, "verdict": verdict,
            "improved": improved, "worsened": worsened,
            # حکمِ کلان عمداً محتاط است: «بهتر» فقط وقتی که هیچ سنجه‌ای بدتر نشده.
            "overall": ("better" if improved and not worsened
                        else "worse" if worsened and not improved
                        else "mixed" if improved or worsened else "flat")}


def card() -> tuple:
    """بی‌آرگومان، پس `capability_registry` خودش پیدایش می‌کند."""
    import html
    m = measure()
    if not m:
        return "🧠 <b>بردِ بازیابی</b>\n\nزیرسیستمِ ادغام در دسترس نیست.", []
    body = (f"🧠 <b>بردِ بازیابی</b>\n\n"
            f"رخدادِ بازیابی: <b>{m.get('events')}</b> در {m.get('rows')} سیکل\n"
            f"کلیدها: {m.get('keys')} · بردِ میانه: <b>{m.get('reach_median')}</b> · "
            f"بیشینه: {m.get('reach_max')}\n"
            f"بازتابِ خود: {round(float(m.get('self_ratio') or 0), 3)} "
            f"<i>(کمتر بهتر)</i>\n"
            f"پوشش: {round(float(m.get('coverage') or 0), 4)}")
    t = trend()
    if t.get("ok"):
        body += (f"\n\n<b>روند</b> ({t['samples']} نمونه): "
                 f"{html.escape(str(t['overall']))} — "
                 f"{t['improved']} بهتر، {t['worsened']} بدتر")
        for k, v in (t.get("deltas") or {}).items():
            if t["verdict"].get(k) != "flat":
                arrow = "▲" if v["delta"] > 0 else "▼"
                body += f"\n  {arrow} {html.escape(k)}: {v['first']} → {v['last']}"
    else:
        body += f"\n\n<i>روند: {html.escape(str(t.get('reason')))}</i>"
    return body[:3500], []


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps({"flag": enabled(), "now": measure(),
                      "trend": trend(), "series": str(TREND)},
                     ensure_ascii=False, indent=1))
