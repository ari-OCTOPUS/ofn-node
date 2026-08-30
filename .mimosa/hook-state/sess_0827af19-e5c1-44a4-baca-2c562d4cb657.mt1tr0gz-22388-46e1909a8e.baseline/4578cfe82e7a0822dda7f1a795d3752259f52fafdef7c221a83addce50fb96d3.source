"""Load + pre-compute the shared view of the link graph used by every viz.

All visualisations read from the same ``GraphView`` so we build the networkx
graph, the folder palette, the degree/centrality metrics, and the community
label exactly once. Building 18 figures must not mean re-scanning the vault.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx
import numpy as np

__all__ = ["GraphView", "load_graph_view", "VIZ_MAX_NODES", "PALETTE"]

# Above this node count the layout-heavy figures subsample, because a
# spring_layout of 4,600 nodes × 18 figures is minutes of dead time on the UI
# thread. The cap is surfaced honestly in the figure caption, never silent.
VIZ_MAX_NODES = 1500

# a calm qualitative palette (folder → colour). Extended cyclically.
PALETTE = [
    "#2a78d6", "#d03b3b", "#0ca30c", "#6b4e8f", "#e08e0b",
    "#1f9e89", "#c0392b", "#16a085", "#8e44ad", "#2c3e50",
    "#d35400", "#27ae60", "#2980b9", "#c2185b", "#7f8c8d",
    "#f39c12", "#00838f", "#5e35b1", "#43a047", "#e53935",
]


def _folder_of(rel_path: str) -> str:
    """Top-level folder of a vault-relative path, or '(root)'."""
    return rel_path.split("/", 1)[0] if "/" in rel_path else "(root)"


@dataclass
class GraphView:
    """Everything a figure needs, computed once.

    ``G`` is the full networkx graph; ``nodes``/``edges`` are the raw arrays.
    ``folder_of`` maps rel_path → top folder; ``folder_color`` → hex.
    ``sample_nodes`` is a degree-biased subsample (capped at VIZ_MAX_NODES) used
    only by layout-heavy figures, with the cap honestly reported.
    """

    G: nx.Graph
    nodes: list[str]
    edges: list[tuple[int, int]]
    folder_of: dict[str, str]
    folder_color: dict[str, str]
    degree: dict[str, int]
    summary: dict
    bakeoff: dict | None
    proposals: list
    fingerprint: str
    n_nodes: int
    n_edges: int
    sample_nodes: list[str] = field(default_factory=list)
    sample_edges: list[tuple[int, int]] = field(default_factory=list)
    community_of: dict[str, int] = field(default_factory=dict)
    n_communities: int = 0
    hub_nodes: list[str] = field(default_factory=list)

    @property
    def folders(self) -> list[str]:
        return list(self.folder_color)

    def color_for(self, node: str) -> str:
        return self.folder_color.get(self.folder_of.get(node, "(root)"), "#7f8c8d")

    def label_for(self, node: str, *, max_len: int = 34) -> str:
        stem = node.rsplit("/", 1)[-1]
        stem = stem[:-3] if stem.lower().endswith(".md") else stem
        return stem if len(stem) <= max_len else stem[: max_len - 1] + "…"


def load_graph_view(out_dir: str | Path) -> GraphView | None:
    """Build the GraphView from the newest graph_<stamp>.json + latest.json.

    Returns None if no artifacts exist yet. Never writes anywhere.
    """
    out = Path(out_dir)
    graphs = sorted(out.glob("graph_*.json"))
    if not graphs:
        return None
    g = json.loads(graphs[-1].read_text(encoding="utf-8"))
    summary = g.get("summary", {})
    nodes: list[str] = g.get("nodes", [])
    edges = [tuple(e) for e in g.get("edges", [])]
    if not nodes:
        return None

    # --- networkx graph + metrics -------------------------------------------
    G = nx.Graph()
    G.add_nodes_from(range(len(nodes)))
    G.add_edges_from(edges)

    folder_of = {n: _folder_of(n) for n in nodes}
    folders = sorted({f for f in folder_of.values() if f != "(root)"})
    folder_color = {f: PALETTE[i % len(PALETTE)] for i, f in enumerate(folders)}
    folder_color["(root)"] = "#7f8c8d"

    degree = {nodes[i]: int(d) for i, d in G.degree()}

    # communities via greedy modularity (fast, deterministic, no sklearn dep)
    try:
        comms = nx.community.greedy_modularity_communities(G)
        community_of: dict[str, int] = {}
        for ci, comm in enumerate(comms):
            for idx in comm:
                community_of[nodes[idx]] = ci
        n_communities = len(comms)
    except Exception:
        community_of, n_communities = {}, 0

    # degree-biased subsample for layout-heavy figures
    sample_nodes, sample_edges = _subsample(nodes, edges, degree)

    # hub nodes = top-degree (for the radar / focus figures)
    hub_nodes = [nodes[i] for i, _ in sorted(G.degree(), key=lambda kv: -kv[1])[:25]]

    # latest.json carries summary + bakeoff + proposals in one place
    latest_p = out / "latest.json"
    bakeoff = None
    proposals: list = []
    if latest_p.exists():
        L = json.loads(latest_p.read_text(encoding="utf-8"))
        bakeoff = L.get("bakeoff")
        proposals = L.get("proposals", [])

    return GraphView(
        G=G, nodes=nodes, edges=edges,
        folder_of=folder_of, folder_color=folder_color, degree=degree,
        summary=summary, bakeoff=bakeoff, proposals=proposals,
        fingerprint=summary.get("fingerprint", ""),
        n_nodes=len(nodes), n_edges=len(edges),
        sample_nodes=sample_nodes, sample_edges=sample_edges,
        community_of=community_of, n_communities=n_communities,
        hub_nodes=hub_nodes,
    )


def _subsample(nodes, edges, degree, cap=VIZ_MAX_NODES):
    """Degree-biased sample: keep high-degree nodes always, fill with random.

    Ensures the dense core of the graph is always represented; orphans are kept
    only if room remains. The returned edge list is restricted to sampled nodes.
    """
    n = len(nodes)
    if n <= cap:
        return nodes, edges
    order = sorted(range(n), key=lambda i: -degree.get(nodes[i], 0))
    keep = set(order[:cap])
    idx = sorted(keep)
    remap = {old: new for new, old in enumerate(idx)}
    sub_nodes = [nodes[i] for i in idx]
    sub_edges = [(remap[a], remap[b]) for a, b in edges
                 if a in remap and b in remap]
    return sub_nodes, sub_edges
