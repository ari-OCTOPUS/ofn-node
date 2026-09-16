#!/usr/bin/env python3
"""curriculum.py — SM-B0: School Memory numeric core (offline، $0).

SCHOOL-MEMORY-SPEC §۱۰·SM-B0: curriculum graph loader + L(G) + awareness
diffusion + insight-events. هندسه = همان L(G) که Time-Architecture و
Doctor's spectral_mine استفاده می‌کنند (da/dt = −L(G)·a + input).

§۸ safety: awareness = field metric، نه sentience claim. هر node epistemic-tagged.
No PII. bounded ~200 nodes. propose-only insight-events.
هیچ import از *_gate/chrono/money. $0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


# ─── Topic Node ────────────────────────────────────────────────────────────────
@dataclass
class TopicNode:
    """یک نودِ curriculum. id · title · embedding x∈R^6 · epistemic_tag."""
    id: str                      # e.g. "A01", "B15", "F33"
    layer: str                   # A|B|C|D|E|F
    title: str
    short_desc: str = ""
    coord: list[float] = field(default_factory=lambda: [0.0] * 6)  # x∈R^6
    epistemic_tag: str = "Established"   # Established|Strong|Testable|Speculative
    valid_until: str = ""
    sources: list[str] = field(default_factory=list)


@dataclass
class CurriculumEdge:
    """یالِ جهت‌دار: v_i → v_j با label و weight."""
    src: str
    dst: str
    label: str = "depends-on"   # depends-on|influences|similar-to|part-of
    weight: float = 0.5


# ─── Curriculum Graph ──────────────────────────────────────────────────────────
class CurriculumGraph:
    """G = (V, E). ~200 nodes در 6 لایه. L(G) = D − W.
    awareness diffusion: ȧ = −L(G)·a + input(t).
    shared machinery با spectral_mine (همان L(G))."""

    def __init__(self):
        self.nodes: dict[str, TopicNode] = {}
        self.edges: list[CurriculumEdge] = []

    @property
    def n_nodes(self) -> int:
        return len(self.nodes)

    @property
    def n_edges(self) -> int:
        return len(self.edges)

    def add_node(self, node: TopicNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: CurriculumEdge) -> None:
        if edge.src in self.nodes and edge.dst in self.nodes:
            self.edges.append(edge)

    def node_index(self) -> dict[str, int]:
        """id → index برای ماتریس."""
        return {nid: i for i, nid in enumerate(sorted(self.nodes.keys()))}

    def laplacian(self) -> "list | object":
        """L(G) = D − W. خروجی: matrix (numpy یا list-of-list).
        همانی که spectral_mine و awareness diffusion استفاده می‌کنند."""
        n = self.n_nodes
        if n == 0:
            return [] if not _HAS_NUMPY else np.zeros((0, 0))
        idx = self.node_index()
        if _HAS_NUMPY:
            W = np.zeros((n, n))
            D = np.zeros((n, n))
            for e in self.edges:
                i, j = idx[e.src], idx[e.dst]
                W[i][j] = e.weight
                W[j][i] = e.weight   # symmetric
                D[i][i] += e.weight
                D[j][j] += e.weight
            return D - W
        # pure-python
        W = [[0.0] * n for _ in range(n)]
        D = [[0.0] * n for _ in range(n)]
        for e in self.edges:
            i, j = idx[e.src], idx[e.dst]
            W[i][j] = e.weight
            W[j][i] = e.weight
            D[i][i] += e.weight
            D[j][j] += e.weight
        return [[D[i][i] - W[i][j] for j in range(n)] for i in range(n)]

    def spectral_gap(self) -> float:
        """شکافِ طیفی λ₂ − λ₁. shared با Doctor spectral_mine."""
        L = self.laplacian()
        if _HAS_NUMPY and hasattr(L, "shape"):
            try:
                eigvals = sorted(np.linalg.eigvalsh(L))
                return float(eigvals[1] - eigvals[0]) if len(eigvals) > 1 else 0.0
            except Exception:  # noqa: BLE001
                return 0.0
        # pure: Gershgorin تقریب
        return 0.0


# ─── Awareness Field ───────────────────────────────────────────────────────────
def clip01(v: float) -> float:
    if v != v:
        return 0.0
    return max(0.0, min(1.0, float(v)))


class AwarenessField:
    """a(t) ∈ [0,1]^N. diffusion: ȧ = −L·a + input.
    مطالعهٔ v_k → a_k بالا → به همسایگان پخش می‌شود."""

    def __init__(self, graph: CurriculumGraph, dt: float = 0.1):
        self.graph = graph
        self.dt = dt
        self.n = graph.n_nodes
        self.idx = graph.node_index()
        self.a = [0.0] * self.n
        self._L = graph.laplacian()

    def study(self, topic_id: str, intensity: float = 0.5) -> None:
        """مطالعهٔ topic → a_k += intensity."""
        i = self.idx.get(topic_id)
        if i is not None and i < self.n:
            self.a[i] = clip01(self.a[i] + intensity)

    def observe(self, topic_id: str, intensity: float = 0.3) -> None:
        """مشاهده (lighter than study)."""
        self.study(topic_id, intensity)

    def tick(self, inputs: dict[str, float] | None = None) -> list[float]:
        """یک گامِ diffusion: a ← clip(a + dt·(−L·a + input), 0, 1).
        inputs = {topic_id: signal}."""
        if inputs:
            for tid, sig in inputs.items():
                i = self.idx.get(tid)
                if i is not None:
                    self.a[i] += self.dt * sig
        if _HAS_NUMPY and hasattr(self._L, "shape"):
            La = self._L @ np.asarray(self.a)
            self.a = [clip01(self.a[i] - self.dt * float(La[i]))
                      for i in range(self.n)]
        else:
            # pure: a_i ← a_i - dt * Σ_j L_ij * a_j
            L = self._L
            new_a = list(self.a)
            for i in range(self.n):
                diff = sum(L[i][j] * self.a[j] for j in range(self.n)) if i < len(L) else 0.0
                new_a[i] = clip01(self.a[i] - self.dt * diff)
            self.a = new_a
        return list(self.a)

    def awareness_of(self, topic_id: str) -> float:
        i = self.idx.get(topic_id)
        return self.a[i] if i is not None else 0.0

    def mean_awareness(self) -> float:
        return sum(self.a) / max(self.n, 1)

    def ignited_topics(self, theta_high: float = 0.7) -> list[str]:
        """topicهایی که a_i از θ_high گذشته."""
        rev = {i: tid for tid, i in self.idx.items()}
        return [rev[i] for i in range(self.n) if self.a[i] >= theta_high]


# ─── Insight Events (propose-only) ─────────────────────────────────────────────
@dataclass
class InsightEvent:
    """یک insight از awareness dynamics. propose-only، هرگز effector."""
    kind: str               # topic-ignited | structural-shift | co-activation
    topic_id: str | None
    detail: str
    propose_new_edge: bool = False   # اگر True → human-append لازم
    timestamp: int = 0


def detect_insights(field: AwarenessField, graph: CurriculumGraph,
                    prev_gap: float | None = None,
                    theta_high: float = 0.7,
                    co_activation_threshold: float = 0.6) -> list[InsightEvent]:
    """insight detection از awareness field. propose-only.
    (i) topic ignited: a_i ≥ θ_high
    (ii) structural shift: Δ(spectral gap) بزرگ
    (iii) co-activation: چند topic همزمان بالا → propose new edge (human-gated)"""
    events = []
    # (i) ignited
    for tid in field.ignited_topics(theta_high):
        events.append(InsightEvent(kind="topic-ignited", topic_id=tid,
                                   detail=f"awareness of {tid} crossed {theta_high}"))
    # (ii) structural shift
    gap = graph.spectral_gap()
    if prev_gap is not None and abs(gap - prev_gap) > 0.1:
        events.append(InsightEvent(kind="structural-shift", topic_id=None,
                                   detail=f"spectral gap shifted {prev_gap:.3f}→{gap:.3f}"))
    # (iii) co-activation → propose new edge
    high = [tid for tid in field.ignited_topics(co_activation_threshold)]
    if len(high) >= 2:
        events.append(InsightEvent(
            kind="co-activation", topic_id=None,
            detail=f"co-activated: {high[:4]}",
            propose_new_edge=True))   # human-append لازم
    return events


# ─── Seed Curriculum (representative ~8/layer) ─────────────────────────────────
def seed_curriculum() -> CurriculumGraph:
    """ساختِ curriculum با seed topics (~48 nodes، 6 layers).
    کاملِ 200-row table = verdict مالک (§۹)."""
    g = CurriculumGraph()
    seeds = {
        "A": [("attention", [1, 0.3, 0.1, 0.2, 0.4, 0.8]),
              ("working-memory", [1, 0.4, 0.1, 0.2, 0.3, 0.7]),
              ("habit-loop", [0.9, 0.3, 0.2, 0.3, 0.4, 0.6]),
              ("emotion-regulation", [1, 0.3, 0.1, 0.4, 0.2, 0.7]),
              ("identity", [0.8, 0.5, 0.3, 0.6, 0.3, 0.9]),
              ("self-narrative", [0.8, 0.5, 0.4, 0.7, 0.3, 0.8]),
              ("motivation", [0.9, 0.4, 0.2, 0.4, 0.3, 0.6]),
              ("perception-bias", [1, 0.3, 0.1, 0.3, 0.2, 0.7])],
        "B": [("trust", [0.4, 0.8, 0.3, 0.5, 0.3, 0.5]),
              ("reciprocity", [0.4, 0.9, 0.3, 0.5, 0.2, 0.4]),
              ("small-team-dynamics", [0.4, 0.9, 0.3, 0.4, 0.3, 0.5]),
              ("family-systems", [0.5, 0.8, 0.4, 0.6, 0.2, 0.5]),
              ("homophily", [0.4, 0.9, 0.3, 0.4, 0.3, 0.4]),
              ("social-contagion", [0.4, 0.8, 0.3, 0.5, 0.4, 0.5]),
              ("status", [0.3, 0.8, 0.4, 0.6, 0.3, 0.5]),
              ("cooperation", [0.4, 0.9, 0.4, 0.5, 0.3, 0.5])],
        "C": [("law", [0.2, 0.4, 0.9, 0.6, 0.3, 0.4]),
              ("markets", [0.2, 0.5, 0.9, 0.4, 0.4, 0.3]),
              ("inequality", [0.3, 0.5, 0.9, 0.5, 0.3, 0.5]),
              ("bureaucracy", [0.2, 0.4, 0.9, 0.5, 0.4, 0.3]),
              ("power", [0.3, 0.5, 0.9, 0.6, 0.3, 0.5]),
              ("collective-action", [0.3, 0.6, 0.9, 0.5, 0.3, 0.4]),
              ("institutions", [0.2, 0.4, 0.9, 0.6, 0.4, 0.4]),
              ("governance", [0.2, 0.4, 0.9, 0.6, 0.4, 0.4])],
        "D": [("narrative", [0.5, 0.5, 0.4, 0.9, 0.4, 0.7]),
              ("myth-religion", [0.5, 0.5, 0.6, 0.9, 0.2, 0.8]),
              ("art", [0.6, 0.4, 0.4, 0.9, 0.3, 0.7]),
              ("media-ecology", [0.4, 0.5, 0.4, 0.8, 0.7, 0.5]),
              ("values", [0.5, 0.5, 0.5, 0.9, 0.3, 0.7]),
              ("ritual", [0.6, 0.6, 0.6, 0.9, 0.2, 0.6]),
              ("meaning-making", [0.6, 0.5, 0.5, 0.9, 0.3, 0.9]),
              ("taboo", [0.5, 0.6, 0.5, 0.9, 0.2, 0.6])],
        "E": [("platforms", [0.3, 0.4, 0.5, 0.5, 0.9, 0.5]),
              ("recommender-loops", [0.5, 0.5, 0.3, 0.5, 0.9, 0.6]),
              ("ai-agency", [0.4, 0.4, 0.5, 0.5, 0.9, 0.7]),
              ("attention-economy", [0.6, 0.4, 0.3, 0.5, 0.9, 0.6]),
              ("privacy", [0.5, 0.4, 0.5, 0.4, 0.9, 0.4]),
              ("addiction", [0.7, 0.4, 0.3, 0.4, 0.9, 0.6]),
              ("digital-identity", [0.6, 0.5, 0.4, 0.6, 0.9, 0.7]),
              ("automation", [0.3, 0.3, 0.6, 0.4, 0.9, 0.4])],
        "F": [("historical-cycles", [0.2, 0.4, 0.9, 0.6, 0.4, 0.5]),
              ("demographic-transition", [0.2, 0.3, 0.9, 0.4, 0.4, 0.3]),
              ("climate", [0.1, 0.3, 0.9, 0.4, 0.5, 0.4]),
              ("pandemics", [0.2, 0.4, 0.9, 0.4, 0.4, 0.4]),
              ("technological-phase-shifts", [0.2, 0.3, 0.9, 0.5, 0.8, 0.5]),
              ("existential-risk", [0.2, 0.3, 0.9, 0.5, 0.6, 0.6]),
              ("long-termism", [0.2, 0.3, 0.8, 0.6, 0.5, 0.7]),
              ("civilizational-resilience", [0.2, 0.4, 0.9, 0.6, 0.5, 0.6])],
    }
    # add nodes
    for layer, topics in seeds.items():
        for i, (title, coord) in enumerate(topics):
            nid = f"{layer}{i+1:02d}"
            g.add_node(TopicNode(id=nid, layer=layer, title=title, coord=coord,
                                 epistemic_tag="Testable"))
    # add edges: within-layer chain + some cross-layer
    idx = g.node_index()
    for layer in seeds:
        ids = [f"{layer}{i+1:02d}" for i in range(len(seeds[layer]))]
        for k in range(len(ids) - 1):
            g.add_edge(CurriculumEdge(ids[k], ids[k+1], "depends-on", 0.6))
    # cross-layer: A→B, B→C, C→D, D→E, E→F (first node of each)
    for l1, l2 in [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "F")]:
        g.add_edge(CurriculumEdge(f"{l1}01", f"{l2}01", "influences", 0.5))
    return g
