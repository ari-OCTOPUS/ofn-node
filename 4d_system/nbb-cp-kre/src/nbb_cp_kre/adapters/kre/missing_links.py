"""Missing-link proposals — the actual deliverable of the whole pipeline.

The winning representation from the bake-off is refit on the FULL graph and used
to rank non-edges. Nothing here writes to the vault and nothing is applied:
every result is a :class:`LinkProposal` with status ``proposed``, matching
``policy.yaml`` (``modify_file`` requires approval) and INV-2.
"""

from __future__ import annotations

import numpy as np

from ...kernel.types import LinkGraph, LinkProposal
from .representations import REGISTRY, adjacency

__all__ = ["propose_missing_links"]


def propose_missing_links(
    graph: LinkGraph,
    representation_name: str,
    *,
    top_k: int = 40,
    max_candidates: int = 4_000_000,
    seed: int = 0,
    min_degree: int = 1,
) -> list[LinkProposal]:
    n, edges = graph.n, graph.edges
    if n < 3 or not edges:
        return []

    rep = next((r for r in REGISTRY if r.name == representation_name), None)
    if rep is None or rep.name == "random_control":
        rep = next(r for r in REGISTRY if r.name == "adamic_adar")

    A = adjacency(n, edges)
    deg = np.asarray(A.sum(1)).ravel()
    existing = {(min(a, b), max(a, b)) for a, b in edges}

    # Candidate pool: pairs at graph distance 2 (share a neighbour) — the only
    # pairs any structural method can rank meaningfully — plus, when that pool
    # is thin, a random sample so isolated notes are not silently excluded.
    A2 = (A @ A).tocoo()
    cands: list[tuple[int, int]] = []
    for u, v in zip(A2.row, A2.col):
        if u >= v:
            continue
        k = (int(u), int(v))
        if k in existing or deg[u] < min_degree or deg[v] < min_degree:
            continue
        cands.append(k)
        if len(cands) >= max_candidates:
            break

    dropped_note = None
    if len(cands) >= max_candidates:
        dropped_note = f"candidate pool truncated at {max_candidates:,} pairs"

    if len(cands) < top_k * 10:
        rng = np.random.default_rng(seed)
        extra, tries = set(), 0
        while len(extra) < top_k * 10 and tries < top_k * 2000:
            u, v = int(rng.integers(0, n)), int(rng.integers(0, n))
            tries += 1
            if u == v:
                continue
            k = (min(u, v), max(u, v))
            if k in existing or k in extra:
                continue
            extra.add(k)
        cands = list({*cands, *extra})

    if not cands:
        return []

    rng = np.random.default_rng(seed)
    scores, _ = rep.score(A, cands, rng)

    # Embedding scorers are cosine similarities, so the head of the ranking
    # saturates at ~1.000 and ties are broken arbitrarily. Adamic–Adar is used
    # purely as a deterministic tie-breaker; it never overrides the winner.
    tiebreak = next(r for r in REGISTRY if r.name == "adamic_adar")
    aa, _ = tiebreak.score(A, cands, rng)
    order = np.lexsort((-aa, -np.round(scores, 6)))[:top_k]

    out: list[LinkProposal] = []
    Acsr = A.tocsr()
    for rank, i in enumerate(order, start=1):
        u, v = cands[int(i)]
        shared = Acsr[u].dot(Acsr[v].T).toarray().ravel()[0]
        ev = {
            "representation": rep.name,
            "shared_neighbours": int(shared),
            "degree_source": int(deg[u]),
            "degree_target": int(deg[v]),
            "adamic_adar": round(float(aa[int(i)]), 4),
        }
        if dropped_note:
            ev["caveat"] = dropped_note
        out.append(LinkProposal(
            source=graph.nodes[u], target=graph.nodes[v],
            score=float(scores[int(i)]), rank=rank, evidence=ev,
        ))
    return out
