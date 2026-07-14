"""
brain/state.py — State definition for the LangGraph agent workflow.

This TypedDict flows through all nodes in the graph, carrying:
    - input data (series, label)
    - computed metrics
    - agent narratives
    - reflection results
    - experiment metadata
"""
from __future__ import annotations

from typing import TypedDict, Optional, Any
from langgraph.graph import MessagesState


class AgentState(TypedDict, total=False):
    """
    State that flows through the LangGraph workflow.
    `total=False` means all fields are optional — nodes add what they produce.
    """
    # ── Input ──
    series: list[float]               # the raw time series
    label: str                         # source label
    thread_id: str                     # for conversation tracking

    # ── Verification (W0) ──
    verified: bool                     # did anchors pass?
    anchor_report: str                 # verification details

    # ── Detection (W1) ──
    temporal_mi: float
    rho_hat: float
    E_shadow_proxy: float
    detectable: bool
    detection_narrative: str

    # ── Analysis (W2) ──
    geometric_narrative: str
    vault_context: str                 # RAG results

    # ── Report (W3) ──
    verdict: str
    confidence: str
    report_card: str

    # ── Reflection (meta) ──
    needs_review: bool
    quality: str                       # ACCEPT / REVISE / REJECT
    feedback: str
    score: float                       # 0-1 quality score
    reflect_count: int                 # B1: شمارِ دورهای بازتاب (برای گیتِ سقف‌دار)

    # ── Auto-experiment ──
    next_hypothesis: str
    suggested_experiments: list[str]

    # ── Operational scores (from SOG synthesis) ──
    sms: float                        # Self-Model Score = L_b - L_i
    sls: float                        # Shadow Leakage Score = L_0 - L_b
    pcai: float                       # Private-Channel Advantage Index
    scores_interpretation: str        # human-readable

    # ── Metadata ──
    experiment_id: int                 # SQLite row ID
    error: str                         # if something went wrong
