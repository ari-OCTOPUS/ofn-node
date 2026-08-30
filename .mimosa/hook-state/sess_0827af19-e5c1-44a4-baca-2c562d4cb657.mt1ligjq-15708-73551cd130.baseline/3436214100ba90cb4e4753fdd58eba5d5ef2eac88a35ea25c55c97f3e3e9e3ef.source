# -*- coding: utf-8 -*-
"""vault_proposals_card — کارتِ «پیشنهادهایِ معلقِ vault» (۲۰۲۶-۰۸-۰۸).

چرا (Why): `vault-proposals.jsonl` (۶ رکوردِ زندهٔ GATE) تا حالا صفر خوانندهٔ
تولیدی داشت — نه انسان (کارتِ تلگرام) نه ماشین (apply) آن را مصرف می‌کرد.
`vault_updater_apply.apply()` فقط AUTO را commit می‌کند و از caller می‌خواند نه
از صف؛ پس این GATEها بی‌نظارت مانده بودند. این کارت اولین خوانندهٔ انسانیِ آن
صف است: شمارش + ۳ موردِ اخیر را به مالک نشان می‌دهد.

این چیست و چه چیزی نیست:
  * فقط‌خواندن روی `state/doctor/vault-proposals.jsonl`؛ $0؛ صفر I/Oِ نوشتنی.
  * فقط نمایش — هیچ‌ چیزی را apply نمی‌کند. `apply()` فقط از caller و فقط AUTO.
  * توسطِ `capability_registry.discover()` خودکار کشف می‌شود (`doctor/` در
    SCAN_DIRS است؛ `card()` بی‌آرگومان است) — هیچ تغییری در center.py نمی‌خواهد.

fail-soft کامل: نبودِ فایل/JSON خراب ⇒ کارتِ «صفِ خالی»، نه کرش.
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_STATE = _HERE.parent / "state" / "doctor"
PROPOSALS_LOG = _STATE / "vault-proposals.jsonl"

CARD_TITLE = "پیشنهادهایِ معلقِ vault"
_MAX_SHOW = 3   # چند موردِ اخیر در کارت


def _read_pending(limit: int = 50) -> list:
    """آخرین N رکوردِ vault-proposals.jsonl را بخوان. fail-soft: نبود ⇒ []."""
    try:
        if not PROPOSALS_LOG.exists():
            return []
        out = []
        for ln in PROPOSALS_LOG.read_text("utf-8", errors="replace").splitlines()[-limit:]:
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


def _fmt_one(rec: dict, idx: int) -> str:
    """یک رکورد را به‌صورتِ یک خطِ خلاصه قالب‌بندی کن."""
    try:
        prop = rec.get("proposal") if isinstance(rec.get("proposal"), dict) else {}
        risk = str(prop.get("risk") or "?")
        kind = (prop.get("classification") or {}).get("kind") or "?"
        ring = (prop.get("classification") or {}).get("target_ring") or "?"
        path = str(prop.get("target_path") or "?")
        # مسیر را کوتاه کن (فقط آخرین ۲ بخش)
        if "/" in path:
            path = "/".join(path.split("/")[-2:])
        if len(path) > 40:
            path = path[:37] + "…"
        ts = str(rec.get("ts") or "?")[:10]   # فقط تاریخ
        ver = rec.get("version")
        ver_s = f" v{ver}" if ver else ""
        return (f"▸ [{ts}]{ver_s} <b>{risk}</b> · {kind} · R{ring} · "
                f"<code>{path}</code>")
    except Exception:  # noqa: BLE001
        return f"▸ (ردیفِ ناخوانا)"


def card() -> str:
    """کارتِ «پیشنهادهایِ معلقِ vault» — ساکت وقتی صف خالی است.

    توسطِ capability_registry خودکار کشف می‌شود (zero-arg card در SCAN_DIRS).
    خروجی: HTML کوتاه با شمارش + ۳ موردِ اخیر. فقط‌خواندن؛ $0؛ fail-soft.
    """
    pending = _read_pending()
    if not pending:
        return ("🗂 <b>صفِ پیشنهادهایِ vault خالی است</b>\n"
                "▸ هیچ GATE ای معلق نیست.\n"
                "▸ نکنی: هیچ — فقط‌خواندنی.")
    n = len(pending)
    recent = pending[-_MAX_SHOW:]
    lines = [f"🗂 <b>{n} پیشنهادِ معلقِ vault</b> "
             f"(آخرینِ {_MAX_SHOW}):"]
    for i, rec in enumerate(recent, 1):
        lines.append(_fmt_one(rec, i))
    if n > _MAX_SHOW:
        lines.append(f"▸ …و {n - _MAX_SHOW} موردِ قدیمی‌تر.")
    lines.append("▸ نکنی: هیچ — فقط‌خواندنی (apply فقط AUTO و از caller).")
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    print(card())
