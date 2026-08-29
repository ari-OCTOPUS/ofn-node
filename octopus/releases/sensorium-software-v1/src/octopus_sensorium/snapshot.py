"""World-state snapshot + deterministic event replay. Not a source of truth about the world."""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DIR = Path("/var/lib/octopus/state/snapshots")
DEFAULT_JOURNAL = Path("/var/lib/octopus/state/events.jsonl")


def _env_float(name: str, default: float) -> float:
    try:
        return max(1.0, float(os.environ.get(name, default)))
    except ValueError:
        return default


# replay_matches_current re-parses the whole journal; callers running it every
# tick would burn a full core once the journal grows. Cache per journal for at
# most this many seconds (verification, not authority — staleness is bounded).
REPLAY_VERIFY_MIN_INTERVAL = _env_float("OCTOPUS_REPLAY_VERIFY_INTERVAL", 60.0)
_REPLAY_CACHE: dict[str, tuple[float, tuple[bool, str]]] = {}


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


def _last_seq(journal: Path) -> int:
    """Last seq in the journal without scanning the whole file.

    Reads a small tail window backwards; falls back to a full line count only
    when the tail has no parseable line (e.g. oversized/corrupt tail).
    """
    if not journal.exists() or not journal.stat().st_size:
        return 0
    size = journal.stat().st_size
    with journal.open("rb") as handle:
        handle.seek(max(0, size - 65536))
        tail = handle.read()
    for raw in reversed(tail.splitlines()):
        if not raw.strip():
            continue
        try:
            return int(json.loads(raw).get("seq", 0))
        except ValueError:
            continue
    seq = 0
    with journal.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                seq += 1
    return seq


def append_event(event: dict[str, Any], journal: Path = DEFAULT_JOURNAL) -> dict[str, Any]:
    journal.parent.mkdir(parents=True, exist_ok=True)
    seq = _last_seq(journal)
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
            try:
                rec = json.loads(line)
            except ValueError:
                continue  # torn line from a crash mid-append; never crash-loop startup replay
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


def apply_event_dedup(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Copy/fixture replay that drops duplicate content hashes. Live G13 uses apply_event."""
    if event.get("kind") == "obs":
        digest = event.get("content_hash")
        hashes = list(state.get("observation_hashes") or [])
        if digest and digest in hashes:
            return state
    return apply_event(state, event)



def replay(journal: Path = DEFAULT_JOURNAL, after_seq: int = 0, initial: dict[str, Any] | None = None) -> dict[str, Any]:
    state = dict(initial or {})
    for event in load_events(journal, after_seq=after_seq):
        apply_event(state, event)
    return state


def replay_matches_current(
    current: dict[str, Any],
    journal: Path = DEFAULT_JOURNAL,
) -> tuple[bool, str]:
    key = str(journal)
    now = time.monotonic()
    cached = _REPLAY_CACHE.get(key)
    if cached is not None and (now - cached[0]) < REPLAY_VERIFY_MIN_INTERVAL:
        return cached[1]
    # Load the journal once so concurrent appends cannot make the two replays diverge.
    events = load_events(journal, after_seq=0)
    from_empty: dict[str, Any] = {}
    for event in events:
        apply_event(from_empty, event)
    after = int(current.get("journal_seq") or 0)
    from_snapshot = dict(canonical_state(current))
    for event in events:
        if int(event.get("seq") or 0) > after:
            apply_event(from_snapshot, event)
    left = state_hash(from_empty)
    right = state_hash(from_snapshot)
    result = (left == right, f"from_empty={left} from_snapshot={right} after_seq={after} n={len(events)}")
    _REPLAY_CACHE[key] = (now, result)
    return result


def save_snapshot(state: dict[str, Any], directory: Path = DEFAULT_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    packed = dict(state)
    packed["state_hash"] = state_hash(packed)
    packed["journal_seq"] = 0
    if DEFAULT_JOURNAL.exists():
        packed["journal_seq"] = _last_seq(DEFAULT_JOURNAL)
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


def diagnose_journal(journal: Path = DEFAULT_JOURNAL) -> dict[str, Any]:
    """Inspect a journal copy. Never rewrites the original file."""
    missing: list[int] = []
    duplicates: list[int] = []
    corrupt: list[int] = []
    seen_seq: set[int] = set()
    seen_hash: set[str] = set()
    last = 0
    count = 0
    if not journal.exists():
        return {"ok": True, "records": 0, "missing": [], "duplicates": [], "corrupt": []}
    with journal.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                corrupt.append(line_no)
                continue
            count += 1
            seq = int(rec.get("seq") or 0)
            if seq in seen_seq:
                duplicates.append(seq)
            seen_seq.add(seq)
            if last and seq > last + 1:
                missing.extend(range(last + 1, seq))
            last = max(last, seq)
            digest = rec.get("content_hash")
            if digest:
                if digest in seen_hash:
                    duplicates.append(seq)
                seen_hash.add(str(digest))
    return {
        "ok": not missing and not duplicates and not corrupt,
        "records": count,
        "missing": missing,
        "duplicates": duplicates,
        "corrupt": corrupt,
    }

