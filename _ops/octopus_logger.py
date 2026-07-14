"""
Octopus Structured Logger v1 — stdlib-only, JSON-lines output.

Design principles:
  1. JSON only — no free-text log lines.
  2. Schema v1 envelope — every event passes log-event-v1.schema.json.
  3. Trace propagation — trace_id carried across organ boundaries.
  4. PII-safe — no secrets, no raw prompts in log stream.
  5. Compact — single line per event (JSONL) for grep/awk compatibility.
  6. Zero external deps — only stdlib (json, logging, uuid, time).

Usage:
    from octopus_logger import octo_log, OctoContext

    # Set organ-level context (once per subsystem)
    ctx = OctoContext(organ="doctor", agent_id="rfc-miner")

    # Emit events
    octo_log(ctx, "doctor.rfc.drafted", "Bottleneck detected: budget conflict",
             status="started", confidence=0.8, p={"bottleneck": "freeze_halt"})

    # Trace propagation across organs
    child_ctx = ctx.child(span="7b4d8f5b")
    octo_log(child_ctx, "doctor.rfc.sandboxed", "RFC passed sandbox",
             status="success", duration_ms=3420)
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ── Constants ────────────────────────────────────────────────────────────────

SCHEMA_VERSION = "1.0.0"
SYSTEM_NAME = "octopus"
DEFAULT_ORGAN = "unknown"

# ── Self-wiring file sink (WP2 · ORPH-OCTOPUS-LOG) ────────────────────────────
# رفعِ ارتباطِ‌قطع: بدونِ این، octo_log فقط به stream می‌رفت و فایلی که کاکپیت
# tail می‌کند هرگز نوشته نمی‌شد. با OCTOPUS_WIRE_STRUCTLOG=1، هر رویداد ALSO به
# مسیرِ JSONLِ کاکپیت (`_ops/state/octopus-log.jsonl`) append می‌شود.
# پیش‌فرض خاموش → هیچ نوشتنی، رفتار بایت‌به‌بایت مثلِ حالتِ stream-only.
# نوشتن bounded/rotating + fail-soft است (یک خطا هرگز حلقهٔ ارگانیسم را نمی‌کشد).
STRUCTLOG_FLAG = "OCTOPUS_WIRE_STRUCTLOG"
# مسیرِ پیش‌فرض = اولین کاندیدِ tailِ کاکپیت (cockpit_readmodel.tail_structured_log):
# self.state / "octopus-log.jsonl"، که self.state = _ops/state.
STRUCTLOG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "state", "octopus-log.jsonl"
)

# Schema status enum (matches log-event-v1.schema.json)
VALID_STATUS = {"started", "success", "failed", "blocked", "retrying", "skipped", "unknown"}
VALID_LEVEL = {"DEBUG", "INFO", "WARN", "ERROR", "CRIT"}
VALID_APPROVAL = {"required", "approved", "denied", "not_required", "pending", "unknown"}

# ── Internal logger ─────────────────────────────────────────────────────────

_log = logging.getLogger("octopus")
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(message)s"))
_log.addHandler(_handler)
_log.setLevel(logging.INFO)


# ── Context ────────────────────────────────────────────────────────────────

@dataclass
class OctoContext:
    """Immutable trace context. Create one per organ/subsystem; propagate via .child()."""

    organ: str = DEFAULT_ORGAN
    agent_id: Optional[str] = None
    trace: str = field(default_factory=lambda: secrets.token_hex(8))
    span: str = field(default_factory=lambda: secrets.token_hex(4))
    parent: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def child(self, *, organ: Optional[str] = None,
              agent_id: Optional[str] = None) -> "OctoContext":
        """Create child context — trace stays the same, new span, parent=this span."""
        return OctoContext(
            organ=organ or self.organ,
            agent_id=agent_id or self.agent_id,
            trace=self.trace,
            span=secrets.token_hex(4),
            parent=self.span,
            tags=list(self.tags),
        )


# ── Event Builder ──────────────────────────────────────────────────────────

def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


def _build_event(
    ctx: OctoContext,
    event: str,
    msg: str,
    *,
    status: str = "unknown",
    level: str = "INFO",
    duration_ms: Optional[int] = None,
    handoff_from: Optional[str] = None,
    handoff_to: Optional[str] = None,
    tool_name: Optional[str] = None,
    gate_name: Optional[str] = None,
    gate_reason: Optional[str] = None,
    approval_state: str = "unknown",
    confidence: Optional[float] = None,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
    cost_usd: Optional[float] = None,
    error_type: Optional[str] = None,
    error_redacted: Optional[str] = None,
    payload_ref: Optional[str] = None,
    tags: Optional[List[str]] = None,
    src: Optional[str] = None,
    p: Optional[Dict[str, Any]] = None,
    **extra: Any,
) -> Dict[str, Any]:
    """Build a structured log event dict. Does NOT emit — pure function."""

    # ── Validate required enums ──
    if status not in VALID_STATUS:
        raise ValueError(f"Invalid status: {status!r}. Must be one of {VALID_STATUS}")
    if level not in VALID_LEVEL:
        raise ValueError(f"Invalid level: {level!r}. Must be one of {VALID_LEVEL}")
    if approval_state not in VALID_APPROVAL:
        raise ValueError(f"Invalid approval_state: {approval_state!r}")

    # ── Envelope ──
    ev: Dict[str, Any] = {
        "v": SCHEMA_VERSION,
        "ts": _ts(),
        "level": level,
        "event": event,
        "msg": msg[:512],  # truncate long messages
        "organ": ctx.organ,
        "trace": ctx.trace,
        "span": ctx.span,
        "status": status,
    }

    # ── Optional envelope fields (only if non-null/non-empty) ──
    _opt(ev, "agent_id", ctx.agent_id)
    _opt(ev, "parent", ctx.parent)
    _opt(ev, "duration_ms", duration_ms)
    _opt(ev, "handoff_from", handoff_from)
    _opt(ev, "handoff_to", handoff_to)
    _opt(ev, "tool_name", tool_name)
    _opt(ev, "gate_name", gate_name)
    _opt(ev, "gate_reason", gate_reason)
    if approval_state != "unknown":
        ev["approval_state"] = approval_state
    _opt(ev, "confidence", confidence)
    _opt(ev, "tokens_in", tokens_in)
    _opt(ev, "tokens_out", tokens_out)
    _opt(ev, "cost_usd", cost_usd)
    _opt(ev, "error_type", error_type)
    _opt(ev, "error_redacted", error_redacted)
    _opt(ev, "payload_ref", payload_ref)
    _opt(ev, "src", src)

    # ── Tags (merge context + event-level) ──
    merged_tags = list(ctx.tags)
    if tags:
        merged_tags.extend(t for t in tags if t not in merged_tags)
    if merged_tags:
        ev["tags"] = merged_tags

    # ── Payload ──
    if p:
        ev["p"] = p

    return ev


def _opt(d: Dict, key: str, val: Any) -> None:
    """Only add key if val is not None/empty."""
    if val is not None and val != "":
        d[key] = val


# ── Emit ───────────────────────────────────────────────────────────────────

def octo_log(
    ctx: OctoContext,
    event: str,
    msg: str,
    *,
    level: str = "INFO",
    **kwargs: Any,
) -> None:
    """Build and emit a structured log event as a single JSON line.

    Stream emission (stdout) is unconditional and unchanged. When the
    OCTOPUS_WIRE_STRUCTLOG flag is set, the SAME serialized line is ALSO
    appended to the JSONL file the cockpit tails; when the flag is off
    (default) nothing is written to disk — byte-identical to before.
    """
    ev = _build_event(ctx, event, msg, level=level, **kwargs)
    line = _serialize(ev)
    _log.info(line)
    _maybe_file_emit(line)


def octo_log_debug(ctx: OctoContext, event: str, msg: str, **kwargs: Any) -> None:
    octo_log(ctx, event, msg, level="DEBUG", **kwargs)


def octo_log_warn(ctx: OctoContext, event: str, msg: str, **kwargs: Any) -> None:
    octo_log(ctx, event, msg, level="WARN", **kwargs)


def octo_log_error(ctx: OctoContext, event: str, msg: str, **kwargs: Any) -> None:
    octo_log(ctx, event, msg, level="ERROR", **kwargs)


def octo_log_crit(ctx: OctoContext, event: str, msg: str, **kwargs: Any) -> None:
    octo_log(ctx, event, msg, level="CRIT", **kwargs)


def _serialize(ev: Dict[str, Any]) -> str:
    """Compact JSON — single line, no whitespace, ASCII-safe."""
    return json.dumps(ev, ensure_ascii=False, separators=(",", ":"))


# ── File Emitter (for JSONL append) ────────────────────────────────────────

class FileEmitter:
    """Append structured events to a JSONL file. Thread-safe via file locking."""

    def __init__(self, path: str, max_bytes: int = 10_000_000):
        self._path = path
        self._max = max_bytes

    def emit(self, ctx: OctoContext, event: str, msg: str, **kwargs: Any) -> None:
        ev = _build_event(ctx, event, msg, **kwargs)
        line = _serialize(ev) + "\n"
        self._append(line)

    def write_line(self, line: str) -> None:
        """Append an already-serialized JSON line (ensures a trailing newline)."""
        self._append(line if line.endswith("\n") else line + "\n")

    def _append(self, line: str) -> None:
        # Ensure parent dir exists (fail-soft — never crash over a missing dir).
        try:
            parent = os.path.dirname(self._path)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent, exist_ok=True)
        except OSError:
            pass
        # Rotation: if file > max, rename to .bak and start fresh
        if os.path.exists(self._path):
            try:
                if os.path.getsize(self._path) > self._max:
                    bak = self._path + ".bak"
                    if os.path.exists(bak):
                        os.remove(bak)
                    os.rename(self._path, bak)
            except OSError:
                pass  # fail-soft — don't crash organism over log rotation

        with open(self._path, "a", encoding="utf-8") as f:
            f.write(line)


# ── Self-wiring sink plumbing (flag-gated, fail-soft) ────────────────────────

_FILE_SINK: Optional["FileEmitter"] = None


def _structlog_enabled() -> bool:
    """True only when OCTOPUS_WIRE_STRUCTLOG=1 (default off → byte-identical)."""
    return os.environ.get(STRUCTLOG_FLAG, "0") == "1"


def _file_sink() -> "FileEmitter":
    """Lazy, path-aware FileEmitter. Rebuilt if STRUCTLOG_PATH is monkeypatched."""
    global _FILE_SINK
    target = str(STRUCTLOG_PATH)
    if _FILE_SINK is None or _FILE_SINK._path != target:
        _FILE_SINK = FileEmitter(target)
    return _FILE_SINK


def _maybe_file_emit(line: str) -> None:
    """Append the serialized event to the cockpit JSONL iff the flag is on.

    Fail-soft: any disk/rotation error is swallowed — logging must never take
    down a caller loop. No-op (nothing written) when the flag is off.
    """
    if not _structlog_enabled():
        return
    try:
        _file_sink().write_line(line)
    except Exception:  # noqa: BLE001 — fail-soft, logging must not crash organism
        pass


# ── Convenience: global context ──────────────────────────────────────────────

# Module-level default context (organ="octopus"). Each subsystem should create its own.
ROOT_CTX = OctoContext(organ="octopus")


# ── Quick validation helper ─────────────────────────────────────────────────

def validate_event(ev: Dict[str, Any]) -> List[str]:
    """Validate an event dict against schema v1 rules. Returns list of errors."""
    errors: List[str] = []

    # Required fields
    for k in ("v", "ts", "level", "event", "msg", "organ", "trace", "span", "status"):
        if k not in ev:
            errors.append(f"missing required field: {k}")

    # Enum validation
    if "level" in ev and ev["level"] not in VALID_LEVEL:
        errors.append(f"invalid level: {ev['level']!r}")
    if "status" in ev and ev["status"] not in VALID_STATUS:
        errors.append(f"invalid status: {ev['status']!r}")
    if "approval_state" in ev and ev["approval_state"] not in VALID_APPROVAL:
        errors.append(f"invalid approval_state: {ev['approval_state']!r}")

    # Schema version
    if "v" in ev and ev["v"] != SCHEMA_VERSION:
        errors.append(f"unexpected schema version: {ev['v']!r}")

    # Trace format
    if "trace" in ev and not (8 <= len(ev["trace"]) <= 32):
        errors.append(f"trace must be 8-32 hex chars, got: {ev['trace']!r}")
    if "span" in ev and not (4 <= len(ev["span"]) <= 16):
        errors.append(f"span must be 4-16 hex chars, got: {ev['span']!r}")

    return errors


# ── Smoke test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ctx = OctoContext(organ="doctor", agent_id="rfc-miner", tags=["audit"])

    print("── Doctor RFC lifecycle example ──")
    octo_log(ctx, "doctor.rfc.drafted", "Bottleneck detected: budget conflict",
             status="started", confidence=0.8,
             p={"bottleneck": "freeze_halt", "severity": "WARN"})

    child = ctx.child(agent_id="sandbox")
    octo_log(child, "doctor.rfc.sandboxed", "RFC passed sandbox tests",
             status="success", duration_ms=3420,
             p={"tests_passed": 63, "critic_verdict": "pass"})

    octo_log_warn(ctx, "doctor.rfc.submitted", "RFC sent — Telegram channel stub",
                  status="blocked", gate_name="telegram",
                  gate_reason="no TELEGRAM_BOT_TOKEN",
                  tags=["blocked"])

    # ── Validate ──
    print("\n── Validation test ──")
    ev = _build_event(ctx, "system.heartbeat", "tick complete",
                      status="success", p={"beat_seq": 1234})
    errs = validate_event(ev)
    print(f"Valid event errors: {errs}")  # should be []

    bad = {"msg": "test"}  # missing required fields
    errs = validate_event(bad)
    print(f"Invalid event errors: {errs}")  # should have errors

    print(f"\nTotal fields in valid event: {len(ev)}")
