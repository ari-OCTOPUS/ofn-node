#!/usr/bin/env python3
"""octopus_events.py — tiny event spine for the revenue cycles (EVENT-DRIVEN-OCTOPUS 2026-09-18).

Design (no new brain, no orchestrator — a transport only):
  1. `emit(kind, item_id, payload)` writes ONE event file into
     state/events/inbox/<kind>/<utc>-<sha8>.json  (atomic tmp+rename).
     That file IS the trigger: systemd .path units watch the inbox dirs.
  2. The same event is appended to state/events/ledger.jsonl (local record).
  3. Best-effort publish `octopus.events.<kind>` on the local NATS leaf
     (127.0.0.1:4223) so the hub JetStream keeps the cross-node record.
     A dead leaf NEVER blocks the cycle: the file already exists.

Fail-closed is enforced at the consumer side by octopus_event_gate.sh which
refuses to run any runner while the local beat file is stale.

Stdlib only. Never raises from emit(): a broken bus must not break money code —
but the receipt path is checked first, and failures are recorded, not swallowed
silently (state/events/emit-errors.jsonl).
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import socket
import sys
import time

EVENTS_ROOT = pathlib.Path(os.environ.get("OCTOPUS_EVENTS_ROOT", "/home/ari/ofn/state/events"))
INBOX = EVENTS_ROOT / "inbox"
LEDGER = EVENTS_ROOT / "ledger.jsonl"
ERRORS = EVENTS_ROOT / "emit-errors.jsonl"
BEAT = EVENTS_ROOT / "beat.json"
NATS_ADDR = os.environ.get("OCTOPUS_NATS_ADDR", "127.0.0.1:4223")
SCHEMA = "octopus.event.v1"


def node_id() -> str:
    n = os.environ.get("OCTOPUS_NODE")
    if n:
        return str(n)
    try:
        out = os.popen("hostname -I").read().split()
        if out:
            return out[0].split(".")[-1]
    except Exception:  # noqa: BLE001
        pass
    return socket.gethostname()[-3:]


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def nats_publish(subject: str, payload: bytes, timeout: float = 2.0) -> bool:
    """Raw NATS protocol PUB to the local leaf. Best-effort; returns False on any trouble."""
    try:
        host, port = NATS_ADDR.split(":")
        s = socket.create_connection((host, int(port)), timeout=timeout)
        try:
            s.recv(4096)  # INFO
            s.sendall(b'CONNECT {"verbose":false,"pedantic":false,"name":"octopus-events"}\r\n')
            s.sendall(b"PUB %s %d\r\n" % (subject.encode(), len(payload)) + payload + b"\r\n")
            s.sendall(b"PING\r\n")
            s.settimeout(timeout)
            try:
                s.recv(64)
            except OSError:
                pass
        finally:
            s.close()
        return True
    except Exception:  # noqa: BLE001
        return False


def emit(kind: str, item_id: str = "", payload: dict | None = None,
         durable: bool = True) -> dict:
    """Write one event file (trigger) + ledger row + best-effort NATS publish."""
    payload = payload or {}
    at = _utc()
    base = {"schema": SCHEMA, "kind": kind, "at": at, "node": node_id(),
            "item_id": str(item_id or ""), "payload": payload}
    sha = _sha(base)
    ev = dict(base, sha256=sha, event_id="%s-%s" % (at, sha[:8]))
    blob = json.dumps(ev, sort_keys=True, ensure_ascii=False, default=str)
    try:
        if durable:
            d = INBOX / kind
            d.mkdir(parents=True, exist_ok=True)
            f = d / (ev["event_id"].replace(":", "") + ".json")
            tmp = f.with_suffix(".json.tmp")
            tmp.write_text(blob + "\n", encoding="utf-8")
            os.replace(str(tmp), str(f))
        with LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(blob + "\n")
    except Exception as exc:  # noqa: BLE001
        _note_error(kind, item_id, exc)
        return ev
    nats_publish("octopus.events." + kind, blob.encode("utf-8"))
    return ev


def _note_error(kind: str, item_id: str, exc: Exception) -> None:
    try:
        ERRORS.parent.mkdir(parents=True, exist_ok=True)
        with ERRORS.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": _utc(), "kind": kind, "item_id": str(item_id),
                                 "error": "%s: %s" % (type(exc).__name__, exc)}) + "\n")
    except Exception:  # noqa: BLE001
        pass


def beat_age_s() -> float:
    try:
        return max(0.0, time.time() - BEAT.stat().st_mtime)
    except OSError:
        return float("inf")


def beat_fresh(max_age: float = 150.0) -> bool:
    return beat_age_s() <= max_age


def _cli() -> int:
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "emit":
        kind = argv[1]
        payload = {}
        item = ""
        i = 2
        while i < len(argv):
            if argv[i] == "--item-id":
                item = argv[i + 1]; i += 2
            elif argv[i] == "--payload":
                payload = json.loads(argv[i + 1]); i += 2
            else:
                i += 1
        ev = emit(kind, item, payload)
        print(json.dumps({"ok": True, "event_id": ev["event_id"], "sha256": ev["sha256"]}))
        return 0
    if cmd == "beat-age":
        age = beat_age_s()
        print(json.dumps({"age_s": None if age == float("inf") else round(age, 1),
                          "fresh": beat_fresh(), "beat_file": str(BEAT)}))
        return 0
    if cmd == "pending":
        d = INBOX / (argv[1] if len(argv) > 1 else "")
        if not d.is_dir():
            print("[]")
            return 0
        print(json.dumps([p.name for p in sorted(d.glob("*.json"))]))
        return 0
    print("unknown command: %s" % cmd, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
