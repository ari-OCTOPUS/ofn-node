#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""paper_mvo.py — Paper Lead MVO: زنجیرهٔ درآمدِ لید به‌صورتِ کاغذی و end-to-end trace-شده.

synthetic lead → canonical intake → score → draft → proposal → fake/sandbox delivery →
simulated owner verdict → durable outcome → (replay/metrics از outcome_store).

**صفر اثرِ بیرونی:** بازاستفاده از توابعِ خالصِ لولهٔ لید (lead_scorer.score_lead،
lead_quote.lead_to_intake، pricing.estimate_price)؛ «delivery» یک تابعِ خالص است که فقط یک
dict برمی‌گرداند — هیچ Telegram/شبکه/پول/EffectorGate. verdict شبیه‌سازی‌شده «سنجش» است،
نه تأییدِ I7. همهٔ رویدادها با IDهای مشترک (correlation/mission/proposal/leg/lead) در
outcome_store ثبت می‌شوند تا لینکِ proposal→outcome قطعی باشد.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "legs"), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _sha(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _fake_deliver(proposal: dict, ok: bool) -> dict:
    """deliv
    یِ ساختگی/sandbox — تابعِ خالص، بدونِ هیچ شبکه/Telegram. فقط نتیجه را گزارش می‌کند
    (هرگز failed را delivered/seen جا نمی‌زند)."""
    return {"delivered": bool(ok), "channel": "sandbox",
            "proposal_id": proposal.get("proposal_id"),
            "reason": None if ok else "simulated-delivery-failure"}


def run_paper_mvo(lead: dict, store, *, mission_id=None, correlation_id=None,
                  verdict: str = "accepted-measurement", deliver_ok: bool = True) -> dict:
    """یک اجرای کاملِ کاغذیِ MVO. verdict ∈ accepted-measurement | rejected | deferred.
    خروجی: traceِ dict با IDهای مشترک + metricsِ جاری. صفر اثرِ بیرونی."""
    import lead_scorer          # noqa: E402 — توابعِ خالصِ لولهٔ لید
    import lead_quote           # noqa: E402
    import pricing              # noqa: E402

    lead = dict(lead or {})
    corr = correlation_id or ("corr_" + _sha(lead)[:12])
    lead_id = str(lead.get("id") or lead.get("attribution_id") or _sha(lead)[:12])
    mission_id = mission_id or ("mis_" + corr[5:])

    # ── canonical intake → score → price (توابعِ واقعیِ خالص) ────────────────────
    scored = lead_scorer.score_lead(lead)
    intake = lead_quote.lead_to_intake(lead, scored.as_dict())
    bd = pricing.estimate_price(intake).to_dict()
    total = bd.get("total_incl_gst") or [0.0, 0.0]
    value_claim = float(total[1]) if isinstance(total, (list, tuple)) and len(total) == 2 else 0.0

    proposal_id = "P-" + _sha({"c": corr, "l": lead_id})[:12]
    proposal = {"proposal_id": proposal_id, "leg_id": "lead", "kind": "quote",
                "payload": {"attribution_id": lead_id, "score": scored.score,
                            "category": scored.category, "value_aud_claimed": value_claim}}
    base = {"correlation_id": corr, "mission_id": mission_id, "proposal_id": proposal_id,
            "leg_id": "lead", "lead_id": lead_id}

    # ── delivery (fake/sandbox) → outcomeِ durable ──────────────────────────────
    d = _fake_deliver(proposal, deliver_ok)
    if not d["delivered"]:
        store.record({**base, "event_type": "failed",
                      "idempotency_key": f"{corr}|{proposal_id}|failed",
                      "payload": {"channel": "sandbox", "reason": d["reason"]}})
        return {"delivered": False, "verdict": None, **base,
                "value_aud_claimed": value_claim, "metrics": store.metrics()}

    store.record({**base, "event_type": "delivered", "value_aud_claimed": value_claim,
                  "idempotency_key": f"{corr}|{proposal_id}|delivered",
                  "payload": {"channel": "sandbox", "score": scored.score,
                              "category": scored.category}})

    # ── simulated owner verdict (سنجش، نه تأییدِ I7) → outcomeِ durable ──────────
    if verdict == "deferred":
        store.record({**base, "event_type": "deferred", "verdict": "later",
                      "idempotency_key": f"{corr}|{proposal_id}|deferred"})
    elif verdict == "rejected":
        store.record({**base, "event_type": "rejected", "verdict": "no",
                      "idempotency_key": f"{corr}|{proposal_id}|rejected"})
    else:  # accepted-measurement — «yes-measurement» عمداً ≠ approved (نه I7)
        store.record({**base, "event_type": "accepted-measurement", "verdict": "yes-measurement",
                      "value_aud_claimed": value_claim,
                      "idempotency_key": f"{corr}|{proposal_id}|accepted"})

    return {"delivered": True, "verdict": verdict, **base,
            "value_aud_claimed": value_claim, "metrics": store.metrics()}
