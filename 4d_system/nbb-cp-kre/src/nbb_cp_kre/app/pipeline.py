"""Orchestration — the ONE place the whole thing runs, mirroring nbb_cp's
single-choke-point discipline (INV-4).

Every filesystem write in this package goes through :class:`ReadOnlyGuard`.
The vault root is registered as protected before anything else happens, so a
write into it raises rather than succeeding quietly (fail closed, INV-12).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from ..adapters.kre.bakeoff import run_bakeoff
from ..adapters.kre.missing_links import propose_missing_links
from ..adapters.vault.linkgraph import build_link_graph
from ..adapters.vault.scanner import DEFAULT_EXCLUDES, scan_vault
from ..kernel.guard import ReadOnlyGuard
from ..kernel.types import PipelineResult

__all__ = ["run_pipeline", "load_result"]

SCHEMA_VERSION = 1


def _summarise_graph(graph, notes) -> dict:
    deg = graph.degree()
    n = graph.n
    isolated = sum(1 for d in deg if d == 0)
    import statistics as st
    top = sorted(range(n), key=lambda i: -deg[i])[:15]
    folders: dict[str, int] = {}
    for nt in notes:
        top_folder = nt.rel_path.split("/")[0] if "/" in nt.rel_path else "(root)"
        folders[top_folder] = folders.get(top_folder, 0) + 1
    return {
        "n_nodes": n,
        "n_edges": graph.m,
        "avg_degree": round(2 * graph.m / n, 3) if n else 0.0,
        "median_degree": st.median(deg) if deg else 0,
        "isolated_notes": isolated,
        "isolated_pct": round(isolated / n, 4) if n else 0.0,
        "broken_links": len(graph.broken),
        "ambiguous_links": len(graph.ambiguous),
        "resolution": graph.resolution_stats,
        "fingerprint": graph.fingerprint(),
        "hubs": [{"note": graph.nodes[i], "degree": deg[i]} for i in top],
        "notes_per_top_folder": dict(sorted(folders.items(), key=lambda kv: -kv[1])),
    }


def run_pipeline(
    vault_root: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    *,
    seeds: list[int] | None = None,
    test_frac: float = 0.20,
    top_k: int = 40,
    max_files: int | None = None,
    extra_excludes: frozenset[str] | None = None,
    include_embeds: bool = True,
    run_competition: bool = True,
    quick: bool = False,
    progress=None,
) -> PipelineResult:
    guard = ReadOnlyGuard([vault_root])
    out = guard.assert_out_dir(out_dir)          # raises if out_dir is inside the vault

    excludes = DEFAULT_EXCLUDES | (extra_excludes or frozenset())

    if progress:
        progress(0.05, "scanning vault (read-only)…")
    report, md_paths = scan_vault(vault_root, excludes=excludes, max_files=max_files)

    if progress:
        progress(0.25, f"parsing {len(md_paths):,} notes…")
    graph, notes = build_link_graph(md_paths, vault_root, include_embeds=include_embeds)
    gsum = _summarise_graph(graph, notes)

    bake = None
    proposals = []
    if run_competition:
        if progress:
            progress(0.45, "running representation competition…")
        from ..adapters.kre.representations import FAST_ONLY, REGISTRY
        reps = tuple(r for r in REGISTRY if r.name in FAST_ONLY) if quick else REGISTRY
        bake = run_bakeoff(
            graph, seeds=seeds, test_frac=test_frac, representations=reps,
            progress=(lambda f, m: progress(0.45 + 0.4 * f, m)) if progress else None,
        )
        if bake.winner and bake.control_ok:
            if progress:
                progress(0.90, "ranking missing links…")
            proposals = propose_missing_links(graph, bake.winner, top_k=top_k)

    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y%m%dT%H%M%S")
    artifacts: dict[str, str] = {}

    def _write(name: str, payload) -> None:
        p = out / name
        with guard.open_write(p) as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2, default=str)
        artifacts[name.split(".")[0]] = str(p)

    _write(f"scan_{stamp}.json", {"schema_version": SCHEMA_VERSION, **report.to_dict()})
    _write(f"graph_{stamp}.json", {
        "schema_version": SCHEMA_VERSION,
        "summary": gsum,
        "nodes": graph.nodes,
        "edges": graph.edges,
        "broken_sample": graph.broken[:200],
        "ambiguous_sample": graph.ambiguous[:200],
    })
    if bake:
        _write(f"bakeoff_{stamp}.json", {"schema_version": SCHEMA_VERSION, **bake.to_dict()})
    _write(f"proposals_{stamp}.json", {
        "schema_version": SCHEMA_VERSION,
        "status": "PROPOSED — no vault file was or will be modified without your verdict",
        "representation": bake.winner if bake else None,
        "proposals": [asdict(p) for p in proposals],
    })
    # latest.json is what the dashboard reads
    _write("latest.json", {
        "schema_version": SCHEMA_VERSION, "stamp": stamp,
        "vault_root": str(Path(vault_root).resolve()),
        "scan": report.to_dict(), "graph": gsum,
        "bakeoff": bake.to_dict() if bake else None,
        "proposals": [asdict(p) for p in proposals],
    })

    if progress:
        progress(1.0, "done")
    return PipelineResult(scan=report, graph_summary=gsum, bakeoff=bake,
                          proposals=proposals, out_dir=str(out), artifacts=artifacts)


def load_result(out_dir: str | os.PathLike[str]) -> dict | None:
    p = Path(out_dir) / "latest.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))
