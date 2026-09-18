#!/usr/bin/env python3
"""octopus_beat.py — the single heartbeat source for the event spine (2026-09-18).

Called by ofn-heartbeat.sh once per 30s beat. Writes state/events/beat.json
(atomic) and publishes `octopus.beat.<node>` on the local NATS leaf.

beat.json is the SYSTEM CLOCK for the event-driven cycles: every gated consumer
refuses to run while it is stale (fail-closed). seq is persisted so it stays
monotonic across daemon restarts.

stdlib only.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import octopus_events as oe  # noqa: E402

SEQ = oe.EVENTS_ROOT / "beat-seq.txt"


def main() -> int:
    try:
        seq = int(SEQ.read_text().strip())
    except Exception:  # noqa: BLE001
        seq = 0
    seq += 1
    try:
        oe.EVENTS_ROOT.mkdir(parents=True, exist_ok=True)
        SEQ.write_text(str(seq), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    try:
        load = float(open("/proc/loadavg").read().split()[0])
    except Exception:  # noqa: BLE001
        load = None
    beat = {"schema": "octopus.beat.v1", "node": oe.node_id(), "seq": seq,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "epoch": round(time.time(), 3), "load1": load,
            "host": os.uname().nodename if hasattr(os, "uname") else ""}
    blob = json.dumps(beat, sort_keys=True)
    try:
        tmp = oe.BEAT.with_suffix(".json.tmp")
        tmp.write_text(blob + "\n", encoding="utf-8")
        os.replace(str(tmp), str(oe.BEAT))
    except Exception as exc:  # noqa: BLE001
        oe._note_error("beat", str(seq), exc)
        print(json.dumps({"ok": False, "error": type(exc).__name__}))
        return 1
    ok = oe.nats_publish("octopus.beat." + beat["node"], blob.encode("utf-8"))
    print(json.dumps({"ok": True, "seq": seq, "nats": ok}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
