#!/usr/bin/env python3
"""topology.py — Part 11: geometric topology. tree + k shortcuts.

full-mesh ممنوع. یال‌ها ~ O(N log N). Warden=root، Archivist=hub، leaves=text-voices.
هیچ import از production."""
from __future__ import annotations
import math
from dataclasses import dataclass, field


@dataclass
class Topology:
    """گرافِ ارتباط = درختِ سلسله‌مراتبی + k میان‌برِ small-world.
    یال‌ها: list of (i, j). full-mesh ممنوع."""
    nodes: list[str] = field(default_factory=list)
    edges: list[tuple[int, int]] = field(default_factory=list)
    root: str = "Warden"
    hub: str = "Archivist"

    def edge_count(self) -> int:
        return len(self.edges)

    def is_full_mesh(self) -> bool:
        """full-mesh = N*(N-1)/2 یال."""
        n = len(self.nodes)
        return self.edge_count() >= n * (n - 1) // 2

    def adjacency(self) -> dict[int, list[int]]:
        adj: dict[int, list[int]] = {i: [] for i in range(len(self.nodes))}
        for (i, j) in self.edges:
            adj.setdefault(i, []).append(j)
            adj.setdefault(j, []).append(i)
        return adj


def build_topology(roles: list[str], k_shortcuts: int = 2) -> Topology:
    """ساختِ tree + k shortcuts.
    Warden (root) → Archivist (hub) → همهٔ leaves.
    + k random small-world shortcut میانِ leaves.
    O(N) tree + O(k·N) shortcuts = O(N log N) typically."""
    if not roles:
        return Topology()
    # normalize: Warden اول، Archivist دوم
    nodes = list(roles)
    if "Warden" in nodes:
        nodes.remove("Warden")
        nodes.insert(0, "Warden")
    if "Archivist" in nodes:
        nodes.remove("Archivist")
        nodes.insert(1, "Archivist")
    idx = {name: i for i, name in enumerate(nodes)}
    edges = set()
    # tree: root → hub
    if "Warden" in idx and "Archivist" in idx:
        edges.add((idx["Warden"], idx["Archivist"]))
    # hub → هر leaf
    hub_i = idx.get("Archivist", 0)
    for name, i in idx.items():
        if name in ("Warden", "Archivist"):
            continue
        edges.add((hub_i, i))
    # k shortcuts: random میانِ leaves (deterministic seed برای تست)
    import random
    rng = random.Random(42)
    leaves = [i for name, i in idx.items() if name not in ("Warden", "Archivist")]
    if len(leaves) > 1:
        for _ in range(min(k_shortcuts, len(leaves))):
            a, b = rng.sample(leaves, 2)
            edges.add((min(a, b), max(a, b)))
    return Topology(nodes=nodes, edges=sorted(edges), root="Warden", hub="Archivist")


def edge_count_is_subquadratic(n: int, edge_count: int) -> bool:
    """assert یال ~ O(N log N) نه O(N²).
    full-mesh = N*(N-1)/2. ما باید به‌مراتب کمتر باشیم."""
    full_mesh = n * (n - 1) // 2
    nlogn = n * max(1, int(math.log2(max(n, 2))))
    # باید زیرِ nlogn * 2 باشه (اجازهٔ slack)
    return edge_count < full_mesh * 0.6 and edge_count <= nlogn * 3
