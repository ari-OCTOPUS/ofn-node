"""Analytical / statistical representations.

Degree distribution, adjacency matrix (community-ordered), treemap,
folder↔folder heatmap, and a radar comparing the top hubs. These are cheap and
do not subsample — they summarise the whole graph.
"""

from __future__ import annotations

import math
from collections import defaultdict

import networkx as nx
import numpy as np
import plotly.graph_objects as go

from .data import GraphView

_INK = "#52514e"
_BG = "white"


# ════════════════════════════════════════════════════════════════════════════
# 11. degree distribution (log-log)
# ════════════════════════════════════════════════════════════════════════════
def render_degree_dist(view: GraphView, **_) -> go.Figure:
    degs = list(view.degree.values())
    counts = defaultdict(int)
    for d in degs:
        counts[d] += 1
    ks = sorted(counts)
    xs = [k for k in ks if k > 0]
    ys = [counts[k] for k in xs]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers",
        marker=dict(size=9, color="#2a78d6", line=dict(width=0.5, color="white")),
        hovertemplate="degree=%{x}<br>notes=%{y}<extra></extra>", showlegend=False))
    # power-law reference line (eyeballed slope of -2)
    if xs:
        k0 = xs[0]; y0 = ys[0]
        ref_x = np.array(xs)
        ref_y = y0 * (ref_x / k0) ** (-2)
        fig.add_trace(go.Scatter(x=ref_x, y=ref_y, mode="lines",
                                 line=dict(color="#d03b3b", dash="dash", width=1.5),
                                 name="مرجعِ توانِ -۲", hoverinfo="skip"))
    fig.update_layout(
        title=dict(text="<b>توزیعِ درجه (Power-law)</b>", font=dict(size=15, color=_INK)),
        xaxis=dict(title="درجه (log)", type="log", gridcolor="#eee"),
        yaxis=dict(title="تعدادِ نوت (log)", type="log", gridcolor="#eee"),
        paper_bgcolor=_BG, plot_bgcolor=_BG, height=560, margin=dict(l=60, r=20, t=54, b=50),
        font=dict(color=_INK))
    return fig


# ════════════════════════════════════════════════════════════════════════════
# 12. adjacency matrix (community-ordered)
# ════════════════════════════════════════════════════════════════════════════
def render_adjacency(view: GraphView, *, max_nodes=1500, **_) -> go.Figure:
    nodes = view.sample_nodes if view.n_nodes > max_nodes else view.nodes
    edges = view.sample_edges if view.n_nodes > max_nodes else view.edges
    capped = view.n_nodes > max_nodes
    n = len(nodes)
    # order by community so the matrix shows block-diagonal structure
    comm = view.community_of
    order = sorted(range(n), key=lambda i: (comm.get(nodes[i], 0), view.degree.get(nodes[i], 0)))
    idx = {old: new for new, old in enumerate(order)}
    M = np.zeros((n, n), dtype=np.uint8)
    for a, b in edges:
        if a in idx and b in idx:
            M[idx[a], idx[b]] = 1; M[idx[b], idx[a]] = 1
    fig = go.Figure(go.Heatmap(
        z=M, colorscale=[[0, "#f7f9fc"], [1, "#2a78d6"]],
        showscale=False, hovertemplate="(%{x}, %{y}) → %{z}<extra></extra>"))
    note = f"  (نمونهٔ {n:,} از {view.n_nodes:,})" if capped else ""
    fig.update_layout(
        title=dict(text=f"<b>ماتریسِ مجاورت (مرتب بر اساس خوشه)</b>{note}", font=dict(size=15, color=_INK)),
        paper_bgcolor=_BG, plot_bgcolor=_BG, height=640, margin=dict(l=20, r=20, t=54, b=20),
        xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        font=dict(color=_INK))
    return fig


# ════════════════════════════════════════════════════════════════════════════
# 13. treemap (folder sizes)
# ════════════════════════════════════════════════════════════════════════════
def render_treemap(view: GraphView, **_) -> go.Figure:
    folders = view.summary.get("notes_per_top_folder", {})
    items = sorted(folders.items(), key=lambda kv: -kv[1])[:30]
    labels = [f"{f}<br>({c})" for f, c in items]
    parents = ["vault"] * len(items)
    vals = [c for _, c in items]
    fig = go.Figure(go.Treemap(
        labels=["vault"] + labels,
        parents=[""] + parents,
        values=[sum(vals)] + vals,
        marker=dict(colors=["#2c3e50"] + [view.folder_color.get(f, "#7f8c8d") for f, _ in items]),
        textinfo="label", hovertemplate="<b>%{label}</b><br>count=%{value}<extra></extra>",
        branchvalues="total"))
    fig.update_layout(
        title=dict(text="<b>Treemap خوشه/فولدرها</b>", font=dict(size=15, color=_INK)),
        paper_bgcolor=_BG, height=620, margin=dict(l=10, r=10, t=54, b=10), font=dict(color=_INK))
    return fig


# ════════════════════════════════════════════════════════════════════════════
# 14. folder ↔ folder heatmap (edges between folders)
# ════════════════════════════════════════════════════════════════════════════
def render_folder_heat(view: GraphView, **_) -> go.Figure:
    folders = list(view.summary.get("notes_per_top_folder", {}).keys())[:25]
    pos = {f: i for i, f in enumerate(folders)}
    M = np.zeros((len(folders), len(folders)), dtype=int)
    for a, b in view.edges:
        fa = view.folder_of.get(view.nodes[a])
        fb = view.folder_of.get(view.nodes[b])
        if fa in pos and fb in pos:
            M[pos[fa], pos[fb]] += 1
            if fa != fb:
                M[pos[fb], pos[fa]] += 1
    fig = go.Figure(go.Heatmap(
        z=M, x=folders, y=folders, colorscale="Blues",
        hovertemplate="%{y} → %{x}<br>یال: %{z}<extra></extra>", colorbar=dict(title="یال")))
    fig.update_layout(
        title=dict(text="<b>حرارتیِ فولدر ↔ فولدر (یال‌های بین‌فولدری)</b>", font=dict(size=15, color=_INK)),
        paper_bgcolor=_BG, plot_bgcolor=_BG, height=680, margin=dict(l=20, r=20, t=54, b=160),
        xaxis=dict(tickangle=-45, automargin=True), yaxis=dict(autorange="reversed"),
        font=dict(color=_INK, size=9))
    return fig


# ════════════════════════════════════════════════════════════════════════════
# 15. radar comparing top hubs
# ════════════════════════════════════════════════════════════════════════════
def render_radar(view: GraphView, *, top_n=5, **_) -> go.Figure:
    hubs = view.hub_nodes[:top_n]
    if not hubs:
        hubs = sorted(view.degree, key=lambda n: -view.degree[n])[:top_n]
    # metrics per hub: degree (norm), reciprocal of depth, folder membership breadth
    metrics = ["درجه", "مرکزیتِ میان‌گرهی", "نزدیکی", "تعدادِ همسایهٔ یکتا"]
    G = view.G
    idx = {n: i for i, n in enumerate(view.nodes)}
    # precompute centralities on the full graph (cheap-ish for 4.6k nodes)
    try:
        betw = nx.betweenness_centrality(G, k=min(500, G.number_of_nodes()), normalized=True)
    except Exception:
        betw = {i: 0 for i in G}
    closeness = nx.closeness_centrality(G)
    maxdeg = max(view.degree.values()) or 1
    maxbetw = max(betw.values()) or 1
    maxclose = max(closeness.values()) or 1
    fig = go.Figure()
    for h in hubs:
        i = idx.get(h)
        if i is None:
            continue
        vals = [
            view.degree.get(h, 0) / maxdeg,
            betw.get(i, 0) / maxbetw,
            closeness.get(i, 0) / maxclose,
            len(set(G.neighbors(i))) / maxdeg if maxdeg else 0,
        ]
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=metrics + [metrics[0]], fill="toself", name=view.label_for(h),
            opacity=0.7, line=dict(width=1.5)))
    fig.update_layout(
        title=dict(text="<b>رادارِ مقایسهٔ hubهای برتر</b>", font=dict(size=15, color=_INK)),
        polar=dict(radialaxis=dict(visible=True, range=[0, 1], gridcolor="#eee")),
        paper_bgcolor=_BG, height=600, margin=dict(l=40, r=40, t=54, b=30),
        legend=dict(orientation="h", y=-0.05), font=dict(color=_INK))
    return fig
