"""stuck_money — کارت‌های پولی که در نیمهٔ راه یخ زده‌اند.

نقطهٔ کورِ ۱۳۴
─────────────
مسیرِ تأییدِ پول عمداً دو مرحله‌ای است: اول `APPROVING` روی دیسک رزرو می‌شود،
بعد اثر آزاد و `APPROVED` ثبت می‌شود. رزروِ اول برای این است که اگر پروسه وسطِ
کار بمیرد، تپِ دومِ مالک پرداختِ دوباره نسازد. این طراحی درست است.

چیزی که کم بود: **راهِ خروج**. کارتی که در `APPROVING` بماند، برای همیشه
می‌ماند — نه خودکار جلو می‌رود (که نباید)، نه کسی خبردار می‌شود (که باید).
همین‌طور `RECONCILE_REQUIRED`. یعنی یک پرداختِ واقعیِ مالک می‌توانست ساکت گم
شود و تنها نشانه‌اش سکوت باشد.

چرا این ماژول فقط نگاه می‌کند
──────────────────────────────
وسوسه این است که یک جارو بنویسیم که کارتِ کهنه را خودش تمام کند. آن جارو یک
**مجریِ خودکارِ پول** است، هر چقدر هم محتاط نوشته شود — و پول هرگز خودکار نیست.
پس این‌جا صفر نوشتن روی وضعیتِ کارت انجام می‌شود؛ فقط فهرست و کارت.

تصمیم مالِ مالک می‌ماند؛ چیزی که عوض می‌شود این است که حالا **می‌داند** تصمیمی
منتظرِ اوست.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SCHEMA = "stuck-money.v1"
# حالت‌هایی که «در حالِ انجام» یعنی، نه «تمام‌شده». ماندنشان = یخ‌زدگی.
STUCK_STATES = ("APPROVING", "RECONCILE_REQUIRED")
STALE_H = 2.0          # بعد از این، «در حالِ انجام» دیگر باورپذیر نیست


def _store_path() -> Path:
    return opslib.STATE_DIR / "pulse" / "pending-cards.json"


def _age_h(rec: dict, now: float) -> "float | None":
    """سنِ رکورد بر حسبِ ساعت. بدونِ مهرِ زمانِ قابلِ خواندن → None (نه صفر).

    صفرگذاشتن یعنی «تازه است» و رکوردِ بی‌تاریخ را از رادار حذف می‌کند — دقیقاً
    برعکسِ چیزی که می‌خواهیم."""
    for k in ("ts", "updated", "created", "decided_at"):
        v = rec.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return max(0.0, (now - float(v)) / 3600.0)
        if isinstance(v, str) and v.strip():
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    t = time.mktime(time.strptime(v[:19], fmt))
                    return max(0.0, (now - t) / 3600.0)
                except (ValueError, OverflowError):
                    continue
    return None


def scan(*, now: "float | None" = None, stale_h: "float | None" = None) -> list:
    """کارت‌های پولیِ یخ‌زده. فقط خواندن — هیچ نوشتنی، هیچ گذاری.

    رکوردِ بی‌تاریخ **مشکوک شمرده می‌شود**، نه سالم: نبودِ شواهد دلیلِ بی‌گناهی
    نیست، و در مسیرِ پول این تفاوت اهمیت دارد."""
    now = time.time() if now is None else float(now)
    limit = STALE_H if stale_h is None else float(stale_h)
    try:
        d = json.loads(_store_path().read_text("utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(d, dict):
        return []
    out = []
    for key, rec in d.items():
        if not isinstance(rec, dict) or not str(key).startswith("money:"):
            continue
        dec = str(rec.get("decision") or "")
        if dec not in STUCK_STATES:
            continue
        age = _age_h(rec, now)
        if age is not None and age < limit:
            continue
        out.append({
            "effect_id": str(key).split(":", 1)[1][:64],
            "decision": dec,
            "age_h": None if age is None else round(age, 1),
            "why": ("بدونِ مهرِ زمان — سن نامعلوم" if age is None
                    else f"{age:.1f} ساعت در «{dec}»"),
        })
    # سنِ نامعلوم **اولِ** فهرست، نه آخر. نسخهٔ اول `-1.0` می‌گذاشت که یعنی
    # «تازه‌تر از هر رکوردِ کهنه» — دقیقاً برعکسِ چیزی که خودِ ماژول ادعا می‌کرد.
    out.sort(key=lambda r: (float("-inf") if r["age_h"] is None else -r["age_h"]))
    return out


def card(*, now: "float | None" = None) -> str:
    """کارتِ فارسی. ساکت نمی‌ماند وقتی چیزی گیر کرده، و شلوغ نمی‌کند وقتی نکرده."""
    import html
    rows = scan(now=now)
    if not rows:
        return ("💰 <b>هیچ پرداختی نیمه‌کاره نیست</b>\n"
                "▸ نکنی: هیچ.")
    lines = [f"💰 <b>{len(rows)} کارتِ پولی نیمه‌کاره مانده</b>",
             "▸ این‌ها نه انجام شده‌اند نه رد — در نیمهٔ راه یخ زده‌اند.",
             ""]
    for r in rows[:8]:
        lines.append(f"▸ <code>{html.escape(r['effect_id'][:20])}</code> — "
                     f"{html.escape(r['why'])}")
    if len(rows) > 8:
        lines.append(f"▸ … و {len(rows) - 8} تای دیگر")
    lines += ["",
              "<b>چرا خودم تمامشان نمی‌کنم:</b> جارویی که کارتِ پولیِ کهنه را "
              "خودش ببندد، یک مجریِ خودکارِ پول است — هر چقدر هم محتاط. "
              "پول هرگز خودکار نیست.",
              "",
              "▸ نکنی: همین‌طور می‌مانند و هیچ پولی جابه‌جا نمی‌شود."]
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    rows = scan()
    print(json.dumps({"schema": SCHEMA, "stuck": len(rows), "rows": rows[:20]},
                     ensure_ascii=False, indent=1))
