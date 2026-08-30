"""
brain/nodes.py — Graph nodes for the LangGraph workflow.

Each node is a function: (state) -> state_update
They use tools, LLM, memory, and RAG to produce intelligent outputs.
"""
from __future__ import annotations

import numpy as np
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from .state import AgentState
from .tools import compute_shadow_metrics, search_vault, query_experiments, get_anchors
from config.settings import get_llm_config
from llm.langchain_models import get_default_chat
from knowledge.ledger import build_system_prompt


# ════════════════════════════════════════════════════════════════════════
#  Node: Load context (RAG + history)
# ════════════════════════════════════════════════════════════════════════

def load_context_node(state: AgentState) -> dict:
    """
    Load relevant context from THREE sources:
    1. 4D-Vault (RAG) — what does the theory say about this type of data?
    2. Experiment history — have we seen similar experiments before?
    3. Past reflections — what did we LEARN from previous runs?

    This is the 'learning from experience' loop: reflections from
    past experiments are fed into the current run.
    """
    label = state.get("label", "")

    # 1. RAG: search vault for theoretical context
    vault_context = ""
    try:
        query = f"ساختار پنهان در داده‌ی سری زمانی {label}"
        vault_context = search_vault.invoke({"query": query, "k": 2})
    except Exception:
        pass

    # 2. History: past experiments with similar source
    history = ""
    try:
        history = query_experiments.invoke({"filter_source": label, "limit": 3})
    except Exception:
        pass

    # 3. Past reflections — THIS IS THE LEARNING LOOP
    past_lessons = ""
    try:
        from memory.store import _ensure_db
        import sqlite3
        from memory.store import DB_PATH
        _ensure_db()
        conn = sqlite3.connect(str(DB_PATH))
        try:
            conn.row_factory = sqlite3.Row
            # Get recent reflections with meaningful feedback
            rows = conn.execute(
                """SELECT r.feedback, r.quality, e.source, e.verdict
                   FROM reflections r
                   JOIN experiments e ON r.experiment_id = e.id
                   WHERE r.feedback IS NOT NULL AND r.feedback != ''
                   ORDER BY r.timestamp DESC LIMIT 5"""
            ).fetchall()
        finally:
            conn.close()
        if rows:
            lessons = []
            for r in rows:
                lessons.append(
                    f"  - [{r['quality']}] {r['source']}: {r['feedback'][:80]}"
                )
            past_lessons = "### درس‌های آموخته‌شده از آزمایش‌های قبلی:\n" + "\n".join(lessons)
    except Exception:
        pass

    # Assemble context — درس‌ها اول، چون پایین‌دست فقط context[:300] مصرف می‌شود
    # و اگر آخر باشند هرگز به LLM نمی‌رسند (حلقه‌ی یادگیری عملاً غیرفعال می‌شد)
    context = ""
    if past_lessons:
        context += f"{past_lessons}\n\n"
    if vault_context and "error" not in vault_context.lower():
        context += f"{vault_context[:400]}\n\n"
    if history and "No matching" not in history:
        context += f"{history[:200]}\n\n"

    return {"vault_context": context}


# ════════════════════════════════════════════════════════════════════════
#  Node: Verify (W0 equivalent)
# ════════════════════════════════════════════════════════════════════════

def verify_node(state: AgentState) -> dict:
    """Verify model anchors are intact (gate)."""
    from core.model import run_self_test

    results = run_self_test()
    all_pass = all(err < 1e-4 for _, (_, _, err) in results.items())

    report = "\n".join(
        f"  {'✓' if err < 1e-4 else '✗'} {name}: {float(comp):.8f} (err={float(err):.1e})"
        for name, (comp, _, err) in results.items()
    )

    return {
        "verified": all_pass,
        "anchor_report": f"Anchor verification:\n{report}",
    }


# ════════════════════════════════════════════════════════════════════════
#  Node: Detect (W1 equivalent) — uses tool-use
# ════════════════════════════════════════════════════════════════════════

def detect_node(state: AgentState) -> dict:
    """
    Analyze the series for shadow structure.
    Uses compute_shadow_metrics tool, then LLM interprets.
    """
    series = state.get("series", [])
    label = state.get("label", "unknown")

    if not series:
        return {"error": "no series provided", "detectable": False}

    # Tool: compute metrics
    metrics = compute_shadow_metrics.invoke({"series": series})

    if "error" in metrics:
        return {"error": metrics["error"], "detectable": False}

    # LLM: interpret the metrics
    cfg = get_llm_config()
    chat = get_default_chat(task="analysis", config=cfg, temperature=0.4)

    system = build_system_prompt("detector (W1)")
    context = state.get("vault_context", "")

    prompt = f"""داده را تحلیل کن — آیا نشانه‌ی بُعد پنهان هست؟

منبع: {label}
نقاط: {metrics['n_points']}
اطلاعات متقابل زمانی: {metrics['temporal_mi']:.6f}
ρ تخمینی: {metrics['rho_hat']:.4f}
E_shadow proxy: {metrics['E_shadow_proxy']:.6f}
قابل‌تشخیص: {'بله' if metrics['detectable'] else 'خیر'}

{f'دانش مرتبط: {context[:300]}' if context else ''}

پاسخ مختصر: آیا λρ≠0 برقرار است؟ چه نوع بُعد پنهانی محتمل است؟"""

    try:
        resp = chat.invoke([
            SystemMessage(content=system),
            HumanMessage(content=prompt),
        ])
        narrative = resp.content
    except Exception as e:
        narrative = f"[LLM error: {e}]\n" + metrics["verdict"]

    return {
        "temporal_mi": float(metrics["temporal_mi"]),
        "rho_hat": float(metrics["rho_hat"]),
        "E_shadow_proxy": float(metrics["E_shadow_proxy"]),
        "detectable": bool(metrics["detectable"]),
        "detection_narrative": narrative,
    }


# ════════════════════════════════════════════════════════════════════════
#  Node: Compute operational scores (from SOG synthesis)
# ════════════════════════════════════════════════════════════════════════

def scores_node(state: AgentState) -> dict:
    """
    Compute the four operational scores (SMS, SLS, PCAI) from the
    SOG synthesis. These translate the theoretical model into
    engineering decision metrics.
    """
    from core.scores import compute_scores_from_model

    scores = compute_scores_from_model()

    return {
        "sms": float(scores.sms),
        "sls": float(scores.sls),
        "pcai": float(scores.pcai),
        "scores_interpretation": scores.interpret(),
    }


# ════════════════════════════════════════════════════════════════════════
#  Node: Analyze (W2 equivalent) — uses RAG
# ════════════════════════════════════════════════════════════════════════

def analyze_node(state: AgentState) -> dict:
    """
    Geometric interpretation using RAG from the vault.
    Uses Fugu (creative model) for lateral thinking.
    """
    cfg = get_llm_config()
    chat = get_default_chat(task="geometry", config=cfg, temperature=0.9)

    detectable = state.get("detectable", False)
    temporal_mi = state.get("temporal_mi", 0)
    rho_hat = state.get("rho_hat", 0)
    label = state.get("label", "")

    # RAG: search vault for geometric concepts
    geo_context = ""
    try:
        geo_context = search_vault.invoke({
            "query": "هندسه بُعد پنهان تسراکت Takens",
            "k": 2
        })
    except Exception:
        pass

    system = build_system_prompt("geometric analyst (W2)")
    prompt = f"""یافته‌ها را به زبان هندسی ترجمه کن.

داده: {label}
قابل‌تشخیص: {'بله' if detectable else 'خیر'}
MI: {temporal_mi:.6f}

{f'دانش هندسی مرتبط: {geo_context[:400]}' if geo_context else ''}

این داده نشانه‌ی چه نوع بُعدی است؟ تمثیل تسراکت، Takens، یا Diaconis-Freedman؟
خلاقانه اما دقیق (۳-۴ جمله)."""

    try:
        resp = chat.invoke([
            SystemMessage(content=system),
            HumanMessage(content=prompt),
        ])
        narrative = resp.content
    except Exception as e:
        narrative = f"[LLM error: {e}] تفسیر هندسی: ساختار {'قابل' if detectable else 'غیرقابل'} تشخیص."

    return {"geometric_narrative": narrative}


# ════════════════════════════════════════════════════════════════════════
#  Node: Report (W3 equivalent)
# ════════════════════════════════════════════════════════════════════════

def report_node(state: AgentState) -> dict:
    """Compile the final report card."""
    cfg = get_llm_config()
    chat = get_default_chat(task="report", config=cfg, temperature=0.5)

    detectable = state.get("detectable", False)
    verified = state.get("verified", False)

    prompt = f"""گزارش نهایی آزمایش را بساز.

داده: {state.get('label', '')}
مدل تأیید شده: {'بله' if verified else 'خیر'}
قابل‌تشخیص: {'بله' if detectable else 'خیر'}
MI: {state.get('temporal_mi', 0):.6f}

تشخیص:
{state.get('detection_narrative', '')[:400]}

تحلیل هندسی:
{state.get('geometric_narrative', '')[:400]}

یک report card کوتاه: فرضیه / نتیجه / درجه اطمینان / محدودیت.
صادق باش — نتیجه منفی هم ارزشمند است."""

    system = build_system_prompt("reporter (W3)")
    try:
        resp = chat.invoke([
            SystemMessage(content=system),
            HumanMessage(content=prompt),
        ])
        report_card = resp.content
    except Exception as e:
        report_card = f"[error: {e}]"

    # Determine verdict
    if detectable and verified:
        verdict = "HYPOTHESIS SUPPORTED — hidden dimension detected"
        confidence = "high" if state.get("temporal_mi", 0) > 0.01 else "medium"
    elif detectable:
        verdict = "PROVISIONAL — structure detected but model unverified"
        confidence = "low"
    else:
        verdict = "NULL RESULT — no detectable hidden dimension"
        confidence = "high"

    return {
        "report_card": report_card,
        "verdict": verdict,
        "confidence": confidence,
        "needs_review": True,  # always trigger reflection
    }


# ════════════════════════════════════════════════════════════════════════
#  Node: Reflect (meta-agent self-evaluation)
# ════════════════════════════════════════════════════════════════════════

def reflect_node(state: AgentState) -> dict:
    """
    Self-reflection: evaluate the quality of the report.
    Returns ACCEPT / REVISE / REJECT + feedback.
    """
    from .reflection import evaluate_quality

    report = state.get("report_card", "")
    metrics = {
        "temporal_mi": state.get("temporal_mi", 0),
        "detectable": state.get("detectable", False),
        "verified": state.get("verified", False),
    }

    quality, score, feedback = evaluate_quality(report, metrics)

    return {
        "quality": quality,
        "score": score,
        "feedback": feedback,
        # B1: شمارنده‌ی دورهای بازتاب — گیتِ سقف‌دار (patterns.reflect_should_revise)
        # از آن استفاده می‌کند؛ بدونِ فلگ فقط ثبت می‌شود و اثری ندارد.
        "reflect_count": int(state.get("reflect_count", 0) or 0) + 1,
    }


# ════════════════════════════════════════════════════════════════════════
#  Node: Decide next experiment (auto-experiment)
# ════════════════════════════════════════════════════════════════════════

def decide_next_node(state: AgentState) -> dict:
    """
    Suggest the next experiment based on this result and history.
    """
    from .tools import generate_hypothesis

    verdict = state.get("verdict", "")
    label = state.get("label", "")

    domain = "physical" if "lorenz" in label.lower() or "pendulum" in label.lower() else "general"

    try:
        hyp = generate_hypothesis.invoke({"domain": domain})
    except Exception:
        hyp = "تست داده‌ی با ساختار حافظه‌ی متفاوت"

    return {
        "next_hypothesis": hyp,
        "suggested_experiments": [hyp],
    }


# ════════════════════════════════════════════════════════════════════════
#  Conditional edge functions
# ════════════════════════════════════════════════════════════════════════

def route_after_verify(state: AgentState) -> str:
    """If verification failed, halt. Otherwise proceed to detect."""
    if state.get("verified", False):
        return "detect"
    return END_NODE


def route_after_report(state: AgentState) -> str:
    """If report needs review, go to reflect. Otherwise done."""
    if state.get("needs_review", False):
        return "reflect"
    return END_NODE


def route_after_reflect(state: AgentState) -> str:
    """If reflection says REVISE, go back to report. Otherwise decide_next."""
    if state.get("quality") == "REVISE":
        return "report"
    return "decide_next"


END_NODE = "__end__"
