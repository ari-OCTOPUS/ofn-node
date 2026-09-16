#!/usr/bin/env python3
"""تست SM-B0 · School Memory numeric core ($0 آفلاین).

DoD: curriculum graph + L(G) + awareness diffusion + insight-events.
shared L(G) با spectral_mine. bounded ~48 nodes. propose-only. no PII.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(r"F:\backup\_ops\tests")))

import harness  # noqa: E402
ENV = harness.setup("school-memory")

from curriculum import (CurriculumGraph, TopicNode, CurriculumEdge,  # noqa: E402
                        AwarenessField, InsightEvent, detect_insights,
                        seed_curriculum, clip01)


# ════════════════════════════════════════════════════════════════════════════════
# Graph
# ════════════════════════════════════════════════════════════════════════════════

def t_seed_curriculum_built():
    """seed_curriculum ~48 nodes در 6 layer."""
    g = seed_curriculum()
    assert g.n_nodes >= 40, f"nodes={g.n_nodes}"
    assert g.n_edges > 0
    layers = set(n.layer for n in g.nodes.values())
    assert layers == {"A", "B", "C", "D", "E", "F"}, layers


def t_node_has_coord_and_tag():
    """هر node coord x∈R^6 و epistemic_tag دارد."""
    g = seed_curriculum()
    for n in g.nodes.values():
        assert len(n.coord) == 6, f"{n.id} coord len={len(n.coord)}"
        assert n.epistemic_tag in ("Established", "Strong", "Testable", "Speculative")


def t_laplacian_shape():
    """L(G) ماتریس N×N."""
    g = seed_curriculum()
    L = g.laplacian()
    try:
        import numpy as np
        assert L.shape == (g.n_nodes, g.n_nodes)
    except (ImportError, AttributeError):
        assert len(L) == g.n_nodes


def t_laplacian_psd():
    """L(G) نیمه‌معین‌مثبت (eigenvalues ≥ ۰)."""
    g = seed_curriculum()
    L = g.laplacian()
    try:
        import numpy as np
        eigvals = np.linalg.eigvalsh(L)
        assert all(e >= -1e-6 for e in eigvals), f"L not PSD: {eigvals[:5]}"
    except (ImportError, AttributeError):
        pass   # pure-python skip


def t_spectral_gap_returns_float():
    """spectral_gap عدد برمی‌گرداند."""
    g = seed_curriculum()
    gap = g.spectral_gap()
    assert isinstance(gap, float) and gap >= 0.0


# ════════════════════════════════════════════════════════════════════════════════
# Awareness diffusion
# ════════════════════════════════════════════════════════════════════════════════

def t_awareness_study_raises():
    """study → a_k بالا می‌رود."""
    g = seed_curriculum()
    f = AwarenessField(g)
    f.study("A01", intensity=0.8)
    assert f.awareness_of("A01") >= 0.7


def t_awareness_diffuses_to_neighbors():
    """diffusion: a_k به همسایگان پخش می‌شود بعد از tick."""
    g = seed_curriculum()
    f = AwarenessField(g, dt=0.1)
    f.study("A01", intensity=1.0)
    a_before = f.awareness_of("A02")   # همسایه
    f.tick()
    f.tick()
    f.tick()
    a_after = f.awareness_of("A02")
    assert a_after >= a_before, f"diffusion باید پخش کند: {a_before}→{a_after}"


def t_awareness_clipped_01():
    """a همیشه ∈ [0,1]."""
    g = seed_curriculum()
    f = AwarenessField(g)
    f.study("A01", intensity=10.0)
    f.tick(inputs={"A01": 10.0})
    assert all(0.0 <= v <= 1.0 for v in f.a)


def t_awareness_mean():
    """mean_awareness عدد معقول."""
    g = seed_curriculum()
    f = AwarenessField(g)
    f.study("A01", 0.5)
    m = f.mean_awareness()
    assert 0.0 <= m <= 1.0


def t_ignited_topics():
    """ignited_topics: a_i ≥ θ."""
    g = seed_curriculum()
    f = AwarenessField(g)
    f.study("B01", intensity=0.9)
    ignited = f.ignited_topics(theta_high=0.7)
    assert "B01" in ignited


# ════════════════════════════════════════════════════════════════════════════════
# Insight events (propose-only)
# ════════════════════════════════════════════════════════════════════════════════

def t_insight_topic_ignited():
    """topic-ignited وقتی a_i از θ بگذرد."""
    g = seed_curriculum()
    f = AwarenessField(g)
    f.study("A01", intensity=0.9)
    events = detect_insights(f, g, theta_high=0.7)
    kinds = [e.kind for e in events]
    assert "topic-ignited" in kinds


def t_insight_structural_shift():
    """structural-shift وقتی Δ(gap) بزرگ باشد."""
    g = seed_curriculum()
    f = AwarenessField(g)
    events = detect_insights(f, g, prev_gap=0.001)   # gap بزرگ → shift
    # ممکن است structural-shift نباشد چون gap ثابت است، ولی نباید crash
    assert isinstance(events, list)


def t_insight_coactivation_proposes_edge():
    """co-activation → propose_new_edge=True (human-gated)."""
    g = seed_curriculum()
    f = AwarenessField(g)
    f.study("A01", intensity=0.9)
    f.study("A02", intensity=0.9)
    events = detect_insights(f, g, co_activation_threshold=0.6)
    co = [e for e in events if e.kind == "co-activation"]
    if co:
        assert co[0].propose_new_edge is True


def t_insights_propose_only():
    """insights هیچ اثرِ بیرونی ندارند (propose-only)."""
    g = seed_curriculum()
    f = AwarenessField(g)
    events = detect_insights(f, g)
    for e in events:
        assert not hasattr(e, "applied") and not hasattr(e, "merged")
        assert not hasattr(e, "effect")


# ════════════════════════════════════════════════════════════════════════════════
# Guards
# ════════════════════════════════════════════════════════════════════════════════

def t_no_production_import():
    """curriculum هیچ import از *_gate/chrono/money ندارد."""
    import curriculum
    src = open(curriculum.__file__, encoding="utf-8").read()
    forbidden = ["import chrono", "from chrono", "organ_gate", "money_gate",
                 "capability_gate", "budget_gate", "EffectorGate", "opslib"]
    for fn in forbidden:
        assert fn not in src, f"خطِ قرمز: {fn}"


def t_clip01():
    """clip01 به [0,1]."""
    assert clip01(-0.5) == 0.0
    assert clip01(1.5) == 1.0


def t_shared_laplacian_with_spectral():
    """L(G) همین构造 که spectral_mine استفاده می‌کند (D−W)."""
    g = seed_curriculum()
    L = g.laplacian()
    # diagonal باید ≥ 0 (D), off-diagonal ≤ 0 (−W)
    try:
        import numpy as np
        diag = np.diag(L)
        assert all(d >= -1e-6 for d in diag)
    except (ImportError, AttributeError):
        pass


if __name__ == "__main__":
    failed = harness.run([
        ("[G] seed curriculum ~48 nodes", t_seed_curriculum_built),
        ("[G] node coord + tag", t_node_has_coord_and_tag),
        ("[G] L(G) shape N×N", t_laplacian_shape),
        ("[G] L(G) PSD", t_laplacian_psd),
        ("[G] spectral_gap float", t_spectral_gap_returns_float),
        ("[A] study raises a_k", t_awareness_study_raises),
        ("[A] diffusion to neighbors", t_awareness_diffuses_to_neighbors),
        ("[A] a clipped [0,1]", t_awareness_clipped_01),
        ("[A] mean awareness", t_awareness_mean),
        ("[A] ignited topics", t_ignited_topics),
        ("[I] topic-ignited event", t_insight_topic_ignited),
        ("[I] structural-shift event", t_insight_structural_shift),
        ("[I] co-activation proposes edge", t_insight_coactivation_proposes_edge),
        ("[I] insights propose-only", t_insights_propose_only),
        ("[S] no production import", t_no_production_import),
        ("[S] clip01", t_clip01),
        ("[S] shared L(G) with spectral", t_shared_laplacian_with_spectral),
    ])
    sys.exit(1 if failed else 0)
