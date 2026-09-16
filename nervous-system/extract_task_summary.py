#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_task_summary.py — Lightweight summary emitter for task-data.js

Reads the full task-data.js emitted by extract_obsidian_tasks.py and produces
a ~2KB task-summary-data.js for fast dashboard loading.

Schema mirrors window.TASK_DATA but omits the heavy open_tasks/done_tasks arrays.
The admin UI expects TK.summary.open_tasks, TK.summary.by_priority, etc.

Pattern: stdlib-only, offline, additive. Does NOT replace extract_obsidian_tasks.py.
Dependency: MUST run AFTER extract_obsidian_tasks.py.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

NS_DIR = Path("F:/backup/nervous-system")


def _read_js_var(path: Path, var_name: str) -> dict[str, Any] | None:
    """Read a JS file that sets window.VAR_NAME = {...}; and extract the JSON."""
    if not path.exists():
        return None
    try:
        text = path.read_text("utf-8", errors="replace")
        prefix = f"window.{var_name} = "
        if prefix in text:
            start = text.index(prefix) + len(prefix)
            json_text = text[start:].strip().rstrip(";\n")
            return json.loads(json_text)
        return json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[extract_task_summary] read/parse failed for {path}: {exc}")
        return None


def main() -> int:
    os.makedirs(NS_DIR, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    full = _read_js_var(NS_DIR / "task-data.js", "TASK_DATA")
    if full is None:
        print("[extract_task_summary] WARNING: task-data.js not found — emitting empty summary")
        summary_payload = {
            "generated": generated,
            "summary": {
                "files_scanned": 0,
                "files_with_tasks": 0,
                "total_tasks": 0,
                "open_tasks": 0,
                "done_tasks": 0,
                "completion_rate": 0.0,
                "by_priority": {"بحرانی": 0, "بالا": 0, "متوسط": 0, "کم": 0},
                "next_action": None,
            },
            "by_project": {},
            "stale": True,
            "note": "task-data.js missing — run extract_obsidian_tasks.py first",
        }
    else:
        sm = full.get("summary", {})
        by_project_raw = full.get("by_project", {})
        # Sort projects by total task count descending, keep top 10
        top_projects = dict(
            sorted(
                by_project_raw.items(),
                key=lambda x: x[1].get("total", 0),
                reverse=True,
            )[:10]
        )
        summary_payload = {
            "generated": generated,
            "summary": {
                "files_scanned": sm.get("files_scanned", 0),
                "files_with_tasks": sm.get("files_with_tasks", 0),
                "total_tasks": sm.get("total_tasks", 0),
                "open_tasks": sm.get("open_tasks", 0),
                "done_tasks": sm.get("done_tasks", 0),
                "completion_rate": sm.get("completion_rate", 0.0),
                "by_priority": sm.get("by_priority", {}),
                "next_action": sm.get("next_action"),
            },
            "by_project": top_projects,
            "stale": False,
            "note": "lightweight summary — load task-data.js for full task list",
        }

    out_path = NS_DIR / "task-summary-data.js"
    js = "window.TASK_SUMMARY_DATA = " + json.dumps(summary_payload, ensure_ascii=False, default=str) + ";\n"
    out_path.write_text(js, encoding="utf-8")
    print(
        f"[extract_task_summary] task-summary-data.js refreshed: {len(js)} chars, "
        f"{summary_payload['summary']['open_tasks']} open / "
        f"{summary_payload['summary']['total_tasks']} total"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
