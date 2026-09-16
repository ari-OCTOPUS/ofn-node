"""Live pipeline wrapper — fingerprint-keyed cache + read-only note bodies.

This is the v0.2 "live" extension of :mod:`nbb_cp_kre.app.pipeline`. It adds two
things the dashboard needs to feel alive, without touching the kernel or the
existing pipeline:

1. **Cache by graph fingerprint.** Building the link graph + running the
   representation bakeoff is the expensive part (minutes on a real vault). The
   fingerprint of the *graph* (not the files) changes only when a wikilink is
   added/removed/renamed — a typo fix in a note body does not move it. So we
   cache the heavy ``bakeoff``/``proposals`` artifacts keyed on that fingerprint
   and skip recomputing them when they would be identical.

2. **Read-only note bodies.** ``read_note_body`` opens a single vault note for
   *reading* only, quarantined through :class:`QuarantinedText` exactly as the
   link parser does (INV-9). The dashboard's "click a node → see its content"
   feature goes through here, so vault text is never treated as trusted.

The cache is written next to the other artifacts in the OUTPUT directory, never
inside the vault (enforced by the same :class:`ReadOnlyGuard`).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from ..adapters.vault.scanner import DEFAULT_EXCLUDES, scan_vault
from ..adapters.vault.linkgraph import build_link_graph
from ..kernel.guard import ReadOnlyGuard, ReadOnlyViolation
from ..kernel.types import QuarantinedText
from .pipeline import run_pipeline, load_result, _summarise_graph

__all__ = [
    "run_live",
    "current_fingerprint",
    "read_note_body",
    "load_cache",
    "CACHE_VERSION",
]

CACHE_VERSION = 2


def _cache_path(out_dir: Path, fingerprint: str) -> Path:
    return out_dir / f"cache_{fingerprint}.json"


def current_fingerprint(
    vault_root: str | os.PathLike[str],
    *,
    extra_excludes: frozenset[str] | None = None,
    include_embeds: bool = True,
) -> str | None:
    """Compute the graph fingerprint without writing anything.

    Returns ``None`` if the vault has no notes. This is the cheap probe the
    dashboard uses to answer "did the *link structure* actually change, or did
    someone just edit prose?" before deciding whether to re-run the bakeoff.
    """
    excludes = DEFAULT_EXCLUDES | (extra_excludes or frozenset())
    try:
        _report, md_paths = scan_vault(vault_root, excludes=excludes)
        if not md_paths:
            return None
        graph, _notes = build_link_graph(md_paths, vault_root, include_embeds=include_embeds)
        return graph.fingerprint()
    except Exception:
        return None


def load_cache(out_dir: str | os.PathLike[str], fingerprint: str) -> dict | None:
    """Return the cached bakeoff+proposals for this fingerprint, or None."""
    p = _cache_path(Path(out_dir), fingerprint)
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("cache_version") != CACHE_VERSION:
            return None
        return d
    except (OSError, ValueError):
        return None


def run_live(
    vault_root: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    *,
    seeds: list[int] | None = None,
    test_frac: float = 0.20,
    top_k: int = 40,
    extra_excludes: frozenset[str] | None = None,
    include_embeds: bool = True,
    quick: bool = False,
    force: bool = False,
    progress: Callable[[float, str], None] | None = None,
) -> dict:
    """Run the pipeline, reusing the heavy bakeoff when the graph is unchanged.

    Always refreshes ``scan`` + ``graph`` (cheap, <1 s + a few seconds on a big
    vault) so the dashboard reflects the live vault, and reuses the expensive
    ``bakeoff``/``proposals`` artifacts when the link fingerprint matches the
    last run.

    Returns the same ``latest.json`` shape :func:`load_result` produces, so the
    dashboard code path is unchanged.
    """
    guard = ReadOnlyGuard([vault_root])
    out = guard.assert_out_dir(out_dir)
    excludes = DEFAULT_EXCLUDES | (extra_excludes or frozenset())

    def _p(f: float, m: str) -> None:
        if progress:
            progress(f, m)

    _p(0.05, "اسکنِ زندهٔ vault (فقط خواندن)…")
    report, md_paths = scan_vault(vault_root, excludes=excludes)
    _p(0.20, f"پیمایش {len(md_paths):,} نوت…")
    graph, notes = build_link_graph(md_paths, vault_root, include_embeds=include_embeds)
    gsum = _summarise_graph(graph, notes)
    fp = graph.fingerprint()

    # --- the expensive part: reuse if the graph structure is identical --------
    cached = None if force else load_cache(out, fp)
    bake = None
    proposals: list = []
    if cached is not None:
        bake = cached.get("bakeoff")
        proposals = cached.get("proposals", [])
        _p(0.80, f"گراف همان است (fingerprint {fp}) — bakeoff از کش")
    else:
        if progress:
            _p(0.40, "اجرای مسابقهٔ نمایش‌ها…")
        from ..adapters.kre.representations import FAST_ONLY, REGISTRY
        from ..adapters.kre.bakeoff import run_bakeoff
        from ..adapters.kre.missing_links import propose_missing_links
        reps = tuple(r for r in REGISTRY if r.name in FAST_ONLY) if quick else REGISTRY
        bake = run_bakeoff(
            graph, seeds=seeds, test_frac=test_frac, representations=reps,
            progress=(lambda f, m: _p(0.40 + 0.40 * f, m)) if progress else None,
        ).to_dict()
        if bake.get("winner") and bake.get("control_ok"):
            _p(0.90, "رتبه‌بندیِ لینک‌های گم‌شده…")
            props = propose_missing_links(graph, bake["winner"], top_k=top_k)
            proposals = [asdict(p) for p in props]
        # persist the cache for next time (OUTSIDE the vault)
        try:
            with guard.open_write(_cache_path(out, fp)) as fh:
                json.dump({
                    "cache_version": CACHE_VERSION,
                    "fingerprint": fp,
                    "n_nodes": graph.n,
                    "n_edges": graph.m,
                    "bakeoff": bake,
                    "proposals": proposals,
                }, fh, ensure_ascii=False, indent=2, default=str)
        except (ReadOnlyViolation, OSError):
            pass

    # --- write latest.json + the per-stamp artifacts (same shape as pipeline) -
    from datetime import datetime, timezone
    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y%m%dT%H%M%S")
    artifacts: dict[str, str] = {}

    def _write(name: str, payload) -> None:
        p = out / name
        try:
            with guard.open_write(p) as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2, default=str)
            artifacts[name.split(".")[0]] = str(p)
        except (ReadOnlyViolation, OSError):
            pass

    _write(f"scan_{stamp}.json", {"schema_version": 1, **report.to_dict()})
    _write(f"graph_{stamp}.json", {
        "schema_version": 1,
        "summary": gsum,
        "nodes": graph.nodes,
        "edges": graph.edges,
        "broken_sample": graph.broken[:200],
        "ambiguous_sample": graph.ambiguous[:200],
    })
    if bake:
        _write(f"bakeoff_{stamp}.json", {"schema_version": 1, **bake})
    _write(f"proposals_{stamp}.json", {
        "schema_version": 1,
        "status": "PROPOSED — no vault file was or will be modified without your verdict",
        "representation": bake.get("winner") if bake else None,
        "proposals": proposals,
    })
    latest = {
        "schema_version": 1, "stamp": stamp,
        "vault_root": str(Path(vault_root).resolve()),
        "scan": report.to_dict(), "graph": gsum,
        "bakeoff": bake, "proposals": proposals,
        "fingerprint": fp, "from_cache": cached is not None,
    }
    _write("latest.json", latest)
    _p(1.0, "اتمام")
    return latest


def read_note_body(
    vault_root: str | os.PathLike[str], rel_path: str, *, max_chars: int = 20000
) -> QuarantinedText:
    """Open ONE vault note for reading, wrapped as untrusted text (INV-9).

    The dashboard calls this when the user clicks a node. ``str()`` on the
    result shows the delimited form; the raw body is only reachable via the
    explicit ``unwrap_for_parsing()`` the link parser uses. We never write, so
    no guard is needed for reads (the guard gates writes only).
    """
    root = Path(vault_root).resolve()
    p = (root / rel_path.lstrip("\\/")).resolve(strict=False)
    # belt-and-suspenders: refuse anything that escaped the vault root. Compare
    # the RESOLVED path (after ".." expansion), not the raw joined path, or a
    # "../escape.md" would sneak past because the unexpanded form nominally sits
    # beneath root.
    try:
        p.relative_to(root)
    except ValueError as exc:
        raise ReadOnlyViolation(f"refusing to read outside vault root: {p}") from exc
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return QuarantinedText(_body=f"(unreadable: {exc})", source=rel_path)
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n… [truncated at {max_chars:,} chars]"
    return QuarantinedText(_body=text, source=rel_path)
