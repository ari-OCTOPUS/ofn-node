"""
brain/tools.py — Tools that agents can invoke autonomously.

These are LangChain @tool-decorated functions that give agents
the ability to: compute, plot, search the vault, query history,
and generate hypotheses.

This is the 'tool-use' capability — agents decide when to call these.
"""
from __future__ import annotations

import json
import numpy as np
from pathlib import Path

from langchain_core.tools import tool


# ════════════════════════════════════════════════════════════════════════
#  Tool 1: Compute shadow metrics on a series
# ════════════════════════════════════════════════════════════════════════

@tool
def compute_shadow_metrics(series: list[float]) -> dict:
    """
    Compute E_shadow, Δ_self proxy, temporal MI, and detectability
    on a time series. Returns a dict with all metrics.

    Use this when you need to analyze whether a series shows
    signs of a hidden dimension.
    """
    from core.metrics import empirical_shadow, fit_shadow_parameters

    arr = np.array(series, dtype=float)
    if len(arr) < 20:
        return {"error": "series too short (need ≥20 points)"}

    shadow = empirical_shadow(arr)
    fit = fit_shadow_parameters(arr)

    return {
        "temporal_mi": float(round(shadow["temporal_mi"], 6)),
        "lag1_rho": float(round(shadow["lag1_rho"], 4)),
        "memory_len": float(round(shadow["memory_len"], 4)),
        "rho_hat": float(round(fit["rho_hat"], 4)),
        "E_shadow_proxy": float(round(fit.get("E_shadow_proxy", 0), 6)),
        "detectable": bool(fit.get("detectable", False)),
        "verdict": fit.get("classification", "unknown"),
        "n_points": int(len(arr)),
        "autocorr": [float(round(a, 4)) for a in shadow["autocorr"]],
    }


# ════════════════════════════════════════════════════════════════════════
#  Tool 2: Search the knowledge vault (RAG)
# ════════════════════════════════════════════════════════════════════════

@tool
def search_vault(query: str, k: int = 3) -> str:
    """
    Search the 4D-Vault knowledge base using semantic similarity.
    Returns relevant notes about the query.

    Use this to look up definitions, principles, or connections
    from the project's knowledge base.
    """
    try:
        from memory.vectorstore import search_vault as _search
        results = _search(query, k=k)
        if not results:
            return "No relevant notes found."
        out = []
        for i, r in enumerate(results, 1):
            out.append(f"[{i}] {r['title']} (relevance: {r['relevance']})\n{r['content'][:300]}")
        return "\n\n---\n\n".join(out)
    except Exception as e:
        return f"Search error: {e}"


# ════════════════════════════════════════════════════════════════════════
#  Tool 3: Query past experiments from history
# ════════════════════════════════════════════════════════════════════════

@tool
def query_experiments(filter_source: str = "", filter_verdict: str = "",
                      limit: int = 5) -> str:
    """
    Query the experiment history from SQLite.
    Find past experiments by source type or verdict.

    Use this to learn from previous experiments and avoid
    repeating work.
    """
    try:
        from memory.store import query_experiments as _query
        results = _query(source=filter_source, verdict=filter_verdict, limit=limit)
        if not results:
            return "No matching past experiments found."

        out = [f"Found {len(results)} experiments:"]
        for r in results:
            out.append(
                f"  #{r['id']} [{r['timestamp'][:10]}] "
                f"source={r['source']} | "
                f"E_shadow={r['e_shadow']:.4f} | "
                f"Δ_self={r['delta_self']:.4f} | "
                f"verdict={r['verdict']}"
            )
        return "\n".join(out)
    except Exception as e:
        return f"Query error: {e}"


# ════════════════════════════════════════════════════════════════════════
#  Tool 4: Generate a hypothesis for next experiment
# ════════════════════════════════════════════════════════════════════════

@tool
def generate_hypothesis(domain: str = "general") -> str:
    """
    Generate a hypothesis for what kind of hidden structure
    might be present in a given domain.

    Use this to suggest what data or experiment to try next.
    """
    from config.settings import get_llm_config
    from llm.langchain_models import get_default_chat
    from langchain_core.messages import HumanMessage, SystemMessage

    cfg = get_llm_config()
    chat = get_default_chat(task="creative", config=cfg, temperature=0.9)

    prompt = f"""یک hypothesis جدید برای کشف بُعد پنهان در دامنه‌ی «{domain}» تولید کن.

بر اساس این الگوها فکر کن:
- اگر داده‌ی دارای حافظه (ρ≠0) و نشت (λ≠0) باشد، E_shadow > 0 است
- بُعد پنهان ممکن است فیزیکی، اطلاعاتی، یا اقتصادی باشد
- نتیجه‌ی منفی هم ارزشمند است

یک فرضیه‌ی قابل‌آزمون بنویس (۲-۳ جمله)."""

    try:
        resp = chat.invoke([SystemMessage(content="تو یک ایجنت تحقیقاتی هستی."),
                           HumanMessage(content=prompt)])
        hypothesis = resp.content
    except Exception:
        hypothesis = f"[hypothesis for {domain}: تست داده‌ی جدید با ساختارِ پنهانِ متفاوت]"

    # Save to database
    try:
        from memory.store import save_hypothesis
        save_hypothesis(domain, hypothesis)
    except Exception:
        pass

    return hypothesis


# ════════════════════════════════════════════════════════════════════════
#  Tool 5: Get model anchors for verification
# ════════════════════════════════════════════════════════════════════════

@tool
def get_anchors() -> dict:
    """
    Get the canonical model anchor values (from 4.py) for verification.

    Returns all anchor values that any analysis should be checked against.
    """
    from core.model import ANCHORS
    return {k: round(v, 8) if isinstance(v, float) else v for k, v in ANCHORS.items()}


# ════════════════════════════════════════════════════════════════════════
#  Tool list for binding to agents
# ════════════════════════════════════════════════════════════════════════

ALL_TOOLS = [
    compute_shadow_metrics,
    search_vault,
    query_experiments,
    generate_hypothesis,
    get_anchors,
]


if __name__ == "__main__":
    print("=== Testing tools ===\n")

    # Test compute_shadow_metrics
    rng = np.random.default_rng(42)
    s = np.zeros(5000)
    for t in range(1, 5000):
        s[t] = 0.7 * s[t-1] + rng.normal(0, 0.1)

    print("1. compute_shadow_metrics:")
    result = compute_shadow_metrics.invoke({"series": s.tolist()[:500]})
    print(f"   {result}")

    # Test get_anchors
    print("\n2. get_anchors:")
    anchors = get_anchors.invoke({})
    print(f"   {anchors}")

    # Test query_experiments
    print("\n3. query_experiments:")
    hist = query_experiments.invoke({"limit": 3})
    print(f"   {hist[:200]}")

    # Test search_vault
    print("\n4. search_vault:")
    result = search_vault.invoke({"query": "Delta_self", "k": 2})
    print(f"   {result[:200]}")
