# -*- coding: utf-8 -*-
"""کارت‌های تلگرامِ chord — فقط ساختِ متن (pure). هیچ botای این‌جا نیست.

وایرینگِ واقعی به center.py/render.py = لِینِ سریالِ worktree، پشتِ فلگِ خاموشِ
OCTOPUS_WIRE_CHORD، فقط بعد از رأیِ مالک. این فایل عمداً هیچ importی از
telegram_center ندارد تا policy از مسیرِ UI دورزدنی نباشد.
"""
from __future__ import annotations

_V_EMOJI = {"HEALTHY": "🟢", "OBSERVE_MORE": "🟡", "PROPOSE_PATCH": "🧩",
            "REQUEST_APPROVAL": "🗳", "BLOCK": "⛔", "UNKNOWN": "❔"}


def render_assessment_card(a: dict) -> str:
    """dictِ ChordAssessment → کارتِ کوتاهِ PII-امن برای /doctor یا /health."""
    v = str(a.get("verdict", "UNKNOWN"))
    lines = [
        f"🧭 CHORD — {a.get('mission_id', '?')}",
        f"{_V_EMOJI.get(v, '❔')} Verdict: {v}"
        + ("  (نیازمندِ تأییدِ مالک)" if a.get("approval_required") else ""),
        f"فاصله: {a.get('weighted_distance', '?')} · اطمینان: {a.get('confidence', '?')}"
        f" · عدم‌قطعیت: {a.get('uncertainty', '?')}",
        f"شواهد: {a.get('evidence_summary', '-')}",
    ]
    gaps = a.get("component_gaps") or {}
    if gaps:
        worst = sorted(gaps.items(), key=lambda kv: kv[1].get("weighted", 0),
                       reverse=True)[:3]
        lines.append("شکاف‌ها: " + " · ".join(f"{d} {g.get('gap', 0):+.2f}"
                                              for d, g in worst))
    probe = a.get("recommended_next_probe")
    if probe:
        lines.append(f"قدمِ امنِ بعدی: {probe}")
    lines.append("(shadow — مشورتی؛ اجرا فقط از مسیرِ approval/allowlist)")
    return "\n".join(lines)


def render_health_summary(assessments: list, max_items: int = 3) -> str:
    """خلاصهٔ /health: بدترین‌ها اول."""
    if not assessments:
        return "🧭 CHORD: هنوز ارزیابی‌ای ثبت نشده (shadow mode)."
    order = {"BLOCK": 0, "REQUEST_APPROVAL": 1, "UNKNOWN": 2,
             "OBSERVE_MORE": 3, "PROPOSE_PATCH": 4, "HEALTHY": 5}
    top = sorted(assessments, key=lambda a: order.get(str(a.get("verdict")), 9))[:max_items]
    lines = [f"🧭 CHORD ({len(assessments)} ارزیابی، {max_items} موردِ مهم):"]
    for a in top:
        v = str(a.get("verdict", "?"))
        lines.append(f"{_V_EMOJI.get(v, '❔')} {a.get('mission_id', '?')} — {v}"
                     f" · d={a.get('weighted_distance', '?')}")
    return "\n".join(lines)
