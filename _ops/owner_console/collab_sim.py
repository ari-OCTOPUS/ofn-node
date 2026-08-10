#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collab_sim.py — deterministic echo simulation (WP-E6).

Multi-turn deterministic scenario:
  owner input → clarify → collaborator response → scrubbed memory
  → proposal card → digest → replay trace

No token/network/send/live state. Fixed seed = fixed output.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from owner_console import collaborator, collab_memory, collab_digest  # noqa: E402

SCHEMA = "CollabSim.v1"

# Frozen scenario (preregistered)
SCENARIO = [
    {"turn": 1, "role": "owner", "text": "هدف فعلی چیه؟"},
    {"turn": 2, "role": "owner", "text": "وضعیت runtime رو نشون بده"},
    {"turn": 3, "role": "owner", "text": "کدام موانع هستن؟"},
    {"turn": 4, "role": "owner", "text": "قابلیت‌ها رو لیست کن"},
    {"turn": 5, "role": "owner", "text": "این متن مبهم است که چی می‌خوای"},
]


def run_simulation(*, state_dir: Path | None = None) -> dict:
    """Run a deterministic multi-turn simulation.

    Returns a complete trace with all turns, memory records, digest, and replay info.
    """
    # Arm collaborator flags for simulation
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    os.environ["OCTOPUS_WIRE_COLLAB_MEMORY"] = "1"

    trace = []
    memory_records = []

    for step in SCENARIO:
        reply = collaborator.handle(step["text"], state_dir=state_dir)
        trace.append({
            "turn": step["turn"],
            "role": step["role"],
            "input": step["text"],
            "reply_kind": reply.get("kind"),
            "reply_text": str(reply.get("text", ""))[:200],
            "external_effect": reply.get("external_effect"),
            "estimated_cost": reply.get("estimated_cost"),
            "send_attempted": reply.get("send_attempted"),
            "rationale": (reply.get("data") or {}).get("rationale"),
            "model_source": reply.get("model_source"),
        })

    # Read memory records
    if state_dir:
        mem_path = state_dir / "collab-memory.jsonl"
        if mem_path.exists():
            for line in mem_path.read_text("utf-8").splitlines():
                try:
                    memory_records.append(json.loads(line))
                except ValueError:
                    continue

    # Build digest (with a fake snapshot for determinism)
    fake_snapshot = {
        "organism": {"beat": 99999, "halted": False, "frozen": False},
        "health": {},
        "flags": {"OCTOPUS_WIRE_COLLAB": "1"},
    }
    digest = collab_digest.build_digest(snapshot=fake_snapshot)

    # Cleanup flags
    os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)

    result = {
        "schema": SCHEMA,
        "n_turns": len(SCENARIO),
        "trace": trace,
        "memory_records": len(memory_records),
        "digest": digest,
        "deterministic": True,
        "note": ("DETERMINISTIC ECHO SIMULATION — no token/network/send/live state. "
                 "Fixed scenario = fixed output. Real efficacy requires real model."),
        "security_proof": {
            "all_external_effect_false": all(t["external_effect"] is False for t in trace),
            "all_cost_zero": all(t["estimated_cost"] == 0 for t in trace),
            "all_send_attempted_false": all(t["send_attempted"] is False for t in trace),
        },
    }

    return result


if __name__ == "__main__":
    import tempfile
    sd = Path(tempfile.mkdtemp(prefix="collab-sim-"))
    result = run_simulation(state_dir=sd)
    print(json.dumps(result, ensure_ascii=False, indent=2))
