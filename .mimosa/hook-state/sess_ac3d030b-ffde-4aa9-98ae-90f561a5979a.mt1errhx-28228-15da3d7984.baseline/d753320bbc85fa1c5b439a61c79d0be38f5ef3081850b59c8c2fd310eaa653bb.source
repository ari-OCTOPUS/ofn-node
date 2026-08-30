"""The competing representations.

Every scorer takes the **training** graph only and returns a score per candidate
pair. numpy/scipy/networkx live here (adapters layer) so the kernel stays pure.

Scalability is explicit, never silent: each representation declares
``max_nodes``. Above it the representation is SKIPPED and the reason is recorded
in the report, because a silently-truncated benchmark reads as "we tested
everything" when it did not.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

__all__ = ["REGISTRY", "FAST_ONLY", "Representation", "adjacency"]

EMB_DIM = 16


def adjacency(n: int, edges: list[tuple[int, int]]) -> sp.csr_matrix:
    if not edges:
        return sp.csr_matrix((n, n), dtype=np.float64)
    r = np.array([e[0] for e in edges] + [e[1] for e in edges])
    c = np.array([e[1] for e in edges] + [e[0] for e in edges])
    v = np.ones(len(r))
    return sp.csr_matrix((v, (r, c)), shape=(n, n))


# ---------------------------------------------------------------- heuristics
def _score_adamic_adar(A: sp.csr_matrix, pairs, rng) -> np.ndarray:
    deg = np.asarray(A.sum(1)).ravel()
    w = np.zeros_like(deg)
    nz = deg > 1
    w[nz] = 1.0 / np.log(deg[nz])
    W = sp.diags(w)
    out = np.empty(len(pairs))
    Acsr = A.tocsr()
    for k, (u, v) in enumerate(pairs):
        out[k] = Acsr[u].multiply(W.diagonal()).dot(Acsr[v].T).toarray().ravel()[0] \
            if Acsr[u].nnz and Acsr[v].nnz else 0.0
    return out


def _score_common_neighbors(A: sp.csr_matrix, pairs, rng) -> np.ndarray:
    Acsr = A.tocsr()
    return np.array([Acsr[u].dot(Acsr[v].T).toarray().ravel()[0] for u, v in pairs])


def _score_pref_attachment(A: sp.csr_matrix, pairs, rng) -> np.ndarray:
    deg = np.asarray(A.sum(1)).ravel()
    return np.array([deg[u] * deg[v] for u, v in pairs], dtype=float)


def _score_random(A, pairs, rng) -> np.ndarray:
    return rng.random(len(pairs))


# ---------------------------------------------------------------- embeddings
def _emb_score(emb: np.ndarray, pairs, mode: str) -> np.ndarray:
    a = emb[[p[0] for p in pairs]]
    b = emb[[p[1] for p in pairs]]
    if mode == "neg_dist":
        return -np.linalg.norm(a - b, axis=1)
    na = np.linalg.norm(a, axis=1) + 1e-12
    nb = np.linalg.norm(b, axis=1) + 1e-12
    return (a * b).sum(1) / (na * nb)


def _spectral(A: sp.csr_matrix, k: int = EMB_DIM) -> np.ndarray:
    n = A.shape[0]
    A = A + sp.eye(n) * 1e-6
    d = np.asarray(A.sum(1)).ravel()
    Dm = sp.diags(1.0 / np.sqrt(np.maximum(d, 1e-12)))
    An = (Dm @ A @ Dm).tocsc()
    k = min(k, n - 2) if n > 3 else 1
    try:
        w, V = spl.eigsh(An, k=k, which="LA")
    except Exception:                                    # tiny/degenerate graphs
        w, V = np.linalg.eigh(An.toarray())
        order = np.argsort(-w)[:k]
        w, V = w[order], V[:, order]
    return V * np.sqrt(np.abs(w))


def _score_spectral(A, pairs, rng):
    return _emb_score(_spectral(A), pairs, "cosine")


def _deepwalk(A: sp.csr_matrix, rng, walk_len: int = 40, n_walks: int = 10,
              window: int = 5, k: int = EMB_DIM) -> np.ndarray:
    """Sampled DeepWalk: random walks -> PPMI co-occurrence -> truncated SVD.
    Sparse throughout, so it scales to 10^4-10^5 nodes."""
    n = A.shape[0]
    indptr, indices = A.indptr, A.indices
    rows, cols = [], []
    for _ in range(n_walks):
        for start in rng.permutation(n):
            cur = int(start)
            walk = [cur]
            for _ in range(walk_len - 1):
                lo, hi = indptr[cur], indptr[cur + 1]
                if hi == lo:
                    break
                cur = int(indices[rng.integers(lo, hi)])
                walk.append(cur)
            L = len(walk)
            for i in range(L):
                for j in range(i + 1, min(i + window + 1, L)):
                    rows.append(walk[i]); cols.append(walk[j])
                    rows.append(walk[j]); cols.append(walk[i])
    if not rows:
        return np.zeros((n, k))
    C = sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    total = C.sum()
    rowsum = np.asarray(C.sum(1)).ravel() + 1e-12
    colsum = np.asarray(C.sum(0)).ravel() + 1e-12
    C = C.tocoo()
    pmi = np.log(np.maximum(
        (C.data * total) / (rowsum[C.row] * colsum[C.col]), 1.0) + 1e-12)
    M = sp.csr_matrix((pmi, (C.row, C.col)), shape=(n, n))
    kk = min(k, min(M.shape) - 1)
    U, s, _ = spl.svds(M, k=max(1, kk))
    return U * np.sqrt(s)


def _score_deepwalk(A, pairs, rng):
    return _emb_score(_deepwalk(A, rng), pairs, "cosine")


def _score_force(A, pairs, rng, dim: int = 16):
    import networkx as nx
    G = nx.from_scipy_sparse_array(A)
    pos = nx.spring_layout(G, dim=dim, seed=int(rng.integers(0, 2**31 - 1)),
                           iterations=60)
    emb = np.array([pos[i] for i in range(A.shape[0])])
    return _emb_score(emb, pairs, "neg_dist")


def _score_force2d(A, pairs, rng):
    return _score_force(A, pairs, rng, dim=2)


def _score_isomap(A, pairs, rng, k: int = EMB_DIM):
    """Classical MDS on graph geodesics (the core of Isomap). Dense O(n^3)."""
    import networkx as nx
    G = nx.from_scipy_sparse_array(A)
    n = A.shape[0]
    D = np.full((n, n), np.nan)
    for src, dd in nx.all_pairs_shortest_path_length(G):
        for dst, val in dd.items():
            D[src, dst] = val
    finite = D[np.isfinite(D)]
    D = np.where(np.isfinite(D), D, (finite.max() * 2) if finite.size else 1.0)
    J = np.eye(n) - np.ones((n, n)) / n
    B = -0.5 * J @ (D ** 2) @ J
    w, V = np.linalg.eigh(B)
    order = np.argsort(-w)[:k]
    return _emb_score(V[:, order] * np.sqrt(np.maximum(w[order], 0)), pairs, "neg_dist")


@dataclass(frozen=True)
class Representation:
    name: str
    label: str
    fn: Callable
    max_nodes: int
    family: str

    def score(self, A, pairs, rng) -> tuple[np.ndarray, float]:
        t0 = time.perf_counter()
        s = self.fn(A, pairs, rng)
        s = np.nan_to_num(np.asarray(s, dtype=float),
                          nan=0.0, posinf=0.0, neginf=0.0)
        return s, time.perf_counter() - t0


FAST_ONLY = ("random_control", "common_neighbors", "adamic_adar",
             "pref_attachment", "spectral_eigenmap", "deepwalk")

REGISTRY: tuple[Representation, ...] = (
    Representation("random_control", "Random (control)", _score_random, 10**9, "control"),
    Representation("common_neighbors", "Common neighbours", _score_common_neighbors, 200_000, "local"),
    Representation("adamic_adar", "Adamic–Adar", _score_adamic_adar, 200_000, "local"),
    Representation("pref_attachment", "Preferential attachment", _score_pref_attachment, 10**9, "degree"),
    Representation("spectral_eigenmap", "Spectral eigenmap", _score_spectral, 200_000, "spectral"),
    Representation("deepwalk", "DeepWalk (sampled)", _score_deepwalk, 200_000, "random-walk"),
    Representation("force_layout_2d", "Force layout 2D", _score_force2d, 6_000, "layout"),
    Representation("force_layout_16d", "Force layout 16D", _score_force, 6_000, "layout"),
    Representation("isomap_geodesic", "Isomap (geodesic MDS)", _score_isomap, 3_000, "manifold"),
)
