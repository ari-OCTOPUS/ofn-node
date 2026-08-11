#!/usr/bin/env python3
"""Digest-only, append-only traces for offline Test Intelligence runs.

The trace is intentionally narrower than an application log. Inputs, outputs,
tool arguments, state values, paths, prompts, chat identifiers and credentials
never cross this boundary. They are represented only by SHA-256 digests and
counts. The internal ``octopus.*`` namespace is canonical; any future mapping
to external telemetry conventions must happen outside this module.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA = "octopus.test-intelligence.trace.v1"
_ALLOWED_STATUS = frozenset({"ok", "blocked", "failed", "observed", "unknown"})
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,96}$")


def digest(value: Any) -> str:
    """Return a stable digest without retaining a raw representation."""
    if isinstance(value, bytes):
        raw = value
    else:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _token(value: Any, default: str = "unknown") -> str:
    text = str(value or default).strip()
    return text if _TOKEN_RE.fullmatch(text) else "digest-" + digest(text)[7:23]


def _component(value: Any) -> str:
    text = str(value or "").strip()
    if text.startswith("octopus.") and _TOKEN_RE.fullmatch(text):
        return text
    return "octopus.digest-" + digest(text)[7:23]


def _digests(items: Iterable[Any] | None) -> tuple[str, ...]:
    return tuple(digest(item) for item in (items or ()))


@dataclass(frozen=True)
class TraceEvent:
    trace_id: str
    event_id: str
    component: str
    kind: str
    status: str
    input_digest: str
    output_digest: str
    attempted: bool = False
    authorized: bool = False
    executed: bool = False
    tool_call_digests: tuple[str, ...] = field(default_factory=tuple)
    state_mutation_digests: tuple[str, ...] = field(default_factory=tuple)
    reason_code: str = "none"
    ts: float = 0.0
    schema: str = SCHEMA

    @property
    def tool_call_count(self) -> int:
        return len(self.tool_call_digests)

    @property
    def state_mutation_count(self) -> int:
        return len(self.state_mutation_digests)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.schema != SCHEMA:
            errors.append("wrong-schema")
        if not self.component.startswith("octopus.") or not _TOKEN_RE.fullmatch(self.component):
            errors.append("invalid-component")
        if not _TOKEN_RE.fullmatch(self.trace_id) or not _TOKEN_RE.fullmatch(self.event_id):
            errors.append("invalid-identifier")
        if not _TOKEN_RE.fullmatch(self.kind):
            errors.append("invalid-kind")
        if self.status not in _ALLOWED_STATUS:
            errors.append("invalid-status")
        if not _DIGEST_RE.fullmatch(self.input_digest):
            errors.append("invalid-input-digest")
        if not _DIGEST_RE.fullmatch(self.output_digest):
            errors.append("invalid-output-digest")
        if any(not _DIGEST_RE.fullmatch(v) for v in self.tool_call_digests):
            errors.append("invalid-tool-digest")
        if any(not _DIGEST_RE.fullmatch(v) for v in self.state_mutation_digests):
            errors.append("invalid-mutation-digest")
        if self.authorized and not self.attempted:
            errors.append("authorized-without-attempt")
        if self.executed and not self.authorized:
            errors.append("executed-without-authorization")
        if not _TOKEN_RE.fullmatch(self.reason_code):
            errors.append("invalid-reason-code")
        return errors

    def as_record(self) -> dict[str, Any]:
        rec = asdict(self)
        rec["tool_call_count"] = self.tool_call_count
        rec["state_mutation_count"] = self.state_mutation_count
        return rec


def make_event(*, trace_id: str, event_id: str, component: str, kind: str,
               status: str, inputs: Any = None, outputs: Any = None,
               attempted: bool = False, authorized: bool = False,
               executed: bool = False, tool_calls: Iterable[Any] | None = None,
               state_mutations: Iterable[Any] | None = None,
               reason_code: str = "none", now: float | None = None) -> TraceEvent:
    """Construct an event while digesting all potentially sensitive values."""
    event = TraceEvent(
        trace_id=_token(trace_id),
        event_id=_token(event_id),
        component=_component(component),
        kind=_token(kind),
        status=str(status),
        input_digest=digest(inputs),
        output_digest=digest(outputs),
        attempted=bool(attempted),
        authorized=bool(authorized),
        executed=bool(executed),
        tool_call_digests=_digests(tool_calls),
        state_mutation_digests=_digests(state_mutations),
        reason_code=_token(reason_code, "none"),
        ts=float(time.time() if now is None else now),
    )
    errors = event.validate()
    if errors:
        raise ValueError("invalid trace event: " + ",".join(errors))
    return event


class TraceSink:
    """Single-writer JSONL sink. Existing content is never truncated."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def append(self, event: TraceEvent) -> None:
        errors = event.validate()
        if errors:
            raise ValueError("invalid trace event: " + ",".join(errors))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event.as_record(), ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")) + "\n"
        flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
        fd = os.open(str(self.path), flags, 0o600)
        try:
            os.write(fd, line.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)


def trace_shape(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return a content-free shape useful for deterministic snapshots."""
    return {
        "schema": record.get("schema"),
        "component": record.get("component"),
        "kind": record.get("kind"),
        "status": record.get("status"),
        "attempted": bool(record.get("attempted")),
        "authorized": bool(record.get("authorized")),
        "executed": bool(record.get("executed")),
        "tool_call_count": int(record.get("tool_call_count", 0)),
        "state_mutation_count": int(record.get("state_mutation_count", 0)),
        "reason_code": record.get("reason_code"),
    }
