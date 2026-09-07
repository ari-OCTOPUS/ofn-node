#!/usr/bin/env python3
"""spine.py — UNIFY U-1+U-2: ستون‌فقرات رویداد واحد + هویت run_id.

این ماژول **تنها** راه نوشتن رویداد است. هیچ جزئی حق ندارد events.jsonl را
مستقیم باز کند یا بنویسد — همه از `spine.emit()` استفاده می‌کنند.

U-1 (یک نویسنده): تمام emitها از این تابع واحد می‌گذرند.
U-2 (یک هویت): هر محرک بیرونی یک run_id ریشه می‌گیرد که تا آخرین اثر ارث می‌رسد.

Schema هشت فیلد اجباری:
  ts_utc · run_id · parent_id · source · type · payload · evidence_ref · gate_decision

type از enum بسته می‌آید. تایپ ناشناخته = رد نوشتن.
"""
from __future__ import annotations

import contextvars, hashlib, json, sys, time, uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE / "budget"))

LOG = _HERE / "state" / "events.jsonl"
MAX_KEEP = 2000  # بزرگ‌تر از events.py چون ستون‌فقرات است

# ── U-2: run_id propagation ─────────────────────────────────────────────────
_run_id: contextvars.ContextVar[str] = contextvars.ContextVar("spine_run_id", default="")
_parent_id: contextvars.ContextVar[str] = contextvars.ContextVar("spine_parent", default="")

# ── U-1: closed type enum ───────────────────────────────────────────────────
EVENT_TYPES = frozenset({
    # organism
    "system.heartbeat", "task.started", "task.completed", "task.failed",
    "task.blocked", "task.resume", "task.progress",
    # governance
    "approval.required", "approval.granted", "approval.denied",
    "handoff.created", "incident.opened", "incident.contained",
    # sensors (U1)
    "sensor.reading", "sensor.unknown", "sensor.degraded",
    # tools (F2/INV-TOOL-GUARD)
    "tool.call", "tool.result", "tool.validated", "tool.rejected", "tool.retried",
    # wedge (F4)
    "wedge.detected", "wedge.recovered", "wedge.stack_captured",
    # spine lifecycle
    "spine.emit", "spine.run_started", "spine.run_completed",
    # router (F5)
    "router.decision", "router.structural_to_code", "router.model_task",
    # telegram
    "telegram.message_received", "telegram.message_sent",
    "telegram.question_asked", "telegram.answer_recorded",
    # backup
    "backup.hourly_ok", "backup.hourly_fail", "backup.daily_ok",
    # calibration / standing-GO
    "calibration.settled", "standing_go.minted", "standing_go.halted",
})

_current_run_id = contextvars.ContextVar("current_run_id", default="")


def new_run_id() -> str:
    """Generate a new root run_id (U-2)."""
    return f"R-{uuid.uuid4().hex[:12]}"


def begin_run(source: str, description: str = "") -> str:
    """Start a new run — returns the run_id. All events within will inherit it."""
    rid = new_run_id()
    _current_run_id.set(rid)
    emit("spine.run_started", source=source,
         payload={"description": description[:200]}, run_id=rid)
    return rid


def get_run_id() -> str:
    """Get the current run_id (empty if not in a run)."""
    return _current_run_id.get()


def end_run(source: str, summary: str = "") -> None:
    """End the current run."""
    rid = _current_run_id.get()
    if rid:
        emit("spine.run_completed", source=source,
             payload={"summary": summary[:300]}, run_id=rid)
        _current_run_id.set("")


def emit(event_type: str, source: str, *,
         payload: dict | None = None,
         parent_id: str = "",
         evidence_ref: str | None = None,
         gate_decision: str = "not_applicable",
         run_id: str = "",
         idempotency_key: str = "",
         _direct: bool = False) -> dict | None:
    """THE sole way to write an event. Fail-closed on unknown types.

    This replaces events.emit() for all new code. Legacy events.emit() calls
    should be migrated to spine.emit() gradually (UNIFY U-1).
    """
    if event_type not in EVENT_TYPES:
        # fail-closed: unknown type = refuse to write
        return None

    ts = time.time()
    rid = run_id or _current_run_id.get() or new_run_id()
    rec = {
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ts)),
        "run_id": rid,
        "parent_id": parent_id or _parent_id.get(),
        "source": source,
        "type": event_type,
        "payload": payload or {},
        "evidence_ref": evidence_ref,  # None or path — never empty string
        "gate_decision": gate_decision,  # allow | deny | not_applicable
    }
    if idempotency_key:
        rec["idempotency_key"] = idempotency_key
        rec["idempotency_sha256"] = hashlib.sha256(
            f"{rid}:{idempotency_key}".encode()).hexdigest()

    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        # append with lock (reuse opslib pattern)
        import fcntl
        with open(LOG, "a", encoding="utf-8") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\\n")
            fh.flush()
            # trim if too long
    except OSError:
        pass
    return rec


def validate_log(path: Path | None = None) -> dict:
    """U-1 audit: check that all events in the log have valid schema."""
    p = path or LOG
    if not p.exists():
        return {"rows": 0, "invalid": 0, "missing_run_id": 0, "unknown_types": 0}
    rows, invalid, missing_rid, unknown = 0, 0, 0, 0
    for line in p.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        rows += 1
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            invalid += 1
            continue
        if not d.get("run_id"):
            missing_rid += 1
        if d.get("type") not in EVENT_TYPES:
            unknown += 1
        # check required fields
        for f in ("ts_utc", "run_id", "source", "type"):
            if not d.get(f):
                invalid += 1
                break
    return {"rows": rows, "invalid": invalid,
            "missing_run_id": missing_rid, "unknown_types": unknown}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.validate:
        r = validate_log()
        print(json.dumps(r, ensure_ascii=False))
    else:
        print(f"spine: {len(EVENT_TYPES)} event types registered | LOG={LOG}")
