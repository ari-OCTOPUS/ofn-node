# -*- coding: utf-8 -*-
"""code_autonomy_card — کارتِ «اقداماتِ خودمختارِ کد» (۲۰۲۶-۰۸-۰۸).

چرا (Why): `state/cortex/code-autonomy-applied.jsonl` یک حلقهٔ داخلی در
`code_autonomy.py` داشت (خطِ ۵۹۲/۸۲۰) ولی **هیچ قابلیتِ رویتیِ مالک‌سطح**
نداشت. این کارت اولین سطحِ انسانیِ آن دفتر است: آخرین اقداماتِ خودمختارِ
کد را نشان می‌دهد — چه applied شد، چه rollback شد، چه canary سبز بود.

این چیست و چه چیزی نیست:
  * فقط‌خواندن روی `state/cortex/code-autonomy-applied.jsonl`؛ $0؛ صفر I/Oِ نوشتنی.
  * فقط نمایش — هیچ چیزی را apply/rollback نمی‌کند.
  * توسطِ `capability_registry.discover()` خودکار کشف می‌شود.

fail-soft کامل: نبودِ فایل/JSON خراب ⇒ کارتِ «اقدامی نیست»، نه کرش.
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
APPLIED_LOG = _HERE / "state" / "cortex" / "code-autonomy-applied.jsonl"

CARD_TITLE = "اقداماتِ خودمختارِ کد"
_MAX_SHOW = 3


def _read_applied(limit: int = 50) -> list:
    """آخرین N ردیفِ code-autonomy-applied.jsonl را بخوان. fail-soft: نبود ⇒ []."""
    try:
        if not APPLIED_LOG.exists():
            return []
        out = []
        for ln in APPLIED_LOG.read_text("utf-8", errors="replace").splitlines()[-limit:]:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
        return out
    except Exception:  # noqa: BLE001
        return []


def _fmt_one(rec: dict) -> str:
    """یک اقدام را به‌صورتِ یک خطِ خلاصه قالب‌بندی کن."""
    try:
        target = str(rec.get("target") or "?")
        if "/" in target:
            target = target.split("/")[-1]
        if len(target) > 40:
            target = target[:37] + "…"
        applied = rec.get("applied")
        rolled = rec.get("rolled_back")
        canary = rec.get("canary_green")
        reason = str(rec.get("reason") or "")[:50]
        if rolled:
            mark = "↩️"
            verdict = "rollback"
        elif applied:
            mark = "✅"
            verdict = "applied" + (" ✓canary" if canary else "")
        else:
            mark = "❌"
            verdict = "failed"
        ts = str(rec.get("ts") or "")[:10]
        return f"{mark} [{ts}] <code>{target}</code> ({verdict}){(' — '+reason) if reason else ''}"
    except Exception:  # noqa: BLE001
        return "⚪ (ردیفِ ناخوانا)"


def card() -> str:
    """کارتِ «اقداماتِ خودمختارِ کد» — ساکت وقتی اقدامی نیست.

    توسطِ capability_registry خودکار کشف می‌شود (zero-arg card در SCAN_DIRS).
    خروجی: HTML کوتاه با شمارشِ applied/rollback/failed + ۳ موردِ اخیر. فقط‌خواندن.
    """
    rows = _read_applied()
    if not rows:
        return ("🤖 <b>اقداماتِ خودمختارِ کد خالی است</b>\n"
                "▸ هنوز هیچ اقدامِ خودمختاری ثبت نشده.\n"
                "▸ نکنی: هیچ — فقط‌خواندنی.")
    n = len(rows)
    applied_n = sum(1 for r in rows if r.get("applied") and not r.get("rolled_back"))
    rolled_n = sum(1 for r in rows if r.get("rolled_back"))
    failed_n = n - applied_n - rolled_n
    recent = rows[-_MAX_SHOW:]
    lines = [f"🤖 <b>{n} اقدامِ خودمختارِ کد</b> "
             f"(✅{applied_n} · ↩️{rolled_n} · ❌{failed_n}) — آخرینِ {_MAX_SHOW}:"]
    for rec in recent:
        lines.append(_fmt_one(rec))
    lines.append("▸ نکنی: هیچ — فقط‌خواندنی (code_autonomy خودش apply/rollback می‌کند).")
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    print(card())
