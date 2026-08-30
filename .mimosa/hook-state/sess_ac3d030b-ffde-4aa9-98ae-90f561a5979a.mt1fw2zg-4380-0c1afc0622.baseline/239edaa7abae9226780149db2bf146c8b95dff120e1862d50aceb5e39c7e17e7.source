# -*- coding: utf-8 -*-
"""money_fsm_card — کارتِ «تخلف‌های ماشینِ حالتِ پول» (۲۰۲۶-۰۸-۰۸).

چرا (Why): `state/money-fsm-violations.jsonl` (نوشته‌شده توسط
`outcomes/pending_card_recovery.py:602`) تا حالا **صفر خوانندهٔ تولیدی** داشت
(فقط تست). این کارت اولین خوانندهٔ تولیدیِ آن است: مالک می‌بیند چند بار
تلاشِ انتقالِ حالتِ غیرمجاز (مثلاً APPROVED→PENDING) رخ داده و کدام enforce شده.

این چیست و چه چیزی نیست:
  * فقط‌خواندن روی `state/money-fsm-violations.jsonl`؛ $0؛ صفر I/Oِ نوشتنی.
  * فقط نمایش — هیچ چیزی را enforce/block نمی‌کند.
  * توسطِ `capability_registry.discover()` خودکار کشف می‌شود.

fail-soft کامل: نبودِ فایل/JSON خراب ⇒ کارتِ «تخلفی نیست»، نه کرش.
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
FSM_LOG = _HERE / "state" / "money-fsm-violations.jsonl"

CARD_TITLE = "تخلف‌های ماشینِ حالتِ پول"
_MAX_SHOW = 3


def _read_violations(limit: int = 50) -> list:
    """آخرین N ردیفِ money-fsm-violations.jsonl را بخوان. fail-soft: نبود ⇒ []."""
    try:
        if not FSM_LOG.exists():
            return []
        out = []
        for ln in FSM_LOG.read_text("utf-8", errors="replace").splitlines()[-limit:]:
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
    """یک تخلف را به‌صورتِ یک خطِ خلاصه قالب‌بندی کن."""
    try:
        frm = str(rec.get("from") or "?")
        to = str(rec.get("to") or "?")
        eff = str(rec.get("effect_id") or "?")
        enforced = rec.get("enforced")
        mark = "🛑" if enforced else "⚠️"
        verdict = "enforced" if enforced else "not-enforced"
        ts = str(rec.get("ts") or "")
        # ts ممکن است epoch int باشد — فقط ۶ رقمِ آخرِ ثانیه
        if ts and ts.replace(".", "").isdigit():
            try:
                import datetime as _dt
                ts = _dt.datetime.fromtimestamp(float(ts)).strftime("%m-%d %H:%M")
            except Exception:  # noqa: BLE001
                ts = ts[:10]
        else:
            ts = ts[:10]
        return f"{mark} [{ts}] {frm}→{to} ({eff}, {verdict})"
    except Exception:  # noqa: BLE001
        return "⚪ (ردیفِ ناخوانا)"


def card() -> str:
    """کارتِ «تخلف‌های ماشینِ حالتِ پول» — ساکت وقتی تخلفی نیست.

    توسطِ capability_registry خودکار کشف می‌شود (zero-arg card در SCAN_DIRS).
    خروجی: HTML کوتاه با شمارشِ enforced/not-enforced + ۳ موردِ اخیر. فقط‌خواندن.
    """
    rows = _read_violations()
    if not rows:
        return ("💰 <b>تخلفِ ماشینِ حالتِ پول ثبت نشده</b>\n"
                "▸ هیچ انتقالِ غیرمجازی رخ نداده.\n"
                "▸ نکنی: هیچ — فقط‌خواندنی.")
    n = len(rows)
    enf_n = sum(1 for r in rows if r.get("enforced"))
    not_enf_n = n - enf_n
    recent = rows[-_MAX_SHOW:]
    lines = [f"💰 <b>{n} تخلفِ ماشینِ حالتِ پول</b> "
             f"(🛑{enf_n} enforced · ⚠️{not_enf_n} not) — آخرینِ {_MAX_SHOW}:"]
    for rec in recent:
        lines.append(_fmt_one(rec))
    lines.append("▸ نکنی: هیچ — فقط‌خواندنی (pending_card_recovery خودش enforce می‌کند).")
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    print(card())
