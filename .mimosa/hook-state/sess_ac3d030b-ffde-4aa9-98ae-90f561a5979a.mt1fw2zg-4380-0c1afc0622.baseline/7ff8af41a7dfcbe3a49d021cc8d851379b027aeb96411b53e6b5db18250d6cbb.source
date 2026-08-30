#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_graph.py — CH-03 Vault Graph Scanner.

اسکنر گرافِ والت: همهٔ فایل‌های .md را می‌خواند، wiki-linkهای داخلشان را
استخراج می‌کند، گره‌ها و یال‌ها و گروه‌ها می‌سازد، و graph-data.js را تولید.

Source → Transform → Sink:
  F:/backup/**/*.md  →  extract_graph.py  →  nervous-system/graph-data.js
                                            →  OCTOPUS/worlds/graph-data.js

Rules:
  • stdlib-only
  • Read-only — هیچ mutation در والت
  • Fail-soft — اگر فایل خوانده نشد، رد می‌شود
  • Content-free — هیچ محتوای حساس در خروجی
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── paths ────────────────────────────────────────────────────────────────────
VAULT = Path("F:/backup")
NS_DIR = Path("F:/backup/nervous-system")
OCTOPUS_DIR = Path("F:/backup/OCTOPUS/worlds")

# ─── config ───────────────────────────────────────────────────────────────────
SKIP_DIRS = {
    ".git", ".obsidian", "__pycache__", "node_modules",
    ".pytest_cache", ".claude", ".zcode", "_Archive", "_Duplicates",
}
SKIP_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".mp4", ".webm",
             ".zip", ".tar", ".gz", ".7z", ".exe", ".dll", ".pyc"}
MAX_NODES = 300          # حداکثر گره‌های نمایشی
MIN_DEGREE = 1           # حداقل درجه برای نمایش

# ─── palette (deterministic per group) ────────────────────────────────────────
PALETTE = [
    "#3b82f6", "#ef4444", "#22c55e", "#a855f7", "#f59e0b",
    "#06b6d4", "#ec4899", "#84cc16", "#f97316", "#6366f1",
    "#14b8a6", "#e11d48", "#8b5cf6", "#d946ef", "#0ea5e9",
    "#64748b", "#94a3b8", "#78716c", "#a16207", "#be123c",
]

# ─── helpers ──────────────────────────────────────────────────────────────────
def _group_color(name: str) -> str:
    """رنگِ قطعی برای هر گروه (بر اساس hash نام)."""
    h = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16)
    return PALETTE[h % len(PALETTE)]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ─── wiki-link regex ──────────────────────────────────────────────────────────
WIKI_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
# also capture markdown links [text](path.md) as secondary links
MDLINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")


def _collect_md_files(vault: Path) -> list[Path]:
    """جمع‌آوری همهٔ .md files در والت."""
    files: list[Path] = []
    for root, dirs, filenames in os.walk(vault):
        # prune skipped dirs
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS and not d.startswith(".")
        ]
        for fn in filenames:
            if fn.endswith(".md"):
                files.append(Path(root) / fn)
    return files


def _build_lookup(files: list[Path], vault: Path) -> tuple[dict, dict, dict]:
    """ساختن lookup tables برای resolution.

    Returns:
        rel_no_ext:  "Folder/Note Name"  → Path
        basename:    "Note Name"          → list[Path]
        file_id:     Path                 → int (stable index)
    """
    rel_no_ext: dict[str, Path] = {}
    basename: dict[str, list[Path]] = {}
    file_id: dict[Path, int] = {}

    for idx, p in enumerate(files):
        rel = p.relative_to(vault)
        rel_str = rel.as_posix()
        # without .md
        key = rel_str[:-3] if rel_str.endswith(".md") else rel_str
        rel_no_ext[key] = p
        rel_no_ext[key.lower()] = p

        name = rel.stem
        basename.setdefault(name, []).append(p)
        basename.setdefault(name.lower(), []).append(p)

        file_id[p] = idx

    return rel_no_ext, basename, file_id


def _resolve_link(
    link_target: str,
    source: Path,
    vault: Path,
    rel_no_ext: dict[str, Path],
    basename: dict[str, list[Path]],
) -> Path | None:
    """Resolve یک wiki-link target به Path واقعی.

    Strategy:
      1. exact relative from source folder
      2. exact relative from vault root
      3. basename match anywhere
    """
    # strip anchor (#heading)
    target = link_target.split("#")[0].strip()
    if not target:
        return None

    # Strategy 1: relative to source dir
    source_dir = source.parent.relative_to(vault)
    candidate = (source_dir / target).as_posix()
    if candidate in rel_no_ext:
        return rel_no_ext[candidate]
    if candidate.lower() in rel_no_ext:
        return rel_no_ext[candidate.lower()]

    # Strategy 2: absolute from vault root
    if target in rel_no_ext:
        return rel_no_ext[target]
    if target.lower() in rel_no_ext:
        return rel_no_ext[target.lower()]

    # Strategy 3: basename
    name = Path(target).stem
    if name in basename:
        # prefer same folder if multiple matches
        same_folder = [p for p in basename[name]
                       if p.parent.relative_to(vault) == source_dir]
        if same_folder:
            return same_folder[0]
        return basename[name][0]
    if name.lower() in basename:
        same_folder = [p for p in basename[name.lower()]
                       if p.parent.relative_to(vault) == source_dir]
        if same_folder:
            return same_folder[0]
        return basename[name.lower()][0]

    return None


def _group_of(path: Path, vault: Path) -> str:
    """گروهِ یک فایل = اولین بخشِ مسیر نسبت به والت، یا '(root)'."""
    rel = path.relative_to(vault)
    parts = rel.parts
    if len(parts) <= 1:
        return "(root)"
    top = parts[0]
    # normalize some known roots
    return top


def _build_graph(vault: Path) -> dict[str, Any]:
    """Main graph builder."""
    files = _collect_md_files(vault)
    total_files = len(files)

    rel_no_ext, basename_map, file_id = _build_lookup(files, vault)

    # per-file metadata
    links_out: dict[int, set[int]] = {i: set() for i in range(total_files)}
    group_counter: dict[str, int] = {}
    file_group: dict[int, str] = {}

    for p in files:
        fid = file_id[p]
        grp = _group_of(p, vault)
        file_group[fid] = grp
        group_counter[grp] = group_counter.get(grp, 0) + 1

        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except OSError:
            continue

        # wiki-links
        for m in WIKI_RE.finditer(text):
            target = m.group(1).strip()
            resolved = _resolve_link(target, p, vault, rel_no_ext, basename_map)
            if resolved and resolved in file_id:
                tid = file_id[resolved]
                if tid != fid:
                    links_out[fid].add(tid)

        # markdown links to .md
        for m in MDLINK_RE.finditer(text):
            target = m.group(2).strip()
            resolved = _resolve_link(target, p, vault, rel_no_ext, basename_map)
            if resolved and resolved in file_id:
                tid = file_id[resolved]
                if tid != fid:
                    links_out[fid].add(tid)

    # compute degrees
    degree: dict[int, int] = {}
    for fid, outs in links_out.items():
        degree[fid] = len(outs)

    # also count incoming for more accurate degree
    incoming: dict[int, set[int]] = {i: set() for i in range(total_files)}
    for fid, outs in links_out.items():
        for tid in outs:
            incoming[tid].add(fid)

    total_links = sum(len(s) for s in links_out.values())

    # decide shown nodes: top by degree, but keep at least those with degree >= MIN_DEGREE
    # if there are too many, cap at MAX_NODES
    sorted_by_deg = sorted(range(total_files), key=lambda i: degree.get(i, 0), reverse=True)

    shown_set: set[int] = set()
    for i in sorted_by_deg:
        if len(shown_set) >= MAX_NODES:
            break
        if degree.get(i, 0) >= MIN_DEGREE:
            shown_set.add(i)

    # also include any node that is linked to/from a shown node
    # (so edges don't dangle)
    needed: set[int] = set(shown_set)
    for fid in shown_set:
        for tid in links_out.get(fid, set()):
            needed.add(tid)
        for sid in incoming.get(fid, set()):
            needed.add(sid)

    # build remapping for shown nodes
    shown = sorted(needed)
    idx_map = {old: new for new, old in enumerate(shown)}

    # build nodes
    nodes: list[dict] = []
    for old_idx in shown:
        p = files[old_idx]
        rel = p.relative_to(vault)
        label = rel.stem
        grp = file_group.get(old_idx, "(root)")
        deg = degree.get(old_idx, 0) + len(incoming.get(old_idx, set()))
        nodes.append({
            "l": label,
            "g": grp,
            "d": deg,
            "c": _group_color(grp),
        })

    # build edges (only between shown nodes)
    edges: list[list[int]] = []
    seen_edges: set[tuple[int, int]] = set()
    for old_src in shown:
        for old_dst in links_out.get(old_src, set()):
            if old_dst in idx_map:
                pair = (idx_map[old_src], idx_map[old_dst])
                if pair not in seen_edges:
                    seen_edges.add(pair)
                    edges.append(list(pair))

    # build groups
    group_counts: dict[str, int] = {}
    for old_idx in shown:
        grp = file_group.get(old_idx, "(root)")
        group_counts[grp] = group_counts.get(grp, 0) + 1

    groups = [
        {"name": g, "color": _group_color(g), "n": c}
        for g, c in sorted(group_counts.items(), key=lambda x: -x[1])
    ]

    generated = _now_iso()

    return {
        "generated": generated,
        "source": f"Obsidian vault {vault} — read-only scan",
        "total_files": total_files,
        "total_links": total_links,
        "shown_nodes": len(nodes),
        "shown_edges": len(edges),
        "nodes": nodes,
        "edges": edges,
        "groups": groups,
    }


def _emit_js(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    js = "window.OCTOPUS_GRAPH = " + json.dumps(data, ensure_ascii=False, default=str) + ";\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"graph-data.js written: {path} ({len(js)} chars)")


def main() -> int:
    print("CH-03 Vault Graph Scanner starting...")
    data = _build_graph(VAULT)

    # 1. nervous-system
    _emit_js(data, NS_DIR / "graph-data.js")

    # 2. OCTOPUS worlds
    _emit_js(data, OCTOPUS_DIR / "graph-data.js")

    # summary
    print(f"  total_files={data['total_files']}  total_links={data['total_links']}")
    print(f"  shown_nodes={data['shown_nodes']}  shown_edges={data['shown_edges']}")
    print(f"  groups={len(data['groups'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
