"""
brain/auto_experiment.py — Autonomous hypothesis generation and experiment queue.

The system can suggest and queue new experiments based on:
- Pattern from past experiments
- Unexplored data sources
- Theoretical predictions
"""
from __future__ import annotations

from typing import Optional
from config.settings import get_llm_config
from llm.langchain_models import get_default_chat
from langchain_core.messages import HumanMessage, SystemMessage


def suggest_next_experiment(current_verdict: str = "",
                            current_source: str = "",
                            history: list[dict] = None) -> dict:
    """


# ═══ STATUS: RETIRED (2026-08-19, OWNER LOOP-01 دسته‌های A2/A3/B2/B5) ═══
# علت: suggest_next_experiment هرگز caller تولیدی نداشت (فقط self-reference) · canonical زنده: هیچ‌کدام — اگر روزی لازم شد، از Island با benchmark وصل شود (OWNER-DECISION-QUEUE)
# این فایل حذف نمی‌شود (سیاستِ «کد زنده ممکن است حذف شود، درسِ شکست نه»)؛
# صرفاً از نقشهٔ فعال خارج است و نباید توسط کدِ نو import شود.
    Suggest what to test next based on current results and history.

    Returns dict with:
        - hypothesis: what we expect
        - suggested_source: what data to use
        - rationale: why
    """
    cfg = get_llm_config()
    chat = get_default_chat(task="creative", config=cfg, temperature=0.9)

    # Build context from history
    hist_str = ""
    if history:
        seen_sources = set(h.get("source", "") for h in history)
        hist_str = f"آزمایش‌های قبلی: {', '.join(list(seen_sources)[:5])}"

    prompt = f"""برای کشف بُعد پنهان، پیشنهادِ آزمایشِ بعدی را بده.

وضعیت فعلی:
- نتیجه: {current_verdict}
- منبع: {current_source}
- {hist_str}

پاسخ را در این قالب بده:
HYPOTHESIS: [یک فرضیه]
SOURCE: [پیشنهاد داده: Lorenz / Brownian / AR(1) / Yahoo Finance / ...]
RATIONALE: [یک جمله دلیل]

متنوع باش — منابعی که قبلاً تست نشده‌اند را پیشنهاد بده."""

    try:
        resp = chat.invoke([
            SystemMessage(content="تو یک ایجنت تحقیقاتی هستی که آزمایش طراحی می‌کند."),
            HumanMessage(content=prompt),
        ])
        text = resp.content
    except Exception:
        text = "HYPOTHESIS: تست Lorenz\nSOURCE: physical\nRATIONALE: مثال Takens"

    # Parse response
    result = {"hypothesis": text, "suggested_source": "unknown", "rationale": ""}
    for line in text.split("\n"):
        if line.strip().startswith("HYPOTHESIS:"):
            result["hypothesis"] = line.split(":", 1)[1].strip()
        elif line.strip().startswith("SOURCE:"):
            result["suggested_source"] = line.split(":", 1)[1].strip()
        elif line.strip().startswith("RATIONALE:"):
            result["rationale"] = line.split(":", 1)[1].strip()

    # Save hypothesis
    try:
        from memory.store import save_hypothesis
        save_hypothesis(current_source, result["hypothesis"], result["rationale"])
    except Exception:
        pass

    return result


def get_experiment_queue(limit: int = 5) -> list[dict]:
    """Get pending hypotheses that should be tested."""
    try:
        from memory.store import get_pending_hypotheses
        return get_pending_hypotheses(limit)
    except Exception:
        return []


def mark_hypothesis_tested(hypothesis_id: int, result: str = ""):
    """Mark a hypothesis as tested."""
    try:
        from memory.store import _ensure_db
        import sqlite3
        from memory.store import DB_PATH
        _ensure_db()
        conn = sqlite3.connect(str(DB_PATH))
        try:
            conn.execute(
                "UPDATE hypotheses SET tested=1, result=? WHERE id=?",
                (result, hypothesis_id)
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        # B5: قبلاً except:pass — هم اتصال نشت می‌کرد هم شکست بی‌صدا بود
        import logging
        logging.getLogger(__name__).warning("mark_hypothesis_tested failed: %s", e)


if __name__ == "__main__":
    suggestion = suggest_next_experiment(
        current_verdict="SUPPORTED",
        current_source="AR(1)+noise",
    )
    print("=== Suggested next experiment ===")
    for k, v in suggestion.items():
        print(f"  {k}: {v}")
