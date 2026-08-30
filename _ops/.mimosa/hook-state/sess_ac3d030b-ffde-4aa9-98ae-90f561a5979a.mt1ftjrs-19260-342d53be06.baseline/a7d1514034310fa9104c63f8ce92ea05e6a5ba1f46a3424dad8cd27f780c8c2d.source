#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""broken_reader_analysis.py — C21 (مگا‌دستور #۱۷): BROKEN_READER بدون تغییر wiring.py.

تحلیل: call graph reader · state path mismatch · schema mismatch · cache · flag.
Patch برای hot file فقط diff پیشنهادی — اجرا توسط A/B."""
from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
WIRING = _ROOT / "_ops" / "wiring.py"

ANALYSIS = {
    "schema": "broken-reader-analysis/1",
    "cause": "BROKEN_READER",
    "definition": "reader فقط spend-shape می‌بیند؛ ۳ منبع دیگر (knowledge/telegram/telemetry) کور است",
    "call_graph": [
        {"step": 1, "caller": "organism.py::run_cycle", "calls": "wiring._observations_from_snapshot",
         "file": "hot", "line_range": "unknown"},
        {"step": 2, "caller": "wiring._observations_from_snapshot", "reads": [
            "state/pulse/life-currency-latest.json::per_organ_alltime_musd",
            "state/pulse/life-currency-latest.json::suspect_zero_total",
            "state/pulse/life-currency-latest.json::monthly_musd"],
         "missing_reads": [
            "_ops/organs/state/knowledge-afferent.jsonl (sidecar events)",
            "_ops/state/spine/spine.db::events (telegram/bitemporal)",
            "_ops/state/pulse/memory-read-latest.json (telemetry)"],
         "file": "wiring.py", "hot": True},
        {"step": 3, "caller": "wiring", "builds": "sensory_observation → afferent_beat",
         "effect": "ratio = spend_events / total_possible; اگر spend=0 → ratio latches 0.0"},
    ],
    "root_causes": [
        {"id": "BR-1", "type": "state_path_mismatch",
         "description": "knowledge events در _ops/organs/state/ نوشته می‌شوند ولی reader از _ops/state/pulse/ می‌خواند",
         "severity": "primary"},
        {"id": "BR-2", "type": "schema_mismatch",
         "description": "sidecar events schema=afferent-event/1 ولی reader Observation objects می‌سازد",
         "severity": "secondary"},
        {"id": "BR-3", "type": "disabled_flag",
         "description": "CHRONO_AFFERENT_EVERY_N_BEATS=1440 یعنی تقریباً هر ۴ ساعت یک‌بار — عملاً کور",
         "severity": "tertiary"},
    ],
    "proposed_diff": {
        "file": "_ops/wiring.py",
        "type": "PROPOSAL_ONLY — اجرا توسط A/B",
        "location": "_observations_from_snapshot()",
        "addition": """
# C21 PROPOSAL: read knowledge afferent events as additional observations
try:
    ka_ledger = Path(__file__).parent / "organs/state/knowledge-afferent.jsonl"
    if ka_ledger.exists():
        ka_lines = ka_ledger.read_text(encoding="utf-8").strip().splitlines()
        ka_events = [json.loads(l) for l in ka_lines[-20:] if l.strip()]
        for ev in ka_events:
            if ev.get("extra", {}).get("quality") == "VALID":
                observations.append({
                    "metric": f"knowledge_{ev.get('note_type', 'note')}",
                    "value": 1,
                    "unit": "event",
                    "occurred_at": ev.get("occurred_at"),
                    "source": "knowledge_afferent",
                })
except Exception:
    pass  # fail-soft: knowledge source نباید راستی را بکشد
""",
        "rollback": "حذف بلوک try/except بالا",
        "test": "test_observations_include_knowledge.py — snap با حداقل ۱ رویداد knowledge VALID → observations شامل knowledge_*",
    },
    "priority": "NO_SOURCE canary اول (C17) → سپس این patch → سپس THRESHOLD (آخر)",
}


def analyze() -> dict:
    """تحلیل از روی کد زنده — بدون تغییر."""
    # verify call path exists
    wiring_exists = WIRING.exists()
    snapshot_fn = "_observations_from_snapshot" in WIRING.read_text(encoding="utf-8") if wiring_exists else False
    ANALYSIS["verified"] = {
        "wiring_exists": wiring_exists,
        "snapshot_fn_found": snapshot_fn,
        "knowledge_sidecar_path_correct": (_ROOT / "_ops/organs/state/knowledge-afferent.jsonl").exists(),
    }
    return ANALYSIS


if __name__ == "__main__":
    print(json.dumps(analyze(), ensure_ascii=False, indent=1))
