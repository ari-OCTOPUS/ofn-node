#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capability_classifier.py — read-only runtime capability classifier (WP-F).

هدف: جلوگیری از تکرار اشتباه «source-default = live» و «wired = effective».

برای هر قابلیت، این ابزار یک طبقه‌بندی دقیق می‌دهد:

  implemented             — کد موجود است؟
  configured              — flag در config صراحتاً مقدار دارد؟
  armed                   — flag در runtime با مقدار فعال loaded شده؟
  executed_recently       — کد اخیراً اجرا شده (artifact تازه)؟
  artifact_fresh          — artifact تولیدشده تازه است؟
  consumed                — خروجی توسط یک reader/downstream خوانده شده؟
  decision_changing_evidence — ورودیِ یک تصمیم/اقدام شده؟
  effect_evidence         — اثر واقعی ثبت شده؟
  outcome_evidence        — outcome improvement اندازه‌گیری شده؟
  unknown_reason          — اگر UNKNOWN، چرا؟

قواعد:
  - flag روشن به‌تنهایی executed نیست.
  - artifact تازه به‌تنهایی consumed نیست.
  - consumer code به‌تنهایی recent consumption نیست.
  - applied record به‌تنهایی measured lift نیست.
  - PID snapshot به‌تنهایی current health نیست.
  - missing evidence => UNKNOWN، نه false/healthy.

این ابزار read-only است و هیچ state canonical را بازنویسی نمی‌کند.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
STATE = _HERE / "state"
SCHEMA = "CapabilityClassifierReport.v1"

# How old can an artifact be before it's considered "not recent"?
FRESH_THRESHOLD_H = 48


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return default


def _read_jsonl_last_ts(path: Path) -> str | None:
    """Get the timestamp of the last entry in a JSONL file."""
    try:
        lines = path.read_text("utf-8").splitlines()
        if not lines:
            return None
        last = lines[-1].strip()
        if not last:
            return None
        d = json.loads(last)
        return d.get("ts") or d.get("timestamp")
    except (OSError, ValueError):
        return None


def _is_fresh(ts_str: str | None, threshold_h: float = FRESH_THRESHOLD_H) -> str:
    """Check if a timestamp is within the freshness threshold. Returns fresh/stale/unknown."""
    if not ts_str:
        return "unknown"
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(ts_str, fmt).replace(tzinfo=timezone.utc)
            age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
            return "fresh" if age_h < threshold_h else "stale"
        except ValueError:
            continue
    return "unknown"


def _flag_armed(flag_name: str) -> str:
    """Check if a flag is armed in flags-loaded snapshots. Returns armed/disarmed/unknown."""
    for snapshot_name in ["organism", "cortex"]:
        snapshot = _read_json(STATE / f"flags-loaded-{snapshot_name}.json")
        if snapshot and isinstance(snapshot, dict):
            flags = snapshot.get("flags", {})
            val = flags.get(flag_name)
            if val is not None:
                return "armed" if str(val) == "1" else "disarmed"
    return "unknown"


# ─── capability definitions ──────────────────────────────────────────────────
# Each capability is defined declaratively: what flag, what artifact, what
# freshness source, what reader evidence, what decision/effect/outcome evidence.

CAPABILITIES = {
    "semantic_memory_rich_think": {
        "description": "semantic_memory gist injection into cortex.think()",
        "flag": "OCTOPUS_WIRE_CORTEX_RICH_THINK",
        "artifact": "semantic_memory.jsonl",
        "artifact_dir": "state",
        "reader_code": "cortex.py::think()",
        "reader_evidence": "prompt-context injection (not autonomous decision)",
    },
    "bcm_learned_pressure": {
        "description": "BCM learned pressure → PainAssessment / protective apply (ADR-035 dual-mode)",
        "flag": "OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL",
        "artifact": "neural/effect-shadow.jsonl",
        "artifact_dir": "state",
        "reader_code": "wiring.py::emit_pain_assessment",
        "reader_evidence": "applied into protective score (historical applied=true)",
    },
    "vault_rag": {
        "description": "Vault RAG evidence injection into retrieval_router",
        "flag": "OCTOPUS_WIRE_VAULT_RAG",
        "artifact": "memory/memory.db",
        "artifact_dir": "state",
        "reader_code": "retrieval_router.py",
        "reader_evidence": "context injection at decision point",
    },
    "c6_hypothesis_producer": {
        "description": "C6 hypothesis → sandbox experiment → RFC card",
        "flag": "OCTOPUS_WIRE_C6_TRIGGER",
        "artifact": "c6/hypothesis-queue.jsonl",
        "artifact_dir": "state",
        "reader_code": "c6_trigger.py::c6_research_beat",
        "reader_evidence": "proposal-wired (human-gated RFC card)",
    },
    "doctor_self_knowledge": {
        "description": "Doctor self-knowledge smallest_fix",
        "flag": "OCTOPUS_WIRE_DOCTOR_SELFKNOW",
        "artifact": "doctor/self-knowledge-latest.json",
        "artifact_dir": "state",
        "reader_code": "organ_dialogue.py (display only)",
        "reader_evidence": "display-only (no machine action consumer)",
    },
    "body_bridge_reader": {
        "description": "kernel_bridge_reader (WP-D shadow reader)",
        "flag": "OCTOPUS_WIRE_KERNEL_BRIDGE_READER",
        "artifact": "kernel-bridge-reader-report.json",
        "artifact_dir": "state",
        "reader_code": "kernel_bridge_reader.py (this codebase)",
        "reader_evidence": "observability report (no decision consumer yet)",
    },
}


def classify_capability(name: str, spec: dict) -> dict:
    """Classify a single capability on the evidence ladder."""
    result = {
        "name": name,
        "description": spec.get("description", ""),
        "implemented": True,  # if it's in CAPABILITIES dict, code exists
        "configured": "unknown",
        "armed": "unknown",
        "executed_recently": "unknown",
        "artifact_fresh": "unknown",
        "consumed": "unknown",
        "decision_changing_evidence": "unknown",
        "effect_evidence": "unknown",
        "outcome_evidence": "unknown",
        "unknown_reasons": [],
    }

    # configured + armed: from flags-loaded snapshots
    flag = spec.get("flag")
    if flag:
        armed_status = _flag_armed(flag)
        result["armed"] = armed_status
        if armed_status == "armed":
            result["configured"] = "yes"
        elif armed_status == "disarmed":
            result["configured"] = "yes_but_off"
        else:
            result["configured"] = "unknown"
            result["unknown_reasons"].append(f"flag {flag} not in snapshots")
    else:
        result["configured"] = "no_flag"

    # artifact freshness
    artifact = spec.get("artifact")
    if artifact:
        # Artifacts live under STATE (which tests can override); some are in subdirs
        art_path = STATE / artifact
        if art_path.exists():
            # Try to get freshness from JSONL last entry or file mtime
            if art_path.suffix == ".jsonl":
                last_ts = _read_jsonl_last_ts(art_path)
                result["artifact_fresh"] = _is_fresh(last_ts)
                if last_ts:
                    result["executed_recently"] = result["artifact_fresh"]
            elif art_path.suffix == ".json":
                data = _read_json(art_path)
                if isinstance(data, dict):
                    ts = data.get("ts") or data.get("timestamp") or data.get("updated")
                    result["artifact_fresh"] = _is_fresh(ts)
                    if ts:
                        result["executed_recently"] = result["artifact_fresh"]
                else:
                    result["artifact_fresh"] = "unknown"
            else:
                result["artifact_fresh"] = "unknown"
        else:
            result["artifact_fresh"] = "missing"
            result["unknown_reasons"].append(f"artifact {artifact} not found")

    # consumed: based on reader_evidence description
    reader_ev = spec.get("reader_evidence", "")
    ev_lower_consumed = reader_ev.lower()
    # If the evidence explicitly says "no consumer" or "display-only", consumed = no
    has_no_consumer = any(p in ev_lower_consumed for p in
                          ["no machine action consumer", "no consumer",
                           "no decision consumer", "display-only"])
    has_reader = any(p in ev_lower_consumed for p in
                     ["injection", "applied into", "reader", "proposal-wired",
                      "context injection", "prompt-context", "scoring",
                      "report", "retrieval"])
    if has_no_consumer:
        result["consumed"] = "no"
    elif has_reader:
        result["consumed"] = "claimed"  # reader exists, but not independently verified here
        result["unknown_reasons"].append(
            "reader code exists; recent consumption not independently verified")
    else:
        result["consumed"] = "unknown"
        result["unknown_reasons"].append("no reader evidence found")

    # decision_changing: based on reader evidence
    # Be careful: "not autonomous decision" contains "decision" but means the
    # OPPOSITE. We check for negation patterns and affirmative patterns.
    ev_lower = reader_ev.lower()
    has_negation = any(neg in ev_lower for neg in
                       ["not autonomous", "no decision", "no machine action",
                        "no consumer", "not consumed", "display-only",
                        "observability only", "no production decision"])
    has_proposal = "proposal-wired" in ev_lower
    has_display = "display-only" in ev_lower or "observability" in ev_lower
    has_context = ("context injection" in ev_lower or
                    "prompt-context" in ev_lower)
    has_score = "applied into protective score" in ev_lower

    if has_negation or has_display:
        result["decision_changing_evidence"] = "no"
    elif has_proposal:
        result["decision_changing_evidence"] = "proposal-wired"
    elif has_context:
        result["decision_changing_evidence"] = "no"  # context ≠ decision
    elif has_score:
        result["decision_changing_evidence"] = "claimed"
    else:
        result["decision_changing_evidence"] = "unknown"

    # effect + outcome: never assumed from lower rungs
    result["effect_evidence"] = "unknown"
    result["unknown_reasons"].append("effect evidence requires trace/receipt audit")
    result["outcome_evidence"] = "unknown"
    result["unknown_reasons"].append("outcome evidence requires controlled measurement")

    return result


def classify_all() -> dict:
    """Classify all registered capabilities. Returns a structured report."""
    capabilities = {}
    for name, spec in CAPABILITIES.items():
        capabilities[name] = classify_capability(name, spec)

    # Summary counts
    from collections import Counter
    armed_count = sum(1 for c in capabilities.values() if c["armed"] == "armed")
    fresh_count = sum(1 for c in capabilities.values() if c["artifact_fresh"] == "fresh")
    consumed_count = sum(1 for c in capabilities.values() if c["consumed"] == "claimed")

    report = {
        "schema": SCHEMA,
        "ts": _utc_iso(),
        "freshness_threshold_h": FRESH_THRESHOLD_H,
        "n_capabilities": len(capabilities),
        "summary": {
            "implemented": len(capabilities),
            "armed": armed_count,
            "artifact_fresh": fresh_count,
            "consumed_claimed": consumed_count,
            "decision_changing": "see per-capability",
            "effect_evidence": 0,
            "outcome_evidence": 0,
        },
        "capabilities": capabilities,
        "note": ("Read-only classifier. Flag-on ≠ executed. Artifact-fresh ≠ consumed. "
                 "Consumed ≠ decision-changing. Missing evidence => UNKNOWN."),
    }

    return report


if __name__ == "__main__":
    r = classify_all()
    print(json.dumps(r, ensure_ascii=False, indent=2))
