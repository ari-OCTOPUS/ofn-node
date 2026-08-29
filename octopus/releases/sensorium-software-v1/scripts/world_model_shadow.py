#!/usr/bin/env python3
"""Persistence world-model shadow. Predictor only. Never calls planner. File IPC only."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, "/opt/octopus/cognition/src")
from octopus_cognition.ledger import ChainedLedger, state_hash  # noqa: E402
from octopus_cognition.world_model.contracts import PersistenceModel  # noqa: E402

HOMEO = Path("/var/lib/octopus/state/homeostasis/latest.json")
FUSION = Path("/var/lib/octopus/state/fusion/latest-frame.json")
DIR = Path("/var/lib/octopus/state/world_model")
LATEST = DIR / "latest.json"
BOOT = Path("/proc/sys/kernel/random/boot_id")
DOMAIN = "sensorium_health"
HORIZON_S = 30
ACTION = "NO_ACTION_OBSERVE_ONLY"
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


def unresolved(bodies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    done = {b.get("prediction_id") for b in bodies if b.get("schema") == "octopus.prediction-outcome.v1"}
    return [
        b
        for b in bodies
        if b.get("schema") == "octopus.prediction.v1" and b.get("prediction_id") not in done
    ]


def main() -> int:
    DIR.mkdir(parents=True, exist_ok=True)
    ledger = ChainedLedger(DIR, "octopus.prediction-ledger.head.v1")
    model = PersistenceModel()
    while True:
        homeo = _load(HOMEO)
        frame = _load(FUSION)
        now_ns = time.time_ns()
        bodies = ledger.bodies()
        pending = unresolved(bodies)
        inflight = [p for p in pending if int(p.get("due_at_ns") or 0) > now_ns]
        skip = bool(inflight) or len(pending) >= 3 or not homeo
        issued = None
        if not skip:
            state, missing = extract_state(homeo)
            usable = not missing and bool(state)
            t0 = time.perf_counter_ns()
            issued_at = now_ns
            hashed = state_hash(state) if state else "sha256:" + ("0" * 64)
            pred = model.predict(DOMAIN, state, ACTION, issued_at, hashed, HORIZON_S)
            cpu_ns = time.perf_counter_ns() - t0
            body = {
                "schema": "octopus.prediction.v1",
                "prediction_id": pred.prediction_id,
                "boot_id": BOOT.read_text(encoding="utf-8").strip() if BOOT.exists() else "",
                "domain": DOMAIN,
                "issued_at_ns": issued_at,
                "due_at_ns": issued_at + HORIZON_S * 1_000_000_000,
                "state_frame_hash": hashed,
                "fusion_frame_id": frame.get("frame_id"),
                "action": ACTION,
                "model_version": pred.model_version,
                "baseline_version": PersistenceModel.version,
                "state": state,
                "missing_mask": missing,
                "prediction": dict(pred.mean),
                "baseline": dict(state),
                "uncertainty": dict(pred.uncertainty),
                "status": "PENDING",
                "usable_at_issue": usable,
                "cost": {
                    "cpu_ns": cpu_ns,
                    "tokens": 0,
                    "rollouts": 0,
                    "planner_invoked": False,
                },
            }
            if usable:
                ledger.append(body)
                issued = body
            else:
                issued = {**body, "status": "SKIPPED_INCOMPLETE_STATE"}
        ok, _, detail = ledger.verify()
        LATEST.write_text(
            json.dumps(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "model_version": PersistenceModel.version,
                    "role": "predictor_shadow",
                    "planner_invoked": False,
                    "ledger_ok": ok,
                    "ledger_detail": detail,
                    "pending": len(unresolved(ledger.bodies())),
                    "last_prediction_id": (issued or {}).get("prediction_id"),
                    "skipped": skip or (issued or {}).get("status") == "SKIPPED_INCOMPLETE_STATE",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        time.sleep(5)


if __name__ == "__main__":
    raise SystemExit(main())
