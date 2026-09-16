# -*- coding: utf-8 -*-
"""defect_queue_card — کارتِ «صفِ نقص‌های خودترمیمی» (۲۰۲۶-۰۸-۰۸).

چرا (Why): `state/self-patch/defect-queue.jsonl` (۱۲ ردیفِ زنده) یک حلقهٔ
داخلی در self_patch.py داشت (`_queue_effective()`) ولی **هیچ قابلیتِ رویتی
برایِ مالک** نداشت — مالک نمی‌دید self-patch چه نقص‌هایی پیدا کرده، کدام
گرفته‌شده، کدام باز. این کارت اولین سطحِ انسانیِ آن صف است.

این چیست و چه چیزی نیست:
  * فقط‌خواندن روی `state/self-patch/defect-queue.jsonl`؛ $0؛ صفر I/Oِ نوشتنی.
  * فقط نمایش — هیچ چیزی را apply/fix نمی‌کند. حلقهٔ خودترمیمی دست‌نخورده.
  * توسطِ `capability_registry.discover()` خودکار کشف می‌شود (`card()`
    بی‌آرگومان در SCAN_DIRS ریشه) — هیچ تغییری در center.py نمی‌خواهد.

fail-soft کامل: نبودِ فایل/JSON خراب ⇒ کارتِ «صفِ خالی»، نه کرش.
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
PROPERTIES_LOG = _HERE / "state" / "self-patch" / "defect-queue.jsonl"

CARD_TITLE = "صفِ نقص‌های خودترمیمی"
_MAX_SHOW = 3   # چند موردِ اخیر در کارت


def _read_queue(limit: int = 100) -> list:
    """آخرین N ردیفِ defect-queue.jsonl را بخوان. fail-soft: نبود ⇒ []."""
    try:
        if not PROPERTIES_LOG.exists():
            return []
        out = []
        for ln in PROPERTIES_LOG.read_text("utf-8", errors="replace").splitlines()[-limit:]:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
        return out
    except Exception:  # noqa: BLE001 — کارت هرگز کرش نمی‌کند
        return []


def _status_counts(rows: list) -> dict:
    """شمارش بر اساسِ فیلدِ status (open/taken/closed/...)."""
    counts: dict[str, int] = {}
    # آخرین وضعیتِ هر id ملاک است (مثل rules_store)
    by_id: dict[str, dict] = {}
    for r in rows:
        rid = r.get("id") or r.get("ts")
        if rid:
            by_id[str(rid)] = r
    for r in by_id.values():
        s = str(r.get("status") or "unknown")
        counts[s] = counts.get(s, 0) + 1
    return counts


def _fmt_one(rec: dict) -> str:
    """یک ردیف را به‌صورتِ یک خطِ خلاصه قالب‌بندی کن."""
    try:
        target = str(rec.get("target") or "?")
        if "/" in target:
            target = target.split("/")[-1]
        if len(target) > 40:
            target = target[:37] + "…"
        status = str(rec.get("status") or "?")
        defect = str(rec.get("defect") or "?")
        if len(defect) > 60:
            defect = defect[:57] + "…"
        mark = {"open": "🔴", "taken": "🟡", "closed": "🟢"}.get(status, "⚪")
        return f"{mark} <code>{target}</code> ({status}) — {defect}"
    except Exception:  # noqa: BLE001
        return "⚪ (ردیفِ ناخوانا)"


def card() -> str:
    """کارتِ «صفِ نقص‌های خودترمیمی» — ساکت وقتی صف خالی است.

    توسطِ capability_registry خودکار کشف می‌شود (zero-arg card در SCAN_DIRS).
    خروجی: HTML کوتاه با شمارشِ وضعیت‌ها + ۳ موردِ اخیر. فقط‌خواندن؛ $0؛ fail-soft.
    """
    rows = _read_queue()
    if not rows:
        return ("🔧 <b>صفِ نقص‌های خودترمیمی خالی است</b>\n"
                "▸ self-patch هنوز هیچ نقصی پیدا نکرده.\n"
                "▸ نکنی: هیچ — فقط‌خواندنی.")
    counts = _status_counts(rows)
    # آخرینِ N موردِ باز یا اخیر (اولِ بازها، بعد بقیه)
    open_rows = [r for r in rows if (r.get("status") or "") == "open"]
    recent = (open_rows + [r for r in rows if (r.get("status") or "") != "open"])[-_MAX_SHOW:]
    status_line = " · ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    lines = [f"🔧 <b>صفِ نقص‌های خودترمیمی</b> ({status_line}):"]
    for rec in recent:
        lines.append(_fmt_one(rec))
    lines.append("▸ نکنی: هیچ — فقط‌خواندنی (self-patch خودش حلقه را می‌بندد).")
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    print(card())
