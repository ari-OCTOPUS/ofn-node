"""models.py — دامنهٔ داده‌ایِ Bridge: state machine، Command، Principal،
Decision، Event + توابعِ کمکیِ زمان/شناسه/canonical-hash.

هیچ I/O ای این‌جا نیست — فقط تعریفِ نوع و قواعدِ خالص. stdlib-only.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


# ── State machine ────────────────────────────────────────────────────────
class CommandState(str, Enum):
    """وضعیت‌های یک فرمان. str-Enum تا مستقیم در JSON/SQLite بنشیند.

    (StrEnum فقط ۳٫۱۱+ است؛ این نسخه روی ۳٫۹ هم کار می‌کند — DietPi.)
    """
    RECEIVED = "received"
    AUTHORIZED = "authorized"
    DISPATCHED = "dispatched"
    ACCEPTED = "accepted"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    REJECTED = "rejected"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    UNKNOWN_OUTCOME = "unknown_outcome"

    def __str__(self) -> str:  # noqa: D401
        return self.value


TERMINAL_STATES = frozenset({
    CommandState.SUCCEEDED,
    CommandState.REJECTED,
    CommandState.FAILED,
    CommandState.EXPIRED,
    CommandState.CANCELLED,
    CommandState.UNKNOWN_OUTCOME,
})

# گذارهای مجاز — هر چیزِ خارجِ این جدول رد می‌شود (fail-closed).
ALLOWED_TRANSITIONS: dict = {
    None: {CommandState.RECEIVED},
    CommandState.RECEIVED: {
        CommandState.AUTHORIZED, CommandState.REJECTED,
        CommandState.EXPIRED, CommandState.CANCELLED,
    },
    CommandState.AUTHORIZED: {
        CommandState.DISPATCHED, CommandState.EXPIRED, CommandState.CANCELLED,
    },
    CommandState.DISPATCHED: {
        CommandState.ACCEPTED, CommandState.REJECTED, CommandState.FAILED,
        CommandState.UNKNOWN_OUTCOME, CommandState.CANCELLED,
    },
    CommandState.ACCEPTED: {
        CommandState.RUNNING, CommandState.SUCCEEDED,
        CommandState.FAILED, CommandState.CANCELLED,
    },
    CommandState.RUNNING: {
        CommandState.SUCCEEDED, CommandState.FAILED,
        CommandState.CANCELLED, CommandState.UNKNOWN_OUTCOME,
    },
}


def transition_allowed(from_state, to_state) -> bool:
    """آیا گذار from→to مجاز است؟ terminal ها هیچ خروجی ندارند."""
    if from_state in TERMINAL_STATES:
        return False
    return to_state in ALLOWED_TRANSITIONS.get(from_state, frozenset())


# ── زمان / شناسه / canonical ────────────────────────────────────────────
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    """ISO-8601 با Z (UTC). ورودیِ naive را UTC فرض می‌کند."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(s: str) -> datetime:
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def new_id() -> str:
    """شناسهٔ uuid7 (زمان‌مرتب) — 48-bit ms + رندوم، نسخهٔ ۷.

    زمان‌مرتب بودن باعث می‌شود ترتیبِ درج در store قابلِ استناد باشد.
    """
    ms = int(time.time() * 1000) & ((1 << 48) - 1)
    ba = bytearray(ms.to_bytes(6, "big") + os.urandom(10))
    ba[6] = (ba[6] & 0x0F) | 0x70   # version 7
    ba[8] = (ba[8] & 0x3F) | 0x80   # variant RFC-4122
    return str(uuid.UUID(bytes=bytes(ba)))


def canonical(obj) -> str:
    """JSON قطعی برای هش — کلیدهای مرتب، بدونِ فاصله، unicode خام."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str)


def sha256_hex(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
    return h.hexdigest()


# ── Dataclasses ──────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Principal:
    principal_id: str
    scopes: frozenset          # frozenset[str]
    audience: str              # "octopus-bridge" | "octopus-bridge-local"
    instance_id: "str | None" = None

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes


@dataclass(frozen=True)
class Command:
    message_id: str
    operation: str
    source_principal: str
    target_agent: str          # "ofn" | "hypno"
    target_instance: str       # اجباری — broadcast نداریم
    issued_at: datetime
    expires_at: datetime
    policy_version: str = "0"
    correlation_id: str = ""
    idempotency_key: "str | None" = None
    causation_id: "str | None" = None
    traceparent: "str | None" = None
    parameters: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "message_id": self.message_id,
            "operation": self.operation,
            "source_principal": self.source_principal,
            "target_agent": self.target_agent,
            "target_instance": self.target_instance,
            "issued_at": iso(self.issued_at),
            "expires_at": iso(self.expires_at),
            "policy_version": self.policy_version,
            "correlation_id": self.correlation_id,
            "idempotency_key": self.idempotency_key,
            "causation_id": self.causation_id,
            "traceparent": self.traceparent,
            "parameters": self.parameters,
        }

    @staticmethod
    def from_json(d: dict) -> "Command":
        return Command(
            message_id=str(d.get("message_id") or new_id()),
            operation=str(d["operation"]),
            source_principal=str(d.get("source_principal", "")),
            target_agent=str(d.get("target_agent", "")),
            target_instance=str(d.get("target_instance", "")),
            issued_at=parse_iso(d["issued_at"]) if d.get("issued_at") else now_utc(),
            expires_at=parse_iso(d["expires_at"]) if d.get("expires_at") else now_utc(),
            policy_version=str(d.get("policy_version", "0")),
            correlation_id=str(d.get("correlation_id", "")),
            idempotency_key=d.get("idempotency_key"),
            causation_id=d.get("causation_id"),
            traceparent=d.get("traceparent"),
            parameters=dict(d.get("parameters") or {}),
        )

    def digest(self) -> str:
        return sha256_hex(canonical(self.to_json()))


@dataclass(frozen=True)
class Decision:
    outcome: str               # "allow" | "deny" | "approval_required"
    reason_code: str
    policy_version: str = "0"
    expires_at: "datetime | None" = None
    audit_fields: dict = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.outcome == "allow"


@dataclass(frozen=True)
class Event:
    message_id: str
    kind: str                  # "heartbeat" | "status" | "task_complete" | ...
    source_agent: str
    source_instance: str
    payload: dict = field(default_factory=dict)
    observed_at: datetime = field(default_factory=now_utc)
    traceparent: "str | None" = None

    def to_json(self) -> dict:
        return {
            "message_id": self.message_id,
            "kind": self.kind,
            "source_agent": self.source_agent,
            "source_instance": self.source_instance,
            "payload": self.payload,
            "observed_at": iso(self.observed_at),
            "traceparent": self.traceparent,
        }
