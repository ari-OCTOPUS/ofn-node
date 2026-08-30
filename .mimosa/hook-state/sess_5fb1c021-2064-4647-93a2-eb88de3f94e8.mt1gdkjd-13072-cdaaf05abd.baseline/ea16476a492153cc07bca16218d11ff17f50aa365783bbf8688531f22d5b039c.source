"""Off-loop entrypoint. Reads (read-only) -> computes 5 metrics -> optionally emits
to the epi stream -> writes _ops/state/epi-latest.json. Does NOT import organism.py.
Advisory and reversible.

Numbers are MEANINGLESS until Phase 1-3 fill upstream data. Do NOT wire into the
loop before Phase 5 (behind OCTOPUS_WIRE_EPISTEMICS).

Usage:
    python -m _ops.epistemics.run_offloop            # print only (default)
    python -m _ops.epistemics.run_offloop --emit     # also append to epi-ledger
"""
from __future__ import annotations

import argparse
import json
import os
import time

from . import emit as emitter
from . import metrics, readers

EPI_LATEST = "_ops/state/epi-latest.json"


def compute_all() -> list:
    fitness = readers.read_fitness_history() or []
    # TODO(GLM): map real fields -> the inputs below once upstream data exists.
    state_labels = fitness if isinstance(fitness, list) else []
    sv = readers.read_self_vs_twin()
    return [
        metrics.identifiability(state_labels),
        metrics.channel([]),                         # TODO: paired (H, H_hat) from telemetry/reconcile
        metrics.levels(readers.read_topology()),
        metrics.self_reference(sv["err_self"], sv["err_other"]) if sv else metrics.self_reference([], []),
        metrics.method(),
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true", help="append to the epi stream (default: print only)")
    args = ap.parse_args()

    results = compute_all()
    snapshot = {
        "ts": time.time(),
        "metrics": results,
        "note": "OFF-LOOP scaffold; not authoritative until upstream data is live",
    }

    if args.emit:
        for r in results:
            emitter.emit(r, dedup_key=f"{r['metric']}:{int(snapshot['ts'])}")
        os.makedirs(os.path.dirname(EPI_LATEST), exist_ok=True)
        with open(EPI_LATEST, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
