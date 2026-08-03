"""Read-only vault inventory.

Fixes the two defects observed in the 2026-07-31 Octopus manifest:

1. ``.claude`` was not excluded, so 49,939 of the 50,000-file budget was spent
   inside it and **no real note folder was ever reached**. Agent/tooling dirs
   are now excluded by default and every exclusion hit is counted and reported.
2. The 50k cap was silent — the report claimed a vault-wide picture it did not
   have. Here the cap is opt-in, breadth-first (so every top-level folder is
   sampled before the budget runs out), and ``cap_hit`` is surfaced loudly.

This module never opens a file for writing. It reads bytes only.
"""

from __future__ import annotations

import os
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from ...kernel.types import ScanReport

__all__ = ["DEFAULT_EXCLUDES", "scan_vault"]

#: Directory names skipped by default. The first block is what the original
#: Octopus scanner already had; the second block is what it was missing.
DEFAULT_EXCLUDES: frozenset[str] = frozenset({
    # original octopus excludes
    ".cache", ".env", ".git", ".idea", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".venv", ".vscode", "__pycache__", "build",
    "dist", "env", "node_modules", "venv",
    # MISSING in the original scan — this is what ate the 50k budget
    ".claude", ".claude-server-commander", ".cursor", ".copilot", ".kimi-code",
    ".kimi-webbridge", ".kimi-work", ".zcode", ".obsidian", ".trash",
    ".ollama", ".streamlit", ".android", ".n8n", "_worktrees",
    "site-packages", "Lib", "Scripts", ".ipynb_checkpoints", ".github",
})


def _iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def scan_vault(
    root: str | os.PathLike[str],
    *,
    excludes: frozenset[str] | None = None,
    max_files: int | None = None,
    max_note_mb: float = 4.0,
    follow_symlinks: bool = False,
) -> tuple[ScanReport, list[Path]]:
    """Walk ``root`` breadth-first and return (report, markdown paths).

    Breadth-first matters: if a cap is ever hit, the sample is spread across the
    vault instead of being swallowed by whichever deep folder happened to sort
    first. That is precisely the failure mode of the original scan.
    """
    started = time.perf_counter()
    root_p = Path(root).expanduser().resolve(strict=False)
    if not root_p.is_dir():
        raise NotADirectoryError(f"vault root not found: {root_p}")

    ex = DEFAULT_EXCLUDES if excludes is None else excludes
    max_bytes = int(max_note_mb * 1024 * 1024)

    md_paths: list[Path] = []
    excluded_hits: dict[str, int] = {}
    skipped_large: list[str] = []
    unreadable: list[str] = []
    per_top: dict[str, int] = {}
    n_dirs = n_files = md_bytes = 0
    cap_hit = False

    queue: deque[Path] = deque([root_p])
    while queue:
        d = queue.popleft()
        n_dirs += 1
        try:
            entries = list(os.scandir(d))
        except OSError as exc:                        # unreadable dir → record, continue
            unreadable.append(f"{d}: {exc.__class__.__name__}")
            continue

        for e in entries:
            try:
                is_dir = e.is_dir(follow_symlinks=follow_symlinks)
            except OSError:
                unreadable.append(str(e.path))
                continue
            if is_dir:
                if e.name in ex or (e.name.startswith(".") and e.name not in {".", ".."}):
                    excluded_hits[e.name] = excluded_hits.get(e.name, 0) + 1
                    continue
                queue.append(Path(e.path))
                continue

            n_files += 1
            if not e.name.lower().endswith(".md"):
                continue
            try:
                st = e.stat()
            except OSError:
                unreadable.append(e.path)
                continue
            if st.st_size > max_bytes:
                skipped_large.append(os.path.relpath(e.path, root_p))
                continue

            md_paths.append(Path(e.path))
            md_bytes += st.st_size
            rel = os.path.relpath(e.path, root_p).replace("\\", "/")
            top = rel.split("/")[0] if "/" in rel else "(root)"
            per_top[top] = per_top.get(top, 0) + 1

            if max_files is not None and len(md_paths) >= max_files:
                cap_hit = True
                queue.clear()
                break

    warnings: list[str] = []
    if cap_hit:
        warnings.append(
            f"CAP HIT at {max_files} markdown files — this inventory is INCOMPLETE. "
            f"Re-run without --max-files for a full picture."
        )
    if not md_paths:
        warnings.append("no markdown files found — check the root path and excludes")
    dominant = max(per_top.items(), key=lambda kv: kv[1], default=None)
    if dominant and len(md_paths) and dominant[1] / len(md_paths) > 0.80:
        warnings.append(
            f"{dominant[1]/len(md_paths):.0%} of all markdown sits in '{dominant[0]}' — "
            f"if that folder is tooling rather than notes, add it to --exclude."
        )

    report = ScanReport(
        root=str(root_p),
        scanned_at=_iso_now(),
        elapsed_s=round(time.perf_counter() - started, 3),
        n_dirs_walked=n_dirs,
        n_files_seen=n_files,
        n_markdown=len(md_paths),
        bytes_markdown=md_bytes,
        excluded_dirs=sorted(ex),
        excluded_hits=dict(sorted(excluded_hits.items(), key=lambda kv: -kv[1])),
        skipped_too_large=skipped_large[:200],
        unreadable=unreadable[:200],
        cap_hit=cap_hit,
        per_top_folder=dict(sorted(per_top.items(), key=lambda kv: -kv[1])),
        warnings=warnings,
    )
    return report, md_paths
