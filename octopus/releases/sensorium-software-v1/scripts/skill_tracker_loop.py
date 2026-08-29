#!/usr/bin/env python3
"""Resolve due predictions against later state. Never rewrite predictions. Never import planner."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, "/opt/octopus/cognition/src")
from octopus_cognition.ledger import ChainedLedger, state_hash  # noqa: E402
from octopus_cognition.metacontrol.skill import DomainSkillTracker  # noqa: E402

HOMEO = Path("/var/lib/octopus/state/homeostasis/latest.json")
FUSION = Path("/var/lib/octopus/state/fusion/latest-frame.json")
WM_DIR = Path("/var/lib/octopus/state/world_model")
DIR = Path("/var/lib/octopus/state/skill")
LATEST = DIR / "latest.json"
WINDOW = DIR / "window.json"
STATE_KEYS = ("compute_pressure", "memory_pressure", "storage_integrity", "sensor_coverage")


def _load(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def extract_state(homeo: dict[str, Any]) -> tuple[dict[str, float], list[str]]:
    variables = homeo.get("variables") or {}
    state: dict[str, float] = {}
    missing: list[str] = []
    for key in STATE_KEYS:
        reading = variables.get(key) or {}
        value = reading.get("value")
        if value is None or reading.get("stale"):
            missing.append(key)
            continue
        state[key] = float(value)
    return state, missing


def mse(left: dict[str, float], right: dict[str, float], keys: tuple[str, ...]) -> float | None:
    diffs: list[float] = []
    for key in keys:
        if key not in left or key not in right:
            continue
        diffs.append((float(left[key]) - float(right[key])) ** 2)
    if not diffs:
        return None
    return sum(diffs) / len(diffs)


def main() -> int:
    DIR.mkdir(parents=True, exist_ok=True)
    ledger = ChainedLedger(WM_DIR, "octopus.prediction-ledger.head.v1")
    tracker = DomainSkillTracker(window=200, minimum=50)
    saved = _load(WINDOW)
    if saved:
        tracker.loads(saved)
    while True:
        homeo = _load(HOMEO)
        frame = _load(FUSION)
        now_ns = time.time_ns()
        observed, missing = extract_state(homeo)
        bodies = ledger.bodies()
        done = {b.get("prediction_id") for b in bodies if b.get("schema") == "octopus.prediction-outcome.v1"}
        resolved = 0
        for pred in bodies:
            if pred.get("schema") != "octopus.prediction.v1":
                continue
            pid = pred.get("prediction_id")
            if pid in done:
                continue
            if int(pred.get("due_at_ns") or 0) > now_ns:
                continue
            model_loss = mse(pred.get("prediction") or {}, observed, STATE_KEYS)
            baseline_loss = mse(pred.get("baseline") or pred.get("state") or {}, observed, STATE_KEYS)
            usable = (
                bool(pred.get("usable_at_issue"))
                and not missing
                and model_loss is not None
                and baseline_loss is not None
            )
            reason = None
            if not pred.get("usable_at_issue"):
                reason = "incomplete_at_issue"
            elif missing:
                reason = "incomplete_at_outcome"
            elif model_loss is None:
                reason = "no_overlap"
            outcome = {
                "schema": "octopus.prediction-outcome.v1",
                "prediction_id": pid,
                "observed_state_frame_hash": state_hash(observed) if observed else None,
                "fusion_frame_id": frame.get("frame_id"),
                "resolved_at_ns": now_ns,
                "observed": observed,
                "missing_mask": missing,
                "model_loss": model_loss,
                "baseline_loss": baseline_loss,
                "usable": usable,
                "exclusion_reason": reason,
            }
            ledger.append(outcome)
            if usable:
                tracker.record(float(model_loss), float(baseline_loss))
                resolved += 1
            done.add(pid)
        report = tracker.report()
        WINDOW.write_text(json.dumps(tracker.dumps()) + "\n", encoding="utf-8")
        LATEST.write_text(
            json.dumps(
                {
                    "schema": "octopus.skill.v1",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "domain": "sensorium_health",
                    "baseline_version": "persistence-v1",
                    "model_version": "persistence-v1",
                    "score": report.score,
                    "lower_bound": report.lower_bound,
                    "samples": report.samples,
                    "eligible": report.eligible,
                    "reason": report.reason,
                    "calibration_error": report.calibration_error,
                    "model_mse": report.model_mse,
                    "baseline_mse": report.baseline_mse,
                    "resolved_this_tick": resolved,
                    "planner_invoked": False,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        time.sleep(5)


if __name__ == "__main__":
    raise SystemExit(main())
