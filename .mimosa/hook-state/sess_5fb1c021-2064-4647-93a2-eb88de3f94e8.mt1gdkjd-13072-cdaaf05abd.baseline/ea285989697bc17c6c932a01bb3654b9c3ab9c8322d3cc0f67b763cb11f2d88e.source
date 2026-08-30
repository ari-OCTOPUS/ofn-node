#!/usr/bin/env python3
"""Read-only: which Phase-0 watchlist sites have fired (ADR-042)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS / "budget"))
import opslib  # noqa: E402

CAT = _OPS / "tg_site_fire_catalog.json"


def main() -> int:
    catalog = json.loads(CAT.read_text(encoding="utf-8"))
    log = Path(opslib.STATE_DIR) / "tg-site-fire.jsonl"
    fired_keys = set()
    n_rows = 0
    if log.exists():
        for ln in log.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            n_rows += 1
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            fired_keys.add((str(r.get("caller_file") or "").replace("\\", "/"),
                            int(r.get("caller_line") or 0)))
    alive, dead = [], []
    for row in catalog:
        key = (str(row["rel"]).replace("\\", "/"), int(row["line"]))
        (alive if key in fired_keys else dead).append(row)
    print(json.dumps({
        "flag": os.environ.get("OCTOPUS_TG_SITE_FIRE_LOG"),
        "log_path": str(log),
        "log_exists": log.exists(),
        "log_rows": n_rows,
        "watchlist": len(catalog),
        "fired_watchlist": len(alive),
        "dead_code_candidates": len(dead),
        "note": "48h window not enforced here; compare log mtime vs collection start.",
        "fired_sample": [{"rel": a["rel"], "line": a["line"], "func": a["func"]}
                         for a in alive[:20]],
        "dead_sample": [{"rel": d["rel"], "line": d["line"], "func": d["func"]}
                        for d in dead[:20]],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
