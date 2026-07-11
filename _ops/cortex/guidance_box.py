#!/usr/bin/env python3
"""guidance_box.py — «جعبهٔ راهنماییِ انسان» (Human-Guidance Box، از دکترین).

رأی/دکترین: «فقط چند چیزِ اهرم‌بالا را که *همین حالا* به مالک نیاز دارند نشان بده —
هرگز مبهم.» به‌جای فهرستِ بلندِ همه‌چیز، این ماژول از stateِ *موجود* چند سیگنالِ
واقعاً پُراهرم را جمع می‌کند و به سوال‌های مشخص + «چرا» تبدیل می‌کند:

  • تأییدهای معطل   (رویدادِ approval.required — منتظرِ آره/نهِ تو)
  • کارهای مسدود    (رویدادِ task.blocked — منتظرِ رفعِ مانع از سمتِ تو)
  • زیرسیستم‌های در «ترس» (state/cortex/stress-latest.json — بد کار می‌کنند)
  • نیازها          (state/needs-nudge.json — داده/تأیید/اقدامِ یک‌باره)

رتبه‌بندی بر اساسِ اهرم (پول > مسدود > تأیید > ترس > نیاز)، dedupe، سقفِ ~۵ آیتم.
هر آیتم = یک سوالِ مشخص + یک «چرا». مشاهدهٔ خالص: هیچ نوشتنی، هیچ اثری، fail-soft.
هم‌شکلِ stress.py/innervation.py — داشبورد صداشان می‌زند؛ هرگز نمی‌نویسند.

$0 · stdlib + opslib · read-only · fail-soft · content-free (scrub containment).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))
import events  # noqa: E402  (فقط خواننده: events.recent — هیچ emit)

STATE = opslib.STATE_DIR

# containment (parity با registry_scan.scrub / events._scrub_str) — هیچ رشتهٔ ممنوع echo نمی‌شود
_BANNED_ECHO = ("اونلی", "onlyfans", "صبا")

# اهرم (leverage): پول > مسدود > تأیید > ترس > نیاز (دکترین: «پول/مسدود/تأیید اول»)
LEV_MONEY, LEV_BLOCKED, LEV_APPROVAL, LEV_FEAR, LEV_NEEDS = 100, 80, 70, 55, 45
TOP_N = 5
# پنجرهٔ تازگیِ رویداد: رویدادهای append-only حل‌شده را جفتِ resolution نداریم، پس
# فقط سیگنال‌های اخیر شمرده می‌شوند (کهنه‌ها fade می‌شوند). fail-soft.
WINDOW_H = float(os.environ.get("GUIDANCE_WINDOW_H", "72"))
# ترس/عصب‌کشی از منبعِ خودشان می‌آیند → رویدادِ task.blockedشان دوباره شمرده نشود
_SELF_SOURCED = frozenset({"stress-homeostat", "innervation"})
_MONEY_RE = re.compile(r"پول|دلار|مالی|بودجه|سقف|واریز|پرداخت|خرج|هزینه|cap|usd|aud|\$",
                       re.IGNORECASE)


# ── ابزارهای کوچک ────────────────────────────────────────────────────────────
def _scrub(s: str, cap: int = 160) -> str:
    """هر رشتهٔ حاوی echo ِ ممنوع → کاملاً redact (parity با registry_scan.scrub)."""
    v = str(s or "")[:cap]
    low = v.lower()
    if any(b in low or b in v for b in _BANNED_ECHO):
        return "(redacted:containment)"
    return v


def _prio(score: int) -> str:
    return "high" if score >= 70 else "medium" if score >= 45 else "low"


def _is_money(*texts: str) -> bool:
    return any(_MONEY_RE.search(str(t or "")) for t in texts)


def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def _mk(q: str, why: str, source: str, score: int) -> dict:
    return {"q": _scrub(q), "why": _scrub(why), "source": source,
            "priority": _prio(score), "_score": score}


def _recent_events() -> list[dict]:
    """رویدادهای درونِ پنجرهٔ تازگی (جدید→قدیم). fail-soft: هر خطا = []"""
    try:
        cut = time.time() - WINDOW_H * 3600.0
        return [e for e in events.recent(400) if float(e.get("ts", 0)) >= cut]
    except Exception:  # noqa: BLE001
        return []


# ── جمع‌کننده‌های هر منبع (هر کدام fail-soft داخلِ guidance) ────────────────────
def _approvals(evs: list[dict]) -> list[dict]:
    out = []
    for e in evs:
        if e.get("event_name") != "approval.required":
            continue
        summ = e.get("summary") or "یه کار منتظرِ تأییدِ توست"
        nxt = e.get("next_action") or ""
        money = _is_money(summ, nxt)
        out.append(_mk(f"{summ} — تأیید یا رد؟",
                       nxt or "کارِ برگشت‌ناپذیر/مالی منتظرِ رأیِ توست",
                       "money" if money else "approval",
                       LEV_MONEY if money else LEV_APPROVAL))
    return out


def _blocked(evs: list[dict]) -> list[dict]:
    out = []
    for e in evs:
        if e.get("event_name") != "task.blocked":
            continue
        if e.get("agent_id") in _SELF_SOURCED:
            continue                                   # اجتنابِ دوباره‌شماری با منبعِ ترس/عصب‌کشی
        summ = e.get("summary") or "یک کار گیر کرده"
        nxt = e.get("next_action") or ""
        money = _is_money(summ, nxt)
        out.append(_mk(f"گیر کرده: {summ} — بازش کنیم؟",
                       nxt or "کارِ مسدود منتظرِ رفعِ مانع از سمتِ توست",
                       "money" if money else "blocked",
                       LEV_MONEY if money else LEV_BLOCKED))
    return out


def _fear() -> list[dict]:
    d = _read_json(STATE / "cortex" / "stress-latest.json")
    subs = d.get("subsystems") or {}
    out = []
    for sid in (d.get("in_fear") or []):
        sub = subs.get(sid) or {}
        name = sub.get("name") or str(sid)
        detail = sub.get("detail") or ""
        if sid == "money":
            out.append(_mk(f"خرجِ ماه به سقف نزدیک شده ({detail}) — نگه دارم یا سقف را بازبینی کنیم؟",
                           "زیرسیستمِ مالی از آستانهٔ ترس گذشت؛ خودمختاری‌اش تنگ شد",
                           "money", LEV_MONEY))
        else:
            out.append(_mk(f"{name} بد کار می‌کند ({detail}) — رسیدگی کنیم؟",
                           "زیرسیستم از آستانهٔ ترس گذشت و محافظه‌کار شد تا تو ببینی",
                           "fear", LEV_FEAR))
    return out


def _needs() -> list[dict]:
    st = _read_json(STATE / "needs-nudge.json")
    try:
        n = int(st.get("last_n") or 0)
    except (TypeError, ValueError):
        n = 0
    if n <= 0:
        return []
    return [_mk(f"{n} چیز روی میزت هست که سیستم برای پیش‌رفتن لازم دارد — /now را باز می‌کنی؟",
                "داده/تأیید/اقدامِ یک‌باره که بدونِ تو معطل مانده",
                "needs", LEV_NEEDS)]


# ── API ─────────────────────────────────────────────────────────────────────
def guidance() -> dict:
    """جعبهٔ راهنمایی: چند سوالِ پُراهرم که همین حالا به مالک نیاز دارند.

    خروجی: {items:[{q, why, source, priority}], n}. مرتب بر اساسِ اهرم، dedupe، سقفِ ۵.
    مشاهدهٔ خالص و fail-soft: هر منبع مستقل try می‌شود؛ هیچ خطایی به مصرف‌کننده نمی‌رسد."""
    evs = _recent_events()
    items: list[dict] = []
    for coll in (lambda: _approvals(evs), lambda: _blocked(evs), _fear, _needs):
        try:
            items += coll()
        except Exception:  # noqa: BLE001 — یک منبعِ خراب بقیه را نمی‌کشد
            continue
    # مرتب بر اساسِ اهرم (نزولی، پایدار) سپس dedupe بر qِ نرمال‌شده (بالاترین اهرم می‌ماند)
    items.sort(key=lambda it: -it["_score"])
    seen: set[str] = set()
    ranked: list[dict] = []
    for it in items:
        key = re.sub(r"\s+", " ", it["q"]).strip().casefold()
        if key in seen:
            continue
        seen.add(key)
        ranked.append(it)
    ranked = ranked[:TOP_N]
    for it in ranked:
        it.pop("_score", None)
    return {"ts": opslib.now_iso(), "schema": "guidance.v1",
            "items": ranked, "n": len(ranked)}


def summary(g: "dict | None" = None) -> str:
    """یک‌خطِ داشبورد: «🧭 راهنمایی: N چیز که همین حالا به تو نیاز دارد»."""
    d = g or guidance()
    n = d.get("n", 0)
    if not n:
        return "🧭 راهنمایی: چیزی همین حالا از تو نمی‌خواهد — 🟢"
    top = d["items"][0]["q"]
    return f"🧭 راهنمایی: {n} چیز که همین حالا به تو نیاز دارد — «{top}»"


if __name__ == "__main__":
    print(json.dumps(guidance(), ensure_ascii=False, indent=2))