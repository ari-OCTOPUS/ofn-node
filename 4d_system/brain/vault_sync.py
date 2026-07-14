"""
brain/vault_sync.py — موتور همگام‌سازی با Obsidian Vault

سه کار اصلی:
  ۱. wikilink‌گذاری خودکار فایل‌های موجود vault
  ۲. تولید یادداشت خودکار از کشف‌های سیستم (با LaTeX + wikilinks)
  ۳. parse کردن گراف wikilink برای نمایش تعاملی

قانون طلایی: فایل‌های موجود vault فقط wikilink اضافه میشن (never overwritten).
یادداشت‌های خودکار فقط در 07-تحلیل-پژوهش/ نوشه میشن.
"""
from __future__ import annotations

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


# مسیر vault — قابلِ‌تنظیم با env (VAULT_DIR)؛ پیش‌فرض همان Desktop/4D-Vault.
# نکته: Path.home()/"Desktop" با ری‌دایرکتِ OneDrive یا جابه‌جاییِ پروژه می‌شکند؛
# env override راهِ فرار است بدونِ تغییرِ رفتارِ پیش‌فرض.
DESKTOP = Path.home() / "Desktop"
VAULT_DIR = (Path(os.getenv("VAULT_DIR")) if os.getenv("VAULT_DIR")
             else DESKTOP / "4D-Vault")
ANALYSIS_DIR = VAULT_DIR / "07-تحلیل-پژوهش"


# ════════════════════════════════════════════════════════════════════════
#  رجیستری مفاهیم — برای wikilink‌گذاری خودکار
# ════════════════════════════════════════════════════════════════════════

# هر مدخل: (عبارت‌های قابل جستجو, نام wikilink هدف)
# فقط اولین رخدادِ بدون wikilink جایگزین میشه
CONCEPT_REGISTRY = [
    # مفاهیم ریاضی محوری
    (["Δ_self", "Δself", "Delta_self", "دلتا‌سلف"], "Delta-self"),
    (["E_shadow", "Eshadow", "سایه‌اطلاعاتی", "سایه اطلاعاتی"], "E-shadow"),
    (["I_pred", "Ipred", "اطلاعات پیش‌بینی"], "I-pred"),
    (["chain rule", "chain-rule", "اتحاد chain", "قضیه‌ی زنجیره"], "اتحاد-chain-rule"),
    (["DARE", "ریکاتی", "Riccati"], "DARE-معادله‌ی-ریکاتی"),
    (["قضیه‌ی شناسایی", "identifiability theorem", "شناسایی‌پذیری"], "قضیه‌ی-شناسایی"),
    (["کف کالمن", "Kalman floor", "کالمن‌فلر"], "کف-کالمن"),

    # مدل SOG
    (["مدل خطی-گاوسی", "linear-Gaussian model", "SOG model", "مدل SOG"], "مدل-خطی-گاوسی"),
    (["سه کف اطلاعاتی", "three information floors", "کف‌اطلاعاتی"], "سه-کف-اطلاعاتی"),
    (["نقطه‌ی کار", "operating point"], "نقطه‌ی-کار"),

    # هندسه
    (["تسراکت", "tesseract", "هیپرکیوب"], "تسراکت-و-سایه"),
    (["Theorema Egregium", "قضیه‌ی درخشان"], "Theorema-Egregium"),
    (["Takens", "تاکنس"], "قضیه‌ی-Takens"),
    (["فلت‌لند", "Flatland"], "فلت‌لند-و-ابعاد"),

    # فلسفه — اصول پنج‌گانه
    (["اصل ۱", "اصل یک", "Principle 1"], "اصل-۱-شناسایی"),
    (["اصل ۲", "اصل دو", "Principle 2"], "اصل-۲-کانال"),
    (["اصل ۳", "اصل سه", "Principle 3"], "اصل-۳-سطح"),
    (["اصل ۴", "اصل چهار", "Principle 4"], "اصل-۴-خودارجاع"),
    (["اصل ۵", "اصل پنج", "Principle 5"], "اصل-۵-روش"),

    # سیستم
    (["Orchestrator", "ارکستر"], "Orchestrator"),
    (["shadow detector", "W1", "تشخیص‌دهنده سایه"], "W1-Detector"),
    (["analyst", "W2", "تحلیل‌گر"], "W2-Analyst"),
    (["reporter", "W3", "گزارش‌گر"], "W3-Reporter"),
    (["verifier", "W0", "تأییدگر"], "W0-Verifier"),
]


# ════════════════════════════════════════════════════════════════════════
#  ۱. Wikilink‌گذاری خودکار
# ════════════════════════════════════════════════════════════════════════

@dataclass
class LinkResult:
    """نتیجه‌ی wikilink‌گذاری یک فایل."""
    file: str
    links_added: int
    concepts_linked: list[str] = field(default_factory=list)


def autolink_vault(dry_run: bool = False) -> list[LinkResult]:
    """
    اسکن همه‌ی فایل‌های vault و wikilink‌گذاری خودکار.

    فقط اولین رخدادِ بدون wikilink از هر مفهوم رو لینک می‌کنه.
    فایل‌های موجود دست‌نخورده باقی می‌مونن (فقط متن body، نه frontmatter).
    """
    results = []

    for md_file in VAULT_DIR.rglob("*.md"):
        # Skip .obsidian directory
        if ".obsidian" in str(md_file) or "آرشیو" in str(md_file):
            continue

        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        # Split frontmatter and body
        frontmatter = ""
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = "---" + parts[1] + "---"
                body = parts[2]

        original_body = body
        links_added = 0
        concepts_linked = []

        for search_terms, target in CONCEPT_REGISTRY:
            # Skip if already linked in this file (هر دو فرم: ساده و alias)
            if f"[[{target}]]" in body or f"[[{target}|" in body:
                continue

            for term in search_terms:
                # Case-insensitive search, but not inside existing [[ ]] or `code`
                pattern = re.compile(
                    rf'(?<!\[\[)(?<!`)({re.escape(term)})(?!\])(?!`)',
                    re.IGNORECASE
                )
                match = pattern.search(body)
                if match:
                    # Replace only first occurrence
                    start, end = match.start(1), match.end(1)
                    matched_text = body[start:end]
                    body = body[:start] + f"[[{target}|{matched_text}]]" + body[end:]
                    links_added += 1
                    concepts_linked.append(target)
                    break  # Only link first occurrence per concept

        if links_added > 0:
            new_content = frontmatter + body if frontmatter else body
            if not dry_run:
                md_file.write_text(new_content, encoding="utf-8")

            results.append(LinkResult(
                file=str(md_file.relative_to(VAULT_DIR)),
                links_added=links_added,
                concepts_linked=concepts_linked,
            ))

    return results


# ════════════════════════════════════════════════════════════════════════
#  ۲. تولید یادداشت خودکار از کشف‌های سیستم
# ════════════════════════════════════════════════════════════════════════

def create_discovery_note(pattern: dict, insight: str = "") -> str:
    """
    تولید یک یادداشت Obsidian از یک pattern ذخیره‌شده.
    برمی‌گرداند: مسیر فایل ایجادشده.
    """
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    name = pattern.get("name", "unnamed")
    # Clean name for filename
    safe_name = re.sub(r'[^\w\-آ-ی]', '-', name)[:50]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"🔍-{safe_name}-{timestamp}.md"
    filepath = ANALYSIS_DIR / filename

    rho = pattern.get("rho", "?")
    lam = pattern.get("lam", "?")
    delta = pattern.get("delta_self", 0)
    e_shadow = pattern.get("e_shadow", 0)
    pcai = pattern.get("pcai", 0)
    detectable = pattern.get("detectable", False)
    tags_str = pattern.get("tags", "")

    # تگ‌های frontmatter بدون # و با quote — وگرنه YAML نامعتبر می‌شود
    # (# بعد از فاصله در YAML شروعِ comment است)
    tag_items = ["کشف", "auto-generated"] + [
        t.strip().replace(" ", "-") for t in tags_str.split(",") if t.strip()
    ]
    tags_yaml = ", ".join(f'"{t}"' for t in dict.fromkeys(tag_items))

    content = f"""---
aliases: ["{safe_name}"]
tags: [{tags_yaml}]
timestamp: {datetime.now().isoformat()}
type: discovery
rhythm_id: {pattern.get('id', '?')}
related: ["[[Delta-self]]", "[[E-shadow]]", "[[نقطه‌ی-کار]]"]
---

# 🔍 کشف: {name}

> [!abstract] خلاصه
> منبع: `{tags_str}` | تشخیص‌پذیر: {'✅ بله' if detectable else '❌ خیر'}
> تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## پارامترها

| پارامتر | مقدار |
|---|---|
| ρ (rho) | `{rho}` |
| λ (lambda) | `{lam}` |
| Δ_self | `{delta:.6f}` nat/گام |
| E_shadow | `{e_shadow:.6f}` nat/گام |
| PCAI | `{pcai:.4f}` |

## معادلات

> [!info] مدل خطی-گاوسی — [[مدل-خطی-گاوسی]]
> $$s(t+1) = \\rho \\cdot s(t) + m(t) + \\zeta(t)$$
> $$Y(t) = b(t) + \\lambda \\cdot s(t) + \\varepsilon(t)$$

> [!tip] ارزش درون‌نگری — [[Delta-self]]
> $$\\Delta_{{self}} = \\frac{{1}}{{2}}\\log\\!\\left(\\frac{{S_b}}{{S}}\\right) = {delta:.6f} \\text{{ nat/گام}}$$

> [!tip] کشف سایه — [[E-shadow]]
> $$E_{{shadow}} = \\frac{{1}}{{2}}\\log\\!\\left(\\frac{{\\sigma_z^2}}{{S_b}}\\right) = {e_shadow:.6f} \\text{{ nat/گام}}$$

> [!important] اتحاد — [[اتحاد-chain-rule]]
> $$\\frac{{1}}{{2}}\\log\\!\\left(\\frac{{\\sigma_z^2}}{{S}}\\right) = E_{{shadow}} + \\Delta_{{self}} = {e_shadow + delta:.6f}$$

## تحلیل

{insight[:500] if insight else '(بدون تحلیل)'}

## ارتباطات

- این کشف در [[نقطه‌ی-کار]] با ρ={rho}، λ={lam} قرار داره
- قابل‌مقایسه با [[📊 جدول-لنگرها]]
- اساس ریاضی: [[DARE-معادله‌ی-ریکاتی]] و [[کف-کالمن]]

## داده‌ی خام
"""

    if pattern.get("rhythm_file"):
        content += f"\n> [!note] فایل ریتم\n> `{pattern['rhythm_file']}`\n"

    content += f"\n---\n*تولیدشده توسط ایده‌یاب شخصی در {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"

    filepath.write_text(content, encoding="utf-8")
    return str(filepath.relative_to(VAULT_DIR))


# ════════════════════════════════════════════════════════════════════════
#  ۳. Parse کردن گراف wikilink
# ════════════════════════════════════════════════════════════════════════

@dataclass
class VaultGraph:
    """گراف wikilink‌های vault."""
    nodes: list[dict] = field(default_factory=list)      # {id, name, path, folder, color}
    edges: list[dict] = field(default_factory=list)       # {source, target}
    adjacency: dict = field(default_factory=dict)         # name -> [linked names]

    @property
    def n_nodes(self) -> int:
        return len(self.nodes)

    @property
    def n_edges(self) -> int:
        return len(self.edges)

    @property
    def hubs(self) -> list[dict]:
        """node‌هایی با بیشترین incoming links."""
        incoming = {}
        for e in self.edges:
            incoming[e["target"]] = incoming.get(e["target"], 0) + 1
        sorted_hubs = sorted(incoming.items(), key=lambda x: -x[1])
        return [{"name": n, "incoming": c} for n, c in sorted_hubs[:10]]


def parse_vault_graph() -> VaultGraph:
    """
    اسکن vault و ساخت گراف wikilink.
    """
    graph = VaultGraph()

    # رنگ‌بندی بر اساس پوشه
    folder_colors = {
        "00-MOC": "#e74c3c",
        "01-مفاهیم-ریاضی": "#3498db",
        "02-مدل-SOG": "#2ecc71",
        "03-فلسفه": "#9b59b6",
        "04-هندسه-ابعاد": "#e67e22",
        "05-سیستم-مولتی‌ایجنت": "#1abc9c",
        "06-منابع-داده": "#f1c40f",
        "07-تحلیل-پژوهش": "#e91e63",
        "08-ادبیات": "#607d8b",
        "09-پیوست‌ها": "#95a5a6",
    }

    # Collect all node names (filename stems)
    node_map = {}  # stem -> full path
    for md_file in VAULT_DIR.rglob("*.md"):
        if ".obsidian" in str(md_file) or "آرشیو" in str(md_file):
            continue
        stem = md_file.stem
        # Normalize: remove emoji prefixes for matching
        clean_stem = re.sub(r'^[^\wآ-ی]+', '', stem).strip()
        node_map[clean_stem] = md_file
        node_map[stem] = md_file

    # Build nodes
    seen_nodes = set()
    for md_file in VAULT_DIR.rglob("*.md"):
        if ".obsidian" in str(md_file) or "آرشیو" in str(md_file):
            continue
        if str(md_file) in seen_nodes:
            continue
        seen_nodes.add(str(md_file))

        stem = md_file.stem
        rel_path = str(md_file.relative_to(VAULT_DIR))
        folder = rel_path.split("/")[0].split("\\")[0] if "/" in rel_path or "\\" in rel_path else "root"
        # Normalize folder
        folder = folder.replace("\\", "/").split("/")[0]
        color = folder_colors.get(folder, "#bdc3c7")

        graph.nodes.append({
            "id": stem,
            "name": stem,
            "path": rel_path,
            "folder": folder,
            "color": color,
        })
        graph.adjacency[stem] = []

    # Parse wikilinks from each file
    wikilink_pattern = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')

    for md_file in VAULT_DIR.rglob("*.md"):
        if ".obsidian" in str(md_file) or "آرشیو" in str(md_file):
            continue
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        source_stem = md_file.stem

        for match in wikilink_pattern.finditer(content):
            target = match.group(1).strip()
            # Remove folder prefix if present
            target_clean = target.split("/")[-1].split("\\")[-1]
            # Try to match with existing nodes
            matched = None
            for node in graph.nodes:
                if node["id"] == target_clean or node["name"] == target_clean:
                    matched = node["id"]
                    break
                # Fuzzy match: target is substring of node name
                if target_clean in node["name"] or node["name"] in target_clean:
                    matched = node["id"]
                    break

            if matched and matched != source_stem:
                edge = {"source": source_stem, "target": matched}
                if edge not in graph.edges:
                    graph.edges.append(edge)
                    graph.adjacency[source_stem].append(matched)

    return graph


def get_node_content(node_name: str) -> Optional[str]:
    """خواندن محتوای یک node از vault."""
    for md_file in VAULT_DIR.rglob("*.md"):
        if ".obsidian" in str(md_file) or "آرشیو" in str(md_file):
            continue
        if md_file.stem == node_name:
            try:
                return md_file.read_text(encoding="utf-8", errors="replace")
            except Exception:
                return None
    return None


def get_vault_stats() -> dict:
    """آمار کلی vault."""
    graph = parse_vault_graph()

    # Count files per folder
    folder_counts = {}
    for md_file in VAULT_DIR.rglob("*.md"):
        if ".obsidian" in str(md_file) or "آرشیو" in str(md_file):
            continue
        rel = md_file.relative_to(VAULT_DIR)
        folder = str(rel).split("\\")[0].split("/")[0]
        folder_counts[folder] = folder_counts.get(folder, 0) + 1

    return {
        "total_files": graph.n_nodes,
        "total_links": graph.n_edges,
        "folders": len(folder_counts),
        "hubs": graph.hubs[:5],
        "folder_counts": folder_counts,
        "avg_links": graph.n_edges / max(graph.n_nodes, 1),
    }


# ════════════════════════════════════════════════════════════════════════
#  Test
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=== Vault Graph Parser ===\n")

    graph = parse_vault_graph()
    print(f"Nodes: {graph.n_nodes}")
    print(f"Edges: {graph.n_edges}")
    print(f"Avg links/node: {graph.n_edges / max(graph.n_nodes, 1):.1f}")

    print(f"\nTop hubs:")
    for h in graph.hubs:
        print(f"  {h['name']:40s} ← {h['incoming']} links")

    print(f"\n=== Dry Run: Autolink ===\n")
    results = autolink_vault(dry_run=True)
    total_links = sum(r.links_added for r in results)
    print(f"Would add {total_links} wikilinks across {len(results)} files")
    for r in results[:10]:
        print(f"  {r.file:50s} +{r.links_added} links: {', '.join(r.concepts_linked[:3])}")
