"""Append-only evidence files. Existing records are never rewritten.

Index writes are batched: each observation appends a small durable record to
indexes/pending.jsonl; the six JSON index files are rewritten at most once per
OCTOPUS_INDEX_FLUSH_EVERY observations or OCTOPUS_INDEX_FLUSH_MAX_AGE seconds.
On startup a non-empty pending journal is merged into the indexes first, so a
crash never loses index state (observations.jsonl stays the source of truth).
"""

from __future__ import annotations

import atexit
import json
import os
import time
from pathlib import Path
from typing import Any

from octopus_sensorium.evidence.canonical_json import canonical_json
from octopus_sensorium.evidence.content_hash import content_hash

DEFAULT_DIR = Path("/var/lib/octopus/state/evidence")
JSONL_NAME = "observations.jsonl"
RETENTION_SECONDS = 14 * 24 * 3600

INDEX_NAMES = ("event_id", "sensor_id", "sequence", "timestamp", "subject", "observed_property")
BUCKET_INDEXES = ("sensor_id", "subject", "observed_property")
PENDING_NAME = "indexes/pending.jsonl"


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return max(1.0, float(os.environ.get(name, default)))
    except ValueError:
        return default


INDEX_FLUSH_EVERY = _env_int("OCTOPUS_INDEX_FLUSH_EVERY", 200)
INDEX_FLUSH_MAX_AGE = _env_float("OCTOPUS_INDEX_FLUSH_MAX_AGE", 300.0)


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o640)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def _index_path(directory: Path, name: str) -> Path:
    return directory / "indexes" / f"{name}.json"


def _load_index(directory: Path, name: str) -> dict[str, Any]:
    path = _index_path(directory, name)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_index(directory: Path, name: str, data: dict[str, Any]) -> None:
    path = _index_path(directory, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _apply_entry(idx: dict[str, Any], name: str, obs: dict[str, Any], offset: int, digest: str) -> bool:
    event_id = str(obs.get("event_id") or "")
    sensor_id = str(obs.get("sensor_id") or "")
    seq = str(obs.get("sequence_number") or "")
    ts = str((obs.get("time") or {}).get("ingestion_time") or "")
    subject = str(((obs.get("subject") or {}).get("entity_id")) or "")
    prop = str(obs.get("observed_property") or "")
    if name == "event_id" and event_id:
        idx[event_id] = {"offset": offset, "hash": digest, "sensor_id": sensor_id}
    elif name == "sensor_id" and sensor_id:
        bucket = list(idx.get(sensor_id) or [])
        bucket.append(event_id)
        idx[sensor_id] = bucket[-4096:]
    elif name == "sequence" and seq and sensor_id:
        idx[f"{sensor_id}:{seq}"] = event_id
    elif name == "timestamp" and ts:
        idx[ts] = event_id
    elif name == "subject" and subject:
        bucket = list(idx.get(subject) or [])
        bucket.append(event_id)
        idx[subject] = bucket[-4096:]
    elif name == "observed_property" and prop:
        bucket = list(idx.get(prop) or [])
        bucket.append(event_id)
        idx[prop] = bucket[-4096:]
    else:
        return False
    return True


def _update_indexes(directory: Path, obs: dict[str, Any], offset: int, digest: str) -> None:
    """Immediate (unbatched) index update. Kept for compatibility/tooling."""
    for name in INDEX_NAMES:
        idx = _load_index(directory, name)
        if _apply_entry(idx, name, obs, offset, digest):
            _save_index(directory, name, idx)


class _DirState:
    def __init__(self) -> None:
        self.pending: list[dict[str, Any]] = []
        self.first_pending_at: float | None = None
        self.event_ids: set[str] | None = None
        self.recovered = False


_states: dict[str, _DirState] = {}


def _pending_path(directory: Path) -> Path:
    return directory / PENDING_NAME


def _dedupe_buckets(idx: dict[str, Any]) -> None:
    for value in idx.values():
        if isinstance(value, list):
            seen: set[str] = set()
            out: list[str] = []
            for item in value:
                if item not in seen:
                    seen.add(item)
                    out.append(item)
            value[:] = out[-4096:]


def _apply_entries(directory: Path, entries: list[dict[str, Any]]) -> None:
    for name in INDEX_NAMES:
        idx = _load_index(directory, name)
        dirty = False
        for entry in entries:
            obs = entry.get("obs") or {}
            dirty = _apply_entry(idx, name, obs, int(entry.get("offset") or 0), str(entry.get("digest") or "")) or dirty
        if dirty:
            _save_index(directory, name, idx)


def _truncate_pending(directory: Path) -> None:
    path = _pending_path(directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8"):
        pass


def _recover_pending(directory: Path, st: _DirState) -> None:
    path = _pending_path(directory)
    if not path.exists() or path.stat().st_size == 0:
        return
    entries: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except ValueError:
                continue  # torn tail line from a crash; earlier lines are intact
    except OSError:
        return
    if entries:
        _apply_entries(directory, entries)
        for name in BUCKET_INDEXES:
            idx = _load_index(directory, name)
            _dedupe_buckets(idx)
            _save_index(directory, name, idx)
    _truncate_pending(directory)


def _state(directory: Path) -> _DirState:
    key = str(directory)
    st = _states.get(key)
    if st is None:
        st = _DirState()
        _states[key] = st
    if not st.recovered:
        st.recovered = True
        _recover_pending(directory, st)
    return st


def flush_indexes(directory: Path = DEFAULT_DIR) -> int:
    """Merge pending index updates into the JSON indexes. Returns entries flushed."""
    st = _states.get(str(directory))
    if st is None or not st.pending:
        return 0
    entries = st.pending
    st.pending = []
    st.first_pending_at = None
    _apply_entries(directory, entries)
    _truncate_pending(directory)
    return len(entries)


def _queue_index_update(directory: Path, obs: dict[str, Any], offset: int, digest: str, st: _DirState) -> None:
    entry = {"obs": obs, "offset": offset, "digest": digest}
    st.pending.append(entry)
    if st.first_pending_at is None:
        st.first_pending_at = time.monotonic()
    _append_jsonl(_pending_path(directory), {"event_id": obs.get("event_id"), "offset": offset, "digest": digest, "obs": obs})
    if len(st.pending) >= INDEX_FLUSH_EVERY or (time.monotonic() - st.first_pending_at) >= INDEX_FLUSH_MAX_AGE:
        flush_indexes(directory)


def _load_event_ids(directory: Path, st: _DirState) -> set[str]:
    if st.event_ids is None:
        st.event_ids = set(_load_index(directory, "event_id").keys())
        for entry in st.pending:
            event_id = str((entry.get("obs") or {}).get("event_id") or "")
            if event_id:
                st.event_ids.add(event_id)
    return st.event_ids


def detect_duplicate(obs: dict[str, Any], directory: Path = DEFAULT_DIR) -> bool:
    event_id = str(obs.get("event_id") or "")
    if not event_id:
        return False
    return event_id in _load_event_ids(directory, _state(directory))


def persist_observation(sensor_id: str, obs: dict[str, Any], directory: Path = DEFAULT_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    st = _state(directory)
    digest = content_hash(canonical_json(obs))
    jsonl = directory / JSONL_NAME
    offset = jsonl.stat().st_size if jsonl.exists() else 0
    if detect_duplicate(obs, directory):
        return directory / f"last_{sensor_id.replace('.', '_')}.json"
    record = {
        "event_id": obs.get("event_id"),
        "sensor_id": sensor_id,
        "content_hash": digest,
        "observation": obs,
    }
    _append_jsonl(jsonl, record)
    _queue_index_update(directory, obs, offset, digest, st)
    event_id = str(obs.get("event_id") or "")
    if event_id and st.event_ids is not None:
        st.event_ids.add(event_id)
    blob = json.dumps(obs, indent=2, ensure_ascii=False)
    last = directory / "last_l1_observation.json"
    last.write_text(blob, encoding="utf-8")
    safe_id = sensor_id.replace(".", "_")
    path = directory / f"last_{safe_id}.json"
    path.write_text(blob, encoding="utf-8")
    (directory / f"last_{safe_id}.hash").write_text(digest + "\n", encoding="utf-8")
    if obs.get("observation_type") == "event":
        (directory / f"last_{safe_id}_event.json").write_text(blob, encoding="utf-8")
    return path


def persist_derived(sensor_id: str, event: dict[str, Any], directory: Path = DEFAULT_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    safe = sensor_id.replace(".", "_")
    path = directory / f"last_{safe}.json"
    path.write_text(json.dumps(event, indent=2, ensure_ascii=False), encoding="utf-8")
    derived = directory / "derived.jsonl"
    _append_jsonl(
        derived,
        {"sensor_id": sensor_id, "event_id": event.get("event_id"), "event": event},
    )
    return path


def verify_jsonl(directory: Path = DEFAULT_DIR) -> tuple[bool, str]:
    path = directory / JSONL_NAME
    if not path.exists():
        return True, "empty"
    count = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                return False, f"corrupt json at record {count + 1}"
            obs = rec.get("observation") or {}
            expected = rec.get("content_hash")
            if expected and expected != content_hash(canonical_json(obs)):
                return False, f"hash mismatch at {obs.get('event_id')}"
            count += 1
    return True, f"records={count}"


def _flush_all_at_exit() -> None:
    for key in list(_states):
        try:
            flush_indexes(Path(key))
        except Exception:
            pass


atexit.register(_flush_all_at_exit)
