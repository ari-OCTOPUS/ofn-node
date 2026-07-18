# -*- coding: utf-8 -*-
"""گیتِ عدم‌قطعیت — قبل از هر policy اجرا می‌شود. fail-closed.

خروجی: dict(open: bool, verdict_hint: str|None, reasons: list)
- شواهدِ کم → UNKNOWN (نه «سالم»)
- تناقض → OBSERVE_MORE و بستنِ خودترمیمیِ خودکار
- عدم‌قطعیتِ بالا → بستنِ PROPOSE_PATCH
"""
from __future__ import annotations

from .schemas import StateVector, Verdict

# آستانه‌های v0 — بعد از دورهٔ سایه با دادهٔ واقعی کالیبره می‌شوند (نه با سلیقه).
MIN_COVERAGE = 0.35          # زیرِ این: اصلاً نمی‌دانیم
SOFT_COVERAGE = 0.60         # زیرِ این: فقط مشاهدهٔ بیشتر
MAX_UNCERTAINTY_FOR_PATCH = 0.60
CONTRADICTION_LIMIT = 0      # هر تناقضِ ثبت‌شده = مشاهدهٔ بیشتر


def gate(vec: StateVector, contradiction_count: int = 0) -> dict:
    reasons = []
    errs = vec.validate()
    if errs:
        return {"open": False, "verdict_hint": Verdict.UNKNOWN,
                "reasons": ["invalid-vector"] + errs}

    if vec.evidence_coverage < MIN_COVERAGE:
        reasons.append(f"evidence_coverage={vec.evidence_coverage:.2f}<{MIN_COVERAGE} → UNKNOWN")
        return {"open": False, "verdict_hint": Verdict.UNKNOWN, "reasons": reasons}

    if contradiction_count > CONTRADICTION_LIMIT:
        reasons.append(f"contradictions={contradiction_count} → collect evidence first")
        return {"open": False, "verdict_hint": Verdict.OBSERVE_MORE, "reasons": reasons}

    if vec.evidence_coverage < SOFT_COVERAGE:
        reasons.append(f"evidence_coverage={vec.evidence_coverage:.2f}<{SOFT_COVERAGE} → observe more")
        return {"open": False, "verdict_hint": Verdict.OBSERVE_MORE, "reasons": reasons}

    if vec.uncertainty > MAX_UNCERTAINTY_FOR_PATCH:
        reasons.append(f"uncertainty={vec.uncertainty:.2f}>{MAX_UNCERTAINTY_FOR_PATCH} → auto-repair closed")
        return {"open": False, "verdict_hint": Verdict.OBSERVE_MORE, "reasons": reasons}

    reasons.append("gate-open: coverage/uncertainty within v0 thresholds")
    return {"open": True, "verdict_hint": None, "reasons": reasons}
