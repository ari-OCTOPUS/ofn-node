"""
ui/visuals.py — Visual components for «ایده‌یاب شخصی».

Custom gauges, pipeline flow diagrams, and interactive geometric
visualizations designed for visual-spatial thinkers.

All components use Plotly for interactivity (hover, zoom, pan).
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ════════════════════════════════════════════════════════════════════════
#  Radial Gauge — for SMS, SLS, PCAI
# ════════════════════════════════════════════════════════════════════════

def radial_gauge(value: float, label: str, min_val: float = 0, max_val: float = 1,
                 color: str = "#1f3a5f", subtitle: str = "",
                 threshold_low: float = None, threshold_high: float = None) -> go.Figure:
    """
    A beautiful radial gauge for a single metric.

    Usage: st.plotly_chart(radial_gauge(0.12, "Δ_self"))
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'size': 40, 'color': color}, 'valueformat': '.4f'},
        title={'text': f"<b>{label}</b><br><span style='font-size:12px;color:gray'>{subtitle}</span>",
               'font': {'size': 14}},
        gauge={
            'axis': {'range': [min_val, max_val], 'tickwidth': 1, 'tickcolor': "#cccccc"},
            'bar': {'color': color, 'thickness': 0.35},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e0e0e0",
            'steps': [
                {'range': [min_val, min_val + (max_val-min_val)*0.33], 'color': '#f0f0f0'},
                {'range': [min_val + (max_val-min_val)*0.33, min_val + (max_val-min_val)*0.66], 'color': '#e0e0e0'},
                {'range': [min_val + (max_val-min_val)*0.66, max_val], 'color': '#d0d0d0'},
            ],
            'threshold': {
                'line': {'color': "#b0392b", 'width': 4},
                'thickness': 0.8,
                'value': threshold_high,
            } if threshold_high is not None else {},
        }
    ))

    fig.update_layout(
        height=220, margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor="white",
    )
    return fig


# ════════════════════════════════════════════════════════════════════════
#  Pipeline Flow Diagram — horizontal node chain
# ════════════════════════════════════════════════════════════════════════

def pipeline_flow(active_node: str = "", completed_nodes: list[str] = None) -> go.Figure:
    """
    Visualize the 8-step pipeline as a horizontal flow.
    Highlights the active node.
    """
    nodes = [
        ("📚", "load_context", "#6b4e8f"),
        ("✅", "verify",       "#2d8659"),
        ("🔍", "detect",       "#1f3a5f"),
        ("📊", "scores",       "#b8860b"),
        ("📐", "analyze",      "#8b4513"),
        ("📝", "report",       "#1f3a5f"),
        ("🪞", "reflect",      "#6b4e8f"),
        ("🔮", "decide_next",  "#b0392b"),
    ]

    completed = completed_nodes or []

    fig = go.Figure()

    for i, (icon, name, color) in enumerate(nodes):
        x = i * 1.5
        is_active = name == active_node
        is_done = name in completed

        bg_color = color if (is_active or is_done) else "#e8e8e8"
        text_color = "white" if (is_active or is_done) else "#999999"
        size = 55 if is_active else 45

        # Node circle
        fig.add_trace(go.Scatter(
            x=[x], y=[0],
            mode='markers+text',
            marker=dict(size=size, color=bg_color,
                       line=dict(width=2, color="white")),
            text=f"{icon}",
            textfont=dict(size=20),
            showlegend=False,
            hovertemplate=f"<b>{name}</b><br>{'فعال' if is_active else ('انجام‌شده' if is_done else 'در انتظار')}<extra></extra>",
        ))

        # Label below
        fig.add_trace(go.Scatter(
            x=[x], y=[-0.5],
            mode='text',
            text=f"<b>{name}</b>" if is_active else name,
            textfont=dict(size=9, color=color if is_active else "#999"),
            showlegend=False,
            hoverinfo='skip',
        ))

        # Arrow to next node
        if i < len(nodes) - 1:
            arrow_color = color if is_done else "#cccccc"
            fig.add_annotation(
                x=x + 1.2, y=0,
                ax=x + 0.35, ay=0,
                xref='x', yref='y', axref='x', ayref='y',
                showarrow=True, arrowhead=3, arrowsize=1.5,
                arrowwidth=2, arrowcolor=arrow_color,
            )

    # Reflection loop arrow (report → reflect → report)
    fig.add_annotation(
        x=6 * 1.5, y=0.8,  # report
        ax=7.5, ay=0.8,     # reflect
        xref='x', yref='y', axref='x', ayref='y',
        showarrow=True, arrowhead=2, arrowsize=1,
        arrowwidth=1.5, arrowcolor="#6b4e8f",
    )
    fig.add_annotation(
        text="↻ reflection loop", x=6.75, y=1.0,
        xref='x', yref='y', showarrow=False,
        font=dict(size=8, color="#6b4e8f"),
    )

    fig.update_layout(
        height=200, showlegend=False,
        xaxis=dict(visible=False, range=[-0.5, len(nodes)*1.5]),
        yaxis=dict(visible=False, range=[-1, 1.3]),
        paper_bgcolor="white", margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


# ════════════════════════════════════════════════════════════════════════
#  Tesseract Projection — 4D cube shadow in 3D
# ════════════════════════════════════════════════════════════════════════

def tesseract_projection(rotation: float = 0) -> go.Figure:
    """
    Interactive 3D tesseract (4D hypercube) projected into 3D.
    The rotation parameter controls the 4D rotation angle.

    This visualizes the core metaphor: a 4D object casting a 3D shadow.
    """
    # 16 vertices of a tesseract in 4D
    vertices_4d = np.array([
        [s1, s2, s3, s4]
        for s1 in [-1, 1] for s2 in [-1, 1] for s3 in [-1, 1] for s4 in [-1, 1]
    ], dtype=float)

    # Apply 4D rotation in the xw-plane
    angle = rotation * np.pi / 180
    cos_a, sin_a = np.cos(angle), np.sin(angle)
    rotated = vertices_4d.copy()
    rotated[:, 0] = vertices_4d[:, 0] * cos_a - vertices_4d[:, 3] * sin_a
    rotated[:, 3] = vertices_4d[:, 0] * sin_a + vertices_4d[:, 3] * cos_a

    # Project 4D → 3D (simple perspective projection along w-axis)
    distance = 3.0
    w = rotated[:, 3]
    scale = distance / (distance - w)
    vertices_3d = rotated[:, :3] * scale[:, np.newaxis]

    # 32 edges of the tesseract
    edges = []
    for i in range(16):
        for j in range(i+1, 16):
            diff = np.sum(np.abs(vertices_4d[i] - vertices_4d[j]))
            if diff == 2:  # differ in exactly one coordinate
                edges.append((i, j))

    fig = go.Figure()

    # Draw edges
    for i, j in edges:
        fig.add_trace(go.Scatter3d(
            x=[vertices_3d[i, 0], vertices_3d[j, 0]],
            y=[vertices_3d[i, 1], vertices_3d[j, 1]],
            z=[vertices_3d[i, 2], vertices_3d[j, 2]],
            mode='lines',
            line=dict(color='#1f3a5f', width=3),
            showlegend=False,
            hoverinfo='skip',
        ))

    # Draw vertices
    fig.add_trace(go.Scatter3d(
        x=vertices_3d[:, 0], y=vertices_3d[:, 1], z=vertices_3d[:, 2],
        mode='markers',
        marker=dict(size=6, color='#b0392b',
                    line=dict(width=1, color='white')),
        showlegend=False,
        hovertemplate='<b>Vertex</b><br>x=%{x:.2f} y=%{y:.2f} z=%{z:.2f}<extra></extra>',
    ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
            bgcolor="white",
        ),
        height=400, margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor="white",
        title=dict(text=f"<b>تسراکت</b> — سایه‌ی ۳بعدی از یک جسم ۴بعدی (دوران: {rotation:.0f}°)",
                   font=dict(size=12)),
    )
    return fig


# ════════════════════════════════════════════════════════════════════════
#  Shadow Decomposition — the chain rule visualized
# ═══════════════════════════½═════════════════════════════════════════════

def shadow_decomposition_chart(sigma_z2: float, S_b: float, S: float) -> go.Figure:
    """
    Visualize the chain rule identity: ½log(σ_z²/S) = E_shadow + Δ_self

    Shows three levels (null, blind, informed) as stacked bars.
    """
    e_shadow = 0.5 * np.log(sigma_z2 / S_b) if sigma_z2 > 0 and S_b > 0 else 0
    delta_self = 0.5 * np.log(S_b / S) if S_b > 0 and S > 0 else 0
    total = 0.5 * np.log(sigma_z2 / S) if sigma_z2 > 0 and S > 0 else 0

    fig = go.Figure()

    # Stacked bar: E_shadow + Δ_self
    fig.add_trace(go.Bar(
        x=["کلِ رمزِ بُعد پنهان"],
        y=[e_shadow],
        name=f'E_shadow ({e_shadow:.4f})',
        marker_color='#6b4e8f',
        text=[f'E_shadow<br>{e_shadow:.4f}'],
        textposition='inside',
    ))
    fig.add_trace(go.Bar(
        x=["کلِ رمزِ بُعد پنهان"],
        y=[delta_self],
        name=f'Δ_self ({delta_self:.4f})',
        marker_color='#1f3a5f',
        text=[f'Δ_self<br>{delta_self:.4f}'],
        textposition='inside',
    ))

    fig.update_layout(
        barmode='stack',
        title=dict(text="<b>تجزیه‌ی سایه</b>: ½log(σ_z²/S) = E_shadow + Δ_self",
                   font=dict(size=13)),
        yaxis_title="nat / گام",
        height=350, showlegend=True,
        paper_bgcolor="white",
        font=dict(size=11),
    )

    # Add annotation for the ratio
    ratio = delta_self / e_shadow if abs(e_shadow) > 1e-10 else float('inf')
    fig.add_annotation(
        x=0, y=total * 1.05,
        text=f"Δ_self / E_shadow = {ratio:.1f}×<br>«دسترسیِ درون» {ratio:.0f} برابر «کشفِ وجود»",
        showarrow=False, font=dict(size=11, color="#b0392b"),
    )

    return fig


# ════════════════════════════════════════════════════════════════════════
#  λ-grid heatmap — Δ_self and E_shadow across parameter space
# ════════════════════════════════════════════════════════════════════════

def lambda_grid_heatmap(rho_values: list[float], lambda_values: list[float],
                        se=0.1, sz=0.05, sd=0.1, metric: str = "delta_self") -> go.Figure:
    """
    Heatmap of Δ_self or E_shadow across the ρ × λ parameter space.
    """
    from core.model import solve_from_stds

    z_values = []
    for rho in rho_values:
        row = []
        for lam in lambda_values:
            try:
                sol = solve_from_stds(rho=rho, lam=lam, se=se, sz=sz, sd=sd)
                if metric == "delta_self":
                    row.append(sol.Delta_self)
                elif metric == "e_shadow":
                    row.append(max(sol.E_shadow, 0))
                elif metric == "pcai":
                    from core.scores import compute_scores_from_model
                    scores = compute_scores_from_model(rho=rho, lam=lam, se=se, sz=sz, sd=sd)
                    row.append(scores.pcai)
                else:
                    row.append(0)
            except Exception:
                row.append(0)
        z_values.append(row)

    titles = {
        "delta_self": "Δ_self — ارزش درون‌نگری",
        "e_shadow": "E_shadow — ردِ بُعد پنهان",
        "pcai": "PCAI — مزیت کانال خصوصی",
    }

    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=[f"{l:.1f}" for l in lambda_values],
        y=[f"{r:.1f}" for r in rho_values],
        colorscale='Viridis',
        text=[[f"{v:.4f}" for v in row] for row in z_values],
        texttemplate="%{text}",
        textfont={"size": 8},
        hovertemplate="ρ=%{y}, λ=%{x}<br>value=%{z:.4f}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text=f"<b>{titles.get(metric, metric)}</b> در فضای پارامتر",
                   font=dict(size=13)),
        xaxis_title="λ (شدت نشت)",
        yaxis_title="ρ (حافظه)",
        height=400,
        paper_bgcolor="white",
    )
    return fig


# ════════════════════════════════════════════════════════════════════════
#  Time series with detection overlay
# ════════════════════════════════════════════════════════════════════════

def series_with_shadow(series: np.ndarray, temporal_mi: float = 0,
                       detectable: bool = False) -> go.Figure:
    """
    Interactive time series with shadow detection overlay.
    """
    fig = go.Figure()

    # The series
    fig.add_trace(go.Scatter(
        y=series[:2000] if len(series) > 2000 else series,
        mode='lines',
        line=dict(color='#1f3a5f', width=0.8),
        name='سری زمانی',
    ))

    # Rolling mean (the "shadow")
    window = min(50, len(series) // 10)
    if window > 1:
        rolling = np.convolve(series, np.ones(window)/window, mode='valid')
        fig.add_trace(go.Scatter(
            y=rolling[:2000] if len(rolling) > 2000 else rolling,
            mode='lines',
            line=dict(color='#b0392b', width=2),
            name=f'میانگین متحرک (پنجره={window})',
        ))

    # Status badge
    status_color = "#2d8659" if detectable else "#b0392b"
    status_text = "بُعد پنهان شناسایی شد ✓" if detectable else "الگوی قابل‌تشخیص نیست ✗"

    fig.update_layout(
        title=dict(text=f"<b>{status_text}</b><br><span style='font-size:11px;color:gray'>temporal MI = {temporal_mi:.6f} nat/گام</span>",
                   font=dict(color=status_color, size=13)),
        xaxis_title="زمان",
        yaxis_title="مقدار",
        height=350, showlegend=True,
        paper_bgcolor="white",
        hovermode='x unified',
    )
    return fig


# ════════════════════════════════════════════════════════════════════════
#  Knowledge graph mini-view
# ════════════════════════════════════════════════════════════════════════

def knowledge_graph_view(query: str = "E_shadow", k: int = 8) -> go.Figure:
    """
    Visualize related concepts from the vault as a force-directed graph.
    """
    from memory.vectorstore import search_vault

    try:
        results = search_vault(query, k=k)
    except Exception:
        results = []

    if not results:
        fig = go.Figure()
        fig.update_layout(annotations=[dict(
            text="Vault در دسترس نیست", x=0.5, y=0.5, showarrow=False
        )])
        return fig

    # Build a simple graph: center = query, satellites = results
    n = len(results)
    angles = np.linspace(0, 2*np.pi, n, endpoint=False)

    fig = go.Figure()

    # Edges
    for i, r in enumerate(results):
        fig.add_trace(go.Scatter(
            x=[0, np.cos(angles[i])],
            y=[0, np.sin(angles[i])],
            mode='lines',
            line=dict(width=r['relevance']*5, color='#cccccc'),
            showlegend=False, hoverinfo='skip',
        ))

    # Center node
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode='markers+text',
        marker=dict(size=40, color='#1f3a5f'),
        text=[query], textposition='middle center',
        textfont=dict(size=10, color='white'),
        showlegend=False,
    ))

    # Satellite nodes
    for i, r in enumerate(results):
        fig.add_trace(go.Scatter(
            x=[np.cos(angles[i])], y=[np.sin(angles[i])],
            mode='markers+text',
            marker=dict(size=20 + r['relevance']*30,
                       color='#6b4e8f', line=dict(width=1, color='white')),
            text=[r['title'][:15]], textposition='top center',
            textfont=dict(size=8),
            showlegend=False,
            hovertemplate=f"<b>{r['title']}</b><br>relevance: {r['relevance']}<extra></extra>",
        ))

    fig.update_layout(
        height=400, showlegend=False,
        xaxis=dict(visible=False, range=[-1.5, 1.5]),
        yaxis=dict(visible=False, range=[-1.5, 1.5]),
        paper_bgcolor="white", margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig


# ════════════════════════════════════════════════════════════════════════
#  Obsidian Knowledge Graph — force-directed view of vault wikilinks
# ════════════════════════════════════════════════════════════════════════

def _force_directed_layout(nodes: list[dict], edges: list[dict],
                           iterations: int = 200) -> dict[str, tuple[float, float]]:
    """
    الگوریتم force-directed ساده (Fruchterman-Reingold سبک) — numpy-vectorized.
    node‌ها رو طوری توزیع می‌کنه که overlaps کم بشه و hub‌ها مرکز بشن.
    """
    n = len(nodes)
    if n == 0:
        return {}

    node_ids = [nd["id"] for nd in nodes]
    index = {nd_id: i for i, nd_id in enumerate(node_ids)}

    # Initialize random positions (deterministic)
    rng = np.random.default_rng(42)
    P = rng.uniform(-1, 1, size=(n, 2))

    # Edge index arrays (only edges whose endpoints exist)
    edge_pairs = [(index[e["source"]], index[e["target"]])
                  for e in edges
                  if e["source"] in index and e["target"] in index]
    if edge_pairs:
        src = np.array([p[0] for p in edge_pairs], dtype=np.intp)
        dst = np.array([p[1] for p in edge_pairs], dtype=np.intp)
    else:
        src = dst = np.empty(0, dtype=np.intp)

    # Force-directed iterations
    k = 1.0 / max(n ** 0.5, 1)  # optimal distance
    temperature = 0.5

    for _ in range(iterations):
        # Repulsive forces (all pairs, vectorized)
        diff = P[:, None, :] - P[None, :, :]              # (n, n, 2)
        dist = np.maximum(np.sqrt((diff ** 2).sum(axis=2)), 0.01)  # (n, n)
        np.fill_diagonal(dist, np.inf)                    # no self-force
        force = (k * k) / dist                            # (n, n)
        disp = (diff / dist[:, :, None] * force[:, :, None]).sum(axis=1)  # (n, 2)

        # Attractive forces (edges only, vectorized)
        if len(src):
            ediff = P[src] - P[dst]                       # (m, 2)
            edist = np.maximum(np.sqrt((ediff ** 2).sum(axis=1)), 0.01)
            eforce = (edist * edist / k)
            pull = ediff / edist[:, None] * eforce[:, None]
            np.add.at(disp, src, -pull)
            np.add.at(disp, dst, pull)

        # Apply displacements (limited by temperature)
        dnorm = np.maximum(np.sqrt((disp ** 2).sum(axis=1)), 0.01)
        limited = np.minimum(dnorm, temperature)
        P += disp / dnorm[:, None] * limited[:, None]

        # Cool down
        temperature *= 0.95

    # Normalize to [-1, 1]
    x_min, y_min = P.min(axis=0)
    x_range = (P[:, 0].max() - x_min) or 1
    y_range = (P[:, 1].max() - y_min) or 1
    P[:, 0] = (P[:, 0] - x_min) / x_range * 2 - 1
    P[:, 1] = (P[:, 1] - y_min) / y_range * 2 - 1

    return {nd_id: (float(P[i, 0]), float(P[i, 1])) for nd_id, i in index.items()}


def obsidian_graph(graph=None) -> go.Figure:
    """
    گراف دانش Obsidian — force-directed از wikilink‌های vault.
    node‌ها بر اساس پوشه رنگی، size بر اساس incoming links.

    graph: یک VaultGraph از قبل parse‌شده (اختیاری — برای جلوگیری از parse تکراری).
    """
    if graph is None:
        from brain.vault_sync import parse_vault_graph
        graph = parse_vault_graph()

    if graph.n_nodes == 0:
        fig = go.Figure()
        fig.add_annotation(text="Vault خالی است", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=20))
        fig.update_layout(height=600, xaxis=dict(visible=False),
                          yaxis=dict(visible=False))
        return fig

    # ── مقیاس‌پذیری: chidمانِ force-directed از O(n²) است. با هزاران یادداشت
    # کند می‌شود؛ پس فقط پُراتصال‌ترین MAX_NODES گره را نگه می‌داریم (هاب‌ها) ──
    MAX_NODES = 150
    nodes = graph.nodes
    edges = graph.edges
    truncated_note = ""
    if len(nodes) > MAX_NODES:
        deg = {}
        for e in edges:
            deg[e["source"]] = deg.get(e["source"], 0) + 1
            deg[e["target"]] = deg.get(e["target"], 0) + 1
        keep_ids = {nd["id"] for nd in sorted(
            nodes, key=lambda n: deg.get(n["id"], 0), reverse=True)[:MAX_NODES]}
        nodes = [nd for nd in nodes if nd["id"] in keep_ids]
        edges = [e for e in edges if e["source"] in keep_ids and e["target"] in keep_ids]
        truncated_note = f" (نمایشِ {MAX_NODES} هابِ اصلی از {graph.n_nodes} یادداشت)"

    # Compute layout (روی مجموعه‌ی محدودشده — سریع)
    pos = _force_directed_layout(nodes, edges, iterations=150)
    graph_nodes, graph_edges = nodes, edges

    # Count incoming links per node
    incoming = {}
    for e in graph_edges:
        incoming[e["target"]] = incoming.get(e["target"], 0) + 1

    # Draw edges
    edge_x, edge_y = [], []
    for e in graph_edges:
        if e["source"] in pos and e["target"] in pos:
            edge_x += [pos[e["source"]][0], pos[e["target"]][0], None]
            edge_y += [pos[e["source"]][1], pos[e["target"]][1], None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=0.5, color="#bbb"),
        hoverinfo="none", showlegend=False,
    )

    # Draw nodes, grouped by folder for legend
    folder_groups = {}
    for nd in graph_nodes:
        folder = nd.get("folder", "root")
        if folder not in folder_groups:
            folder_groups[folder] = {"x": [], "y": [], "text": [], "size": [], "color": nd["color"]}

        nd_id = nd["id"]
        if nd_id in pos:
            folder_groups[folder]["x"].append(pos[nd_id][0])
            folder_groups[folder]["y"].append(pos[nd_id][1])
            folder_groups[folder]["text"].append(nd_id)
            # Size based on incoming links (min 8, max 30)
            inc = incoming.get(nd_id, 0)
            folder_groups[folder]["size"].append(8 + min(inc * 2, 22))

    node_traces = [edge_trace]
    for folder, data in folder_groups.items():
        # Shorten folder name for legend
        short = folder[:15] if len(folder) > 15 else folder
        node_traces.append(go.Scatter(
            x=data["x"], y=data["y"], mode="markers",
            marker=dict(size=data["size"], color=data["color"],
                        line=dict(width=1, color="white")),
            text=data["text"], textposition="top center",
            textfont=dict(size=7),
            name=short,
            hovertemplate="<b>%{text}</b><br>folder: " + short + "<extra></extra>",
            showlegend=True,
        ))

    fig = go.Figure(data=node_traces)
    fig.update_layout(
        height=700, showlegend=True,
        title=dict(text=f"شبکه‌ی دانش{truncated_note}", font=dict(size=11)) if truncated_note else None,
        legend=dict(font=dict(size=8), orientation="h",
                    yanchor="bottom", y=-0.1),
        xaxis=dict(visible=False, range=[-1.2, 1.2]),
        yaxis=dict(visible=False, range=[-1.2, 1.2]),
        paper_bgcolor="white", margin=dict(l=0, r=0, t=30 if truncated_note else 0, b=40),
        hovermode="closest",
    )
    return fig


def rhythm_radar(rhythms: list[dict]) -> go.Figure:
    """
    نمودار راداری برای مقایسه‌ی ریتم‌های ذخیره‌شده.
    محورها: MI، ρ، detectable، n_points (normalized).
    """
    if not rhythms:
        fig = go.Figure()
        fig.add_annotation(text="ریتمی ذخیره نشده", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=16))
        return fig

    categories = ["MI", "ρ̂", "Detect.", "Size"]

    # Normalize values
    max_mi = max((r.get("mi", 0) for r in rhythms), default=1) or 1
    max_n = max((r.get("n_points", 1) for r in rhythms), default=1) or 1

    fig = go.Figure()
    for r in rhythms[:6]:  # max 6 rhythms
        values = [
            r.get("mi", 0) / max_mi,
            abs(r.get("rho_hat", 0)),
            1.0 if r.get("detectable") else 0.0,
            r.get("n_points", 0) / max_n,
        ]
        values += values[:1]  # close the polygon
        fig.add_trace(go.Scatterpolar(
            r=values, theta=categories + categories[:1],
            fill="toself", name=r.get("name", "?")[:20],
            opacity=0.6,
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        height=400, showlegend=True,
        legend=dict(font=dict(size=8)),
    )
    return fig
