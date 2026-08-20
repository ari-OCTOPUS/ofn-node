# -*- coding: utf-8 -*-
"""local_commands.py — A2/A10 firewall: owner slash commands never reach a model.

Typed LocalCommandResult is the only return type. Raw strings are forbidden.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
_OPS = _HERE.parent
MEMORY_STORE = _ROOT / "research/full_loop/state/memory.jsonl"
FEEDBACK = _OPS / "state" / "telegram" / "owner-feedback.jsonl"
STOP_FLAG = _OPS / "state" / "telegram" / "owner-stop.flag"
RATE_FILE = _OPS / "state" / "telegram" / "owner-reply-rate.json"

CANONICAL_BOT_ID = 7992324219
HANDLER_SCHEMA_VERSION = "typed-v1"

COMMAND_TABLE = {
    "/status": {"local_handler": "status_text", "reads_memory": True, "writes_memory": False,
                "model_allowed": False, "owner_only": True, "expected_receipt": "local-status"},
    "/health": {"local_handler": "status_text", "reads_memory": True, "writes_memory": False,
                "model_allowed": False, "owner_only": True, "expected_receipt": "local-health"},
    "/memory": {"local_handler": "memory_text", "reads_memory": True, "writes_memory": False,
                "model_allowed": False, "owner_only": True, "expected_receipt": "local-memory"},
    "/help": {"local_handler": "help_text", "reads_memory": False, "writes_memory": False,
                "model_allowed": False, "owner_only": True, "expected_receipt": "local-help"},
    "/capabilities": {"local_handler": "capabilities_text", "reads_memory": False, "writes_memory": False,
                      "model_allowed": False, "owner_only": True, "expected_receipt": "local-capabilities"},
    "/remember": {"local_handler": "_remember", "reads_memory": False, "writes_memory": True,
                  "model_allowed": False, "owner_only": True, "expected_receipt": "local-remember"},
    "/good": {"local_handler": "_feedback", "reads_memory": False, "writes_memory": True,
              "model_allowed": False, "owner_only": True, "expected_receipt": "local-feedback"},
    "/bad": {"local_handler": "_feedback", "reads_memory": False, "writes_memory": True,
             "model_allowed": False, "owner_only": True, "expected_receipt": "local-feedback"},
    "/correct": {"local_handler": "_correct", "reads_memory": True, "writes_memory": True,
                 "model_allowed": False, "owner_only": True, "expected_receipt": "local-correct"},
    "/stop": {"local_handler": "_stop", "reads_memory": False, "writes_memory": True,
              "model_allowed": False, "owner_only": True, "expected_receipt": "local-stop"},
    "/resume": {"local_handler": "_resume", "reads_memory": False, "writes_memory": True,
                "model_allowed": False, "owner_only": True, "expected_receipt": "local-resume"},
    "/why": {"local_handler": "_why", "reads_memory": True, "writes_memory": False,
             "model_allowed": False, "owner_only": True, "expected_receipt": "local-why"},
    # ── Telegram cockpit (FULL-GREEN 2026-08-21): سریع، read-only (جز pause/resume) ──
    "/loops": {"local_handler": "loops_text", "reads_memory": False, "writes_memory": False,
               "model_allowed": False, "owner_only": True, "expected_receipt": "cockpit-loops"},
    "/task": {"local_handler": "task_text", "reads_memory": False, "writes_memory": False,
              "model_allowed": False, "owner_only": True, "expected_receipt": "cockpit-task"},
    "/receipts": {"local_handler": "receipts_text", "reads_memory": False, "writes_memory": False,
                  "model_allowed": False, "owner_only": True, "expected_receipt": "cockpit-receipts"},
    "/dlq": {"local_handler": "dlq_text", "reads_memory": False, "writes_memory": False,
             "model_allowed": False, "owner_only": True, "expected_receipt": "cockpit-dlq"},
    "/memory_status": {"local_handler": "memory_status_text", "reads_memory": True, "writes_memory": False,
                       "model_allowed": False, "owner_only": True, "expected_receipt": "cockpit-memory-status"},
    "/brain_status": {"local_handler": "brain_status_text", "reads_memory": False, "writes_memory": False,
                      "model_allowed": False, "owner_only": True, "expected_receipt": "cockpit-brain-status"},
    "/pause": {"local_handler": "pause_text", "reads_memory": False, "writes_memory": True,
               "model_allowed": False, "owner_only": True, "expected_receipt": "cockpit-pause"},
}

ALIASES = {
    "/وضعیت": "/status",
    "/سلامت": "/health",
    "/حافظه": "/memory",
    "/راهنما": "/help",
    "/توقف": "/stop",
    "/ادامه": "/resume",
    "/چرا": "/why",
}

_RECALL_RE = re.compile(
    r"(کلمه\s*رمز|passphrase|password\s*word|what\s+was\s+the\s+(secret|pass))",
    re.I,
)


@dataclass(frozen=True)
class LocalCommandResult:
    handled: bool
    kind: str
    text: str
    memory_id: str | None = None
    evidence_ids: tuple[str, ...] = ()
    model_allowed: bool = False
    retrieved_id: str | None = None
    used_in_context: bool = False
    future_filtered: int = 0
    keyboard: None = None
    executable: bool = False
    receipt: str | None = None
    unknown_command: str | None = None
    extras: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        out = {
            "kind": self.kind,
            "text": self.text,
            "keyboard": self.keyboard,
            "executable": self.executable,
            "model_allowed": self.model_allowed,
            "handled": self.handled,
            "handler_schema_version": HANDLER_SCHEMA_VERSION,
        }
        if self.memory_id:
            out["memory_id"] = self.memory_id
        if self.retrieved_id:
            out["retrieved_id"] = self.retrieved_id
        if self.used_in_context:
            out["used_in_context"] = True
        out["future_filtered"] = self.future_filtered
        if self.receipt:
            out["receipt"] = self.receipt
        if self.unknown_command:
            out["unknown_command"] = self.unknown_command
        if self.evidence_ids:
            out["evidence_ids"] = list(self.evidence_ids)
        out.update(self.extras)
        return out


def _ok(kind: str, text: str, **kw) -> LocalCommandResult:
    extras = dict(kw.pop("extras", {}) or {})
    mid = kw.pop("memory_id", None)
    rid = kw.pop("retrieved_id", None)
    used = kw.pop("used_in_context", False)
    ff = kw.pop("future_filtered", 0)
    receipt = kw.pop("receipt", None)
    unk = kw.pop("unknown_command", None)
    evid = tuple(kw.pop("evidence_ids", ()) or ())
    extras.update(kw)
    return LocalCommandResult(
        handled=True, kind=kind, text=text, memory_id=mid,
        evidence_ids=evid, model_allowed=False, retrieved_id=rid,
        used_in_context=bool(used), future_filtered=int(ff),
        receipt=receipt, unknown_command=unk, extras=extras,
    )


def _snapshot() -> dict:
    out = {}
    try:
        d = json.loads((_OPS / "state" / "ORGANISM-STATE.json").read_text(encoding="utf-8"))
        out["beat"] = d.get("beat")
    except Exception:  # noqa: BLE001
        out["beat"] = None
    try:
        m = json.loads((_OPS / "state" / "pulse" / "memory-read-latest.json")
                       .read_text(encoding="utf-8"))
        out["memread"] = f"{m.get('status')}/r{m.get('memory_reads_per_cycle')}/{m.get('readback')}"
    except Exception:  # noqa: BLE001
        out["memread"] = "?"
    out["stop"] = STOP_FLAG.exists()
    try:
        sys_p = str(_OPS / "telegram_center")
        import sys
        if sys_p not in sys.path:
            sys.path.insert(0, sys_p)
        from process_identity import load as _id_load  # noqa: WPS433
        ident = _id_load()
    except Exception:  # noqa: BLE001
        ident = {}
    out["build"] = ident.get("short_build_id") or HANDLER_SCHEMA_VERSION
    out["pid"] = ident.get("process_id")
    return out


def status_text() -> str:
    s = _snapshot()
    halt = "STOP" if s["stop"] else "run"
    pid = s.get("pid") or "-"
    return (f"🐙 beat={s['beat']} · memory={s['memread']} · {halt} · "
            f"bot={CANONICAL_BOT_ID} · build={s['build']} · pid={pid} · "
            f"schema={HANDLER_SCHEMA_VERSION} · executable=false")


def help_text() -> str:
    return ("فرمان‌های محلی (صفر مدل): /status /health /memory /help "
            "/capabilities /remember /good /bad /correct /stop /resume /why")


def memory_text() -> str:
    last = last_remember()
    if not last:
        return "حافظهٔ حلقه خالی است. با /remember چیزی ثبت کن."
    return (f"آخرین ثبت: {last.get('id')} · {str(last.get('text') or '')[:80]}")


def capabilities_text() -> str:
    return ("حلقهٔ مالک: ingest دوزمانی → حافظه → HC/WM → gate → "
            "مدل امضاشده (پولی تا A13 خاموش) → یک پاسخ → memory commit. executable=false")


def _normalize_cmd(text: str) -> tuple[str, str]:
    raw = (text or "").strip()
    if not raw:
        return "", ""
    first = raw.split()[0]
    first = first.split("@", 1)[0].lower()
    first = ALIASES.get(first, first)
    return first, raw


def is_slash(text: str) -> bool:
    t = (text or "").lstrip()
    return t.startswith("/")


def is_local_firewall(text: str) -> bool:
    cmd, _ = _normalize_cmd(text)
    return bool(cmd.startswith("/"))


def handle_local(text: str, *, model_fn=None, memory_store: Path | None = None) -> LocalCommandResult:
    """Typed result only. model_fn must never be called. Exceptions → LOCAL_COMMAND_ERROR."""
    try:
        return _handle_local_inner(text, model_fn=model_fn, memory_store=memory_store)
    except Exception:  # noqa: BLE001
        return _ok("LOCAL_COMMAND_ERROR", "خطای فرمان محلی. مدل صدا نشد.")


def _handle_local_inner(text: str, *, model_fn=None, memory_store: Path | None = None) -> LocalCommandResult:
    cmd, raw = _normalize_cmd(text)
    if not cmd.startswith("/"):
        return LocalCommandResult(handled=False, kind="", text="")
    if cmd not in COMMAND_TABLE:
        return _ok("local-help", "فرمان ناشناخته. " + help_text(), unknown_command=cmd)
    spec = COMMAND_TABLE[cmd]
    if spec["model_allowed"] and model_fn is not None:
        model_fn({"forbidden": True, "cmd": cmd})
    if cmd in ("/status", "/health"):
        return _ok("local-command", status_text(), receipt=spec["expected_receipt"])
    if cmd == "/memory":
        return _ok("local-command", memory_text(), receipt=spec["expected_receipt"])
    if cmd == "/help":
        return _ok("local-command", help_text(), receipt=spec["expected_receipt"])
    if cmd == "/capabilities":
        return _ok("local-command", capabilities_text(), receipt=spec["expected_receipt"])
    if cmd == "/remember":
        parts = raw.split(maxsplit=1)
        if len(parts) < 2:
            return _ok("local-command", "usage: /remember <text>")
        mid, msg = _remember(parts[1], store=memory_store)
        return _ok("local-command", msg, memory_id=mid, receipt="local-remember")
    if cmd == "/correct":
        return _correct(raw, store=memory_store)
    if cmd in ("/good", "/bad"):
        return _ok("local-command", _feedback(cmd, raw), receipt="local-feedback")
    if cmd == "/stop":
        return _ok("local-command", _stop(), receipt="local-stop")
    if cmd == "/resume":
        parts = raw.split(maxsplit=1)
        if len(parts) >= 2 and parts[1].strip():
            return _ok("local-command", resume_cockpit_text(parts[1].strip()),
                       receipt="cockpit-resume")
        return _ok("local-command", _resume(), receipt="local-resume")
    if cmd == "/why":
        return _ok("local-command", _why(), receipt="local-why")
    if cmd == "/loops":
        return _ok("local-command", loops_text(), receipt=spec["expected_receipt"])
    if cmd == "/task":
        return _ok("local-command", task_text(raw), receipt=spec["expected_receipt"])
    if cmd == "/receipts":
        return _ok("local-command", receipts_text(raw), receipt=spec["expected_receipt"])
    if cmd == "/dlq":
        return _ok("local-command", dlq_text(), receipt=spec["expected_receipt"])
    if cmd == "/memory_status":
        return _ok("local-command", memory_status_text(), receipt=spec["expected_receipt"])
    if cmd == "/brain_status":
        return _ok("local-command", brain_status_text(), receipt=spec["expected_receipt"])
    if cmd == "/pause":
        return _ok("local-command", pause_text(), receipt=spec["expected_receipt"])
    return _ok("local-help", help_text())


def _iter_memory(store: Path) -> list[dict]:
    rows = []
    if not store.exists():
        return rows
    try:
        for line in store.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("provenance") == "owner_direct":
                rows.append(row)
    except (OSError, ValueError):
        return []
    return rows


def last_remember(*, store: Path | None = None, as_of: str | None = None) -> dict | None:
    """Current = latest row. Historical = latest with occurred_at <= as_of. Never deletes."""
    rows = _iter_memory(Path(store) if store is not None else MEMORY_STORE)
    if as_of:
        rows = [r for r in rows if str(r.get("occurred_at") or "") <= as_of]
    return rows[-1] if rows else None


def try_recall(text: str, *, store: Path | None = None, as_of: str | None = None) -> LocalCommandResult | None:
    """Local recall first. Exact memory → zero model."""
    if not _RECALL_RE.search(text or ""):
        return None
    row = last_remember(store=store, as_of=as_of)
    if not row:
        return _ok("local-recall-miss", "چیزی در حافظهٔ /remember نیست.")
    body = str(row.get("text") or "")
    payload = body.split(":", 1)[1].strip() if ":" in body else body
    return _ok("local-recall", payload,
               memory_id=row.get("id"), retrieved_id=row.get("id"),
               used_in_context=True, future_filtered=0,
               evidence_ids=(str(row.get("id")),))


def _remember(payload: str, *, store: Path | None = None) -> tuple[str, str]:
    import hashlib
    from datetime import datetime, timezone
    mid = f"mem-{hashlib.sha256(f'semantic|{payload}'.encode()).hexdigest()[:12]}"
    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    row = {"id": mid, "kind": "semantic", "text": payload, "turn_id": "owner-cmd",
           "provenance": "owner_direct",
           "occurred_at": now, "recorded_at": now, "supersedes": None}
    dest = Path(store) if store is not None else MEMORY_STORE
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return mid, f"✓ ثبت شد: {mid} (semantic candidate — تا تأیید شما fact نمی‌شود)"


def _correct(raw: str, *, store: Path | None = None) -> LocalCommandResult:
    """Append a new version. Previous row is kept. `/correct <turn_id> کلمه درست: صدف`."""
    dest = Path(store) if store is not None else MEMORY_STORE
    rest = raw.split(maxsplit=1)
    if len(rest) < 2:
        return _ok("local-command", "usage: /correct <turn_id> کلمه درست: <text>")
    body = rest[1]
    bits = body.split(maxsplit=1)
    turn_id = bits[0]
    remainder = bits[1] if len(bits) > 1 else ""
    payload = remainder
    for sep in ("کلمه درست:", "کلمهٔ درست:"):
        if sep in remainder:
            payload = remainder.split(sep, 1)[1].strip()
            break
    if not payload:
        return _ok("local-command", "usage: /correct <turn_id> کلمه درست: <text>")
    prev = last_remember(store=dest)
    mid, _msg = _remember(payload, store=dest)
    return _ok("local-command", f"✓ اصلاح ثبت شد: {mid} (نسخهٔ قبلی حذف نشد)",
               memory_id=mid, receipt="local-correct",
               extras={"supersedes": (prev or {}).get("id"), "turn_id": turn_id})


def _feedback(cmd: str, raw: str) -> str:
    FEEDBACK.parent.mkdir(parents=True, exist_ok=True)
    with FEEDBACK.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"cmd": cmd, "text": raw, "pid": os.getpid()}, ensure_ascii=False) + "\n")
    return f"ثبت {cmd} — بدون مدل."


def _stop() -> str:
    STOP_FLAG.parent.mkdir(parents=True, exist_ok=True)
    STOP_FLAG.write_text("owner-stop\n", encoding="utf-8")
    return "توقف پایدار: پاسخ شناختی قطع شد. /resume برای ادامه."


def _resume() -> str:
    try:
        STOP_FLAG.unlink()
    except OSError:
        pass
    return "ادامه. فرمان‌های محلی فعال‌اند."


def _why() -> str:
    p = _OPS / "state" / "organs" / "halts.jsonl"
    last = None
    if p.exists():
        try:
            lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
            last = json.loads(lines[-1]) if lines else None
        except (OSError, ValueError, IndexError):
            last = None
    if not last:
        return "halt ماشینی در organs/halts.jsonl نیست. protective halt زنده را از /status ببین."
    return (f"آخرین halt: {last.get('cause_machine')} · تکرار={last.get('repeat_count')} · "
            f"{last.get('root_rfc_id')}")


def stopped() -> bool:
    return STOP_FLAG.exists()


# ── Telegram cockpit (FULL-GREEN 2026-08-21) ────────────────────────────────
# همه read-only و fail-soft؛ هیچ محتوای خصوصی/secret نمایش داده نمی‌شود.
# استثنا: /pause و /resume <nonce> (kill switch با nonce و ماندگاری روی دیسک).

def _state_dir() -> Path:
    base = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    return Path(base) if base else (_OPS / "state")


def _readj(path: Path) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return {}


def loops_text() -> str:
    reg = _state_dir() / "loops" / "LOOP-REGISTRY.json"
    d = _readj(reg)
    entries = d.get("entries") or []
    incidents = d.get("incidents") or []
    counts: dict = {}
    for e in entries:
        counts[str(e.get("status") or "open")] = counts.get(str(e.get("status") or "open"), 0) + 1
    for inc in incidents:
        k = str(inc.get("status") or "OPEN").lower()
        counts[k] = counts.get(k, 0) + 1
    parts = [f"{k}={v}" for k, v in sorted(counts.items())]
    return f"🔁 loops: " + (" · ".join(parts) if parts else "registry خالی") + \
           f" (کل: {len(entries) + len(incidents)})"


def _find_event(event_id: str) -> dict | None:
    safe = str(event_id or "").strip().replace(":", "_").replace("/", "_")
    if not safe:
        return None
    p = _state_dir() / "telegram" / "loop" / "events" / f"{safe}.json"
    return _readj(p) or None


def task_text(raw: str) -> str:
    parts = raw.split(maxsplit=1)
    if len(parts) < 2:
        return "usage: /task <event_id|task_id>"
    target = parts[1].strip()
    ev = _find_event(target)
    if ev is None:
        ev_dir = _state_dir() / "telegram" / "loop" / "events"
        try:
            for f in sorted(ev_dir.glob("*.json")):
                d = _readj(f)
                if d.get("task_id") == target or d.get("event_id") == target:
                    ev = d
                    break
        except OSError:
            ev = None
    if ev is None:
        return f"task/event «{target[:60]}» در state ماندگار نیست."
    ts = ev.get("transitions") or []
    tl = " → ".join(str(t.get("transition")) for t in ts[-8:]) or ev.get("state")
    return (f"🧾 {ev.get('event_id')} · {ev.get('state')}\n"
            f"task={ev.get('task_id')} run={ev.get('run_id')}\n"
            f"timeline: {tl}\nreadback={bool(ev.get('readback_verified'))}")


def receipts_text(raw: str) -> str:
    parts = raw.split(maxsplit=1)
    if len(parts) < 2:
        return "usage: /receipts <event_id>"
    ev = _find_event(parts[1].strip())
    if ev is None:
        return "receipt برای این event نیست."
    ids = ev.get("reply_receipt_ids") or []
    if ev.get("reply_receipt_id"):
        ids = list(ids) + [ev["reply_receipt_id"]]
    out = [f"📬 {ev.get('event_id')} · receipts={len(ids)} · readback={bool(ev.get('readback_verified'))}"]
    ob_dir = _state_dir() / "telegram" / "loop" / "outbox"
    try:
        for f in sorted(ob_dir.glob("*.json")):
            r = _readj(f)
            if r.get("message_key") in ids or r.get("event_id") == ev.get("event_id"):
                out.append(f"  {r.get('message_key','')[:12]} {r.get('state')} mid={r.get('message_id')}")
    except OSError:
        pass
    return "\n".join(out) if len(out) > 1 else out[0]


def dlq_text() -> str:
    ev_dir = _state_dir() / "telegram" / "loop" / "events"
    ob_dir = _state_dir() / "telegram" / "loop" / "outbox"
    n_events = n_outbox = 0
    try:
        n_events = sum(1 for f in ev_dir.glob("*.json")
                       if _readj(f).get("state") in ("NEEDS_RECONCILIATION", "DEAD_LETTERED"))
        n_outbox = sum(1 for f in ob_dir.glob("*.json")
                       if _readj(f).get("state") in ("DELIVERY_FAILED", "DLQ", "NEEDS_RECONCILIATION"))
    except OSError:
        pass
    return f"🗑 DLQ: events={n_events} · outbox={n_outbox}"


def memory_status_text() -> str:
    mr = _readj(_state_dir() / "pulse" / "memory-read-latest.json")
    mu = _readj(_state_dir() / "pulse" / "memory-read-last.json")
    line = f"🧠 memory: read-only={not bool(os.environ.get('OCTOPUS_MEMORY_WRITE_ALLOWED'))}"
    if mr:
        line += f" · readback_ok={mr.get('readback_ok')} reads={mr.get('reads') or mr.get('n')}"
    if mu and mu.get("ts"):
        line += f" · last={mu.get('ts')}"
    return line + " (بدون نمایش محتوا)"


def brain_status_text() -> str:
    parity = _readj(_state_dir() / "pulse" / "beat-parity.json")
    c = parity.get("counters") or {}
    fourd = _readj(_state_dir() / "pulse" / "fourd-health-latest.json")
    out = ["🧠 brains:"]
    if c:
        out.append(f"  parity: matched={c.get('matched')} missing_old={c.get('missing_old')} " +
                   ("NO_BASELINE" if (c.get('missing_old') or 0) > 0 else "ok"))
    else:
        out.append("  parity: state نیست")
    out.append(f"  4d: {'ok' if fourd else 'state نیست'}")
    return "\n".join(out)


KILL_SWITCH_FILE = "kill-switch.json"


def pause_text() -> str:
    import uuid
    nonce = uuid.uuid4().hex[:16]
    path = _state_dir() / "telegram" / "loop" / KILL_SWITCH_FILE
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"killed": True, "nonce": nonce}, ensure_ascii=False),
                        encoding="utf-8")
    except OSError:
        return "پایانِ dispatch ثبت نشد (state قابل نوشتن نیست)."
    os.environ["OCTOPUS_TG_LOOP_KILL"] = "1"
    return (f"🛑 dispatch متوقف شد. برای ادامه: /resume {nonce}\n"
            f"(nonce یک‌بار مصرف است و در state می‌ماند.)")


def resume_cockpit_text(nonce: str) -> str:
    path = _state_dir() / "telegram" / "loop" / KILL_SWITCH_FILE
    d = _readj(path)
    if not d or d.get("nonce") != str(nonce).strip():
        return "nonce نادرست یا منقضی. /pause را دوباره اجرا کن."
    try:
        path.unlink()
    except OSError:
        pass
    os.environ.pop("OCTOPUS_TG_LOOP_KILL", None)
    return "▶️ dispatch از سر گرفته شد."
