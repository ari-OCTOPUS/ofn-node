"""Obsidian-accurate link extraction and resolution.

Validated against real notes from this vault, which use **full vault-relative
targets with aliases**:

    [[07 - Knowledge/AUTHORITY-TREE-doctrine-v1|AUTHORITY-TREE-doctrine-v1]]

A naive ``basename()`` parser silently merges every ``INDEX``/``HANDOFF``/
``README``/``MAP`` across folders into one node, which fabricates edges that do
not exist. Resolution order below mirrors Obsidian:

1. exact vault-relative path
2. path relative to the linking note's own folder
3. unique basename anywhere in the vault
4. ambiguous basename → shortest path wins, and the ambiguity is *recorded*

Reads only. Note bodies are wrapped in :class:`QuarantinedText` (INV-9) so they
can never be handed to a model as instructions.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import unquote

from ...kernel.types import LinkGraph, Note, QuarantinedText

__all__ = ["parse_note", "build_link_graph", "WIKILINK_RE", "EMBED_RE", "MDLINK_RE"]

WIKILINK_RE = re.compile(r"(?<!!)\[\[([^\[\]]+?)\]\]")
EMBED_RE = re.compile(r"!\[\[([^\[\]]+?)\]\]")
MDLINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(<?([^)<>\s]+?)>?\)")
FRONTMATTER_RE = re.compile(r"\A﻿?---\r?\n(.*?)\r?\n---\s*?\r?\n", re.S)
INLINE_TAG_RE = re.compile(r"(?:^|[\s(])#([A-Za-z؀-ۿ][\w/؀-ۿ-]{1,40})")
CODE_FENCE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.S)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def _norm(p: str) -> str:
    return p.replace("\\", "/").strip().lstrip("./").lower()


def _strip_target(raw: str) -> str:
    """`path/note#heading^block|alias` -> `path/note` (lowercased, .md stripped)."""
    t = raw.split("|", 1)[0]
    t = t.split("#", 1)[0]
    t = t.split("^", 1)[0]
    t = unquote(t).strip()
    if t.lower().endswith(".md"):
        t = t[:-3]
    return _norm(t)


def _parse_frontmatter(text: str) -> tuple[dict[str, str], list[str], str]:
    """Return (scalars, tags, body_without_frontmatter). Deliberately a tiny
    line parser — no PyYAML dependency, and malformed frontmatter degrades to
    'no metadata' rather than raising (fail closed, keep scanning)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, [], text
    scalars: dict[str, str] = {}
    tags: list[str] = []
    current_list: str | None = None
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        if line.lstrip().startswith("- ") and current_list:
            if current_list == "tags":
                tags.append(line.lstrip()[2:].strip().strip("\"'"))
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k = k.strip().lower()
        v = v.strip()
        current_list = k if v == "" else None
        if k == "tags":
            if v.startswith("[") and v.endswith("]"):
                tags += [t.strip().strip("\"'") for t in v[1:-1].split(",") if t.strip()]
            elif v:
                tags += [t.strip() for t in re.split(r"[,\s]+", v) if t.strip()]
        elif v:
            scalars[k] = v.strip("\"'")
    return scalars, [t for t in tags if t], text[m.end():]


def parse_note(path: Path, root: Path) -> tuple[Note, list[str], list[str]]:
    """Return (note, wikilink_targets, embed_targets). Never writes."""
    rel = os.path.relpath(path, root).replace("\\", "/")
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        raw = ""
    scalars, fm_tags, body = _parse_frontmatter(raw)

    quarantined = QuarantinedText(body, source=rel)
    text = quarantined.unwrap_for_parsing()
    # code blocks are not links
    text = INLINE_CODE_RE.sub(" ", CODE_FENCE_RE.sub(" ", text))

    embeds = [_strip_target(t) for t in EMBED_RE.findall(text)]
    wiki = [_strip_target(t) for t in WIKILINK_RE.findall(text)]
    md = [_strip_target(t) for t in MDLINK_RE.findall(text)
          if not re.match(r"^[a-z][a-z0-9+.-]*://", t, re.I)]

    tags = sorted({*fm_tags, *INLINE_TAG_RE.findall(text)})
    try:
        st = path.stat()
        size, mtime, ctime = st.st_size, st.st_mtime, st.st_ctime
    except OSError:
        size = mtime = ctime = 0

    note = Note(
        rel_path=rel,
        stem=Path(rel).stem,
        folder=("" if Path(rel).parent == Path(".")
                else str(Path(rel).parent).replace("\\", "/")),
        depth=rel.count("/"),
        size_bytes=size,
        mtime=mtime,
        ctime=ctime,
        n_chars=len(body),
        n_words=len(body.split()),
        fm_type=scalars.get("type"),
        fm_status=scalars.get("status"),
        tags=tags[:40],
    )
    return note, [t for t in wiki + md if t], [t for t in embeds if t]


def build_link_graph(
    md_paths: list[Path],
    root: str | os.PathLike[str],
    *,
    include_embeds: bool = True,
) -> tuple[LinkGraph, list[Note]]:
    root_p = Path(root).expanduser().resolve(strict=False)

    notes: list[Note] = []
    raw_links: list[tuple[str, str]] = []
    for p in md_paths:
        note, links, embeds = parse_note(p, root_p)
        notes.append(note)
        src = _norm(note.rel_path)
        for t in links:
            raw_links.append((src, t))
        if include_embeds:
            for t in embeds:
                raw_links.append((src, t))

    notes.sort(key=lambda n: n.rel_path.lower())
    keys = [_norm(n.rel_path) for n in notes]
    idx = {k: i for i, k in enumerate(keys)}
    # path without the .md suffix — that is what a wikilink target looks like
    noext = {k[:-3] if k.endswith(".md") else k: i for k, i in idx.items()}

    by_stem: dict[str, list[int]] = {}
    for i, n in enumerate(notes):
        by_stem.setdefault(n.stem.lower(), []).append(i)

    stats = {"exact": 0, "relative": 0, "unique_stem": 0, "ambiguous": 0, "broken": 0}
    directed: set[tuple[int, int]] = set()
    broken: list[tuple[str, str]] = []
    ambiguous: list[tuple[str, str, int]] = []

    for src, target in raw_links:
        s = idx.get(src)
        if s is None:
            continue
        hit: int | None = None

        if target in noext:                                   # 1. exact
            hit = noext[target]
            stats["exact"] += 1
        else:
            src_dir = os.path.dirname(src)
            cand = _norm(os.path.normpath(os.path.join(src_dir, target))) if src_dir else target
            if cand in noext:                                 # 2. relative to source
                hit = noext[cand]
                stats["relative"] += 1
            else:
                pool = by_stem.get(os.path.basename(target), [])
                if len(pool) == 1:                            # 3. unique basename
                    hit = pool[0]
                    stats["unique_stem"] += 1
                elif len(pool) > 1:                           # 4. ambiguous
                    hit = min(pool, key=lambda i: (notes[i].depth, len(notes[i].rel_path)))
                    stats["ambiguous"] += 1
                    ambiguous.append((notes[s].rel_path, target, len(pool)))

        if hit is None:
            stats["broken"] += 1
            broken.append((notes[s].rel_path, target))
        elif hit != s:
            directed.add((s, hit))

    undirected = sorted({(min(a, b), max(a, b)) for a, b in directed})
    graph = LinkGraph(
        nodes=[n.rel_path for n in notes],
        edges=undirected,
        directed=sorted(directed),
        broken=broken[:500],
        ambiguous=ambiguous[:500],
        resolution_stats=stats,
    )
    return graph, notes
