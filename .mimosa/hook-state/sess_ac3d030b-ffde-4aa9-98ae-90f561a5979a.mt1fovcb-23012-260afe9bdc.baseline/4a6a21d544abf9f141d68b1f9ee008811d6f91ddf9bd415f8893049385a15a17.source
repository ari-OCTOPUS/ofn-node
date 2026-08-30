#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""context_fence.py — جداسازیِ ساختاریِ «داده» از «دستور» در promptها + غربالِ injection.

هر متنِ بازیابی‌شده (حافظه/Vault/web/Telegram/state/log) داده است نه دستور. این ماژول آن را
در بلوکِ DATA_NOT_INSTRUCTIONِ محصور می‌گذارد (فرارِ delimiter خنثی می‌شود) و الگوهای تزریقِ
دستور را می‌سنجد/برچسب می‌زند. خروجیِ ساختاری، بخش‌های اعتماد از هم جدا.

انضباط: پشتِ OCTOPUS_WIRE_CONTEXT_FENCE (پیش‌فرض خاموش → passthroughِ بایت‌به‌بایت). stdlib فقط،
تابعِ خالص، صفر side-effقت. v1 = fence/screen/build؛ سیم‌کشی به model_router = گامِ جدا.
"""
from __future__ import annotations

import os
import re

FLAG = "OCTOPUS_WIRE_CONTEXT_FENCE"
_OPEN = "⟦DATA_NOT_INSTRUCTION"
_CLOSE = "⟦/DATA_NOT_INSTRUCTION⟧"

# الگوهای تزریقِ دستور در دادهٔ نامعتمد
_INJECTION = [
    (re.compile(r"ignore\s+(all\s+|the\s+|your\s+)?(previous|above|prior|earlier)\s+instructions?", re.I), "ignore-instructions"),
    (re.compile(r"disregard\s+(all\s+|the\s+|your\s+)?(previous|above|prior|system)", re.I), "disregard"),
    (re.compile(r"\byou\s+are\s+now\b|\bnew\s+instructions?\b|\bnew\s+system\s+prompt\b", re.I), "role-override"),
    (re.compile(r"(^|\n)\s*(system|assistant|developer)\s*:", re.I), "role-marker"),
    (re.compile(r"\breveal\s+(your\s+)?(system\s+prompt|instructions)\b", re.I), "prompt-exfil"),
    (re.compile(r"</?(system|instructions?|prompt)>", re.I), "fake-tag"),
]


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def screen(text: str) -> dict:
    """غربالِ injection. خروجی: {clean(bool), findings[list of codes], n}."""
    s = str(text or "")
    findings = [code for rx, code in _INJECTION if rx.search(s)]
    # فرارِ delimiter هم یک نشانه است
    if _OPEN in s or _CLOSE in s:
        findings.append("delimiter-escape-attempt")
    return {"clean": not findings, "findings": sorted(set(findings)), "n": len(set(findings))}


def fence_block(text: str, source: str, ref: str = None) -> str:
    """متنِ نامعتمد را در بلوکِ DATA_NOT_INSTRUCTION محصور کن (فرارِ delimiter خنثی).
    فلگ خاموش → متنِ خام بایت‌به‌بایت (رفتارِ فعلی)."""
    s = str(text or "")
    if not enabled():
        return s
    # خنثی‌سازیِ فرارِ delimiter: توکنِ محصورگر را در دادهٔ خام بشکن
    safe = s.replace("⟦", "⟦​")
    hdr = f"{_OPEN} source={_scrub_attr(source)}"
    if ref:
        hdr += f" ref={_scrub_attr(ref)}"
    hdr += "⟧"
    return f"{hdr}\n{safe}\n{_CLOSE}"


def build_context(sections: dict) -> dict:
    """بستهٔ کانتکستِ ساختاری — بخش‌ها بر اساسِ اعتماد جدا (نه یک blob). دادهٔ نامعتمد fence+screen.

    ورودی sections: {constraints, verified_state, verified_facts, procedures, episodes,
    candidate_beliefs, contradictions, untrusted_data:[{text,source,ref?}]}.
    خروجی: همان کلیدها؛ untrusted_data هر آیتم fence‌شده + screen‌شده."""
    out = {k: list(sections.get(k) or []) for k in
           ("constraints", "verified_state", "verified_facts", "procedures", "episodes",
            "candidate_beliefs", "contradictions")}
    fenced = []
    for item in (sections.get("untrusted_data") or []):
        text = item.get("text", "") if isinstance(item, dict) else str(item)
        src = item.get("source", "unknown") if isinstance(item, dict) else "unknown"
        ref = item.get("ref") if isinstance(item, dict) else None
        sc = screen(text)
        fenced.append({"fenced": fence_block(text, src, ref), "source": src, "ref": ref,
                       "screen": sc})
    out["untrusted_data"] = fenced
    out["_fence_enabled"] = enabled()
    out["_injection_flagged"] = sum(1 for f in fenced if not f["screen"]["clean"])
    return out


def _scrub_attr(v) -> str:
    return re.sub(r"[^\w:.\-/@]", "_", str(v or "unknown"))[:64]
