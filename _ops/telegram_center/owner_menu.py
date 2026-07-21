#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
owner_menu — single source of truth for the owner's 6-option Telegram menu + callback routing.

WHY: the connectivity audit found D-009 — render.py/center.py hardcode callback_data and the
`actions.py` skeleton is an orphan. This module makes ONE place define the top navigation, its
callback ids, and where each routes. center.py's eventual change is a one-line delegation, so we
never have to surgically edit the giant live center.py from a fragile sandbox.

Design: pure data + pure functions, stdlib only. mission_contract is imported (it exists + tested).
legs.lead_leg_inbox is imported LAZILY and degrades gracefully — GLM-A delivered it on branch
`claude/lead-leg-backend` (contract: register_lead -> {ok, status, lead_id?, reason?}, gated by
OCTOPUS_WIRE_LEAD_INBOX). Until that branch is merged it simply isn't importable → status "queued".
Additive + inert until center.py delegates to it. Conforms to OCTOPUS-OS §2.
"""
from __future__ import annotations

import importlib
import os
import sys
from typing import Any, Dict, List, Optional

# ensure _ops is importable whether run from center.py or standalone tests
_OPS = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep + "telegram_center", 1)[0]
if _OPS not in sys.path:
    sys.path.insert(0, _OPS)

import mission_contract as mc  # exists, tested (6/6)

# ── the 6-option menu (OCTOPUS-OS §2) ────────────────────────────────
MENU: List[Dict[str, str]] = [
    {"key": "status",  "label": "① وضعیت الان",     "cb": "m:status",  "purpose": "چه اجراست · چه گیر کرده · چه منتظرِ تأیید"},
    {"key": "mission", "label": "② مأموریت جدید",    "cb": "m:mission", "purpose": "به زبانِ ساده بگو؛ Core به پای درست می‌فرستد"},
    {"key": "mytasks", "label": "③ کارهای من",       "cb": "m:mytasks", "purpose": "فقط تصمیم‌هایی که باید تو بگیری"},
    {"key": "legs",    "label": "④ پاها",            "cb": "m:legs",    "purpose": "فهرستِ کوتاه، سبز/زرد/قرمز"},
    {"key": "report",  "label": "⑤ گزارش و دیباگ",   "cb": "m:report",  "purpose": "خطا · اتصالِ قطع · کارِ تکراری · UIِ زائد"},
    {"key": "stop",    "label": "⑥ توقف اضطراری",    "cb": "m:stop",    "purpose": "خواباندنِ اجرای خودکار، بی‌حذفِ داده"},
]
_BY_CB = {m["cb"]: m["key"] for m in MENU}


def build_main_menu(cols: int = 2) -> List[List[Dict[str, str]]]:
    """Inline-keyboard rows: [[{text, callback_data}, ...], ...]."""
    btns = [{"text": m["label"], "callback_data": m["cb"]} for m in MENU]
    return [btns[i:i + cols] for i in range(0, len(btns), cols)]


def route(callback_data: str) -> Optional[str]:
    """Map a menu callback to its handler key. Unknown -> None (fail-closed)."""
    return _BY_CB.get(callback_data)


def looks_like_lead(text: str) -> bool:
    """Cheap heuristic: is this free text likely a painting lead / new-work request?"""
    if not text:
        return False
    t = text.strip().lower()
    kw = ("نقاشی", "لید", "سفارش", "کار جدید", "مشتری", "قیمت", "پیش‌فاکتور", "lead", "quote", "paint")
    return any(k in t for k in kw)


def _lazy(modname: str):
    """Import an _ops module if it exists yet; else None (graceful for GLM-pending modules)."""
    try:
        return importlib.import_module(modname)
    except Exception:
        return None


def _register_lead_canonical(intent: str):
    """مسیرِ canonicalِ نو (Trust-Engine، پشتِ OCTOPUS_WIRE_LEAD_CANDIDATES): متنِ آزادِ مالک را
    به lead_candidate_inbox.submit_candidate بده — متنی که مالک خودش تایپ کرده = consented_inbound
    با basis=explicit (خودش درخواست کرده). خاموش (پیش‌فرض) → None تا caller به مسیرِ frozenِ قدیمی
    fallback کند. هرگز چیزی نمی‌فرستد (submit_candidate هم external_send را همیشه False می‌گذارد)."""
    if os.environ.get("OCTOPUS_WIRE_LEAD_CANDIDATES") != "1":
        return None
    try:
        import hashlib
        _lci = _lazy("legs.lead_candidate_inbox")
        if _lci is None or not hasattr(_lci, "submit_candidate"):
            return None
        text = str(intent or "").strip()
        candidate = {
            "schema_version": "1.1",
            "source": {"channel": "telegram_manual", "source_id": "owner",
                       "external_id": "tg-" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]},
            "candidate_type": "consented_inbound",
            "consent": {"basis": "explicit", "evidence": "owner_typed_in_telegram"},
            "request": {"scope_text": text},
        }
        return _lci.submit_candidate(candidate, source_id="owner")
    except Exception:  # noqa: BLE001 — همگرایی هرگز مسیرِ mission را نمی‌کشد
        return None


def _is_important(intent: str):
    """Classify a request via autonomy_matrix (the owner-gate source of truth).
    Fail-safe: any doubt / unavailable -> important (gate). Matches the doctor's doctrine:
    capability is allowed, but IMPORTANT actions must pass the owner's Telegram approval."""
    try:
        import importlib.util
        amp = os.path.join(_OPS, "cortex", "autonomy_matrix.py")
        spec = importlib.util.spec_from_file_location("autonomy_matrix", amp)
        am = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(am)
        return am.is_important({"title": intent, "action": "intake"})
    except Exception:
        return True, "fail-safe: autonomy_matrix unavailable → gate"


def handle_new_mission(intent: str, *, target_leg: str = "lead",
                       owner: str = "octopus_core", risk: str = "low") -> Dict[str, Any]:
    """Option ②: turn a plain-language request into a conformant mission envelope.

    PHILOSOPHY (owner 2026-07-18) — capability is ALLOWED, gated by the owner, never denied:
    every IMPORTANT action (money/code/delete/send/spawn/genome/multi-agent coordination...) is
    routed to the owner's Telegram approval. autonomy_matrix.is_important is the source of truth;
    important -> status 'needs_approval' (an approval card is emitted; NOTHING runs until owner ✅).
    Free/low-risk -> may proceed. Fail-safe: doubt = gate. This is the doctor's 'bold but protected'."""
    important, why = _is_important(intent)
    if important:
        risk = "high"                                  # force requires_approval=True (the gate)
    env = mc.make_envelope(source="telegram_owner", target_leg=target_leg,
                           owner=owner, action="intake", risk=risk, intent=intent)
    try:  # LIMITED shadow: canonical mission-created (پشتِ OCTOPUS_WIRE_SPINE، flag-off=no-op، fail-soft)
        from pathlib import Path as _P
        _sp = str(_P(__file__).resolve().parents[1] / "spine")
        if _sp not in sys.path:
            sys.path.insert(0, _sp)
        import spine_adapters as _sa
        _sa.mission_created(
            mission_id=env["mission_id"], domain="mission",
            correlation_id=env["trace_id"], source=env["source"],
            target_leg=env["target_leg"], risk=env["risk"], producer="owner_menu")
    except Exception:  # noqa: BLE001 — spine هرگز مسیرِ mission را نمی‌کشد
        pass
    if important:
        env["status"] = "needs_approval"
        env["gate_reason"] = why                       # owner sees WHY a verdict is needed
        return env                                     # capability held behind owner Telegram ✅
    if target_leg == "lead":
        # همگراییِ producer (2026-07-21): اول مسیرِ canonicalِ Trust-Engine (submit_candidate،
        # پشتِ OCTOPUS_WIRE_LEAD_CANDIDATES). خاموش → fallback به inboxِ frozenِ قدیمی.
        rec = _register_lead_canonical(intent) or {}
        if not rec:
            leg = _lazy("legs.lead_leg_inbox")     # frozen fallback
            if leg is not None and hasattr(leg, "register_lead"):
                try:
                    rec = leg.register_lead(intent) or {}
                except Exception:
                    rec = {"status": "blocked"}
        if rec.get("ok") and rec.get("lead_id"):
            env["output_refs"] = [f"lead://{rec['lead_id']}"]
            env["status"] = "running"               # lead actually registered (new/dup/signal)
        elif rec.get("reason") in ("gate_off", "flag off") or rec.get("status") == "gate_off":
            env["status"] = "queued"                # backend present but flag OFF — graceful
        elif rec:
            env["status"] = "blocked"               # empty_text / write_error — surfaced
        else:
            env["status"] = "queued"                # no backend reachable — graceful
        return env
    return env


if __name__ == "__main__":
    assert len(MENU) == 6
    print("menu:", " · ".join(m["label"] for m in MENU))
    e = handle_new_mission("نقاشیِ ساختمانِ مشتری X")
    print("mission:", e["mission_id"], "status=", e["status"], "valid=", mc.validate(e) == [])
