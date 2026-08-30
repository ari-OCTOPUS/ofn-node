#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تیکِ زمان‌بند 4d consolidation — بی‌لمس TCB (جایگزین سیم‌کشی daemon).

env از OCTOPUS-flags.cmd (درس دیپ‌تست). منابع را فقط می‌خواند؛ نوشتن فقط
از خود ConsolidationCycle. حذف صفر.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

VAULT = Path(r"F:\backup")
FOURD = VAULT / "4d_system"
OPS = VAULT / "_ops"
OUT = VAULT / "06-EVIDENCE" / "POISONING-WATCH-4d.md"


def _load_flags() -> None:
    p = OPS / "OCTOPUS-flags.cmd"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    for line in text.splitlines():
        s = line.strip()
        if len(s) >= 5 and s[:4].lower() == "set " and "=" in s:
            k, _, v = s[4:].partition("=")
            k, v = k.strip(), v.strip()
            if k and k not in os.environ:
                os.environ[k] = v


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def gather_sources() -> dict:
    sources: dict = {}
    se = FOURD / "outputs" / "self_evolved"
    fr = _read_json(se / "frontier.json")
    if isinstance(fr, dict):
        n = fr.get("n_cells") or fr.get("cells")
        if n is None:
            n = len(fr)
        if isinstance(n, (int, float)) and n > 0:
            sources["frontier"] = {"cells": int(n), "n_cells": int(n)}
    conc = _read_json(se / "conclusions.json")
    if isinstance(conc, dict) and conc.get("anchors_ok"):
        sources["conclusions"] = conc
    sg = _read_json(se / "self_growth.json") or _read_json(se / "self-portrait.json")
    if isinstance(sg, dict) and (sg.get("current_focus") or sg.get("capabilities")):
        sources["self_growth"] = sg
    db = FOURD / "outputs" / "4d_experiments.db"
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        try:
            rows = [dict(r) for r in con.execute(
                "SELECT * FROM experiments ORDER BY rowid DESC LIMIT 30")]
        except sqlite3.Error:
            rows = []
        try:
            refs = [dict(r) for r in con.execute(
                "SELECT * FROM reflections ORDER BY rowid DESC LIMIT 20")]
        except sqlite3.Error:
            refs = []
        con.close()
        if rows and all(isinstance(d, dict) and "verdict" in d for d in rows):
            sources["experiments"] = rows
        if refs and all(isinstance(d, dict) and "score" in d for d in refs):
            sources["reflections"] = refs
    except sqlite3.Error:
        pass
    return sources


def main() -> int:
    _load_flags()
    sys.path.insert(0, str(FOURD))
    from brain.consolidation import ConsolidationCycle, recall_reach
    sources = gather_sources()
    cyc = ConsolidationCycle()
    before = recall_reach(cyc.history)
    result = cyc.run(sources)
    after = recall_reach(cyc.history)
    rec = {
        "ok": True,
        "sources": sorted(sources),
        "cycle": getattr(result, "cycle", None),
        "insights": list(getattr(result, "insights", None) or [])[:4],
        "similar_keys": list(getattr(result, "similar_keys", None) or []),
        "before": before,
        "after": after,
    }
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    try:
        from datetime import datetime, timezone
        line = (f"\n## 4d-consolidation-tick {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
                f"- sources={rec['sources']} cycle={rec['cycle']} "
                f"sk={rec['similar_keys'][:5]} after_events={after.get('events')}\n")
        with open(OUT, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
