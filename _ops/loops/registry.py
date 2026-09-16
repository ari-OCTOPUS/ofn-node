# -*- coding: utf-8 -*-
"""LOOP-REGISTRY — stable loop_id for each of the 42 seams."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .taxonomy import CLASSES, SLA_S, SEVERITY_RANK

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent

# (seam_id, class, severity, title)
# 39 from DEEP-SCAN-2026-08-20 + 3 telegram organs = 42.
_SEED: tuple[tuple[str, str, str, str], ...] = (
    ("S-D01", "DEADLOCK", "HIGH", "doctor-pulse stuck awaiting-merge since 2026-07-29"),
    ("S-D02", "STALE_TRUTH", "HIGH", "four organs still point at retired os_v1 paths"),
    ("S-D03", "SILENT_DEGRADATION", "MEDIUM", "doctor fugu quota frozen on 2026-07-29"),
    ("S-D04", "FAKE_GREEN", "HIGH", "self_awareness=green with zero readers/writers"),
    ("S-D05", "MISSING_BASELINE", "HIGH", "delta_self_raw worse than blind baseline"),
    ("S-D06", "UNCONSUMED_SIGNAL", "MEDIUM", "doctor suite never runs (run_suite=False)"),
    ("S-D07", "FLOOD_RISK", "MEDIUM", "F-AUTO-ALERT spam (92 files, top signature x346)"),
    ("S-D08", "FAKE_GREEN", "MEDIUM", "five metrics permanently non-informative"),
    ("S-D09", "STALE_TRUTH", "MEDIUM", "doctor structural content frozen since late July"),
    ("S-D10", "STALE_TRUTH", "LOW", "F-AUTO-MEMORY still says 7 rows"),
    ("S-D11", "STALE_TRUTH", "LOW", "EQ-07/08 missing provenance"),
    ("S-A01", "BROKEN_FEEDBACK", "HIGH", "self_knowledge heuristic hardcoded confidence 0.4"),
    ("S-A02", "ORPHAN", "HIGH", "self_insight.py never completed a cycle"),
    ("S-A03", "BROKEN_FEEDBACK", "HIGH", "calibration-latest not read by improve.py"),
    ("S-A04", "FAKE_GREEN", "HIGH", "EQ-14 dishonest metric without registry guard"),
    ("S-A05", "STALE_TRUTH", "MEDIUM", "duplicate note numbers 45 and 72"),
    ("S-A06", "STALE_TRUTH", "MEDIUM", "ALL-AGENTS-INSTRUCTION title vs body drift"),
    ("S-A07", "STALE_TRUTH", "MEDIUM", "note 24 applied=false vs 34% applied today"),
    ("S-A08", "ORPHAN", "MEDIUM", "cockpit does not ingest self-knowledge-latest"),
    ("S-A09", "STARVED_DECISION", "MEDIUM", "knowledge organ wired but off"),
    ("S-A10", "MISSING_BASELINE", "LOW", "always-True self_audit probes trap"),
    ("S-A11", "ORPHAN", "LOW", "hebbian display-only, no actuator consumer"),
    ("S-A12", "FAKE_GREEN", "LOW", "sigma/afferent_ratio hardcoded 1.0 in organism"),
    ("S-A13", "ORPHAN", "LOW", "empty knowledge subdirs + stray silabi_bot"),
    ("S-B01", "SILENT_DEGRADATION", "CRITICAL", "daily quota empty by ~07:17; 14h degraded"),
    ("S-B02", "STARVED_DECISION", "CRITICAL", "FX-pin models=TEST_ONLY; production unpriced"),
    ("S-B03", "STARVED_DECISION", "HIGH", "4d_system formally split from cortex"),
    ("S-B04", "DEADLOCK", "HIGH", "git-write lock timeout + owner-key.enc unlocated"),
    ("S-B05", "MISSING_BASELINE", "HIGH", "brain_core parity missing_old=6383 NO_BASELINE"),
    ("S-B06", "DEADLOCK", "HIGH", "RUN-ORGANISM.bat one-shot instead of :loop"),
    ("S-B07", "STARVED_DECISION", "HIGH", "life-currency milli-rounding starves members"),
    ("S-B08", "ORPHAN", "MEDIUM", "brains invisible on LIVE-ORGANISM-MAP"),
    ("S-B09", "STARVED_DECISION", "MEDIUM", "council stuck at wave-01"),
    ("S-B10", "STALE_TRUTH", "MEDIUM", ".env.bak-20260810 still at vault root"),
    ("S-B11", "FAKE_GREEN", "MEDIUM", "RAW-SHELL was armed; disarmed file remains"),
    ("S-B12", "STALE_TRUTH", "MEDIUM", "_ops/OCTOPUS.env nearly empty"),
    ("S-B13", "STARVED_DECISION", "MEDIUM", "two brains two providers, no unified budget"),
    ("S-B14", "MISSING_BASELINE", "LOW", "clade-ledger all APPLIED, reject path untested"),
    ("S-B15", "UNCONSUMED_SIGNAL", "LOW", "ORG-05 doctor_every_n=1440 (~41h)"),
    ("S-T01", "ORPHAN", "HIGH", "telegram_events=11 with no consumer"),
    ("S-T02", "BROKEN_FEEDBACK", "HIGH", "tg_bridge_once push without inbound closure"),
    ("S-T03", "FLOOD_RISK", "HIGH", "42 seams as 42 telegram messages would mute the channel"),
)

INCIDENTS = (
    {
        "loop_id": "LOOP-TELEGRAM-PROBE-INVALID",
        "class": "BROKEN_FEEDBACK",
        "also": "SILENT_SPAM",
        "severity": "HIGH",
        "status": "OPEN",
        "note": "heartbeat spam suppressed; event→response closure unproven",
        "regression_test": "test_tg_probe_invalid_spam.py",
        "verified": False,
    },
    {
        "loop_id": "LOOP-TELEGRAM-UNOWNED-INSTANT-ALERT",
        "class": "ORPHAN",
        "also": "LOST_ACK",
        "severity": "HIGH",
        "status": "OPEN",
        "note": "fear path outbox-only/dry-run; no fabricated task_id; no live send",
        "regression_test": "test_telegram_shadow_roundtrip.py::t8_sig_fear_cannot_bypass_outbox",
        "verified": False,
    },
)


CLOSURE = {
    "S-A01": "self_knowledge._heuristic: constant 0.4 → None or accuracy-ema",
    "S-A02": "self_insight shadow cycle (journal=false) → evidence; weekly later",
    "S-A03": "improve.gather_signals reads calibration-latest; propose-only",
    "S-A08": "cockpit_brain._TIERS self_knowledge file-read (no subprocess)",
    "S-D01": "daemon one-open-mission+timeout → quarantine failed → slot free",
    "S-T01": "loops.telegram_organ consume spine events (dry_run outbox)",
    "S-T02": "tg_bridge_once: beat excluded from identity; STOP-TG-HEARTBEAT; DLQ after incident+digest",
    "S-T03": "digest+rate-limit+coalesce; never 1-message-per-loop",
    "S-B01": "declare DEGRADED_LOCAL_ONLY; no paid calls this lane",
    "S-B02": "owner FX-pin — STARVED_DECISION card, no secret/pin invent",
}


def loop_id(seam_id: str) -> str:
    return f"loop:{seam_id}"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def seed_entries() -> list[dict[str, Any]]:
    assert len(_SEED) == 42, len(_SEED)
    classes = {c[1] for c in _SEED}
    unknown = classes - set(CLASSES)
    if unknown:
        raise ValueError(f"unknown classes: {unknown}")
    out = []
    for seam, cls, sev, title in _SEED:
        out.append({
            "loop_id": loop_id(seam),
            "seam_id": seam,
            "class": cls,
            "severity": sev,
            "sla_s": SLA_S[sev],
            "title": title,
            "closure_path": CLOSURE.get(seam, "open — needs owner card or later rail"),
            "status": "open",
            "levels": {
                "declared": True,
                "implemented": False,
                "callable": False,
                "observed": False,
                "tested": False,
                "verified": False,
            },
            "regression_test": None,
            "telegram_card_id": None,
            "updated": _now(),
        })
    out.sort(key=lambda e: (SEVERITY_RANK[e["severity"]], e["seam_id"]))
    return out


def mark(entry: dict[str, Any], **levels: bool) -> dict[str, Any]:
    lv = dict(entry.get("levels") or {})
    for k, v in levels.items():
        if k not in lv:
            raise KeyError(k)
        lv[k] = bool(v)
    # verified requires tested+observed+callable; never skip
    if lv.get("verified") and not (lv.get("tested") and lv.get("observed") and lv.get("callable")):
        lv["verified"] = False
    entry["levels"] = lv
    if lv.get("verified"):
        entry["status"] = "verified_closed"
    elif lv.get("tested") and lv.get("implemented"):
        entry["status"] = "shadow_closed" if not lv.get("observed") else "tested_open"
    elif lv.get("implemented"):
        entry["status"] = "implemented_open"
    entry["updated"] = _now()
    return entry


def build(marks: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    entries = seed_entries()
    by = {e["seam_id"]: e for e in entries}
    for seam, patch in (marks or {}).items():
        if seam in by:
            if "levels" in patch:
                mark(by[seam], **patch["levels"])
            for k in ("regression_test", "status", "telegram_card_id", "closure_path"):
                if k in patch:
                    by[seam][k] = patch[k]
            by[seam]["updated"] = _now()
    entries = list(by.values())
    entries.sort(key=lambda e: (SEVERITY_RANK[e["severity"]], e["seam_id"]))
    blob = json.dumps(entries, ensure_ascii=False, sort_keys=True)
    return {
        "schema": "loop-registry/1",
        "n": len(entries),
        "wave1_unlocked": False,
        "closure_bar": {
            "verified_requires": [
                "independent_regression_test",
                "ge_5_distinct_real_events",
                "attribution_ge_0.95",
            ],
            "else": "SHADOW_CLOSED_MAX",
        },
        "content_sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        "entries": entries,
        "incidents": [dict(x, updated=_now()) for x in INCIDENTS],
    }


def write(dest: Path, marks: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    doc = build(marks)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc
