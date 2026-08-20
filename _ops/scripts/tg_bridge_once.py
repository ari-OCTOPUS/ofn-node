#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tg_bridge_once.py — owner-facing Telegram bridge (incident-safe).

2026-08-20 LOOP-TELEGRAM-PROBE-INVALID:
The previous identity hash included `beat`, so a 5-minute scheduler treated
every organism tick as a status change and spammed owner chat with
PROBE_RESPONSE_INVALID while telegram_events stayed 11.

Rules now:
- Heartbeat (beat/memread) is internal telemetry. Never user-facing.
- telegram_events count is NOT proof of closed-loop success.
- User-facing send only on probe/event STATE TRANSITION, coalesced.
- Outbox-first. Injected transport in tests. STOP-TG-HEARTBEAT = safe mode.
- Terminal states: COMPLETED | BLOCKED | DEAD_LETTERED.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "_ops/budget"))

STATE_FILE = _ROOT / "research/full_loop/state/tg-last-push.json"
OUTBOX_FILE = _ROOT / "_ops/state/loops/telegram-bridge-outbox.jsonl"
TELEMETRY_FILE = _ROOT / "_ops/state/loops/tg-bridge-heartbeat.jsonl"
STOP_FILES = (
    _ROOT / "_ops/STOP-TG-HEARTBEAT",
    _ROOT / "_ops/STOP-ORGANISM",
    _ROOT / "_ops/HALT-ALL",
)
PROBE_FILE = _ROOT / "06-EVIDENCE/EVENT-TIME-PROBE-2026-08-20.json"
SPINE_DB = _ROOT / "_ops/state/spine/spine.db"

# Digest at most once per 6h for the same invalid payload; then DEAD_LETTERED.
COALESCE_S = 6 * 3600
MAX_USER_FACING_PER_PAYLOAD = 2  # incident + one digest
TERMINAL_COMPLETED = "COMPLETED"
TERMINAL_BLOCKED = "BLOCKED"
TERMINAL_DLQ = "DEAD_LETTERED"
INVALID = "PROBE_RESPONSE_INVALID"


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def identity_key(s: dict) -> str:
    """User-facing identity — MUST exclude beat (internal telemetry)."""
    body = json.dumps({
        "tg_events": s.get("tg_events"),
        "sc_events": s.get("sc_events"),
        "probe": s.get("probe"),
        "probe_id": s.get("probe_id"),
        "nonce_match": s.get("nonce_match"),
    }, sort_keys=True)
    return _sha(body)[:12]


def payload_hash(s: dict) -> str:
    return _sha(json.dumps({
        "probe": s.get("probe"),
        "probe_id": s.get("probe_id"),
        "task_id": s.get("task_id"),
        "run_id": s.get("run_id"),
        "nonce_match": s.get("nonce_match"),
        "validation_rule": s.get("validation_rule"),
    }, sort_keys=True))[:16]


def stop_armed(paths: tuple[Path, ...] = STOP_FILES) -> bool:
    return any(p.is_file() for p in paths)


def snapshot(now: float | None = None) -> dict:
    import sqlite3
    out: dict[str, Any] = {"ts": now if now is not None else time.time()}
    try:
        d = json.loads((_ROOT / "_ops/state/ORGANISM-STATE.json")
                       .read_text(encoding="utf-8"))
        out["beat"] = d.get("beat")
    except Exception:  # noqa: BLE001
        out["beat"] = None
    try:
        m = json.loads((_ROOT / "_ops/state/pulse/memory-read-latest.json")
                       .read_text(encoding="utf-8"))
        out["memread"] = (m.get("status"), m.get("memory_reads_per_cycle"),
                          m.get("readback"))
        out["memread_ok"] = m.get("status") == "OK"
    except Exception:  # noqa: BLE001
        out["memread"] = None
        out["memread_ok"] = False
    try:
        con = sqlite3.connect(f"file:{SPINE_DB}?mode=ro", uri=True)
        out["tg_events"] = con.execute(
            "SELECT COUNT(*) FROM events WHERE domain='telegram'").fetchone()[0]
        out["sc_events"] = con.execute(
            "SELECT COUNT(*) FROM events WHERE event_time_source="
            "'provider_server_created'").fetchone()[0]
        con.close()
    except Exception:  # noqa: BLE001
        out["tg_events"] = None
        out["sc_events"] = None
    probe = {}
    if PROBE_FILE.is_file():
        try:
            probe = json.loads(PROBE_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            probe = {}
    out["probe"] = probe.get("verdict") if probe else "NOT_RUN"
    out["probe_id"] = probe.get("probe_id")
    out["task_id"] = probe.get("task_id")
    out["run_id"] = probe.get("run_id")
    resp = probe.get("response") if isinstance(probe.get("response"), dict) else {}
    result = probe.get("result") if isinstance(probe.get("result"), dict) else {}
    out["nonce_match"] = resp.get("nonce_match")
    out["http_status"] = resp.get("http_status")
    out["finish_reason"] = resp.get("finish_reason")
    out["spine_event_written"] = result.get("spine_event_written")
    out["executable"] = result.get("executable")
    # Exact validation rule that fails (frozen probe 2026-08-20).
    if out["probe"] == INVALID:
        if resp.get("nonce_match") is False:
            out["validation_rule"] = "response.content == request.nonce (exact)"
        elif not result.get("spine_event_written"):
            out["validation_rule"] = "spine_event_written"
        else:
            out["validation_rule"] = "PROBE_RESPONSE_INVALID"
    else:
        out["validation_rule"] = None
    out["closed_loop"] = False  # count ≠ closure
    out["identity_key"] = identity_key(out)
    out["payload_hash"] = payload_hash(out)
    return out


def classify(
    s: dict,
    prev: dict,
    *,
    now: float,
    stopped: bool,
    coalesce_s: float = COALESCE_S,
) -> dict[str, Any]:
    """Decide user-facing action. Beat changes never send."""
    ph = s.get("payload_hash") or payload_hash(s)
    prev_ph = prev.get("payload_hash")
    prev_probe = prev.get("probe")
    n_sent = int(prev.get("user_facing_n") or 0)
    if prev_ph == ph:
        n_sent = int(prev.get("user_facing_n") or 0)
    else:
        n_sent = 0

    terminal = prev.get("terminal") if prev_ph == ph else None
    reason = "none"
    send = False
    kind = None

    if stopped:
        reason = "safe_mode_stop"
        if s.get("probe") == INVALID:
            terminal = terminal or TERMINAL_BLOCKED
        return _decision(send, kind, reason, terminal, n_sent, ph)

    if s.get("probe") == "PROBE_PASS" and s.get("nonce_match") is True \
            and s.get("spine_event_written") is True:
        # Still not a Telegram closed loop — probe PASS ≠ telegram closure.
        terminal = TERMINAL_COMPLETED
        reason = "probe_completed_not_telegram_closure"
        return _decision(False, None, reason, terminal, n_sent, ph)

    if s.get("probe") == INVALID:
        if prev_probe != INVALID or prev_ph != ph:
            if n_sent == 0:
                send, kind, reason = True, "incident", "probe_invalid_first"
                n_sent = 1
                terminal = TERMINAL_BLOCKED
            else:
                reason = "already_notified"
                terminal = TERMINAL_BLOCKED
        else:
            # Same invalid payload: at most one digest after coalesce window.
            last = float(prev.get("last_user_facing_at") or 0)
            if n_sent >= MAX_USER_FACING_PER_PAYLOAD:
                send, reason, terminal = False, "dead_lettered", TERMINAL_DLQ
            elif n_sent == 1 and last and (now - last) >= coalesce_s:
                send, kind, reason = True, "digest", "invalid_coalesced_digest"
                n_sent = 2
                terminal = TERMINAL_DLQ
            else:
                send, reason, terminal = False, "coalesced_same_invalid", TERMINAL_BLOCKED
        return _decision(send, kind, reason, terminal, n_sent, ph)

    # New telegram events are telemetry, not a closed loop, and not a reason
    # to spam a heartbeat. Only notify if probe verdict itself changed away
    # from INVALID to something else (recovery).
    if prev_probe and prev_probe != s.get("probe"):
        send, kind, reason = True, "incident", "probe_state_transition"
        n_sent = 1
        terminal = TERMINAL_BLOCKED if s.get("probe") not in ("PROBE_PASS",) else TERMINAL_COMPLETED
        return _decision(send, kind, reason, terminal, n_sent, ph)

    return _decision(False, None, "no_user_facing_change", terminal, n_sent, ph)


def _decision(send, kind, reason, terminal, n_sent, ph) -> dict[str, Any]:
    return {
        "send": bool(send),
        "kind": kind,
        "reason": reason,
        "terminal": terminal,
        "user_facing_n": n_sent,
        "payload_hash": ph,
        "idempotency_key": f"probe:{ph}:{kind or 'none'}",
    }


def render(s: dict, kind: str) -> str:
    pid = s.get("probe_id") or "unlocated"
    rule = s.get("validation_rule") or "unlocated"
    if kind == "incident":
        return (
            "INCIDENT LOOP-TELEGRAM-PROBE-INVALID\n"
            f"probe={s.get('probe')} · probe_id={pid}\n"
            f"task_id={s.get('task_id')} · run_id={s.get('run_id')}\n"
            f"rule={rule}\n"
            f"telegram_events={s.get('tg_events')} (count≠closure)\n"
            "heartbeat suppressed; this is a state transition, not a beat."
        )
    return (
        f"DIGEST probe still {s.get('probe')} (payload {s.get('payload_hash')})\n"
        f"telegram_events={s.get('tg_events')} unchanged-or-stale · "
        "no further user-facing until verdict changes · DEAD_LETTERED"
    )


def _append_jsonl(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _env():
    import env_loader
    env_loader.load_env()
    return (os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_OWNER_CHAT_ID"])


def _http_send(token: str, chat_id: str, text: str) -> bool:
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps({"chat_id": chat_id, "text": text}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode()).get("ok") is True


def tick(
    *,
    s: dict | None = None,
    prev: dict | None = None,
    now: float | None = None,
    stopped: bool | None = None,
    send_fn: Callable[[str], bool] | None = None,
    state_file: Path = STATE_FILE,
    outbox_file: Path = OUTBOX_FILE,
    telemetry_file: Path = TELEMETRY_FILE,
    live: bool = False,
) -> dict[str, Any]:
    now = time.time() if now is None else now
    s = s if s is not None else snapshot(now=now)
    if prev is None:
        prev = {}
        if state_file.exists():
            try:
                prev = json.loads(state_file.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                prev = {}
    if stopped is None:
        stopped = stop_armed()
    # Existing spam: if previous push already carried this invalid probe,
    # count it as already notified even if user_facing_n is missing.
    if (s.get("probe") == INVALID and prev.get("probe") == INVALID
            and not prev.get("user_facing_n")):
        prev = dict(prev)
        prev["user_facing_n"] = MAX_USER_FACING_PER_PAYLOAD
        prev["payload_hash"] = prev.get("payload_hash") or s.get("payload_hash")
        prev["last_user_facing_at"] = prev.get("pushed_at") or now

    decision = classify(s, prev, now=now, stopped=stopped)
    telemetry = {
        "ts": now, "beat": s.get("beat"), "probe": s.get("probe"),
        "tg_events": s.get("tg_events"), "identity_key": s.get("identity_key"),
        "payload_hash": s.get("payload_hash"), "reason": decision["reason"],
        "send": decision["send"], "kind": decision["kind"],
        "terminal": decision["terminal"], "memread": s.get("memread"),
        "closed_loop": False,
    }
    _append_jsonl(telemetry_file, telemetry)

    sent = False
    text = None
    if decision["send"]:
        text = render(s, decision["kind"])
        rec = {
            "ts": now, "kind": decision["kind"], "text": text,
            "idempotency_key": decision["idempotency_key"],
            "payload_hash": decision["payload_hash"],
            "terminal": decision["terminal"],
            "mode": "live" if live and not stopped else "dry_run",
            "sent": False,
            "delivery_retry": 0,
            "business_retry": 0,
        }
        _append_jsonl(outbox_file, rec)
        if live and not stopped:
            try:
                ok = bool(send_fn(text)) if send_fn else False
                sent = ok
            except Exception:  # noqa: BLE001
                rec["delivery_retry"] = 1
                sent = False
            rec["sent"] = sent
            _append_jsonl(outbox_file, rec)

    new_state = {
        "key": s.get("identity_key"),
        "identity_key": s.get("identity_key"),
        "payload_hash": decision["payload_hash"],
        "probe": s.get("probe"),
        "probe_id": s.get("probe_id"),
        "task_id": s.get("task_id"),
        "run_id": s.get("run_id"),
        "tg_events": s.get("tg_events"),
        "sc_events": s.get("sc_events"),
        "beat": s.get("beat"),
        "memread": s.get("memread"),
        "ts": now,
        "pushed_at": now if sent or (decision["send"] and not live) else prev.get("pushed_at"),
        "last_user_facing_at": now if decision["send"] else prev.get("last_user_facing_at"),
        "user_facing_n": decision["user_facing_n"],
        "terminal": decision["terminal"],
        "reason": decision["reason"],
        "sent": sent,
        "kind": decision["kind"],
        "closed_loop": False,
        "validation_rule": s.get("validation_rule"),
    }
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(new_state, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    return {"snapshot": s, "decision": decision, "state": new_state,
            "sent": sent, "text": text}


def main(force: bool = False) -> str:
    live_flag = (_ROOT / "_ops/state/loops/LIVE-TG-BRIDGE.flag").is_file()
    r = tick(live=bool(live_flag) and not stop_armed())
    d = r["decision"]
    return (f"{d['reason']} terminal={d['terminal']} send={d['send']} "
            f"kind={d['kind']} beat={r['snapshot'].get('beat')} "
            f"tg_events={r['snapshot'].get('tg_events')} "
            f"probe={r['snapshot'].get('probe')}")


if __name__ == "__main__":
    print(main(force="--force" in sys.argv))
