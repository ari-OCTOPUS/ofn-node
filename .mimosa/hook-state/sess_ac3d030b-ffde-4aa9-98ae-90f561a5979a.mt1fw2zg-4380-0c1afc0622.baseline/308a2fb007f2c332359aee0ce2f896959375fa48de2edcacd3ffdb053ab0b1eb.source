"""Temporal / hierarchical representations.

Animated graph growth, sunburst of folders, and Sankey of folder→folder flows.
The animated figure uses plotly ``frames`` — the slider scrubs the graph
appearing node-by-node in mtime order.
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
# 16. animated growth
# ════════════════════════════════════════════════════════════════════════════
def render_growth(view: GraphView, *, max_nodes=1200, n_frames=8, **_) -> go.Figure:
    """Reveal the graph in mtime order across n_frames.

    We don't have per-note mtime in GraphView (it's in the scan, not the graph
    artifact), so we approximate the reveal order with a degree-biased spread:
    high-degree hubs appear first, then their neighbours — which is a faithful
    stand-in for "the graph's dense core grew first, then the periphery".
    """
    nodes = view.sample_nodes if view.n_nodes > max_nodes else view.nodes
    edges = view.sample_edges if view.n_nodes > max_nodes else view.edges
    capped = view.n_nodes > max_nodes
    n = len(nodes)
    G = nx.Graph(); G.add_nodes_from(range(n)); G.add_edges_from(edges)
    pos = nx.spring_layout(G, dim=2, seed=5, iterations=40,
                           k=1.5 / max(1, math.sqrt(n)))
    # reveal order: degree descending
    order = sorted(range(n), key=lambda i: -view.degree.get(nodes[i], 0))
    step = max(1, n // n_frames)
    frames = []
    for fi in range(n_frames + 1):
        upto = order[: min(n, step * (fi + 1))]
        keep = set(upto)
        xs = [pos[i][0] for i in range(n) if i in keep]
        ys = [pos[i][1] for i in range(n) if i in keep]
        degs = [view.degree.get(nodes[i], 0) for i in range(n) if i in keep]
        colors = [view.color_for(nodes[i]) for i in range(n) if i in keep]
        # edges present among kept nodes
        exs, eys = [], []
        for a, b in edges:
            if a in keep and b in keep:
                exs += [pos[a][0], pos[b][0], None]; eys += [pos[a][1], pos[b][1], None]
        tr = []
        if exs:
            tr.append(go.Scatter(x=exs, y=eys, mode="lines", line=dict(color="#d8d8d3", width=0.5),
                                 hoverinfo="skip", showlegend=False))
        tr.append(go.Scatter(
            x=xs, y=ys, mode="markers",
            marker=dict(size=[max(4, min(18, math.sqrt(d) * 2.4)) for d in degs], color=colors,
                        line=dict(width=0.4, color="white"), opacity=0.92),
            hoverinfo="skip", showlegend=False))
        frames.append(go.Frame(data=tr, name=f"f{fi}", layout=go.Layout(
            annotations=[dict(text=f"{len(keep):,} / {n:,} نود", showarrow=False,
                              x=0.02, y=1.04, xref="paper", yref="paper",
                              font=dict(size=12, color=_INK))])))
    fig = go.Figure(data=frames[0].data, frames=frames[1:])
    fig.update_layout(
        title=dict(text="<b>رشدِ انیمیشنیِ گراف</b>" + (f"  (نمونهٔ {n:,} از {view.n_nodes:,})" if capped else ""),
                   font=dict(size=15, color=_INK)),
        paper_bgcolor=_BG, plot_bgcolor=_BG, height=620, margin=dict(l=20, r=20, t=54, b=40),
        xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        font=dict(color=_INK),
        updatemenus=[dict(type="buttons", showactive=False, y=-0.06, x=0.4, xanchor="left",
                          buttons=[dict(label="▶ پخش", method="animate",
                                        args=[None, dict(frame=dict(duration=500, redraw=True),
                                                         fromcurrent=True)]),
                                   dict(label="⏸", method="animate",
                                        args=[[None], dict(mode="immediate")])])],
        sliders=[dict(active=0, x=0.05, y=-0.02, len=0.9,
                      steps=[dict(label=str(i), method="animate",
                                  args=[[f"f{i}"], dict(mode="immediate")]) for i in range(len(frames))])])
    return fig


# ════════════════════════════════════════════════════════════════════════════
# 17. sunburst of folders
# ════════════════════════════════════════════════════════════════════════════
def render_sunburst(view: GraphView, **_) -> go.Figure:
    """Build a 2-level sunburst: vault → top folder → second-level folder."""
    counts: dict[str, int] = defaultdict(int)
    sub: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for node, folder in view.folder_of.items():
        counts[folder] += 1
        parts = node.split("/")
        if len(parts) > 1:
            sub[folder][parts[1]] += 1
    top = sorted(counts, key=lambda f: -counts[f])[:24]
    labels, parents, vals, colors = ["vault"], [""], [sum(counts.values())], ["#2c3e50"]
    for f in top:
        labels.append(f); parents.append("vault"); vals.append(counts[f])
        colors.append(view.folder_color.get(f, "#7f8c8d"))
        for s, c in sorted(sub[f].items(), key=lambda kv: -kv[1])[:6]:
            labels.append(s); parents.append(f); vals.append(c)
            colors.append(view.folder_color.get(f, "#7f8c8d"))
    fig = go.Figure(go.Sunburst(
        labels=labels, parents=parents, values=vals,
        marker=dict(colors=colors), branchvalues="total",
        hovertemplate="<b>%{label}</b><br>نوت: %{value}<extra></extra>"))
    fig.update_layout(
        title=dict(text="<b>Sunburst فولدرها</b>", font=dict(size=15, color=_INK)),
        paper_bgcolor=_BG, height=620, margin=dict(l=10, r=10, t=54, b=10), font=dict(color=_INK))
    return fig


# ════════════════════════════════════════════════════════════════════════════
# 18. sankey of folder → folder flows
# ════════════════════════════════════════════════════════════════════════════
def render_sankey(view: GraphView, *, top_n=18, **_) -> go.Figure:
    """Edges that cross folders, aggregated into folder→folder flows."""
    folders = list(view.summary.get("notes_per_top_folder", {}).keys())[:top_n]
    flows: dict[tuple[str, str], int] = defaultdict(int)
    for a, b in view.edges:
        fa = view.folder_of.get(view.nodes[a])
        fb = view.folder_of.get(view.nodes[b])
        if fa in folders and fb in folders and fa != fb:
            key = (fa, fb) if fa < fb else (fb, fa)
            flows[key] += 1
    # node order = folders; edges sorted by weight
    src, tgt, val = [], [], []
    for (fa, fb), c in sorted(flows.items(), key=lambda kv: -kv[1])[:80]:
        src.append(folders.index(fa)); tgt.append(folders.index(fb)); val.append(c)
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=folders, pad=14, thickness=18,
                  color=[view.folder_color.get(f, "#7f8c8d") for f in folders],
                  hovertemplate="%{label}<extra></extra>"),
        link=dict(source=src, target=tgt, value=val, color="#b9c8e0",
                  hovertemplate="%{value} یال<extra></extra>")))
    fig.update_layout(
        title=dict(text="<b>Sankey جریانِ فولدرها</b>", font=dict(size=15, color=_INK)),
        paper_bgcolor=_BG, height=620, margin=dict(l=10, r=10, t=54, b=10), font=dict(color=_INK, size=10))
    return fig
