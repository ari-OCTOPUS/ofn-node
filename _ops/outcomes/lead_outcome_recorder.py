#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lead_outcome_recorder.py — بستنِ حلقهٔ لید در حالتِ record-only (spineِ یکپارچه).

lead → (score/intake/quote، خالص) → **Decision Receipt** (با memories_used از Memory Gate) →
**Outcome** (delivered، sandbox) → link. verdict = PENDING (رأیِ مالک بعداً). $۰، **no-send،
no-money، no-auto-approve** — فقط ثبتِ پایدارِ زنجیرهٔ تصمیم→اثر→نتیجه.

پشتِ OCTOPUS_WIRE_LEAD_OUTCOME (پیش‌فرض خاموش → no-op). این «تولیدکنندهٔ» واقعیِ زنجیره است
که تا امروز نبود: Decision Receipt.memories_used را از Memory Gate پر می‌کند و به Outcome لینک
می‌کند. صفر شبکه/Telegram/EffectorGate/پول.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent), str(_HERE.parent / "legs"), str(_HERE.parent / "memory")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_WIRE_LEAD_OUTCOME"


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def record_lead_decision(lead: dict, outcome_store, receipt_store, memory_store=None,
                         mission_id=None, correlation_id=None) -> dict:
    """یک لیدِ واقعی/synthetic را از کلِ spine بگذران و پایدار ثبت کن (record-only).
    خروجی: {receipt_id, outcome_ref, correlation_id, mission_id, delivered, verdict} یا
    {skipped:'flag-off'}. صفر اثرِ بیرونی."""
    if not flag_on():
        return {"skipped": "flag-off"}
    import lead_scorer          # noqa: E402 — توابعِ خالص
    import lead_quote           # noqa: E402
    import pricing              # noqa: E402

    lead = dict(lead or {})
    corr = correlation_id or ("corr_" + _sha(lead)[:12])
    lead_id = str(lead.get("id") or lead.get("attribution_id") or _sha(lead)[:12])
    mission_id = mission_id or ("mis_" + corr[5:])

    # (1) لولهٔ خالص: score → intake → price
    scored = lead_scorer.score_lead(lead)
    intake = lead_quote.lead_to_intake(lead, scored.as_dict())
    bd = pricing.estimate_price(intake).to_dict()
    total = bd.get("total_incl_gst") or [0.0, 0.0]
    value_claim = float(total[1]) if isinstance(total, (list, tuple)) and len(total) == 2 else 0.0
    proposal_id = "P-" + _sha({"c": corr, "l": lead_id})[:12]

    # (2) بازیابیِ حافظهٔ مرتبط (اختیاری) → memories_used (تولیدکنندهٔ واقعیِ receipt)
    memories_used = []
    if memory_store is not None:
        try:
            recs = memory_store.search(str(lead.get("description", "")), namespace="semantic", k=3)
            memories_used = memory_store.as_memories_used(recs)
        except Exception:  # noqa: BLE001 — بازیابی fail-soft
            memories_used = []

    # (3) Decision Receipt (immutable) — تصمیمِ «کوت این لید» با reason_codes، نه CoT
    # receipt_id به هویتِ تصمیم (corr+mission+action) پین می‌شود → replay = همان رسید (idempotent)،
    # بی‌آنکه created_atِ صادقانه (ساعتِ واقعی) دستکاری شود.
    pinned_id = "dr_" + _sha({"corr": corr, "mis": mission_id, "act": str(scored.action)})[:16]
    receipt = {
        "receipt_id": pinned_id,
        "trace_id": corr, "mission_id": mission_id, "correlation_id": corr,
        "objective": "quote painting lead (record-only, no send)"[:290],
        "alternatives": ["draft", "skip"],
        "selected_alternative": ("draft" if scored.action == "draft" else scored.action)[:190],
        "reason_codes": [f"SCORE_{scored.score}", f"CAT_{str(scored.category).upper()[:24]}"],
        "assumptions": ["size/scope from description"],
        "memories_used": memories_used,
        "predicted_outcome": {"value_aud_claimed": value_claim, "action": scored.action},
        "effect_class": "E1",   # ثبتِ داخلیِ پایدار (no send)
    }
    rid = receipt_store.record(receipt)

    # (4) Outcome (delivered، sandbox) + (5) link receipt→outcome (idempotent)
    oref = f"{corr}|{proposal_id}|delivered"
    outcome_store.record({"correlation_id": corr, "mission_id": mission_id,
                          "proposal_id": proposal_id, "leg_id": "lead", "lead_id": lead_id,
                          "event_type": "delivered", "value_aud_claimed": value_claim,
                          "idempotency_key": oref,
                          "payload": {"channel": "sandbox", "score": scored.score,
                                      "category": scored.category, "receipt_id": rid}})
    receipt_store.link_outcome(rid, oref)

    # verdict = PENDING (هیچ رأیِ مالکی جعل نمی‌شود)
    return {"receipt_id": rid, "outcome_ref": oref, "correlation_id": corr,
            "mission_id": mission_id, "proposal_id": proposal_id, "lead_id": lead_id,
            "delivered": True, "verdict": "PENDING", "value_aud_claimed": value_claim,
            "memories_used": len(memories_used),
            # W1: امضای قطعیِ تصمیم (PII-free) تا خاطرهٔ یادگرفته **قابلِ بازیابی** باشد —
            # search روی متنِ خاطره کار می‌کند و شناسهٔ تنها هرگز با توصیفِ لیدِ بعدی
            # match نمی‌شود. category/score/action خروجیِ قطعیِ scorer است، نه متنِ خامِ لید.
            "category": str(scored.category), "score": scored.score,
            "action": str(scored.action)}
