#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""content_draft.py — دستیارِ hero/محتوا: مغز پیش‌نویس می‌دهد، مالک انتخاب می‌کند، هرگز انتشار.

اتصالِ ۳ از CORTEX-CONNECT-ALL. کلاسِ Z: این ماژول **هیچ** مسیرِ انتشاری ندارد؛
`publish()` عمداً وجود دارد و همیشه PermissionError می‌دهد تا هر صداکنندهٔ آینده
بلند بشکند، نه بی‌صدا منتشر کند (Shopify theme Atelier = DRAFT theme_id 159672565860).
  consumer → مالک (OWNER-INPUTS-CARD؛ کارتِ متنی از باتِ درونی) — انتخاب دستی.
  storage  → STATE_DIR/content/hero-drafts.jsonl (append-only، idempotent روی brief_sha).
fallback: مغز نداد ⇒ **هیچ** پیش‌نویسی ساخته نمی‌شود (ok=False، variants=[]) — متنِ
بازاریابیِ جعلی از قالب تولید نمی‌کنیم؛ این جای پیامِ مشتری نیست که سکوت ممنوع باشد.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE.parent, _HERE.parent / "budget", _HERE.parent / "cortex"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import opslib      # noqa: E402
import brain_link  # noqa: E402

TASK = "content_draft"
MAX_TOKENS = 700
SCHEMA = "content_draft.v1"
PUBLISH_ALLOWED = False
_SYSTEM = ("You write hero-section copy for a small Australian handmade gift store (Ziman). "
           "Answer ONLY a JSON object: {\"variants\": [{\"headline\": \"<=8 words\", "
           "\"sub\": \"<=20 words\", \"cta\": \"<=4 words\"}, ...]} with exactly N variants. "
           "No prices, no discounts, no shipping promises, no superlatives you cannot prove.")


def _ledger_path() -> Path:
    return opslib.STATE_DIR / "content" / "hero-drafts.jsonl"


def _sha(s) -> str:
    return hashlib.sha256(str(s or "").encode("utf-8")).hexdigest()[:16]


def _existing(brief_sha: str) -> dict | None:
    p = _ledger_path()
    if not p.exists():
        return None
    last = None
    for ln in p.read_text("utf-8", errors="replace").splitlines():
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("brief_sha") == brief_sha:
            last = d
    return last


def _parse(text: str, n: int) -> list[dict]:
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j <= i:
        return []
    try:
        d = json.loads(text[i:j + 1])
    except ValueError:
        return []
    out = []
    for v in (d.get("variants") if isinstance(d, dict) else []) or []:
        if isinstance(v, dict) and v.get("headline"):
            out.append({"headline": str(v.get("headline"))[:80],
                        "sub": str(v.get("sub") or "")[:200],
                        "cta": str(v.get("cta") or "")[:40]})
    return out[:n]


def draft_hero(brief: str, *, n: int = 3, ask_fn=None, now=None) -> dict:
    brief = str(brief or "").strip()
    if not brief:
        return {"ok": False, "reason": "empty-brief", "variants": [], "schema": SCHEMA}
    bsha = _sha(brief + f"|n={n}")
    prev = _existing(bsha)
    # فقط ردیفِ موفق بازپخش می‌شود؛ ردیفِ ناموفق (مغز نداد/گیت رد کرد) باید retryپذیر بماند
    # (درسِ 17:15 ۰۹-۱۱: ردیفِ not-a-paid-brainِ قبلی، retryِ پس از بازشدنِ گیت را می‌بلید)
    if prev is not None and prev.get("ok") and prev.get("variants"):
        return {**prev, "replayed": True}
    r = brain_link.ask_brain(TASK, f"N={n}\nBrief:\n{brief[:2000]}", system=_SYSTEM,
                             max_tokens=MAX_TOKENS, ask_fn=ask_fn, now=now)
    variants = _parse(str(r.get("text") or ""), n) if r.get("ok") else []
    ok = bool(variants)
    row = {"ts": opslib.now_iso(), "schema": SCHEMA, "brief_sha": bsha, "task": TASK,
           "ok": ok, "reason": "" if ok else str(r.get("reason") or "bad-format"),
           "model": str(r.get("model") or "")[:40] if r.get("ok") else "",
           "variants": variants, "chosen": None, "published": False,
           "production_authorized": False}
    try:
        opslib.append_jsonl(_ledger_path(), row)
    except Exception:  # noqa: BLE001
        pass
    return row


def owner_card(row: dict) -> str:
    import html as _h
    if not row.get("variants"):
        return ("🎨 <b>پیش‌نویسِ hero</b>\n▸ مغز پیش‌نویسی نداد ("
                + _h.escape(str(row.get("reason") or "")) + ") — چیزی ساخته نشد.")
    lines = ["🎨 <b>پیش‌نویس‌های hero — تو انتخاب کن</b>"]
    for i, v in enumerate(row["variants"], 1):
        lines.append(f"\n<b>{i}.</b> {_h.escape(v['headline'])}\n{_h.escape(v['sub'])}\n"
                     f"[{_h.escape(v['cta'])}]")
    lines.append("\n<i>انتشار خودکار نیست (کلاس Z). تم Atelier همچنان DRAFT است.</i>")
    return "\n".join(lines)


def publish(*_a, **_k):
    """عمداً همیشه می‌شکند. انتشار = رأیِ مالک + مسیرِ رسیددارِ خودش، نه این ماژول."""
    raise PermissionError("class Z: publishing hero content requires an owner vote; "
                          "content_draft never publishes")
