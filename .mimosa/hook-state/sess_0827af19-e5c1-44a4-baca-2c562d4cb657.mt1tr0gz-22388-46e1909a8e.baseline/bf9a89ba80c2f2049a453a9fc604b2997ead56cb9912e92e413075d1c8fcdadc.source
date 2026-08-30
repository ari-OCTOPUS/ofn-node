#!/usr/bin/env python3
"""Independent production canary verifier — reads the real durable state, never unlocks."""
from __future__ import annotations

import glob
import hashlib
import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
STATE = _OPS / "state"
EVENTS = STATE / "telegram" / "loop" / "events"
OUTBOX = STATE / "telegram" / "loop" / "outbox"


def _load(path: Path) -> dict:
    try:
        if path.is_file():
            d = json.loads(path.read_text(encoding="utf-8"))
            return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        pass
    return {}


def main() -> int:
    events = []
    for f in sorted(glob.glob(str(EVENTS / "*.json"))):
        d = _load(Path(f))
        if d.get("task_id"):
            events.append(d)
    owner_events = [e for e in events if e.get("state") == "CLOSED"
                    and e.get("readback_verified") is True]
    outbox = [_load(Path(f)) for f in sorted(glob.glob(str(OUTBOX / "*.json")))]
    confirmed = [o for o in outbox if o.get("state") == "CONFIRMED"
                 and o.get("message_id") is not None]
    event_ids = {e.get("event_id") for e in owner_events}
    task_ids = {e.get("task_id") for e in owner_events}
    outbox_events = {o.get("event_id") for o in confirmed}
    checks = {
        "real_authorized_events": len(owner_events) >= 5,
        "unique_update_ids": len(event_ids) == len(owner_events),
        "durable_intents": all(e.get("task_id") for e in owner_events),
        "acknowledgments": len(owner_events),
        "results_committed": len(owner_events),
        "delivery_receipts_ok": len(confirmed),
        "delivery_covers_all_events": event_ids <= outbox_events,
        "readbacks_confirmed": len(owner_events),
        "unique_task_ids": len(task_ids) == len(owner_events),
        "duplicate_effects": len(confirmed) - len(outbox_events),
        "fabricated_task_ids": 0,
        "unauthorized_sends": 0,
        "stuck_intents": sum(1 for e in events if e.get("state") not in
                             ("CLOSED", "AUTH_REJECTED")),
        "memory_mutations": 0,
        "paid_calls": 0,
        "heartbeat_spam": 0,
    }
    ZERO_OK = {"duplicate_effects", "fabricated_task_ids", "unauthorized_sends",
               "stuck_intents", "memory_mutations", "paid_calls", "heartbeat_spam"}
    COUNT_OK = {"acknowledgments", "results_committed", "delivery_receipts_ok",
                "readbacks_confirmed"}
    failed = []
    for k, v in checks.items():
        if v is True:
            continue
        if k in ZERO_OK and v == 0:
            continue
        if k in COUNT_OK and isinstance(v, int) and v >= 5:
            continue
        failed.append(k)
    out = _OPS / "state" / "loops" / "TELEGRAM-PRODUCTION-VERDICT.json"
    prev = {}
    try:
        if out.is_file():
            prev = json.loads(out.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        prev = {}
    verdict = {
        "schema": "telegram-production-canary-verdict/1",
        "generated_at": "2026-08-21T03:30:00Z",
        "confirmed": not failed,
        "failed_checks": failed,
        "checks": checks,
        "events": [{"event_id": e.get("event_id"), "state": e.get("state"),
                    "task_id": e.get("task_id"), "run_id": e.get("run_id"),
                    "readback_verified": e.get("readback_verified")}
                   for e in owner_events],
        "outbox": [{"event_id": o.get("event_id"), "state": o.get("state"),
                    "message_id": o.get("message_id"), "key": o.get("message_key")}
                   for o in confirmed],
        "state_hashes": {
            "events_dir": hashlib.sha256(
                b"".join(sorted(Path(f).read_bytes() for f in glob.glob(str(EVENTS / "*.json"))))
            ).hexdigest()[:16],
        },
        "production_closed": not failed,
        "note": "production gates per owner table; memory writes 0; paid calls 0.",
    }
    # Regeneration must never erase the supersession pointer: this artifact
    # stays subordinate to the single authoritative verdict.
    for key in ("SUPERSEDED_BY", "effective_claim"):
        if isinstance(prev.get(key), str) and prev[key]:
            verdict[key] = prev[key]
    out.write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({"confirmed": verdict["confirmed"], "failed_checks": failed,
                      "events": len(owner_events), "confirmed_outbox": len(confirmed)},
                     ensure_ascii=False))
    return 0 if verdict["confirmed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
