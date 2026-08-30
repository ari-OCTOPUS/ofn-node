"""
brain/self_model.py — مدلِ خودآگاهیِ سیستم

این ماژول به سیستم اجازه می‌ده کدِ خودش رو بخونه، ساختارش رو بفهمه،
و نقشه‌ای از «چه چیزی هست و چه چیزی نیست» بسازه.

خودآگاهی سه لایه:
  Layer 1: Self-Map — کجا چی هست (فایل‌ها، کلاس‌ها، توابع)
  Layer 2: Self-Description — هر بخش چه کار می‌کنه
  Layer 3: Self-Critique — نقاط ضعف و فرصت‌ها
"""
from __future__ import annotations

import os
import ast
import json
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CodeUnit:
    """یک واحد کد: تابع، کلاس، یا فایل."""
    name: str
    kind: str          # "module" | "class" | "function"
    file_path: str
    line_count: int
    docstring: str = ""
    functions: list = field(default_factory=list)  # اگر کلاس است
    imports: list = field(default_factory=list)
    complexity: str = "low"   # low|medium|high


@dataclass
class SelfMap:
    """نقشه‌ی خود سیستم."""
    root: str
    modules: list[CodeUnit] = field(default_factory=list)
    total_lines: int = 0
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    capabilities: list[str] = field(default_factory=list)  # «چه کار می‌تونه بکنه»
    limitations: list[str] = field(default_factory=list)   # «چه کار نمی‌تونه بکنه»


def _analyze_python_file(filepath: str) -> list[CodeUnit]:
    """تحلیل یک فایل Python با AST."""
    units = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        lines = source.count("\n")

        # Module-level docstring
        module_doc = ast.get_docstring(tree) or ""

        # Collect imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        module_unit = CodeUnit(
            name=os.path.basename(filepath),
            kind="module",
            file_path=filepath,
            line_count=lines,
            docstring=module_doc,
            imports=list(set(imports)),
        )

        # Determine complexity
        if lines > 200 or len(imports) > 15:
            module_unit.complexity = "high"
        elif lines > 80:
            module_unit.complexity = "medium"

        units.append(module_unit)

        # Classes and functions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                cls_unit = CodeUnit(
                    name=node.name,
                    kind="class",
                    file_path=filepath,
                    line_count=sum(1 for _ in ast.walk(node)),
                    docstring=ast.get_docstring(node) or "",
                    functions=methods,
                )
                units.append(cls_unit)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_unit = CodeUnit(
                    name=node.name,
                    kind="function",
                    file_path=filepath,
                    line_count=sum(1 for _ in ast.walk(node)),
                    docstring=ast.get_docstring(node) or "",
                )
                units.append(fn_unit)

    except Exception as e:
        pass  # Skip files that can't be parsed

    return units


def build_self_map(root_dir: str = None) -> SelfMap:
    """
    ساخت نقشه‌ی خود سیستم.
    همه‌ی فایل‌های Python رو اسکن می‌کنه.
    """
    if root_dir is None:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    self_map = SelfMap(root=root_dir)

    # Walk the codebase
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip hidden dirs, __pycache__, venv, .git
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in
                       ("__pycache__", "venv", "env", ".streamlit", "node_modules")]

        for fname in filenames:
            if not fname.endswith(".py"):
                continue

            fpath = os.path.join(dirpath, fname)
            units = _analyze_python_file(fpath)
            self_map.modules.extend(units)

            for u in units:
                if u.kind == "module":
                    self_map.total_files += 1
                    self_map.total_lines += u.line_count
                elif u.kind == "class":
                    self_map.total_classes += 1
                elif u.kind == "function":
                    self_map.total_functions += 1

    # Infer capabilities from module/function names and docstrings
    self_map.capabilities = _infer_capabilities(self_map)
    self_map.limitations = _infer_limitations(self_map)

    return self_map


def _infer_capabilities(sm: SelfMap) -> list[str]:
    """از روی نام‌ها و docstringها توانمندی‌ها رو استنتاج کن."""
    caps = []
    all_text = " ".join(m.docstring + " " + m.name for m in sm.modules).lower()

    capability_map = {
        "web search": ["web_research", "search_wikipedia", "search_arxiv", "duckduckgo"],
        "LLM reasoning (Fugu)": ["fugu", "router", "llm"],
        "time-series analysis": ["temporal_mi", "empirical_shadow", "fit_shadow"],
        "autonomous research loop": ["autoloop", "run_step", "run_experiment"],
        "memory (SQLite)": ["store", "save_experiment", "get_patterns", "research_store"],
        "RAG (vector search)": ["vectorstore", "embeddings", "chroma"],
        "visualization (Plotly)": ["visuals", "radial_gauge", "pipeline_flow", "tesseract"],
        "multi-agent graph": ["graph", "langgraph", "nodes", "state"],
        "pattern recognition": ["patterns", "hypotheses", "scores"],
        "SOG mathematical model": ["model.py", "delta_self", "e_shadow", "p_closed"],
        "Streamlit UI": ["app.py", "tab_", "streamlit"],
        "knowledge base (Obsidian)": ["vault", "wikilinks"],
    }

    for cap, keywords in capability_map.items():
        if any(kw.lower() in all_text for kw in keywords):
            caps.append(cap)

    return caps


def _infer_limitations(sm: SelfMap) -> list[str]:
    """از روی ساختار، محدودیت‌ها رو پیدا کن."""
    lims = []

    caps_set = set(sm.capabilities)

    # Check what's missing
    if "self-modifying code" not in caps_set:
        lims.append("نمی‌تونه کد خودش رو تغییر بده — فقط تحلیل می‌کنه")
    if "formal verification" not in caps_set:
        lims.append("هیچ مکانیزم تأیید رسمی (formal proof) نداره")
    if "multi-modal" not in caps_set:
        lims.append("فقط داده‌ی عددی پردازش می‌کنه — نه تصویر/صوت")
    if "real-time learning" not in caps_set:
        lims.append("یادگیری offline است — در لحظه وزن‌ها رو آپدیت نمی‌کنه")

    # Find high-complexity modules (potential fragility)
    high_complex = [m for m in sm.modules if m.complexity == "high"]
    if high_complex:
        names = [m.name for m in high_complex[:3]]
        lims.append(f"ماژول‌های پیچیده ( شکننده ): {', '.join(names)}")

    # Check for test coverage
    test_files = [m for m in sm.modules if "test" in m.name.lower()]
    if len(test_files) < 2:
        lims.append(f"پوشش تست ضعیف — فقط {len(test_files)} فایل تست")

    return lims


def self_model_to_text(sm: SelfMap) -> str:
    """تبدیل مدل خود به متن قابل فهم برای LLM."""
    lines = [
        "# مدلِ خودآگاهیِ سیستم",
        f"# مسیر ریشه: {sm.root}",
        f"# حجم کد: {sm.total_lines} خط در {sm.total_files} فایل",
        f"# کلاس‌ها: {sm.total_classes} | توابع: {sm.total_functions}",
        "",
        "## توانمندی‌ها:",
    ]
    for c in sm.capabilities:
        lines.append(f"  ✅ {c}")

    lines.append("\n## محدودیت‌ها:")
    for l in sm.limitations:
        lines.append(f"  ⚠️ {l}")

    lines.append("\n## ساختار ماژول‌ها:")
    for m in sm.modules:
        if m.kind == "module":
            rel_path = os.path.relpath(m.file_path, sm.root)
            doc = m.docstring.split("\n")[0][:80] if m.docstring else "(بدون docstring)"
            lines.append(f"  📄 {rel_path} ({m.line_count} خط, {m.complexity})")
            if doc:
                lines.append(f"      {doc}")

    return "\n".join(lines)


def get_self_description() -> str:
    """توضیح کوتاه سیستم — برای ورود به LLM."""
    sm = build_self_map()
    return self_model_to_text(sm)


if __name__ == "__main__":
    print("=== Self-Model Analysis ===\n")
    sm = build_self_map()
    print(self_model_to_text(sm))
