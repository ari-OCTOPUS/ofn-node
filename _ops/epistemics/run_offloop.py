"""Off-loop entrypoint. Reads (read-only) -> computes 5 metrics -> optionally emits
to the epi stream -> writes _ops/state/epi-latest.json. Does NOT import organism.py.
Advisory and reversible.

Numbers remain non-authoritative until sample_size >= MIN_SAMPLES (contracts.py).
Do NOT treat as authoritative solely because readers now return non-null samples.
Wire into the loop only behind OCTOPUS_WIRE_EPISTEMICS (Phase 5).

Usage:
    python -m _ops.epistemics.run_offloop            # print only (default)
    python -m _ops.epistemics.run_offloop --emit     # also append to epi-ledger
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from . import emit as emitter
from . import metrics, readers

_OPS = Path(__file__).resolve().parent.parent
EPI_LATEST = str(_OPS / "state" / "epi-latest.json")


def compute_all(ops=None) -> list:
    """Compute five metrics from on-disk readers. Fail-closed on empty inputs."""
    labels = readers.read_state_labels(ops)
    pairs = readers.read_channel_pairs(ops)
    topo = readers.read_topology(ops)
    sv = readers.read_self_vs_twin(ops)
    return [
        metrics.identifiability(labels),
        metrics.channel(pairs),
        metrics.levels(topo),
        (
            metrics.self_reference(sv["err_self"], sv["err_other"])
            if sv
            else metrics.self_reference([], [])
        ),
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
        "note": (
            "OFF-LOOP; readers wired to on-disk uniqueness/outbox/self_audit/"
            "self_accuracy. Not authoritative until MIN_SAMPLES; NOT a "
            "consciousness claim."
        ),
        "reader_sample_sizes": {
            "state_labels": len(readers.read_state_labels()),
            "channel_pairs": len(readers.read_channel_pairs()),
            "topology": (lambda _t: 0 if _t is None else len(_t))(readers.read_topology()),
            "self_vs_twin": (
                len((readers.read_self_vs_twin() or {}).get("err_self") or [])
            ),
            "outbox_counts": readers.read_outbox_counts(),
        },
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
