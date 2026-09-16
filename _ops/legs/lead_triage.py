#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lead_triage.py — غربالِ لیدِ نقاشی: مغز خلاصه/اولویت می‌دهد، پیشنهادِ نهایی در صف با کارتِ مالک.

اتصالِ ۲ از CORTEX-CONNECT-ALL. seamِ واقعی:
  input    → همان dictِ لید که legs/lead_scorer._haystack می‌خواند (description, address)
             + فیلدهای intake v2 روی ۱۳۸ (title, budget, location, score, url, posted_at).
             مسیرِ فایلِ intake روی ۱۳۸ در این لِین **UNKNOWN** (تأییدنشده) — قرارداد
             فیلدها از حافظهٔ لِین‌های قبل است، نه از فایلِ خوانده‌شده.
  consumer → legs/lead_pipeline._card_text (کارتِ مالک) — خطِ `card_line(res)` این ماژول
             برای درجِ خلاصه/اولویت. splice به production خارج از این لِین (گیت).
  storage  → STATE_DIR/leads/triage.jsonl (append-only، idempotent روی lead_id).

fallback (مغز نداد): قاعدهٔ امتیازی از ستونِ score (>=70 high · >=40 medium · else low)
با fallback=True — هرگز اولویتِ جعلیِ «مغزی» ثبت نمی‌شود.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE.parent, _HERE.parent / "budget", _HERE.parent / "cortex"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import opslib      # noqa: E402
import brain_link  # noqa: E402

TASK = "lead_triage"
MAX_TOKENS = 400
SCHEMA = "lead_triage.v1"
PRIORITIES = ("high", "medium", "low")
FLAG = "OCTOPUS_CONNECT_LEAD_TRIAGE"    # پیش‌فرض خاموش؛ روشن‌کردن = تصمیمِ مالک


def enabled() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in ("1", "true", "yes", "on")
_SYSTEM = ("You triage painting/handyman job leads for a small Sydney painter. Answer ONLY a "
           "JSON object: {\"priority\": \"high|medium|low\", \"summary\": \"<=25 words\", "
           "\"why\": \"<=20 words\"}. Be strict: no budget or far location → low.")


def _ledger_path() -> Path:
    return opslib.STATE_DIR / "leads" / "triage.jsonl"


def _sha(s) -> str:
    return hashlib.sha256(str(s or "").encode("utf-8")).hexdigest()[:16]


def lead_key(lead: dict) -> str:
    lid = str(lead.get("lead_id") or lead.get("id") or lead.get("url") or "").strip()
    return lid or _sha(json.dumps(lead, sort_keys=True, ensure_ascii=False))


def _existing(key: str) -> dict | None:
    p = _ledger_path()
    if not p.exists():
        return None
    last = None
    for ln in p.read_text("utf-8", errors="replace").splitlines():
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("lead_key") == key:
            last = d
    return last


def rule_priority(lead: dict) -> str:
    try:
        s = float(lead.get("score") or 0)
    except (TypeError, ValueError):
        s = 0.0
    return "high" if s >= 70 else ("medium" if s >= 40 else "low")


def _prompt(lead: dict) -> str:
    f = {k: str(lead.get(k) or "")[:300] for k in
         ("title", "description", "budget", "location", "address", "posted_at", "score")}
    return "Lead:\n" + "\n".join(f"{k}: {v}" for k, v in f.items() if v)


def _parse(text: str) -> dict | None:
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        d = json.loads(text[i:j + 1])
    except ValueError:
        return None
    if not isinstance(d, dict) or str(d.get("priority", "")).lower() not in PRIORITIES:
        return None
    return {"priority": str(d["priority"]).lower(),
            "summary": str(d.get("summary") or "")[:240],
            "why": str(d.get("why") or "")[:200]}


def triage(lead: dict, *, ask_fn=None, now=None) -> dict:
    lead = dict(lead or {})
    key = lead_key(lead)
    prev = _existing(key)
    if prev is not None:
        return {**prev, "replayed": True}
    r = brain_link.ask_brain(TASK, _prompt(lead), system=_SYSTEM,
                             max_tokens=MAX_TOKENS, ask_fn=ask_fn, now=now)
    parsed = _parse(str(r.get("text") or "")) if r.get("ok") else None
    if parsed:
        fallback, reason = False, ""
    else:
        fallback = True
        reason = str(r.get("reason") or ("bad-format" if r.get("ok") else "no-text"))
        parsed = {"priority": rule_priority(lead), "summary": "", "why": "rule:score"}
    row = {"ts": opslib.now_iso(), "schema": SCHEMA, "lead_key": key,
           "task": TASK, "ok": bool(r.get("ok")), "fallback": fallback, "reason": reason,
           "priority": parsed["priority"], "summary": parsed["summary"], "why": parsed["why"],
           "score": lead.get("score"), "lead_sha": _sha(json.dumps(lead, sort_keys=True, ensure_ascii=False)),
           "queued_for_owner": True, "decided": False, "production_authorized": False}
    try:
        opslib.append_jsonl(_ledger_path(), row)
    except Exception:  # noqa: BLE001
        pass
    return row


def card_line(row: dict) -> str:
    """یک خط برای درج در کارتِ مالکِ lead_pipeline._card_text (بدونِ دکمهٔ تازه)."""
    import html as _h
    ic = {"high": "🔴", "medium": "🟠", "low": "⚪"}.get(str(row.get("priority")), "⚪")
    src = "قاعده" if row.get("fallback") else "مغز"
    s = _h.escape(str(row.get("summary") or row.get("why") or ""))
    return f"{ic} اولویت: {row.get('priority')} ({src})" + (f" — {s}" if s else "")
