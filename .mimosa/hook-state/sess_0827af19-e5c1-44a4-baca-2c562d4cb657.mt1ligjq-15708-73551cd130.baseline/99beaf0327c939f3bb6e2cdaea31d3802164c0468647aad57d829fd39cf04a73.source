"""Topological representations — the graph drawn as a network.

All figures are plotly ``go.Figure`` (matching ``4d_system/ui/visuals.py``),
rendered by the dashboard with ``st.plotly_chart``. Each takes the shared
:class:`GraphView` and an options dict (max_nodes, show_labels, …).
"""

from __future__ import annotations

import math
from typing import Any

import networkx as nx
import numpy as np
import plotly.graph_objects as go

from .data import GraphView

_BG = "white"
_PAPER = "white"
_INK = "#52514e"
_MUTED = "#898781"
_GRID = "#e1e0d9"


def _base_layout(title: str, *, height=620, xax=False, yax=False, zax=False) -> dict:
    lo: dict[str, Any] = dict(
        title=dict(text=f"<b>{title}</b>", font=dict(size=15, color=_INK)),
        paper_bgcolor=_PAPER, plot_bgcolor=_BG, height=height, margin=dict(l=20, r=20, t=54, b=20),
        font=dict(color=_INK),
    )
    if xax:
        lo["xaxis"] = dict(visible=False, showgrid=False, zeroline=False)
    if yax:
        lo["yaxis"] = dict(visible=False, showgrid=False, zeroline=False, scaleanchor="x", scaleratio=1)
    if zax:
        lo["scene"] = dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
                           aspectmode="data")
    return lo


def _edge_traces_2d(pos, edges, color="#cfcfca", width=0.6):
    xs, ys = [], []
    for a, b in edges:
        if a in pos and b in pos:
            xs += [pos[a][0], pos[b][0], None]
            ys += [pos[a][1], pos[b][1], None]
    return go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width),
                      hoverinfo="skip", showlegend=False)


def _node_trace_2d(view, nodes, pos, *, sized=True, labeled=True, max_labels=40):
    xs = [pos[i][0] for i in range(len(nodes))]
    ys = [pos[i][1] for i in range(len(nodes))]
    degs = [view.degree.get(nodes[i], 0) for i in range(len(nodes))]
    colors = [view.color_for(nodes[i]) for i in range(len(nodes))]
    labels = [view.label_for(nodes[i]) for i in range(len(nodes))]
    sizes = [max(6, min(34, 6 + math.sqrt(d) * 3)) for d in degs] if sized else [10] * len(nodes)
    text = labels if labeled else [""] * len(nodes)
    return go.Scatter(
        x=xs, y=ys, mode="markers+text" if labeled else "markers",
        marker=dict(size=sizes, color=colors, line=dict(width=0.5, color="white"), opacity=0.92),
        text=text, textposition="top center", textfont=dict(size=8, color=_INK),
        hovertemplate="<b>%{text}</b><br>degree=%{customdata}<extra></extra>",
        customdata=degs, showlegend=False,
    )


# ════════════════════════════════════════════════════════════════════════════
# 1. force 2D
# ════════════════════════════════════════════════════════════════════════════
def render_force2d(view: GraphView, *, max_nodes=1500, show_labels=True, **_) -> go.Figure:
    nodes = view.sample_nodes if view.n_nodes > max_nodes else view.nodes
    edges = view.sample_edges if view.n_nodes > max_nodes else view.edges
    capped = view.n_nodes > max_nodes
    G = nx.Graph()
    G.add_nodes_from(range(len(nodes)))
    G.add_edges_from(edges)
    # seed for reproducibility; fewer iterations on big graphs to stay responsive
    iters = 60 if len(nodes) <= 700 else 35
    pos = nx.spring_layout(G, dim=2, seed=7, iterations=iters,
                           k=1.5 / max(1, math.sqrt(len(nodes))))
    fig = go.Figure()
    fig.add_trace(_edge_traces_2d(pos, edges))
    fig.add_trace(_node_trace_2d(view, nodes, pos, labeled=show_labels and len(nodes) <= 400))
    fig.update_layout(**_base_layout(
        "گرافِ فشاری ۲بعدی" + (f"  (نمونهٔ {len(nodes):,} از {view.n_nodes:,})" if capped else ""),
        yax=True, xax=True))
    fig.update_layout(legend=dict(orientation="h", y=-0.02))
    return fig


# ════════════════════════════════════════════════════════════════════════════
# 2. force 3D
# ════════════════════════════════════════════════════════════════════════════
def render_force3d(view: GraphView, *, max_nodes=1500, show_labels=False, **_) -> go.Figure:
    nodes = view.sample_nodes if view.n_nodes > max_nodes else view.nodes
    edges = view.sample_edges if view.n_nodes > max_nodes else view.edges
    capped = view.n_nodes > max_nodes
    G = nx.Graph(); G.add_nodes_from(range(len(nodes))); G.add_edges_from(edges)
    iters = 50 if len(nodes) <= 700 else 30
    pos = nx.spring_layout(G, dim=3, seed=11, iterations=iters,
                           k=1.5 / max(1, math.sqrt(len(nodes))))
    xs = [pos[i][0] for i in range(len(nodes))]
    ys = [pos[i][1] for i in range(len(nodes))]
    zs = [pos[i][2] for i in range(len(nodes))]
    degs = [view.degree.get(nodes[i], 0) for i in range(len(nodes))]
    colors = [view.color_for(nodes[i]) for i in range(len(nodes))]
    labels = [view.label_for(nodes[i]) for i in range(len(nodes))]

    ex, ey, ez = [], [], []
    for a, b in edges:
        ex += [pos[a][0], pos[b][0], None]
        ey += [pos[a][1], pos[b][1], None]
        ez += [pos[a][2], pos[b][2], None]

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=ex, y=ey, z=ez, mode="lines",
                               line=dict(color="#cfcfca", width=1), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter3d(
        x=xs, y=ys, z=zs, mode="markers",
        marker=dict(size=[max(4, min(16, math.sqrt(d) * 2.2)) for d in degs],
                    color=colors, line=dict(width=0.4, color="white"), opacity=0.9),
        text=labels, hovertemplate="<b>%{text}</b><br>degree=%{customdata}<extra></extra>",
        customdata=degs, showlegend=False))
    fig.update_layout(**_base_layout(
        "گرافِ فشاری ۳بعدی" + (f"  (نمونهٔ {len(nodes):,} از {view.n_nodes:,})" if capped else ""),
        zax=True))
    return fig


# ════════════════════════════════════════════════════════════════════════════
# 3. circular
# ════════════════════════════════════════════════════════════════════════════
def render_circular(view: GraphView, *, max_nodes=1200, **_) -> go.Figure:
    nodes = view.sample_nodes if view.n_nodes > max_nodes else view.nodes
    edges = view.sample_edges if view.n_nodes > max_nodes else view.edges
    capped = view.n_nodes > max_nodes
    n = len(nodes)
    pos = {i: (math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)}
    fig = go.Figure()
    fig.add_trace(_edge_traces_2d(pos, edges, color="#d8d8d3", width=0.4))
    fig.add_trace(_node_trace_2d(view, nodes, pos, sized=True, labeled=False))
    fig.update_layout(**_base_layout(
        "چیدمانِ حلقوی" + (f"  (نمونهٔ {n:,} از {view.n_nodes:,})" if capped else ""),
        yax=True, xax=True))
    return fig


# ════════════════════════════════════════════════════════════════════════════
# 4. hierarchy (folder tree)
# ════════════════════════════════════════════════════════════════════════════
def render_hierarchy(view: GraphView, *, max_folders=45, **_) -> go.Figure:
    """Folder → subfolder tree, sized by note count."""
    from collections import defaultdict
    tree: dict[str, dict] = defaultdict(lambda: {"count": 0, "children": defaultdict(int)})
    for node, folder in view.folder_of.items():
        parts = node.split("/")
        cur = tree
        for depth, part in enumerate(parts):
            if depth == 0:
                tree[part]["count"] += 1
            else:
                # collapse deeper into top-folder-only for readability
                tree[parts[0]]["count"] += 0
    # build sunburst-like hierarchy edges
    folders = list(view.summary.get("notes_per_top_folder", {}).items())[:max_folders]
    folders.sort(key=lambda kv: -kv[1])
    # layout top folders on an arc, root in center
    root = (0.0, 0.0)
    n = len(folders)
    max_c = max((c for _, c in folders), default=1)
    xs, ys, sizes, colors, labels = [0.0], [0.0], [28], ["#2c3e50"], ["vault"]
    for i, (f, c) in enumerate(folders):
        ang = 2 * math.pi * i / max(1, n)
        r = 1.0
        xs.append(math.cos(ang) * r); ys.append(math.sin(ang) * r)
        sizes.append(max(8, 6 + 26 * math.sqrt(c / max_c)))
        colors.append(view.folder_color.get(f, "#7f8c8d"))
        labels.append(f"{f}\n({c})")
    # spokes
    exs, eys = [], []
    for i in range(1, len(xs)):
        exs += [0.0, xs[i], None]; eys += [0.0, ys[i], None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=exs, y=eys, mode="lines", line=dict(color="#bdbdb7", width=1.4),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text",
                             marker=dict(size=sizes, color=colors, line=dict(width=1, color="white")),
                             text=labels, textposition="middle center", textfont=dict(size=8, color="white"),
                             hovertemplate="%{text}<extra></extra>", showlegend=False))
    fig.update_layout(**_base_layout("درختِ سلسله‌مراتبیِ فولدرها", yax=True, xax=True))
    return fig


# ════════════════════════════════════════════════════════════════════════════
# 5. arc diagram
# ════════════════════════════════════════════════════════════════════════════
def render_arc(view: GraphView, *, max_nodes=900, **_) -> go.Figure:
    nodes = view.sample_nodes if view.n_nodes > max_nodes else view.nodes
    edges = view.sample_edges if view.n_nodes > max_nodes else view.edges
    capped = view.n_nodes > max_nodes
    n = len(nodes)
    xs = list(range(n))
    degs = [view.degree.get(nodes[i], 0) for i in range(n)]
    colors = [view.color_for(nodes[i]) for i in range(n)]
    # arcs: semicircle above the axis between a and b (a<b)
    arc_x, arc_y = [], []
    rng = range(0, n, max(1, n // 200))  # thin dense arcs for performance/readability
    shown = set()
    for a, b in edges:
        if a >= b or (a, b) in shown:
            continue
        shown.add((a, b))
        mid = (a + b) / 2
        half = (b - a) / 2
        t = np.linspace(0, math.pi, 24)
        arc_x += list(xs[a] + half - half * np.cos(t)) + [None]
        arc_y += list(half * np.sin(t)) + [None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=arc_x, y=arc_y, mode="lines",
                             line=dict(color="#9bb3d6", width=0.5), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=xs, y=[0] * n, mode="markers",
        marker=dict(size=[max(3, min(16, math.sqrt(d) * 2)) for d in degs], color=colors,
                    line=dict(width=0.4, color="white")),
        hovertext=[view.label_for(nodes[i]) for i in range(n)],
        hovertemplate="<b>%{hovertext}</b><br>degree=%{customdata}<extra></extra>",
        customdata=degs, showlegend=False))
    fig.update_layout(**_base_layout(
        "نمودارِ قوسی" + (f"  (نمونهٔ {n:,} از {view.n_nodes:,})" if capped else ""),
        yax=True, xax=True))
    fig.update_yaxes(range=[-1, n * 0.27])
    return fig


# ════════════════════════════════════════════════════════════════════════════
# 6. bipartite folder ↔ node (aggregated: folder ↔ folder via shared notes is
#    noisy; show folder node-count as a clean 2-layer graph instead)
# ════════════════════════════════════════════════════════════════════════════
def render_bipartite(view: GraphView, *, max_nodes=900, **_) -> go.Figure:
    """Two rows: top = folders (sized by note count), bottom = a sample of their
    notes, edges = membership. Shows how notes distribute across folders."""
    from collections import defaultdict
    folder_notes: dict[str, list[str]] = defaultdict(list)
    for node, folder in view.folder_of.items():
        folder_notes[folder].append(node)
    folders = sorted(folder_notes, key=lambda f: -len(folder_notes[f]))[:18]
    # sample a few notes per folder for the bottom layer
    sample: list[tuple[str, str]] = []  # (folder, node)
    per = max(1, min(12, max_nodes // max(1, len(folders))))
    for f in folders:
        for nd in folder_notes[f][:per]:
            sample.append((f, nd))
    fy = {f: 1.0 for f in folders}
    fx = {f: i for i, f in enumerate(folders)}
    ny = {nd: 0.0 for _, nd in sample}
    nxs = {nd: i for i, (_, nd) in enumerate(sample)}
    exs, eys = [], []
    for f, nd in sample:
        exs += [fx[f], nxs[nd], None]; eys += [1.0, 0.0, None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=exs, y=eys, mode="lines", line=dict(color="#cfdaee", width=0.5),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=[fx[f] for f in folders], y=[1.0] * len(folders), mode="markers+text",
        marker=dict(size=[max(10, min(40, math.sqrt(len(folder_notes[f])) * 2.5)) for f in folders],
                    color=[view.folder_color.get(f, "#7f8c8d") for f in folders],
                    line=dict(width=1, color="white")),
        text=folders, textposition="top center", textfont=dict(size=9, color=_INK),
        hovertemplate="%{text}: %{customdata} notes<extra></extra>",
        customdata=[len(folder_notes[f]) for f in folders], showlegend=False, name="folders"))
    fig.add_trace(go.Scatter(
        x=list(nxs.values()), y=[0.0] * len(nxs), mode="markers",
        marker=dict(size=5, color="#9aa0a6"),
        hovertext=[view.label_for(nd) for nd in nxs],
        hovertemplate="<b>%{hovertext}</b><extra></extra>", showlegend=False, name="notes"))
    fig.update_layout(**_base_layout("نمودارِ دوجهتهٔ فولدر ↔ نوت", yax=True, xax=True, height=560))
    return fig
