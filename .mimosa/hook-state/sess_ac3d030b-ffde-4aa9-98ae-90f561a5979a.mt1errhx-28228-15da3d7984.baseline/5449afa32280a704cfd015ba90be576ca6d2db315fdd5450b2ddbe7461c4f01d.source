"""
brain/graph.py — The main LangGraph workflow.

This is the 'brain' of the system — a stateful graph that:
    load_context → verify → detect → analyze → report → reflect → decide_next

Features:
    - Checkpointing: state is saved between steps (MemorySaver)
    - Conditional routing: gate at verify, reflection loop
    - Tool access: nodes can call tools
    - RAG: nodes can search the vault
    - Self-reflection: quality loop with feedback
    - Auto-experiment: suggests next hypotheses

The graph is backwards-compatible: if LangGraph is not available,
it falls back to the legacy orchestrator.
"""
from __future__ import annotations

from typing import Optional
import numpy as np

from .state import AgentState
from .nodes import (
    load_context_node, verify_node, detect_node, analyze_node,
    report_node, reflect_node, decide_next_node, scores_node,
    route_after_verify, route_after_report, route_after_reflect,
    END_NODE,
)


def _should_revise(state) -> bool:
    """B1: تصمیمِ حلقه‌ی بازتاب — منطق در brain/patterns.py (خالص و تست‌شده)."""
    from brain.patterns import reflect_should_revise
    return reflect_should_revise(state)


def build_graph():
    """
    Build and compile the LangGraph workflow.

    Returns a compiled graph with checkpointer.
    """
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver

    workflow = StateGraph(AgentState)

    # ── Add nodes ──
    workflow.add_node("load_context", load_context_node)
    workflow.add_node("verify",       verify_node)
    workflow.add_node("detect",       detect_node)
    workflow.add_node("scores",       scores_node)  # operational scores
    workflow.add_node("analyze",      analyze_node)
    workflow.add_node("report",       report_node)
    workflow.add_node("reflect",      reflect_node)
    workflow.add_node("decide_next",  decide_next_node)

    # ── Add edges ──
    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "verify")

    # Gate: if verify fails, halt
    workflow.add_conditional_edges(
        "verify",
        lambda s: "detect" if s.get("verified", False) else END,
    )

    workflow.add_edge("detect", "scores")    # compute SMS/SLS/PCAI
    workflow.add_edge("scores", "analyze")   # then geometric analysis
    workflow.add_edge("analyze", "report")

    # Reflection: always review, then decide
    workflow.add_conditional_edges(
        "report",
        lambda s: "reflect" if s.get("needs_review", True) else "decide_next",
    )

    # After reflect: revise or proceed
    # B1: با REFLECT_GATE=1 سقفِ نرمِ بازتاب اعمال می‌شود (brain/patterns.py)؛
    # فلگ خاموش = دقیقاً رفتارِ قبلی (فقط بررسیِ REVISE).
    workflow.add_conditional_edges(
        "reflect",
        lambda s: "report" if _should_revise(s) else "decide_next",
    )

    workflow.add_edge("decide_next", END)

    # ── Compile with checkpointing ──
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    return app


def run_experiment(series: np.ndarray, label: str = "",
                   thread_id: str = "default") -> dict:
    """
    Run the full intelligent pipeline on a time series.

    This is the main entry point — replaces the legacy orchestrator.
    Returns the final state with all results.
    """
    app = build_graph()

    initial_state: AgentState = {
        "series": series.tolist() if hasattr(series, "tolist") else list(series),
        "label": label,
        "thread_id": thread_id,
    }

    config = {"configurable": {"thread_id": thread_id}}

    # Run the graph to completion
    try:
        final_state = app.invoke(initial_state, config=config)
    except Exception as e:
        # B1: حلقه‌ی report↔reflect وقتی به recursion_limit (پیش‌فرض ۲۵) می‌خورد
        # GraphRecursionError می‌دهد — قبلاً ناگرفته بالا می‌رفت و کلِ آزمایش
        # می‌ترکید. state ناتمام با error برمی‌گردانیم؛ خطاهای دیگر دست‌نخورده.
        if type(e).__name__ != "GraphRecursionError":
            raise
        final_state = dict(initial_state)
        final_state["error"] = ("GraphRecursionError: حلقه‌ی بازتاب به سقف خورد — "
                                "گزارش ناتمام (REFLECT_GATE=1 سقفِ نرم می‌گذارد)")

    # Persist to SQLite
    _save_to_memory(final_state, label)

    return final_state


def run_experiment_streaming(series: np.ndarray, label: str = "",
                             thread_id: str = "default"):
    """
    Stream the pipeline execution — yields (node_name, state) at each step.
    For real-time UI updates.
    """
    app = build_graph()

    initial_state: AgentState = {
        "series": series.tolist() if hasattr(series, "tolist") else list(series),
        "label": label,
        "thread_id": thread_id,
    }

    config = {"configurable": {"thread_id": thread_id}}

    try:
        for output in app.stream(initial_state, config=config):
            for node_name, state_update in output.items():
                yield node_name, state_update
    except Exception as e:
        # B1: همان گاردِ GraphRecursionError برای مسیرِ streaming
        if type(e).__name__ != "GraphRecursionError":
            raise
        yield "error", {"error": "GraphRecursionError: حلقه‌ی بازتاب به سقف خورد"}

    # Final save
    # Get final state from the last checkpoint
    final_state = app.get_state(config)
    if final_state and final_state.values:
        _save_to_memory(final_state.values, label)


def _save_to_memory(state: dict, label: str):
    """Save experiment results AND reflections to SQLite for learning."""
    try:
        from memory.store import save_experiment, save_reflection, ExperimentRecord

        rec = ExperimentRecord(
            source=label,
            n_points=len(state.get("series", [])),
            # Δ_self از داده‌ی خام قابل‌محاسبه نیست (نیازمندِ solve مدل است) —
            # قبلاً کپیِ E_shadow ذخیره می‌شد که AVG(delta_self) را بی‌معنا می‌کرد.
            # ۰٫۰ یعنی صادقانه «محاسبه‌نشده»، تا وقتی node ای آن را واقعاً تولید کند.
            delta_self=state.get("delta_self", 0.0),
            e_shadow=state.get("E_shadow_proxy", 0),
            temporal_mi=state.get("temporal_mi", 0),
            rho_hat=state.get("rho_hat", 0),
            verdict=state.get("verdict", "UNKNOWN"),
            confidence=state.get("confidence", "unknown"),
            detectable=state.get("detectable", False),
            narrative=state.get("report_card", "")[:2000],
            reflection=state.get("feedback", ""),
        )
        exp_id = save_experiment(rec)
        state["experiment_id"] = exp_id

        # Save the reflection explicitly so load_context_node can find it
        feedback = state.get("feedback", "")
        quality = state.get("quality", "ACCEPT")
        score = state.get("score", 0.5)
        if feedback:
            save_reflection(exp_id, quality, feedback, score)
    except Exception as e:
        state["error"] = f"save error: {e}"


def chat_with_memory(query: str, thread_id: str = "chat",
                     history: list[dict] = None) -> str:
    """
    Stateful chat: remembers conversation history.
    Uses RAG to ground answers in the 4D-Vault knowledge base.
    """
    from config.settings import get_llm_config
    from llm.langchain_models import get_default_chat
    from brain.tools import search_vault
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    from knowledge.ledger import build_system_prompt

    # RAG: retrieve relevant context
    rag_context = ""
    try:
        rag_context = search_vault.invoke({"query": query, "k": 3})
    except Exception:
        pass

    # Build message history
    system = build_system_prompt("knowledgeable assistant")
    if rag_context:
        system += f"\n\n### دانش مرتبط از vault:\n{rag_context[:800]}"

    messages = [SystemMessage(content=system)]

    # Add conversation history (last 10 turns)
    if history:
        for msg in history[-10:]:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=query))

    # Get response
    cfg = get_llm_config()
    chat = get_default_chat(task="analysis", config=cfg, temperature=0.5)

    try:
        resp = chat.invoke(messages)
    except Exception as e:
        return f"[error: {e}]"

    # Save to memory (قبلاً بعد از return بود و هرگز اجرا نمی‌شد)
    try:
        from memory.store import save_conversation
        save_conversation(thread_id, "user", query)
        save_conversation(thread_id, "assistant", resp.content)
    except Exception:
        pass

    return resp.content


# ════════════════════════════════════════════════════════════════════════
#  Legacy fallback (if LangGraph import fails)
# ════════════════════════════════════════════════════════════════════════

def run_experiment_fallback(series: np.ndarray, label: str = "") -> dict:
    """
    Fallback pipeline using the legacy orchestrator if LangGraph fails.
    """
    from agents.orchestrator import OrchestratorAgent
    from llm.router import get_router

    orch = OrchestratorAgent(get_router())
    result = orch.run_experiment(series, label=label)

    return {
        "verified": result.verifier.findings.get("all_pass", False),
        "anchor_report": result.verifier.findings.get("report", ""),
        "detectable": result.detector.findings.get("detectable", False) if result.detector else False,
        "temporal_mi": result.detector.findings.get("temporal_mi", 0) if result.detector else 0,
        "rho_hat": result.detector.findings.get("rho_hat", 0) if result.detector else 0,
        "detection_narrative": result.detector.narrative if result.detector else "",
        "geometric_narrative": result.analyst.narrative if result.analyst else "",
        "report_card": result.reporter.narrative if result.reporter else "",
        "verdict": result.reporter.findings.get("verdict", "") if result.reporter else "",
        "confidence": result.reporter.findings.get("confidence", "") if result.reporter else "",
    }


if __name__ == "__main__":
    print("=== Brain graph self-test ===\n")

    # Generate test data
    rng = np.random.default_rng(42)
    series = np.zeros(3000)
    for t in range(1, 3000):
        series[t] = 0.7 * series[t-1] + rng.normal(0, 0.1)

    print(f"Input: AR(1) series, {len(series)} points")
    print("Running intelligent pipeline...\n")

    for node_name, state_update in run_experiment_streaming(series, label="test AR(1)"):
        print(f"  ▶ {node_name}: {list(state_update.keys())}")

    print("\n=== Final results ===")
    result = run_experiment(series, label="test AR(1)")
    print(f"  verdict: {result.get('verdict', 'N/A')}")
    print(f"  confidence: {result.get('confidence', 'N/A')}")
    print(f"  quality: {result.get('quality', 'N/A')}")
    print(f"  detectable: {result.get('detectable', 'N/A')}")
    print(f"  next hypothesis: {result.get('next_hypothesis', 'N/A')[:100]}")
