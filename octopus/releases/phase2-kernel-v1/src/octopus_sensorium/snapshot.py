"""World-state snapshot + deterministic event replay. Not a source of truth about the world."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DIR = Path("/var/lib/octopus/state/snapshots")
DEFAULT_JOURNAL = Path("/var/lib/octopus/state/events.jsonl")


def canonical_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "identity": state.get("identity"),
        "health": state.get("health"),
        "observations_published": int(state.get("observations_published") or 0),
        "invalid_observations": int(state.get("invalid_observations") or 0),
        "readiness_profile": state.get("readiness_profile", "WAVE0_OBSERVE_ONLY"),
        "actuator_authority": state.get("actuator_authority", "NONE"),
        "leg_authority": state.get("leg_authority", "DENIED"),
        "observation_hashes": list(state.get("observation_hashes") or []),
    }


def state_hash(state: dict[str, Any]) -> str:
    blob = json.dumps(canonical_state(state), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def append_event(event: dict[str, Any], journal: Path = DEFAULT_JOURNAL) -> dict[str, Any]:
    journal.parent.mkdir(parents=True, exist_ok=True)
    seq = 0
    if journal.exists() and journal.stat().st_size:
        with journal.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    seq += 1
    event = {"seq": seq + 1, **event}
    line = json.dumps(event, separators=(",", ":"), ensure_ascii=False) + "\n"
    fd = os.open(journal, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o640)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    return event


def load_events(journal: Path = DEFAULT_JOURNAL, after_seq: int = 0) -> list[dict[str, Any]]:
    if not journal.exists():
        return []
    out = []
    with journal.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if int(rec.get("seq", 0)) > after_seq:
                out.append(rec)
    return sorted(out, key=lambda r: int(r["seq"]))


def apply_event(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    kind = event.get("kind")
    if kind == "obs":
        state["observations_published"] = int(state.get("observations_published") or 0) + 1
        hashes = list(state.get("observation_hashes") or [])
        digest = event.get("content_hash")
        if digest:
            hashes.append(digest)
            state["observation_hashes"] = hashes[-512:]
    elif kind == "invalid_obs":
        state["invalid_observations"] = int(state.get("invalid_observations") or 0) + 1
    elif kind == "health":
        health = dict(state.get("health") or {})
        health[event["sensor_id"]] = event["status"]
        state["health"] = health
    elif kind == "identity":
        state["identity"] = event.get("identity")
    return state


def replay(journal: Path = DEFAULT_JOURNAL, after_seq: int = 0, initial: dict[str, Any] | None = None) -> dict[str, Any]:
    state = dict(initial or {})
    for event in load_events(journal, after_seq=after_seq):
        apply_event(state, event)
    return state


def replay_matches_current(
    current: dict[str, Any],
    journal: Path = DEFAULT_JOURNAL,
) -> tuple[bool, str]:
    from_empty = replay(journal, after_seq=0, initial={})
    after = int(current.get("journal_seq") or 0)
    from_snapshot = replay(journal, after_seq=after, initial=canonical_state(current))
    left = state_hash(from_empty)
    right = state_hash(from_snapshot)
    return left == right, f"from_empty={left} from_snapshot={right} after_seq={after}"


def save_snapshot(state: dict[str, Any], directory: Path = DEFAULT_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    packed = dict(state)
    packed["state_hash"] = state_hash(packed)
    packed["journal_seq"] = 0
    if DEFAULT_JOURNAL.exists():
        events = load_events(DEFAULT_JOURNAL, after_seq=0)
        packed["journal_seq"] = events[-1]["seq"] if events else 0
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"snapshot-{ts}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(packed, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)
    latest = directory / "latest.json"
    latest.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def load_latest(directory: Path = DEFAULT_DIR) -> dict[str, Any] | None:
    latest = directory / "latest.json"
    if not latest.exists():
        return None
    return json.loads(latest.read_text(encoding="utf-8"))
