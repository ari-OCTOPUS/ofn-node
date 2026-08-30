"""
brain/reflection.py — Self-reflection: evaluate the quality of agent output.

The meta-agent checks:
1. Are the numbers consistent with anchors?
2. Is the narrative logically sound?
3. Does the verdict match the metrics?

Returns ACCEPT / REVISE / REJECT + a quality score.
"""
from __future__ import annotations

from typing import Tuple
from config.settings import get_llm_config
from llm.langchain_models import get_default_chat
from langchain_core.messages import HumanMessage, SystemMessage


def evaluate_quality(report: str, metrics: dict) -> Tuple[str, float, str]:
    """
    Evaluate the quality of a report.

    Returns (quality, score, feedback):
        quality: "ACCEPT" | "REVISE" | "REJECT"
        score: 0.0 to 1.0
        feedback: textual explanation
    """
    # ── Rule-based checks first (fast, no LLM) ──
    checks = []

    # Check 1: report has content
    if len(report) < 50:
        return "REJECT", 0.1, "report too short"

    # Check 2: verdict matches metrics
    detectable = metrics.get("detectable", False)
    if detectable and "NULL" in report.upper():
        checks.append(("verdict mismatch", -0.2))
    if not detectable and "SUPPORTED" in report.upper():
        checks.append(("verdict mismatch", -0.2))

    # Check 3: mentions key quantities
    mi = metrics.get("temporal_mi", 0)
    if mi > 0.001 and "shadow" not in report.lower():
        checks.append(("missing shadow mention", -0.1))

    # ── LLM-based quality assessment ──
    cfg = get_llm_config()
    try:
        chat = get_default_chat(task="analysis", config=cfg, temperature=0.3)

        prompt = f"""کیفیت این گزارش را ارزیابی کن. ACCEPT یا REVISE بگو.

گزارش:
{report[:600]}

متریک‌ها:
- قابل‌تشخیص: {detectable}
- temporal MI: {mi:.6f}

معیارها:
1. آیا نتیجه با متریک‌ها سازگار است؟
2. آیا تفسیر منطقی است؟
3. آیا محدودیت‌ها ذکر شده‌اند؟

پاسخ: ACCEPT یا REVISE + یک جمله دلیل."""

        resp = chat.invoke([
            SystemMessage(content="تو یک ارزیاب کیفیت هستی. دقیق و سخت‌گیر."),
            HumanMessage(content=prompt),
        ])
        llm_feedback = resp.content

        if "ACCEPT" in llm_feedback.upper():
            base_quality = "ACCEPT"
            base_score = 0.8
        elif "REVISE" in llm_feedback.upper():
            base_quality = "REVISE"
            base_score = 0.4
        else:
            base_quality = "ACCEPT"
            base_score = 0.6
            llm_feedback = "default accept: " + llm_feedback
    except Exception:
        # Fallback: rule-based only
        base_quality = "ACCEPT" if not any(c[1] < -0.15 for c in checks) else "REVISE"
        base_score = 0.6 if base_quality == "ACCEPT" else 0.35
        llm_feedback = "rule-based: " + "; ".join(c[0] for c in checks) if checks else "no issues"

    # Apply rule-based adjustments
    score = base_score + sum(penalty for _, penalty in checks)
    score = max(0.0, min(1.0, score))

    # Final quality based on score
    if score >= 0.6:
        quality = "ACCEPT"
    elif score >= 0.3:
        quality = "REVISE"
    else:
        quality = "REJECT"

    return quality, round(score, 2), llm_feedback


def reflect_on_experiment(state: dict) -> dict:
    """
    Full reflection on an experiment state.
    Saves reflection to memory.
    """
    report = state.get("report_card", "")
    metrics = {
        "temporal_mi": state.get("temporal_mi", 0),
        "detectable": state.get("detectable", False),
        "verified": state.get("verified", False),
    }

    quality, score, feedback = evaluate_quality(report, metrics)

    # Save to SQLite
    try:
        from memory.store import save_reflection
        exp_id = state.get("experiment_id")
        if exp_id:
            save_reflection(exp_id, quality, feedback, score)
    except Exception:
        pass

    return {
        "quality": quality,
        "score": score,
        "feedback": feedback,
    }


if __name__ == "__main__":
    # Test with a sample report
    report = """## گزارش آزمایش

فرضیه: آیا نشانه‌ی بُعد پنهان هست؟
نتیجه: بله — E_shadow > 0 نشان می‌دهد ساختار زمانی وجود دارد.
درجه اطمینان: بالا.
محدودیت: فقط یک منبع داده تست شد."""

    quality, score, feedback = evaluate_quality(report, {
        "temporal_mi": 0.01, "detectable": True
    })
    print(f"Quality: {quality}")
    print(f"Score: {score}")
    print(f"Feedback: {feedback}")
