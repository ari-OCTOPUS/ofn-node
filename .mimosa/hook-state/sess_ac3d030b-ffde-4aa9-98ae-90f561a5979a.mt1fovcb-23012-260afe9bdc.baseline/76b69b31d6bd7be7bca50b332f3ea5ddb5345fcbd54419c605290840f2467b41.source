"""claim_builder.py — Cortex → draft EpistemicClaim از telemetry (ADR-039, post-C5).

این تنها زمانی معنادار است که epistemic واقعاً به cortex وصل شده باشد (post-Go).
فعلاً یک تابعِ propose-only است که یک snapshot از telemetry می‌گیرد و **در صورت وجودِ
سیگنالِ قابل‌آزمون** یک claimِ draft می‌سازد. **هیچ‌وقت claim را auto-run نمی‌کند** —
claim باید توسط owner/sandbox تأیید و سپس اجرا شود.

صادقانه: ساختِ claimِ خوب از telemetry خودش یک مسئلهٔ تحقیقی است (E2 maturity).
این تابع در E1/E2 فقط claim‌های بسیار محتاط می‌سازد یا None برمی‌گرداند.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def draft_from_telemetry(snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """یک snapshotِ telemetry → draft claim یا None.

    محتاط: فقط اگر snapshot یک metric قابل‌مشاهده با مقدارِ numberی داشته باشد،
    یک claimِ descriptive می‌سازد. claim هرگز auto-run نمی‌شود.

    خروجی: dict با فیلدهای لازم برای EpistemicClaim (نه خودِ model — caller آن را
    در کابینِ TCB اعتبارسنجی می‌کند) یا None.
    """
    if not isinstance(snapshot, dict):
        return None
    # به دنبالِ یک metricِ numberی بگرد (مثلاً coherence، beat، discovery_rate)
    metric = None
    for key in ("coherence", "discovery_rate", "convergence", "pain"):
        v = snapshot.get(key)
        if isinstance(v, (int, float)):
            metric = (key, float(v))
            break
    if metric is None:
        return None   # سیگنالِ قابل‌آزمون نیست — صادقانه None

    key, value = metric
    # claimِ محتاط: «metric در بازهٔ X است» — descriptive، آزمون‌پذیر، low-stakes
    return {
        "claim_type": "descriptive",
        "operational_definition": f"{key} از state خوانده می‌شود و مقدارِ عددی دارد",
        "observed_value": value,
        "metric": key,
        "world_mode": "hypothesis",      # هرگز reality
        "execution_scope": "sandbox_only",
        "testability": 0.5,              # محتاط
        "prior": 0.3,
        "note": ("draft از claim_builder — propose-only؛ auto-run ممنوع. "
                 "این یک claimِ آزمون‌پذیرِ low-stakes است، نه ادعای قابلیت."),
        "may_execute": False,
    }


def is_runnable_draft(draft: Dict[str, Any]) -> bool:
    """آیا این draft حداقلِ لازم برای ورود به کابینِ TCB را دارد؟"""
    if not isinstance(draft, dict):
        return False
    return all(k in draft for k in ("operational_definition", "metric",
                                    "world_mode", "testability", "prior")) \
        and draft.get("may_execute") is False
