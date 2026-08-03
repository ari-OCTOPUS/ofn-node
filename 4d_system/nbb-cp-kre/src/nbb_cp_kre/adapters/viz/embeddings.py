"""Embedding representations — nodes placed by a low-dim projection.

Spectral / t-SNE / Isomap live here. These re-use the same ``representations``
math the bakeoff uses, but project to 2D/3D purely for visualisation. Each is
marked ``heavy`` because the projection is O(seconds-to-tens-of-seconds) on a
real vault; the GraphView subsample keeps them bounded.
"""

from __future__ import annotations

import math
from typing import Any

import networkx as nx
import numpy as np
import plotly.graph_objects as go
import scipy.sparse as sp
import scipy.sparse.linalg as spl

from .data import GraphView

_INK = "#52514e"
_BG = "white"


def _adj(n, edges):
    if not edges:
        return sp.csr_matrix((n, n), dtype=np.float64)
    r = np.array([e[0] for e in edges] + [e[1] for e in edges])
    c = np.array([e[1] for e in edges] + [e[0] for e in edges])
    return sp.csr_matrix((np.ones(len(r)), (r, c)), shape=(n, n))


def _spectral(A: sp.csr_matrix, k: int):
    n = A.shape[0]
    A = A + sp.eye(n) * 1e-6
    d = np.asarray(A.sum(1)).ravel()
    Dm = sp.diags(1.0 / np.sqrt(np.maximum(d, 1e-12)))
    An = (Dm @ A @ Dm).tocsc()
    k = min(k, n - 2) if n > 3 else 1
    try:
        w, V = spl.eigsh(An, k=k, which="LA")
    except Exception:
        w, V = np.linalg.eigh(An.toarray())
        order = np.argsort(-w)[:k]; w, V = w[order], V[:, order]
    return V * np.sqrt(np.abs(w))


def _scatter(view, nodes, XY, dims, *, title, heavy_note=""):
    degs = [view.degree.get(nodes[i], 0) for i in range(len(nodes))]
    colors = [view.color_for(nodes[i]) for i in range(len(nodes))]
    labels = [view.label_for(nodes[i]) for i in range(len(nodes))]
    sizes = [max(5, min(20, 5 + math.sqrt(d) * 2.4)) for d in degs]
    common = dict(mode="markers",
                  marker=dict(size=sizes, color=colors, line=dict(width=0.4, color="white"), opacity=0.9),
                  text=labels, hovertemplate="<b>%{text}</b><br>degree=%{customdata}<extra></extra>",
                  customdata=degs, showlegend=False)
    if dims == 2:
        fig = go.Figure(go.Scatter(x=XY[:, 0], y=XY[:, 1], **common))
        fig.update_layout(title=dict(text=f"<b>{title}</b>{heavy_note}", font=dict(size=15, color=_INK)),
                          paper_bgcolor=_BG, plot_bgcolor=_BG, height=620,
                          margin=dict(l=20, r=20, t=54, b=20),
                          xaxis=dict(visible=False), yaxis=dict(visible=False), font=dict(color=_INK))
    else:
        fig = go.Figure(go.Scatter3d(x=XY[:, 0], y=XY[:, 1], z=XY[:, 2], **common))
        fig.update_layout(title=dict(text=f"<b>{title}</b>{heavy_note}", font=dict(size=15, color=_INK)),
                          paper_bgcolor=_BG, height=640, margin=dict(l=10, r=10, t=54, b=10),
                          scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False),
                                     zaxis=dict(visible=False), aspectmode="data"),
                          font=dict(color=_INK))
    return fig


# ════════════════════════════════════════════════════════════════════════════
def render_spectral3d(view: GraphView, *, max_nodes=1500, **_) -> go.Figure:
    nodes = view.sample_nodes if view.n_nodes > max_nodes else view.nodes
    edges = view.sample_edges if view.n_nodes > max_nodes else view.edges
    capped = view.n_nodes > max_nodes
    A = _adj(len(nodes), edges)
    emb = _spectral(A, 3)
    note = f"  (نمونهٔ {len(nodes):,} از {view.n_nodes:,})" if capped else ""
    return _scatter(view, nodes, emb, 3, title="تعبیهٔ طیفی ۳بعدی", heavy_note=note)


# ════════════════════════════════════════════════════════════════════════════
def render_tsne2d(view: GraphView, *, max_nodes=1500, **_) -> go.Figure:
    from sklearn.manifold import TSNE
    nodes = view.sample_nodes if view.n_nodes > max_nodes else view.nodes
    edges = view.sample_edges if view.n_nodes > max_nodes else view.edges
    capped = view.n_nodes > max_nodes
    A = _adj(len(nodes), edges)
    emb = _spectral(A, min(24, max(8, len(nodes) // 4)))
    # perplexity must be < n_samples (sklearn asserts this); floor at 2 for
    # tiny graphs so the figure still renders on small vaults.
    perp = min(30, max(2, (len(nodes) - 1) // 12))
    # sklearn >=1.5 renamed n_iter → max_iter; pass both via try to stay portable.
    kw = dict(n_components=2, perplexity=perp, init="pca", learning_rate="auto",
              random_state=7, max_iter=700)
    try:
        ts = TSNE(**kw).fit_transform(emb)
    except TypeError:  # older sklearn without max_iter
        kw.pop("max_iter"); kw["n_iter"] = 700
        ts = TSNE(**kw).fit_transform(emb)
    note = f"  (نمونهٔ {len(nodes):,} از {view.n_nodes:,})" if capped else ""
    return _scatter(view, nodes, ts, 2, title="تعبیهٔ t-SNE دوبعدی", heavy_note=note)


# ════════════════════════════════════════════════════════════════════════════
def render_isomap2d(view: GraphView, *, max_nodes=1200, **_) -> go.Figure:
    """Classical MDS on graph geodesics (the Isomap core) → 2D."""
    nodes = view.sample_nodes if view.n_nodes > max_nodes else view.nodes
    edges = view.sample_edges if view.n_nodes > max_nodes else view.edges
    capped = view.n_nodes > max_nodes
    G = nx.Graph(); G.add_nodes_from(range(len(nodes))); G.add_edges_from(edges)
    n = len(nodes)
    D = np.full((n, n), np.nan)
    for src, dd in nx.all_pairs_shortest_path_length(G, cutoff=8):
        for dst, v in dd.items():
            D[src, dst] = v
    fin = D[np.isfinite(D)]
    D = np.where(np.isfinite(D), D, (fin.max() * 2) if fin.size else 1.0)
    J = np.eye(n) - np.ones((n, n)) / n
    B = -0.5 * J @ (D ** 2) @ J
    w, V = np.linalg.eigh(B)
    order = np.argsort(-w)[:2]
    emb = V[:, order] * np.sqrt(np.maximum(w[order], 0))
    note = f"  (نمونهٔ {len(nodes):,} از {view.n_nodes:,})" if capped else ""
    return _scatter(view, nodes, emb, 2, title="تعبیهٔ Isomap دوبعدی", heavy_note=note)


# ════════════════════════════════════════════════════════════════════════════
def render_globe3d(view: GraphView, *, max_nodes=1500, **_) -> go.Figure:
    """Scatter nodes onto a sphere using a spectral embedding as (θ, φ)."""
    nodes = view.sample_nodes if view.n_nodes > max_nodes else view.nodes
    edges = view.sample_edges if view.n_nodes > max_nodes else view.edges
    capped = view.n_nodes > max_nodes
    A = _adj(len(nodes), edges)
    emb = _spectral(A, 2)
    # map two dims to spherical angles
    theta = np.arctan2(emb[:, 0], emb[:, 1])          # azimuth
    phi = np.arccos(np.clip(emb[:, 0] / 10.0, -1, 1))  # polar
    r = 1.0
    xs = r * np.sin(phi) * np.cos(theta)
    ys = r * np.sin(phi) * np.sin(theta)
    zs = r * np.cos(phi)
    degs = [view.degree.get(nodes[i], 0) for i in range(len(nodes))]
    colors = [view.color_for(nodes[i]) for i in range(len(nodes))]
    labels = [view.label_for(nodes[i]) for i in range(len(nodes))]
    fig = go.Figure()
    # faint sphere
    u = np.linspace(0, 2 * np.pi, 30); v_ = np.linspace(0, np.pi, 20)
    sx = np.outer(np.cos(u), np.sin(v_)); sy = np.outer(np.sin(u), np.sin(v_)); sz = np.outer(np.ones_like(u), np.cos(v_))
    fig.add_trace(go.Surface(x=sx, y=sy, z=sz, opacity=0.06, colorscale=[[0, "#dbe4f0"], [1, "#dbe4f0"]],
                             showscale=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(
        x=xs, y=ys, z=zs, mode="markers",
        marker=dict(size=[max(4, min(14, math.sqrt(d) * 2)) for d in degs], color=colors,
                    line=dict(width=0.4, color="white"), opacity=0.92),
        text=labels, hovertemplate="<b>%{text}</b><br>degree=%{customdata}<extra></extra>",
        customdata=degs, showlegend=False))
    note = f"  (نمونهٔ {len(nodes):,} از {view.n_nodes:,})" if capped else ""
    fig.update_layout(title=dict(text=f"<b>کرهٔ ۳بعدیِ گراف</b>{note}", font=dict(size=15, color=_INK)),
                      paper_bgcolor=_BG, height=640, margin=dict(l=10, r=10, t=54, b=10),
                      scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
                                 aspectmode="data"), font=dict(color=_INK))
    return fig
