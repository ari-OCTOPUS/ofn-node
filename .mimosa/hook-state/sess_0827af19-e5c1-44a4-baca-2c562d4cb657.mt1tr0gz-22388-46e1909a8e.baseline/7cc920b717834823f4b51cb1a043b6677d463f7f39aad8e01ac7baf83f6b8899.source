"""verdict_probe — کدام رأیِ بازِ مالک، واقعیت **از قبل جوابش را داده**؟

رأیِ مالک (۲۰۲۶-۰۷-۲۷): «اول فقط منقضی‌ها را نشانم بده.»

مسئله: `VERDICT_QUEUE.md` ۴۸ ردیفِ باز دارد و بعضی‌شان تصمیمی می‌خواهند که
واقعیت خودش گرفته. نمونهٔ زندهٔ همان روز — یک ردیف می‌پرسد «سقفِ ضربان ۲۸۸ است و
بودجه ته کشیده، تنها اهرم تویی» در حالی که `daily_cap` همان روز ۲۰۰۰ شد. یعنی
مالک برای تصمیمی تحتِ فشار است که گرفته شده.

طراحی: یک جدولِ کوچکِ **دست‌نویس** از پروب‌ها. هر پروب یک تابعِ فقط‌خواندنی است
که واقعیت را می‌سنجد. عمداً دست‌نویس و نه heuristic — حدس‌زدنِ اینکه یک رأی
منقضی شده بدتر از ندیدنش است، چون مالک را به بستنِ چیزی ترغیب می‌کند که هنوز باز
است.

مرزها: فقط‌خواندنی. **هرگز `VERDICT_QUEUE.md` را بازنویسی نمی‌کند** (قانونِ
اساسی §۷: به نوتِ انسانی فقط append). خروجی یک کارتِ پیشنهاد است؛ بستنِ ردیف
کارِ مالک است.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_VERDICT_PROBE"


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _state(rel: str) -> dict:
    try:
        p = opslib.STATE_DIR / rel
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


# ── پروب‌ها ─────────────────────────────────────────────────────────────────
# هر کدام: () → (satisfied: bool, evidence: str). خطا = (False, "") یعنی ساکت.
def _p_beat_cap():
    c = (_state("ORGANISM-STATE.json").get("cardiac") or {}).get("budget") or {}
    cap = c.get("daily_cap")
    if isinstance(cap, (int, float)) and cap > 288:
        return True, f"سقفِ ضربان الان {int(cap)} است، نه ۲۸۸ (spent={c.get('spent')})"
    return False, ""


def _p_c6_activation():
    p = opslib.OPS / "ACTIVATION-C6-RESEARCH.flag"
    if p.exists():
        return True, "فایلِ ACTIVATION-C6-RESEARCH.flag روی دیسک هست"
    return False, ""


def _p_lead_inbox():
    d = opslib.STATE_DIR / "legs" / "lead-inbox"
    try:
        real = [f for f in d.iterdir() if not f.name.startswith("_TEMPLATE")] if d.is_dir() else []
    except OSError:
        return False, ""
    if d.is_dir() and not real:
        return True, "پوشهٔ lead-inbox ساخته شده ولی فقط قالب دارد — نیمه‌انجام"
    if real:
        return True, f"lead-inbox ساخته شده و {len(real)} ورودیِ واقعی دارد"
    return False, ""


def _p_governor_router():
    """مسیرِ LLM ِ governor امروز تعمیر شد — ردیف‌هایی که آن را باز می‌دانند کهنه‌اند."""
    try:
        rows = [json.loads(x) for x in
                (opslib.STATE_DIR / "paid-calls.jsonl").read_text("utf-8").splitlines()
                if x.strip()][-40:]
    except (OSError, ValueError):
        return False, ""
    ok = [r for r in rows if r.get("tier") == "primary" and r.get("ok")]
    if ok:
        return True, f"{len(ok)} فراخوانِ موفقِ ردهٔ primary در آخرین ۴۰ رکورد"
    return False, ""


PROBES = {
    "VQ-LOOP-001": ("سقفِ ضربانِ روزانه", _p_beat_cap),
    "VQ-C6-002": ("فعال‌سازیِ پژوهشِ C6", _p_c6_activation),
    "VQ-C5-002": ("صندوقِ ورودیِ لید", _p_lead_inbox),
    "VQ-GOV-001": ("مسیرِ LLM ِ گاورنر", _p_governor_router),
}


# ── صف ──────────────────────────────────────────────────────────────────────
def open_rows() -> list:
    """ردیف‌های `open` — فقط شناسه و عنوان، بدونِ محتوا."""
    out = []
    try:
        p = opslib.ORG_ROOT / "VERDICT_QUEUE.md"
        if not p.exists():
            return []
        for line in p.read_text("utf-8", errors="replace").splitlines():
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 4 or not cells[0].startswith("VQ-"):
                continue
            if cells[3].lower().startswith("open"):
                out.append({"id": cells[0], "title": cells[1][:110]})
    except OSError:
        return []
    return out


def expired() -> list:
    """رأی‌هایی که پروبشان می‌گوید واقعیت جوابشان را داده."""
    rows = {r["id"]: r for r in open_rows()}
    out = []
    for vid, (label, fn) in PROBES.items():
        if vid not in rows:
            continue
        try:
            sat, ev = fn()
        except Exception:  # noqa: BLE001 — پروبِ خراب = ساکت، نه ادعای غلط
            continue
        if sat and ev:
            out.append({"id": vid, "label": label,
                        "title": rows[vid]["title"], "evidence": ev})
    return out


def card() -> str:
    """کارتِ «این‌ها دیگر سؤال نیستند». هرگز چیزی را نمی‌بندد."""
    import html
    ex = expired()
    n_open = len(open_rows())
    if not ex:
        return (f"🗳 <b>رأی‌های باز: {n_open}</b>\n"
                "▸ هیچ‌کدام از آن‌هایی که می‌توانم بسنجم منقضی نشده‌اند.\n"
                "▸ نکنی: همین‌طور باز می‌مانند — بستنشان دستِ توست.")
    lines = [f"🗳 <b>{len(ex)} رأی دیگر سؤال نیست</b> (از {n_open} بازِ کل)",
             "<i>واقعیت جوابشان را داده — فقط بستنشان مانده.</i>", ""]
    for e in ex:
        lines.append(f"▸ <code>{html.escape(e['id'])}</code> — {html.escape(e['label'])}")
        lines.append(f"   شاهد: {html.escape(e['evidence'])[:150]}")
    lines.append("")
    lines.append("▸ نکنی: هر بار که تصمیم می‌گیری، این‌ها هم جلوی چشمت‌اند و "
                 "وقتت را می‌گیرند. من فایل را دست نمی‌زنم — بستنشان با توست.")
    return "\n".join(lines)[:3800]


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps({"flag": enabled(), "open": len(open_rows()),
                      "expired": expired()}, ensure_ascii=False, indent=1))
