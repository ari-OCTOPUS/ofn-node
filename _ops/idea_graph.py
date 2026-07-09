#!/usr/bin/env python3
"""idea_graph.py — موتورِ ایده-گراف: ارتباطِ پروژه‌ها/ایده‌ها از محتوای واقعیِ vault.

یک walker که فایل‌های markdownِ vault را می‌خواند و گرافِ ارتباطِ ایده‌ها را از دو لایه
می‌سازد: (۱) frontmatter (type/project/status/tags + کلیدهای رابطه‌ای parent/aligns_to/
extends/sources)، و (۲) wikilink‌های بدنه [[target|alias]].

تحلیل‌ها (propose-only مطلق): هاب‌ها (مرکزی‌ترین)، خوشه‌ها (by tags)، پل‌ها (idea-bridge)،
یال‌های پیشنهادی (tag‌های مشترک ولی بدونِ یال → human-append).

خطوطِ قرمز: فقط خواندن/تحلیل؛ هیچ effector؛ هیچ auto-merge؛ stdlib-only؛ $0 آفلاین.
هیچ import از *_gate/chrono/money production. منبعِ حقیقتِ گراف = خودِ vault، نه یک
tableِ موازی (گراف یک نمایِ فقط‌خواندنی است، نه source-of-truth).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# الگوی wikilink — هم‌سان با find_broken_links.py (بدونِ کاراکترهای # ^ | به‌عنوانِ id)
WIKILINK_RE = re.compile(r"\[\[([^\]\|#\^]+?)(?:[#\^][^\]\|]*)?(?:\|[^\]]*)?\]\]")

# کلیدهای رابطه‌ای frontmatter → label یال
RELATION_KEYS = {
    "project": "belongs-to",
    "parent": "child-of",
    "aligns_to": "aligns-to",
    "extends": "extends",
    "supersedes": "supersedes",
    "superseded_by": "superseded-by",
    "sources": "cites",
    "related": "related",
}

# پوشه‌های منبع (طبقِ انتخابِ «جامع»)
SOURCE_DIRS = ("03 - Projects", "07 - Knowledge", "00 - Inbox", "04 - Architect System")

# پوشه‌های حذفی (نباید پیمایش شوند)
EXCLUDE_DIRS = {".git", ".obsidian", "_Archive", "_Duplicates", "_backups",
                "ledger", "_doctor-research"}


# ════════════════════════════════════════════════════════════════════════════════
# Data classes
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class IdeaNode:
    """یک نوت در گرافِ ایده‌ها."""
    note_id: str           # مسیرِ نسبیِ نرمالایز (بدونِ پسوند)
    title: str             # عنوانِ H1 یا basename
    type: str = ""         # از frontmatter (project/knowledge/log/...)
    status: str = ""       # از frontmatter (active/idea/done/...)
    tags: list = field(default_factory=list)
    folder: str = ""       # پوشهٔ سطحِ بالا (03-Projects/07-Knowledge/...)


@dataclass
class IdeaEdge:
    """یک یالِ جهت‌دار بین دو نوت."""
    src: str               # note_id مبدأ
    dst: str               # note_id مقصد
    label: str = "references"   # references/belongs-to/aligns-to/extends/cites/...
    weight: float = 0.5


# ════════════════════════════════════════════════════════════════════════════════
# Parser — frontmatter (YAML سبک) + wikilinks
# ════════════════════════════════════════════════════════════════════════════════

def _normalize_id(rel_path: str) -> str:
    """مسیرِ نسبی را به note_id نرمالایز کن (حذفِ پسوند، جایگزینیِ \\ با /)."""
    p = rel_path.replace("\\", "/")
    for ext in (".md", ".markdown"):
        if p.lower().endswith(ext):
            p = p[: -len(ext)]
            break
    return p


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """frontmatter سادهٔ YAML را پارس کن. خروجی: (meta, body).
    فقط خطِ `key: value` و `key: [a, b]` و `key: "[[...]]"` را پشتیبانی می‌کند.
    اگر frontmatter نباشد → ({}, text)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    yaml_block = parts[1].strip()
    body = parts[2]
    meta = {}
    for line in yaml_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        # list: [a, b]
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
            meta[key] = items
        else:
            meta[key] = val
    return meta, body


def _extract_title(body: str, note_id: str) -> str:
    """عنوان: اولین H1، یا آخرین بخشِ note_id."""
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()[:120]
    return note_id.rsplit("/", 1)[-1]


def _resolve_target(target: str, nodes_by_basename: dict, nodes_by_id: dict) -> str | None:
    """یک targetِ wikilink را به note_id واقعی resolve کن.
    تطابق: (۱) مسیرِ نسبیِ کامل، (۲) basename، (۳) basename بدونِ فاصله."""
    t = target.strip()
    if not t:
        return None
    # ۱) مسیرِ کامل
    nid = _normalize_id(t)
    if nid in nodes_by_id:
        return nid
    # ۲) basename (نوت‌ها اغلب با basename لینک می‌شوند)
    base = t.rsplit("/", 1)[-1]
    if base in nodes_by_basename:
        return nodes_by_basename[base]
    # ۳) basename بدونِ فاصله (تطبیقِ آسان)
    base_nospace = base.replace(" ", "")
    for bn, nid_full in nodes_by_basename.items():
        if bn.replace(" ", "") == base_nospace:
            return nid_full
    return None  # یالِ شکسته (broken) — گزارش می‌شود ولی گراف را نمی‌شکند


# ════════════════════════════════════════════════════════════════════════════════
# IdeaGraph — گراف + تحلیل
# ════════════════════════════════════════════════════════════════════════════════

class IdeaGraph:
    """گرافِ ارتباطِ ایده‌ها از محتوای vault. فقط خواندن/تحلیل/پیشنهاد."""

    def __init__(self):
        self.nodes: dict[str, IdeaNode] = {}
        self.edges: list[IdeaEdge] = []
        self.broken_targets: list[str] = []   # wikilink‌هایی که resolve نشدند

    @property
    def n_nodes(self) -> int:
        return len(self.nodes)

    @property
    def n_edges(self) -> int:
        return len(self.edges)

    def build(self, vault_root, source_dirs=None, max_files: int = 800) -> dict:
        """گراف را از vault بساز/به‌روز کن. خروجی: {n_nodes, n_edges, n_broken, scanned}."""
        root = Path(vault_root)
        dirs = source_dirs or SOURCE_DIRS
        # ۱) فایل‌های markdown را پیدا کن
        md_files = []
        for d in dirs:
            dp = root / d
            if not dp.exists():
                continue
            for p in dp.rglob("*.md"):
                # حذفیات
                if any(part in EXCLUDE_DIRS for part in p.parts):
                    continue
                md_files.append(p)
                if len(md_files) >= max_files:
                    break
            if len(md_files) >= max_files:
                break
        # ۲) همهٔ نوت‌ها را اول پارس کن (برای resolve)
        nodes_by_id: dict[str, IdeaNode] = {}
        nodes_by_basename: dict[str, str] = {}
        file_meta: list[tuple[Path, dict, str]] = []
        for p in md_files:
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = str(p.relative_to(root))
            nid = _normalize_id(rel)
            meta, body = _parse_frontmatter(text)
            title = _extract_title(body, nid)
            folder = rel.split("/", 1)[0] if "/" in rel else ""
            tags = meta.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            node = IdeaNode(note_id=nid, title=title,
                            type=str(meta.get("type", "")),
                            status=str(meta.get("status", "")),
                            tags=list(tags), folder=folder)
            nodes_by_id[nid] = node
            basename = p.stem
            nodes_by_basename[basename] = nid
            file_meta.append((p, meta, body))
        self.nodes = nodes_by_id
        self.nodes_by_basename = nodes_by_basename
        # ۳) یال‌ها را بساز
        self.edges = []
        self.broken_targets = []
        seen_edges = set()   # (src, dst, label) برای حذفِ دوبلیکت
        for p, meta, body in file_meta:
            rel = str(p.relative_to(root))
            src = _normalize_id(rel)
            # ۳a) یال‌های frontmatter
            for key, label in RELATION_KEYS.items():
                if key not in meta:
                    continue
                val = meta[key]
                if isinstance(val, list):
                    targets = val
                else:
                    targets = [val]
                for t in targets:
                    tgt_id = self._resolve_wikilink_value(str(t))
                    if tgt_id and (src, tgt_id, label) not in seen_edges:
                        self.edges.append(IdeaEdge(src, tgt_id, label, 1.0))
                        seen_edges.add((src, tgt_id, label))
            # ۳b) یال‌های wikilink بدنه
            for m in WIKILINK_RE.finditer(body):
                target = m.group(1).strip()
                tgt_id = _resolve_target(target, nodes_by_basename, nodes_by_id)
                if tgt_id is None:
                    self.broken_targets.append(target)
                    continue
                if (src, tgt_id, "references") not in seen_edges:
                    self.edges.append(IdeaEdge(src, tgt_id, "references", 0.5))
                    seen_edges.add((src, tgt_id, "references"))
        return {"n_nodes": self.n_nodes, "n_edges": self.n_edges,
                "n_broken": len(self.broken_targets), "scanned": len(md_files)}

    def _resolve_wikilink_value(self, val: str) -> str | None:
        """یک مقدارِ wikilink در frontmatter (مثلاً [[...]]) را به note_id resolve کن."""
        m = WIKILINK_RE.search(val)
        if m:
            target = m.group(1).strip()
            return _resolve_target(target, self.nodes_by_basename, self.nodes)
        # اگر wikilink نیست، آن را به‌عنوانِ مسیرِ نسبی امتحان کن
        return _resolve_target(val, self.nodes_by_basename, self.nodes)

    # ─── تحلیل‌ها (propose-only) ──────────────────────────────────────────────────

    def in_degree(self) -> dict[str, int]:
        """in-degree هر نوت = چند یال به آن اشاره می‌کند."""
        deg = {nid: 0 for nid in self.nodes}
        for e in self.edges:
            if e.dst in deg:
                deg[e.dst] += 1
        return deg

    def hubs(self, top_k: int = 10) -> list[tuple[str, int]]:
        """هاب‌ها: نوت‌هایی با بیشترین in-degree (مرکزی‌ترین ایده‌ها)."""
        deg = self.in_degree()
        return sorted(deg.items(), key=lambda x: -x[1])[:top_k]

    def clusters_by_tags(self) -> dict[str, list[str]]:
        """خوشه‌ها بر اساسِ tag: {tag: [note_id, ...]}."""
        clusters: dict[str, list[str]] = {}
        for nid, node in self.nodes.items():
            for tag in node.tags:
                clusters.setdefault(tag.strip().lower(), []).append(nid)
        # فقط خوشه‌های با ≥۲ عضو
        return {t: ns for t, ns in clusters.items() if len(ns) >= 2}

    def bridges(self) -> list[str]:
        """پل‌ها: نوت‌هایی که با tag در ≥۲ خوشه هستند (idea-bridge)."""
        cluster_count: dict[str, int] = {}
        for nid, node in self.nodes.items():
            for tag in set(t.strip().lower() for t in node.tags):
                cluster_count[nid] = cluster_count.get(nid, 0) + 1
        return [nid for nid, c in cluster_count.items() if c >= 2]

    def proposed_edges(self, top_k: int = 20) -> list[dict]:
        """یال‌های پیشنهادی: نوت‌هایی با tag‌های مشترک ولی بدونِ یال.
        پیشنهادِ human-append (propose-only). top_k برای جلوگیری از انفجار."""
        # adjacency set (جهت‌نا.)
        adj = set()
        for e in self.edges:
            adj.add((e.src, e.dst))
            adj.add((e.dst, e.src))
        # برای هر جفتِ نوت با tag مشترک، اگر یال نیست → پیشنهاد
        tag_to_nodes = self.clusters_by_tags()
        proposals = []
        seen = set()
        for tag, nodes in tag_to_nodes.items():
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    a, b = nodes[i], nodes[j]
                    if (a, b) in adj:
                        continue
                    pair = (min(a, b), max(a, b))
                    if pair in seen:
                        continue
                    seen.add(pair)
                    proposals.append({"src": a, "dst": b, "shared_tag": tag,
                                      "propose_new_edge": True})
                    if len(proposals) >= top_k:
                        return proposals
        return proposals

    def analyze(self) -> dict:
        """تحلیلِ کامل: هاب‌ها، خوشه‌ها، پل‌ها، یال‌های پیشنهادی. propose-only."""
        return {
            "n_nodes": self.n_nodes,
            "n_edges": self.n_edges,
            "n_broken_targets": len(self.broken_targets),
            "hubs": [{"note_id": nid, "in_degree": d,
                      "title": self.nodes.get(nid, IdeaNode(nid, "")).title}
                     for nid, d in self.hubs() if d > 0],
            "n_clusters": len(self.clusters_by_tags()),
            "n_bridges": len(self.bridges()),
            "n_proposed_edges": len(self.proposed_edges()),
            "proposed_edges_sample": self.proposed_edges(top_k=5),
            "propose_only": True,
        }


if __name__ == "__main__":
    # اجرای دستی: گراف را از vaultِ واقعی بساز و خلاصه چاپ کن
    import json
    g = IdeaGraph()
    vault = Path(__file__).resolve().parent.parent
    report = g.build(vault)
    print(json.dumps({**report, **g.analyze()}, ensure_ascii=False, indent=2))
