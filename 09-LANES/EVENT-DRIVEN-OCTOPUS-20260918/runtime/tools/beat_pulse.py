#!/usr/bin/env python3
"""beat_pulse.py — beat consumer that turns the 30s beat into idle events (2026-09-18).

No business logic lives here. Two jobs, both fail-closed:

  1. IDLE EVENT: when the event ledger has been quiet for IDLE_AFTER seconds and the
     beat is fresh, emit `idle` (kind=idle) once per IDLE_EVERY seconds. Consumers
     that should only work when there is nothing else to do (e.g. continuous lead
     discovery) are triggered by that event instead of a nightly systemd timer.

  2. RETRY SWEEPER: event files stuck in inbox/<kind>/ for > RETRY_AFTER seconds
     (a runner failed and left them) get re-touched, which re-fires the .path unit.
     Rate-limited per file by the touch itself.

Fail-closed: if beat.json is stale, the pulse emits nothing and touches nothing.
Daemon loop: 15s tick (cheap stat calls). CLI `--once` for tests.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import octopus_events as oe  # noqa: E402

IDLE_AFTER = float(os.environ.get("OCTOPUS_IDLE_AFTER_S", "600"))
IDLE_EVERY = float(os.environ.get("OCTOPUS_IDLE_EVERY_S", "600"))
RETRY_AFTER = float(os.environ.get("OCTOPUS_RETRY_AFTER_S", "600"))
TICK = float(os.environ.get("OCTOPUS_PULSE_TICK_S", "15"))
STATE = oe.EVENTS_ROOT / "pulse-state.json"


def _load() -> dict:
    try:
        return json.loads(STATE.read_text())
    except Exception:  # noqa: BLE001
        return {"last_idle_emit": 0.0}


def _save(st: dict) -> None:
    try:
        tmp = STATE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(st, indent=1), encoding="utf-8")
        os.replace(str(tmp), str(STATE))
    except Exception:  # noqa: BLE001
        pass


def ledger_age() -> float:
    try:
        return max(0.0, time.time() - oe.LEDGER.stat().st_mtime)
    except OSError:
        return float("inf")


def sweeper() -> list:
    """Re-touch stuck event files so their .path unit fires again. Returns touched names."""
    touched = []
    if not oe.INBOX.is_dir():
        return touched
    now = time.time()
    for kind_dir in sorted(p for p in oe.INBOX.iterdir() if p.is_dir()):
        for f in sorted(kind_dir.glob("*.json")):
            try:
                if now - f.stat().st_mtime > RETRY_AFTER:
                    os.utime(str(f), None)
                    touched.append("%s/%s" % (kind_dir.name, f.name))
            except OSError:
                continue
    return touched


def tick() -> dict:
    out = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if not oe.beat_fresh():
        out["beats"] = "STALE"          # fail-closed: emit nothing, touch nothing
        return out
    st = _load()
    age = ledger_age()
    out["ledger_age_s"] = None if age == float("inf") else round(age, 1)
    if age >= IDLE_AFTER and (time.time() - float(st.get("last_idle_emit", 0))) >= IDLE_EVERY:
        ev = oe.emit("idle", "idle-%d" % int(time.time()),
                     {"idle_for_s": round(age, 1), "reason": "no-domain-event"})
        st["last_idle_emit"] = time.time()
        _save(st)
        out["idle_event"] = ev["event_id"]
    touched = sweeper()
    if touched:
        out["retried"] = touched
    return out


def main() -> int:
    once = "--once" in sys.argv
    while True:
        try:
            res = tick()
            if os.environ.get("OCTOPUS_PULSE_VERBOSE") or once:
                print(json.dumps(res))
        except Exception as exc:  # noqa: BLE001 — daemon must never die silent
            try:
                oe._note_error("beat_pulse", "", exc)
            except Exception:  # noqa: BLE001
                pass
        if once:
            return 0
        time.sleep(TICK)


if __name__ == "__main__":
    raise SystemExit(main())
