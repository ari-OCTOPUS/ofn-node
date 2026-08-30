#!/usr/bin/env python3
"""capability_probe.py — Probe-Based Self-Model Updater (EQUIP G10).

Capability claims without passing probe = NOT VERIFIED.
This module manages capability probes and ties probe results to self-model updates.

Design:
  1. Register capability claim with initial confidence.
  2. Probe the capability (run test/fixture).
  3. Update self-model only based on probe outcome.
  4. Claim without probe = UNVERIFIED, never VERIFIED.

Constraints:
  - Only probe results update capability status, not model self-reports.
  - Probe is read-only or fixture-based (no paid models).
  - Self-model only updated from runtime evidence, not from model output.
  - No capability claim can grant policy/goal/identity authority.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))
import opslib  # noqa: E402

CAPABILITY_STORE = opslib.STATE_DIR / "cognition" / "capability-probes.jsonl"
SCHEMA_VERSION = "capability-probe.v1"

# ── Capability states ─────────────────────────────────────────────────────────
CAPABILITY_CLAIMED = "CLAIMED"
CAPABILITY_PROBING = "PROBING"
CAPABILITY_VERIFIED = "VERIFIED"
CAPABILITY_FAILED = "FAILED"
CAPABILITY_STALE = "STALE"


def register_capability(
    capability_id: str,
    description: str,
    *,
    initial_confidence: float = 0.3,
    probe_type: str = "fixture",  # fixture, test, runtime
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Register a capability claim.

    Initial state is CLAIMED — not VERIFIED.
    Confidence starts at 0.3 (low) — must be confirmed by probe.
    """
    entry = {
        "schema_version": SCHEMA_VERSION,
        "capability_id": str(capability_id),
        "description": str(description)[:200],
        "status": CAPABILITY_CLAIMED,
        "confidence": float(max(0.0, min(1.0, initial_confidence))),
        "probe_type": str(probe_type),
        "registered_at": opslib.now_iso(),
        "last_probed_at": None,
        "probe_results": [],
        "metadata": metadata or {},
        # Invariant: capability claim never grants authority
        "grants_authority": False,
        "grants_policy_change": False,
        "grants_goal_change": False,
        "grants_identity_change": False,
    }

    try:
        CAPABILITY_STORE.parent.mkdir(parents=True, exist_ok=True)
        with CAPABILITY_STORE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass

    return entry


def record_probe_result(
    capability_id: str,
    probe_passed: bool,
    *,
    evidence: str = "",
    latency_ms: int = 0,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record probe result for a capability.

    Probe passed -> VERIFIED (confidence raised).
    Probe failed -> FAILED (confidence lowered, remains unverified).
    """
    probe_result = {
        "capability_id": str(capability_id),
        "passed": bool(probe_passed),
        "evidence": str(evidence)[:300],
        "latency_ms": int(latency_ms),
        "ts": opslib.now_iso(),
        "details": details or {},
    }

    # Update the capability record
    capabilities = read_capabilities()
    updated = False
    for cap in capabilities:
        if cap.get("capability_id") == capability_id:
            cap["last_probed_at"] = probe_result["ts"]
            cap["probe_results"].append(probe_result)
            # Keep only last 20 results
            cap["probe_results"] = cap["probe_results"][-20:]

            if probe_passed:
                cap["status"] = CAPABILITY_VERIFIED
                # Increase confidence: Bayesian update toward 1.0
                prior = cap["confidence"]
                cap["confidence"] = round(
                    min(1.0, prior + (1.0 - prior) * 0.5), 4)
            else:
                cap["status"] = CAPABILITY_FAILED
                # Decrease confidence: Bayesian update toward 0.0
                prior = cap["confidence"]
                cap["confidence"] = round(
                    max(0.0, prior * 0.5), 4)

            updated = True
            break

    if not updated:
        # Register as new if not found
        cap = register_capability(capability_id, "auto-registered from probe")
        cap["last_probed_at"] = probe_result["ts"]
        cap["probe_results"] = [probe_result]
        if probe_passed:
            cap["status"] = CAPABILITY_VERIFIED
            cap["confidence"] = 0.5
        else:
            cap["status"] = CAPABILITY_FAILED
            cap["confidence"] = 0.15
        capabilities.append(cap)

    # Persist updated store
    _write_capabilities(capabilities)
    return probe_result


def read_capabilities(capability_id: str | None = None) -> list[dict[str, Any]]:
    """Read capability records. Optionally filter by ID."""
    try:
        if not CAPABILITY_STORE.is_file():
            return []
        lines = CAPABILITY_STORE.read_text("utf-8", errors="replace").splitlines()
        entries = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    d = json.loads(line)
                    if isinstance(d, dict):
                        if capability_id is None or d.get("capability_id") == capability_id:
                            entries.append(d)
                except (json.JSONDecodeError, ValueError):
                    continue
        return entries
    except OSError:
        return []


def _write_capabilities(caps: list[dict[str, Any]]) -> None:
    """Write all capability records to store (atomic-ish)."""
    try:
        CAPABILITY_STORE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CAPABILITY_STORE.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            for cap in caps:
                f.write(json.dumps(cap, ensure_ascii=False) + "\n")
        tmp.replace(CAPABILITY_STORE)
    except OSError:
        pass


def get_capability_status(capability_id: str) -> dict[str, Any]:
    """Get current status of a capability.

    Returns {status, confidence, verified, probe_count}.
    If not found, returns UNVERIFIED with 0 confidence.
    """
    caps = read_capabilities(capability_id)
    if not caps:
        return {
            "capability_id": capability_id,
            "status": "UNKNOWN",
            "confidence": 0.0,
            "verified": False,
            "probe_count": 0,
            "reason": "capability_not_registered",
        }
    cap = caps[-1]  # Latest record
    return {
        "capability_id": cap.get("capability_id"),
        "status": cap.get("status"),
        "confidence": cap.get("confidence", 0.0),
        "verified": cap.get("status") == CAPABILITY_VERIFIED,
        "probe_count": len(cap.get("probe_results", [])),
        "last_probed_at": cap.get("last_probed_at"),
        "grants_authority": False,  # Invariant
    }


def self_model_summary() -> dict[str, Any]:
    """Get summary of all capabilities for self-model update.

    Only verified capabilities contribute to self-model.
    """
    caps = read_capabilities()
    total = len(caps)
    verified = [c for c in caps if c.get("status") == CAPABILITY_VERIFIED]
    failed = [c for c in caps if c.get("status") == CAPABILITY_FAILED]
    claimed = [c for c in caps if c.get("status") == CAPABILITY_CLAIMED]

    if total == 0:
        overall_confidence = 0.0
    else:
        overall_confidence = sum(c.get("confidence", 0.0) for c in caps) / total

    return {
        "total_capabilities": total,
        "verified_count": len(verified),
        "failed_count": len(failed),
        "claimed_count": len(claimed),
        "overall_confidence": round(overall_confidence, 4),
        "verified_capabilities": [
            {"id": c["capability_id"], "confidence": c["confidence"]}
            for c in verified
        ],
        "update_source": "probe_results_only",
        "ts": opslib.now_iso(),
    }


if __name__ == "__main__":
    # Self-test
    cap = register_capability("test.sort", "Can sort a list",
                              initial_confidence=0.3)
    print(f"Registered: {cap['status']} conf={cap['confidence']}")

    result = record_probe_result("test.sort", True,
                                 evidence="sorted [3,1,2] -> [1,2,3]")
    print(f"Probe passed: {result['passed']}")

    status = get_capability_status("test.sort")
    print(f"Status: {status['status']} verified={status['verified']} conf={status['confidence']}")

    summary = self_model_summary()
    print(f"Summary: {summary['verified_count']}/{summary['total_capabilities']} verified")
