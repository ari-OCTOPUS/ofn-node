#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_obsidian_tasks.py — CH-05: Obsidian Notes → Task Queue

Scans the Obsidian vault (F:/backup) for markdown task items (- [ ] / - [x])
and emits task-data.js for the OCTOPUS admin UI.

Pattern: stdlib-only, offline, composable. Persian labels for UI consumers.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

VAULT_ROOT = "F:/backup"
NS_DIR = "F:/backup/nervous-system"

# Dirs to skip entirely (generated, deps, archives, VCS)
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".obsidian", "_Archive", "_Duplicates",
    "nervous-system", ".pytest_cache", ".streamlit", "cassettes", "_code",
    ".claude", ".zcode", "00", "-_", "_launchpad", "_memory", "_ops",
}

# Regexes
TASK_RE = re.compile(r"^[\s]*[-*]\s+\[(.?)]\s+(.*)$")
HEADING_RE = re.compile(r"^#{1,3}\s+(.*)$")
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
HASHTAG_RE = re.compile(r"#(\w+)")

# Priority keywords mapped to levels
PRIORITY_MAP = {
    "urgent": 4, "critical": 4, "blocker": 4, "فوری": 4,
    "high": 3, "مهم": 3,
    "medium": 2, "متوسط": 2,
    "low": 1, "کم": 1,
    "todo": 2, "task": 2,
}

PRIORITY_LABELS = {4: "بحرانی", 3: "بالا", 2: "متوسط", 1: "کم"}


def _priority_from_text(text: str, heading: str) -> int:
    """Derive priority from hashtags, keywords, and heading context."""
    combined = (text + " " + heading).lower()
    for keyword, level in PRIORITY_MAP.items():
        if keyword in combined:
            return level
    return 2  # default medium


def _parse_frontmatter(lines: list[str]) -> dict:
    """Read simple YAML-like frontmatter between --- fences."""
    if not lines or lines[0].strip() != "---":
        return {}
    fm: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def _project_from_path(rel_path: str) -> str:
    """Map a relative path to a project/area label."""
    parts = rel_path.replace("\\", "/").split("/")
    if not parts:
        return "سایر"
    top = parts[0]
    # Root-level files (no folder)
    if top.endswith(".md"):
        return "سایر"
    # Known top-level buckets
    if top.startswith("03 - "):
        return parts[1] if len(parts) > 1 else top
    if top.startswith("04 - "):
        return "معماری"
    if top.startswith("05 - "):
        return "ایجنت‌ها"
    if top.startswith("06 - "):
        return "نقشه‌های معماری"
    if top.startswith("07 - "):
        return "دانش"
    if top.startswith("02 - "):
        return "Life OS"
    if top.startswith("01 - "):
        return "داشبورد"
    if top.startswith("00 - "):
        return "صندوق ورودی"
    if top.startswith("10 - "):
        return "تلگرام"
    return top


def _walk_md_files(root: str) -> list[str]:
    """Yield relative paths to .md files under root, skipping noise dirs."""
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skip dirs
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in filenames:
            if fname.lower().endswith(".md"):
                result.append(os.path.join(dirpath, fname))
    return result


def _extract_tasks(md_path: str) -> list[dict]:
    """Parse a single markdown file and return its task items."""
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return []

    fm = _parse_frontmatter(lines)
    rel = os.path.relpath(md_path, VAULT_ROOT)
    project = _project_from_path(rel)

    tasks = []
    current_heading = ""
    for line in lines:
        stripped = line.rstrip("\n")
        h_match = HEADING_RE.match(stripped)
        if h_match:
            raw_heading = h_match.group(1).strip()
            # Skip decorative separator lines that look like headings
            if len(set(raw_heading)) <= 2 and raw_heading[:3] in ("═══", "───", "━━━", "▬▬▬", "══", "──", "━━", "▬▬"):
                continue
            current_heading = raw_heading
            continue

        t_match = TASK_RE.match(stripped)
        if not t_match:
            continue

        checkbox = t_match.group(1).strip().lower()
        text = t_match.group(2).strip()
        if not text:
            continue

        done = checkbox in ("x", "-", "~")
        priority = _priority_from_text(text, current_heading)
        hashtags = HASHTAG_RE.findall(text)
        dates = DATE_RE.findall(text)
        due = dates[0] if dates else None

        tasks.append({
            "text": text,
            "done": done,
            "priority": priority,
            "priority_label": PRIORITY_LABELS.get(priority, "متوسط"),
            "heading": current_heading,
            "hashtags": hashtags,
            "due": due,
            "file": rel.replace("\\", "/"),
            "project": project,
            "note_status": fm.get("status", ""),
            "note_tags": fm.get("tags", ""),
        })
    return tasks


def main() -> None:
    os.makedirs(NS_DIR, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    md_files = _walk_md_files(VAULT_ROOT)
    all_tasks: list[dict] = []
    files_with_tasks = 0

    for md_path in md_files:
        tasks = _extract_tasks(md_path)
        if tasks:
            all_tasks.extend(tasks)
            files_with_tasks += 1

    open_tasks = [t for t in all_tasks if not t["done"]]
    done_tasks = [t for t in all_tasks if t["done"]]

    # Aggregations
    by_project: dict[str, dict] = {}
    for t in all_tasks:
        proj = t["project"]
        bucket = by_project.setdefault(proj, {"open": 0, "done": 0, "total": 0, "critical": 0, "high": 0})
        bucket["total"] += 1
        if t["done"]:
            bucket["done"] += 1
        else:
            bucket["open"] += 1
        if t["priority"] >= 4:
            bucket["critical"] += 1
        elif t["priority"] == 3:
            bucket["high"] += 1

    by_priority = {"بحرانی": 0, "بالا": 0, "متوسط": 0, "کم": 0}
    for t in open_tasks:
        by_priority[t["priority_label"]] = by_priority.get(t["priority_label"], 0) + 1

    # Next action heuristic: highest-priority open task
    next_action = None
    if open_tasks:
        top = sorted(open_tasks, key=lambda x: (-x["priority"], x["due"] or "9999"))[0]
        next_action = {
            "text": top["text"][:100],
            "project": top["project"],
            "priority": top["priority_label"],
            "file": top["file"],
            "due": top["due"],
        }

    task_data = {
        "generated": generated,
        "summary": {
            "files_scanned": len(md_files),
            "files_with_tasks": files_with_tasks,
            "total_tasks": len(all_tasks),
            "open_tasks": len(open_tasks),
            "done_tasks": len(done_tasks),
            "completion_rate": round(len(done_tasks) / len(all_tasks), 3) if all_tasks else 0,
            "by_priority": by_priority,
            "next_action": next_action,
        },
        "open_tasks": open_tasks,
        "done_tasks": done_tasks,
        "by_project": by_project,
    }

    js = (
        "window.TASK_DATA = "
        + json.dumps(task_data, ensure_ascii=False, default=str)
        + ";\n"
    )
    out_path = os.path.join(NS_DIR, "task-data.js")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(js)

    print(
        f"[extract_obsidian_tasks] task-data.js refreshed: {len(js)} chars, "
        f"{len(md_files)} files scanned, {len(open_tasks)} open / {len(done_tasks)} done"
    )


if __name__ == "__main__":
    main()
