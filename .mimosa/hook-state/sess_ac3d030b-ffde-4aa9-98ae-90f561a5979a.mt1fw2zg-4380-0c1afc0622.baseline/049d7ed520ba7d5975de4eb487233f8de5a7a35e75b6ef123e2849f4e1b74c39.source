#!/usr/bin/env python3
"""Read-only current-state answers for the owner conversation."""
from __future__ import annotations

import json
from pathlib import Path

OPS = Path(__file__).resolve().parents[1]
STATE = OPS / "state"


def _unified() -> tuple[dict, dict]:
    try:
        from unified_control import compass, snapshot
        s = snapshot.build(); return s, compass.build(s)
    except Exception as e:
        return {"blockers": [f"unified-snapshot-error:{type(e).__name__}"]}, {}


def current_goal() -> str:
    s, c = _unified()
    if not c.get("goal"):
        return "🎯 هدف فعالِ قابل‌اثبات پیدا نشد. وضعیت: UNKNOWN"
    m = c.get("metric") or {}
    v = (s.get("goal_cycle") or {}).get("verdict") or {}
    lines = ["🎯 هدف فعلی اختاپوس", c["goal"],
             f"جهت مالک: {c.get('direction') or 'نامعلوم'}",
             f"سنجه: {m.get('path')} → {m.get('key')}",
             f"baseline={m.get('baseline')} · target={m.get('target')}",
             f"روش: {c.get('method') or 'نامعلوم'}",
             f"آمادگی: {c.get('readiness')} ({', '.join(c.get('reasons') or []) or 'بدون هشدار'})"]
    lines.append("حکم مستقل: " + (str(v.get("verdict")) if v else "هنوز صادر نشده"))
    return "\n".join(lines)


def runtime_truth() -> str:
    s, c = _unified()
    h = s.get("heart") or {}; sm = s.get("self_model") or {}; inn = s.get("innervation") or {}
    gc = s.get("goal_cycle") or {}; counts = gc.get("counts") or {}
    return "\n".join([
        "🫀 حقیقت runtime",
        f"قلب: {h.get('authority', 'UNKNOWN')} · production_open={h.get('production_open')}",
        f"خودمدل: {sm.get('authority', 'UNKNOWN')} · age_s={sm.get('age_s')}",
        f"عصب‌کشی: {inn.get('coverage_pct', 'UNKNOWN')}% · نقاط مرده={inn.get('dead_spots') or []}",
        f"چرخه هدف: prereg={counts.get('prereg', 0)} · journal={counts.get('cycles', 0)} · verdict={counts.get('verdicts', 0)}",
        f"قطب‌نما: {c.get('readiness', 'UNKNOWN')} · cadence={c.get('cadence_authority', 'UNKNOWN')}",
        "وضعیت کلی: " + ("کاملاً یکپارچه" if s.get("fully_integrated") else "نیمه‌یکپارچه"),
    ])


def blockers() -> str:
    s, c = _unified()
    bs = list(dict.fromkeys([*(s.get("blockers") or []), *(c.get("reasons") or [])]))
    if not bs:
        return "✅ blocker قابل‌مشاهده‌ای در snapshot فعلی نیست."
    return "⛔ موانع فعلی\n" + "\n".join(f"• {x}" for x in bs)


def discovery() -> str:
    report = OPS / "world_discovery" / "reports" / "WORLD-DISCOVERY-EXECUTION-REPORT-2026-07-30.md"
    status = "UNKNOWN"
    try:
        text = report.read_text("utf-8")
        if "NO_VALID_DISCOVERY" in text:
            status = "NO_VALID_DISCOVERY"
        elif "DISCOVERY_VALIDATED" in text:
            status = "DISCOVERY_VALIDATED"
    except OSError:
        text = ""
    return "\n".join([
        "🌍 World Discovery",
        f"وضعیت آخرین اجرای قابل‌مشاهده: {status}",
        "اجرای ثبت‌شده: ۱۵ منبع، ۸ کاندیدا، صفر کشفِ دو-منبعی معتبر.",
        "چهار فرضیه رقابتی ساخته شد ولی هنوز FACT نیستند.",
        "قدم بعدی: دور relation-level یا آزمایش E0 فقط‌خواندنی؛ بدون خرج و ارسال.",
    ])


def readonly_mission(text: str) -> dict:
    """Proposal only. It is never queued or executed here."""
    intent = str(text or "").strip()
    return {
        "schema": "owner-console.readonly-proposal.v1",
        "status": "PROPOSED_NOT_SUBMITTED",
        "intent": intent,
        "action_type": "read_public_or_local_state",
        "external_effect": False,
        "estimated_cost": 0,
        "requires_owner_gate": False,
        "note": "این فقط proposal است؛ caller زنده باید آن را به Mission/Action Bridge بدهد.",
    }
