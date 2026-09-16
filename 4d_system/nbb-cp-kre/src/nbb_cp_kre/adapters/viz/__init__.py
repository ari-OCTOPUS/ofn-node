"""Visualisation layer (v0.2) — 18 graphical representations of the link graph.

Lives in the adapter layer (alongside ``kre/`` and ``vault/``): it depends on
networkx/numpy/plotly, which the kernel must never import. Direction of
dependency stays ``kernel ← adapters ← app ← ui``.

Each representation is a pure function ``fig = render(view, **opts)`` where
``view`` is a :class:`GraphView` (a networkx graph + folder map + derived
metrics, built once from the latest ``graph_<stamp>.json`` artifact).
"""

from __future__ import annotations

from .data import GraphView, load_graph_view, VIZ_MAX_NODES
from .registry import REGISTRY, VizEntry, viz_by_id

__all__ = ["GraphView", "load_graph_view", "VIZ_MAX_NODES", "REGISTRY", "VizEntry", "viz_by_id"]
