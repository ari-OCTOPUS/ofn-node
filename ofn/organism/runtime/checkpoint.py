"""Versioned checkpoint receipt parser.

The live-skin watcher crashed with KeyError('events') because the observer
expected top-level `events` while the writer stored `latest_event` plus a
nested `database_schema.events`. That is an observer/schema mismatch, not a
truncated file and not a license to invent missing mandatory values.
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CURRENT_SCHEMA_VERSION = 1
KNOWN_SCHEMA_VERSIONS = frozenset({0, 1})

# Historical aliases. Mapping a known old name to a new name is not invention.
# Inventing a numeric default when every alias is absent is forbidden.
MANDATORY_ALIASES: dict[str, tuple[str, ...]] = {
    "old_pid": ("old_pid",),
    "identity_head": ("identity_head",),
    "events": ("events", "latest_event"),
    "episode_count": ("episode_count", "latest_episode_count"),
    "outbox_count": ("outbox_count", "latest_outbox_count"),
    "source_hash": ("source_hash", "git_head"),
}

NESTED_FALLBACK = {
    "identity_head": ("database_schema", "identity_head"),
    "events": ("database_schema", "events"),
    "episode_count": ("database_schema", "episode_count"),
    "outbox_count": ("database_schema", "outbox_count"),
}

OPTIONAL_ALIASES: dict[str, tuple[str, ...]] = {
    "soak_samples": ("soak_samples",),
    "soak_abort": ("soak_abort",),
    "wal_size_bytes": ("wal_size_bytes",),
    "schema_version_before": ("schema_version_before",),
    "new_pid": ("new_pid",),
}


class CheckpointError(ValueError):
    """Structured receipt error. Never used to stuff fake mandatory values."""


@dataclass(frozen=True)
class CheckpointErrorReport:
    kind: str
    path: str | None
    missing: tuple[str, ...] = ()
    message: str = ""
    schema_version: int | None = None
    traceback_note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "path": self.path,
            "missing": list(self.missing),
            "message": self.message,
            "schema_version": self.schema_version,
            "traceback_note": self.traceback_note,
            "invented_mandatory_values": False,
        }


@dataclass(frozen=True)
class ParsedCheckpoint:
    schema_version: int
    payload: dict[str, Any]
    source_path: str | None
    optional: dict[str, Any]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _lookup(payload: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in payload and payload[name] is not None:
            return payload[name]
    return None


def _nested(payload: dict[str, Any], parent: str, child: str) -> Any:
    block = payload.get(parent)
    if isinstance(block, dict) and child in block and block[child] is not None:
        return block[child]
    return None


def detect_schema_version(payload: dict[str, Any]) -> int:
    raw = payload.get("checkpoint_schema_version")
    if raw is None:
        return 0
    try:
        version = int(raw)
    except (TypeError, ValueError) as exc:
        raise CheckpointError("unknown_schema_version") from exc
    if version not in KNOWN_SCHEMA_VERSIONS:
        raise CheckpointError("unknown_schema_version")
    return version


def parse_checkpoint_payload(
    payload: Any,
    *,
    path: str | None = None,
) -> ParsedCheckpoint:
    if not isinstance(payload, dict):
        raise CheckpointError("not_an_object")
    version = detect_schema_version(payload)
    resolved: dict[str, Any] = {}
    missing: list[str] = []
    for field, aliases in MANDATORY_ALIASES.items():
        value = _lookup(payload, aliases)
        if value is None and field in NESTED_FALLBACK:
            parent, child = NESTED_FALLBACK[field]
            value = _nested(payload, parent, child)
        if value is None:
            missing.append(field)
        else:
            resolved[field] = value
    if missing:
        raise CheckpointError("missing_mandatory:" + ",".join(missing))
    optional: dict[str, Any] = {}
    for field, aliases in OPTIONAL_ALIASES.items():
        value = _lookup(payload, aliases)
        if value is not None:
            optional[field] = value
    return ParsedCheckpoint(
        schema_version=version,
        payload=resolved,
        source_path=path,
        optional=optional,
    )


def load_checkpoint_text(text: str, *, path: str | None = None) -> ParsedCheckpoint:
    stripped = text.strip()
    if not stripped:
        raise CheckpointError("truncated_or_empty")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        if not stripped.endswith("}") and not stripped.endswith("]"):
            raise CheckpointError("truncated_or_empty") from exc
        raise CheckpointError("malformed_json") from exc
    return parse_checkpoint_payload(payload, path=path)


def load_checkpoint_file(path: Path) -> ParsedCheckpoint:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CheckpointError("unreadable") from exc
    return load_checkpoint_text(text, path=str(path))


def quarantine_receipt(
    path: Path,
    report: CheckpointErrorReport,
    quarantine_dir: Path,
) -> Path:
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = quarantine_dir / f"{path.name}.{stamp}.bad"
    if path.exists():
        shutil.copy2(path, dest)
    report_path = dest.with_suffix(dest.suffix + ".report.json")
    report_path.write_text(
        json.dumps({**report.as_dict(), "quarantined_at": _utc()}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return dest


def safe_load_checkpoint(
    path: Path,
    quarantine_dir: Path,
) -> tuple[ParsedCheckpoint | None, CheckpointErrorReport | None]:
    """Load one receipt. On failure, quarantine and keep the monitor alive."""
    try:
        parsed = load_checkpoint_file(path)
        return parsed, None
    except CheckpointError as exc:
        kind = str(exc)
        missing: tuple[str, ...] = ()
        if kind.startswith("missing_mandatory:"):
            missing = tuple(kind.split(":", 1)[1].split(","))
            kind = "missing_mandatory"
        report = CheckpointErrorReport(
            kind=kind,
            path=str(path),
            missing=missing,
            message=str(exc),
            traceback_note=(
                "KeyError('events') on 2026-08-25T11:31:04Z: observer required "
                "top-level events; writer emitted latest_event + "
                "database_schema.events. Observer schema was stale relative to "
                "the receipt, which was complete for its own shape."
            ),
        )
        try:
            quarantine_receipt(path, report, quarantine_dir)
        except OSError:
            pass
        return None, report
