#!/usr/bin/env python3
"""money_gate — دیوارِ per-actionِ تأییدِ انسانی برای پولِ واقعی (A2، fail-closed).

قرارداد: هر effectorِ پولِ واقعی پیش از عمل → money_gate.check(amount_aud, action_id, channel).
  • amount ≤ human_gate_aud (AU$20، قفل‌شدهٔ verdict آری 2026-07-07؛ از budgets.yaml) →
    allow (زیرِ آستانهٔ Autonomy Ramp). توجه: سقفِ کلِ خرج را budget_gate می‌بندد — این گیت مستقل و مکمل است.
  • amount > آستانه → فقط با تأییدِ انسانیِ معتبرِ match‌خورده از ApprovalChannel (status ∈ approved/sent).
خودگزارشیِ ایجنت هرگز معتبر نیست. الان paper: channel پیش‌فرض = NotWiredStub → هر مبلغِ >آستانه deny.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opslib                                              # noqa: E402
from approval_channel import ApprovalChannel, NotWiredStub  # noqa: E402

HUMAN_GATE_AUD_HARD = 20.0    # verdict آری 2026-07-07 (قفل‌شده) — کفِ fail-closed


def human_gate_aud() -> float:
    """آستانهٔ human-gate از budgets.yaml (global.human_gate_aud) با کفِ fail-closed = min(20, yaml).
    yaml ناخوانا/بی‌کلید → 20 (هرگز شل‌تر از verdict)."""
    try:
        v = opslib.load_budgets().get("global", {}).get("human_gate_aud")
        if v is not None:
            return min(HUMAN_GATE_AUD_HARD, float(v))
    except Exception:
        pass
    return HUMAN_GATE_AUD_HARD


def check(amount_aud: float, action_id: str, channel: ApprovalChannel | None = None) -> dict:
    """خروجی: {allow: bool, reason: str, ...}. fail-closed: بالای آستانه بدون تأییدِ معتبر = deny."""
    try:
        amt = float(amount_aud)
    except (TypeError, ValueError):
        return {"allow": False, "reason": "amount-not-a-spend"}
    # 2026-08-16 continuous-C: مبلغِ منفی قبلاً از «≤آستانه» رد می‌شد (allow).
    # NaN/Inf هم با دلیلِ دروغینِ over-gate deny می‌شدند. خرجِ نامعتبر = deny.
    if not math.isfinite(amt) or amt < 0.0:
        return {"allow": False, "reason": "amount-not-a-spend"}
    cap = human_gate_aud()
    if amt <= cap:
        return {"allow": True, "reason": f"under-human-gate(≤AU${cap:.0f})"}
    ch = channel or NotWiredStub()
    appr = ch.approval_for(action_id=action_id, amount_aud=amount_aud)
    if appr is not None and appr.valid:
        return {"allow": True, "reason": "human-approved", "via": ch.name,
                "approval": {"action_id": appr.action_id, "amount_aud": appr.amount_aud,
                             "status": appr.status}}
    return {"allow": False,
            "reason": f"over-gate(AU${amt:.2f}>{cap:.0f}) no valid approval via {ch.name}"}
