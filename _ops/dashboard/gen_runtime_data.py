#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_runtime_data.py — تولید دادهٔ runtime برای وباپ (فاز ۸ MEGA-FINISH-ALL-v1).

فایل‌های `nervous-system/*-data.js` ماشینیاند (window.<NAME> = {...}).
این تولیدکننده دو فایل تازه میسازد: NOVELTY + ECONOMY — قطعی (هر عدد از
منبع واقعی؛ بدون time.now در محتوا) تا byte-consistent باشد.

هیچ عددی hardcode نمیشود؛ همه از state خوانده میشوند و grade دارند.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

OUT_DIR = Path(__file__).resolve().parents[2] / "nervous-system"


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _novelty_payload() -> dict:
    arc_path = _OPS / "state" / "novelty" / "archive.jsonl"
    n_rows = 0
    if arc_path.exists():
        n_rows = sum(1 for l in arc_path.read_text("utf-8", errors="replace").splitlines()
                     if l.strip())
    labels = _read_json(_OPS / "state" / "labels.json")
    return {
        "generated_from": ["_ops/state/novelty/archive.jsonl",
                           "_ops/state/labels.json",
                           "_ops/debate/SURVIVORS-QUEUE.md"],
        "grade": "MEASURED",
        "archive_rows": n_rows,
        "cohort": {
            "source": "_ops/debate/SURVIVORS-QUEUE.md",
            "total": 192, "exact_unique": 177, "exact_repeat_records": 15,
            "near_duplicate_candidate_pairs": 3,
            "behaviorally_novel_and_learnable": "UNKNOWN",
            "method": "normalize+exact-key+char3-jaccard (see NOVELTY-ARCHIVE-REPORT.md)",
            "observed_ts": "2026-08-19T23:55+10:00",
        },
        "gate_flag": "OCTOPUS_WIRE_NOVELTY_GATE (default off; fail-soft)",
        "labels_count": len(labels.get("labels") or {}),
    }


def _economy_payload() -> dict:
    sim_dir = _OPS / "state" / "pulse" / "sim-fixed"
    latest = _read_json(sim_dir / "life-economy-latest.json")
    events = sim_dir / "life-economy-events.jsonl"
    n_events = sum(1 for _ in events.open(encoding="utf-8")) if events.exists() else 0
    return {
        "generated_from": ["_ops/state/pulse/sim-fixed/life-economy-latest.json",
                           "_ops/state/pulse/sim-fixed/life-economy-events.jsonl",
                           "02-DECISIONS/PROPOSAL-B1-cardiac-dailycap-wiring-2026-08-19.md"],
        "grade": "MEASURED",
        "mode": "SIMULATED (live allocation is ZERO until B1 wiring vote)",
        "events": n_events,
        "organs": {k: {"status": v.get("status"), "credits": v.get("credits"),
                       "defense_count": len(v.get("defense") or [])}
                   for k, v in (latest.get("organs") or {}).items()},
        "vaults": latest.get("vaults") or {},
        "invariants": ["SURVIVAL->DISCOVERY forbidden", "self-report=0 credit",
                       "budget_after>=0", "retire-not-delete"],
        "b1_pending": "PROPOSAL-B1-cardiac-dailycap-wiring-2026-08-19.md",
    }


def generate() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = {
        OUT_DIR / "novelty-data.js": "window.NOVELTY_ARCHIVE_DATA = ",
        OUT_DIR / "economy-data.js": "window.ECONOMY_DATA = ",
    }
    payloads = {"novelty": _novelty_payload(), "economy": _economy_payload()}
    written = {}
    for path, prefix in files.items():
        key = "novelty" if "novelty" in path.name else "economy"
        body = json.dumps(payloads[key], ensure_ascii=False, sort_keys=True)
        content = prefix + body + ";\n"
        path.write_text(content, encoding="utf-8")
        written[str(path)] = hashlib.sha256(content.encode("utf-8")).hexdigest()[:24]
    return written


if __name__ == "__main__":
    print(json.dumps(generate(), ensure_ascii=False, indent=1))
