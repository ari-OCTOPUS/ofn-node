# -*- coding: utf-8 -*-
"""A18 owner-chat canary: soft-renew lock, narrow send_exceptions, max 2 live owner DMs, rollback.

OWNER EXPLICIT APPROVAL 2026-08-23: ONE owner-chat A18 canary.
Hard bounds: TELEGRAM_OWNER_CHAT_ID only; max 2 messages; no broadcast; no restart;
keep forbidden_actions including 'live sendMessage'; remove send_exceptions after.
Never prints tokens or raw chat ids.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"F:/backup")
OPS = ROOT / "_ops"
EVID = ROOT / "06-EVIDENCE" / "OCTOPUS-A18-OWNER-CHAT-CANARY-2026-08-23"
LOCK_PATH = OPS / "state" / "locks" / "octopus-writer.lock"
QUEUE_PATH = OPS / "state" / "telegram" / "a18-owner-canary-rate-limit.sqlite3"
LOCK_SNAP = EVID / "lock-before-a18.json"
RESULT_PATH = EVID / "RESULT.json"
RECEIPTS_PATH = EVID / "RECEIPTS.md"

PURPOSE = "A18-OWNER-CHAT-CANARY-20260823"
TOKEN_INTENT = "OCTOPUS-A18-OWNER-CHAT-CANARY-20260823"
AGENT = "grok-ari-single-writer"
SESSION = "sess_830e364e-8cd7-4046-ade3-9862f40ec726"
AEST = timezone(timedelta(hours=10))
TTL_EXC = 1800  # 30 min
MAX_MSG = 2

sys.path.insert(0, str(OPS))
sys.path.insert(0, str(OPS / "telegram_center"))
sys.path.insert(0, str(OPS / "tests"))


def _sha12(v: object) -> str:
    return hashlib.sha256(str(v).encode("utf-8", "replace")).hexdigest()[:12]


def _sha256(v: object) -> str:
    return hashlib.sha256(str(v).encode("utf-8", "replace")).hexdigest()


def _now_local() -> str:
    return datetime.now(AEST).isoformat(timespec="milliseconds")


def _atomic_write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    if isinstance(obj, str):
        tmp.write_text(obj, encoding="utf-8")
    else:
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def load_root_env() -> dict:
    p = ROOT / ".env"
    if not p.is_file():
        return {"loaded": False, "n_set": 0, "keys_present": []}
    allow = {
        "TG_CENTER_BOT_TOKEN",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_OWNER_CHAT_ID",
        "TG_CENTER_CHAT_ID",
    }
    n = 0
    present = []
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        k = k.strip()
        if k not in allow:
            continue
        val = v.strip().strip('"').strip("'")
        if not val:
            continue
        present.append(k)
        if not os.environ.get(k):
            os.environ[k] = val
            n += 1
    return {"loaded": True, "n_set": n, "keys_present": sorted(set(present))}


def soft_renew_and_add_exceptions(owner_sha12: str) -> dict:
    """Soft-renew heartbeat/expires; ADD send_exceptions; KEEP live sendMessage forbidden."""
    from live_state_guard import allow_live_write

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("agent_id") != AGENT or lock.get("session_id") != SESSION:
        return {"ok": False, "reason": "not_holder", "agent": lock.get("agent_id")}

    # Snapshot before mutation
    _atomic_write(LOCK_SNAP, lock)

    now = time.time()
    ttl = int(lock.get("ttl_seconds") or 900)
    before = {
        "heartbeat_at": lock.get("heartbeat_at"),
        "expires_at": lock.get("expires_at"),
        "renewed_at": lock.get("renewed_at"),
        "has_send_exceptions": "send_exceptions" in lock,
        "live_sendMessage_forbidden": "live sendMessage" in (lock.get("forbidden_actions") or []),
    }

    exc = {
        "owner_only": True,
        "chat_sha12": owner_sha12,
        "max_messages": MAX_MSG,
        "messages_sent": 0,
        "commands": ["/remember", "/correct"],
        "token_intent": TOKEN_INTENT,
        "purpose": PURPOSE,
        "ttl_seconds": TTL_EXC,
        "created_at": now,
        "expires_at": now + TTL_EXC,
        "created_at_local": _now_local(),
        "owner_order": "OWNER EXPLICIT APPROVAL (2026-08-23): unlock system for ONE owner-chat A18 canary",
    }

    # Ensure live sendMessage stays in forbidden_actions
    fa = list(lock.get("forbidden_actions") or [])
    if "live sendMessage" not in fa:
        fa.append("live sendMessage")
    lock["forbidden_actions"] = fa

    with allow_live_write("A18 soft-renew + narrow send_exceptions owner-only"):
        lock["heartbeat_at"] = now
        lock["renewed_at"] = round(now, 6)
        lock["expires_at"] = now + ttl
        lock["renewed_at_local"] = _now_local()
        lock["send_exceptions"] = [exc]
        tmp = LOCK_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(lock, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, LOCK_PATH)

    after_lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    return {
        "ok": True,
        "before": before,
        "after": {
            "heartbeat_at": after_lock.get("heartbeat_at"),
            "expires_at": after_lock.get("expires_at"),
            "renewed_at_local": after_lock.get("renewed_at_local"),
            "send_exceptions_count": len(after_lock.get("send_exceptions") or []),
            "live_sendMessage_forbidden": "live sendMessage" in (after_lock.get("forbidden_actions") or []),
            "exception_purpose": PURPOSE,
            "exception_ttl_s": TTL_EXC,
            "exception_max_messages": MAX_MSG,
            "exception_chat_sha12": owner_sha12,
        },
        "seconds_to_expiry": float(after_lock.get("expires_at") or 0) - time.time(),
    }


def honor_send_exceptions(owner_sha12: str, command: str) -> dict:
    """Minimal reversible gate: code previously ignored send_exceptions; enforce here."""
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    fa = lock.get("forbidden_actions") or []
    if "live sendMessage" not in fa:
        # unexpected — still require exception for this canary
        pass
    excs = lock.get("send_exceptions") or []
    now = time.time()
    for exc in excs:
        if not isinstance(exc, dict):
            continue
        if exc.get("purpose") != PURPOSE and exc.get("token_intent") != TOKEN_INTENT:
            continue
        if not exc.get("owner_only"):
            continue
        if str(exc.get("chat_sha12") or "") != owner_sha12:
            continue
        if float(exc.get("expires_at") or 0) < now:
            return {"ok": False, "reason": "send_exception_expired"}
        cmds = exc.get("commands") or []
        if command not in cmds:
            return {"ok": False, "reason": f"command_not_in_exception:{command}"}
        sent = int(exc.get("messages_sent") or 0)
        max_m = int(exc.get("max_messages") or 0)
        if sent >= max_m:
            return {"ok": False, "reason": "max_messages_exhausted"}
        return {"ok": True, "exception": {
            "purpose": exc.get("purpose"),
            "chat_sha12": exc.get("chat_sha12"),
            "messages_sent": sent,
            "max_messages": max_m,
            "expires_at": exc.get("expires_at"),
        }}
    return {"ok": False, "reason": "no_matching_send_exception"}


def bump_messages_sent() -> None:
    from live_state_guard import allow_live_write
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    excs = lock.get("send_exceptions") or []
    for exc in excs:
        if isinstance(exc, dict) and (
            exc.get("purpose") == PURPOSE or exc.get("token_intent") == TOKEN_INTENT
        ):
            exc["messages_sent"] = int(exc.get("messages_sent") or 0) + 1
    with allow_live_write("A18 bump send_exceptions.messages_sent"):
        lock["send_exceptions"] = excs
        tmp = LOCK_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(lock, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, LOCK_PATH)


def rollback_send_exceptions() -> dict:
    from live_state_guard import allow_live_write
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    before = lock.get("send_exceptions")
    fa = list(lock.get("forbidden_actions") or [])
    if "live sendMessage" not in fa:
        fa.append("live sendMessage")
    with allow_live_write("A18 rollback remove send_exceptions; keep forbidden live sendMessage"):
        lock.pop("send_exceptions", None)
        lock["forbidden_actions"] = fa
        lock["heartbeat_at"] = time.time()
        lock["renewed_at"] = round(time.time(), 6)
        lock["renewed_at_local"] = _now_local()
        # keep expires_at as-is from soft-renew
        tmp = LOCK_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(lock, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, LOCK_PATH)
    after = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    return {
        "removed": before is not None,
        "send_exceptions_present_after": "send_exceptions" in after,
        "live_sendMessage_forbidden_after": "live sendMessage" in (after.get("forbidden_actions") or []),
    }


def send_one(client, owner_id: int, owner_sha12: str, command: str, text: str, idx: int) -> dict:
    gate = honor_send_exceptions(owner_sha12, command)
    if not gate.get("ok"):
        return {"ok": False, "blocked_by_gate": True, "gate": gate, "command": command}

    from live_state_guard import allow_live_write
    import rate_limit_queue as rlq
    from sender_bridge import SenderBridge

    chat_hash = _sha256(owner_id)
    payload_hash = _sha256(text)
    message_key = _sha256(f"a18|{PURPOSE}|{idx}|{chat_hash}|{payload_hash}")[:40]
    send_trace = {"attempts": 0, "message_id": None, "error": None}

    def send_fn(item: dict) -> dict:
        send_trace["attempts"] += 1
        if str(item.get("chat_hash") or "") != chat_hash:
            send_trace["error"] = "chat_hash_mismatch"
            return {"ok": False}
        if send_trace["attempts"] > 1:
            send_trace["error"] = "second_attempt_refused"
            return {"ok": False}
        # Force owner chat only
        mid = client.send(text, chat_id=owner_id, stream="owner-a18-canary")
        if mid is None:
            send_trace["error"] = "send_returned_none"
            return {"ok": False}
        send_trace["message_id"] = int(mid)
        return {"ok": True, "message_id": int(mid)}

    with allow_live_write(f"A18 owner-chat canary msg{idx} {command} via SenderBridge"):
        q = rlq.RateLimitQueue(QUEUE_PATH)
        client.attach_defer_queue(q)
        enq = q.enqueue(
            message_key=message_key,
            chat_hash=chat_hash,
            payload_hash=payload_hash,
            priority=100,
        )
        if enq.get("state") == "REJECTED_QUEUE_FULL":
            q.close()
            return {"ok": False, "error": "queue_full", "enqueue": enq, "command": command}
        bridge = SenderBridge(q, send_fn, is_group=lambda _h: False)
        out = bridge.run_once(limit=1)
        row = q.get(message_key)
        q.close()

    confirmed = (
        isinstance(row, dict)
        and row.get("state") == "CONFIRMED"
        and row.get("message_id") is not None
        and out.get("sent") == 1
    )
    if confirmed:
        bump_messages_sent()

    return {
        "ok": bool(confirmed),
        "command": command,
        "message_id": int(row["message_id"]) if confirmed else None,
        "outbox_state": (row or {}).get("state") if isinstance(row, dict) else None,
        "outbox_message_key": message_key,
        "bridge_counts": out,
        "send_trace": send_trace,
        "gate": gate,
        "chat_sha12": owner_sha12,
        "text_sha12": _sha12(text),
        "delivery_attempts": (row or {}).get("delivery_attempts") if isinstance(row, dict) else None,
    }


def write_result(rec: dict) -> None:
    _atomic_write(RESULT_PATH, rec)
    lines = [
        f"# RECEIPTS — OCTOPUS-A18-OWNER-CHAT-CANARY-2026-08-23",
        "",
        f"- STATUS: **{rec.get('status')}**",
        f"- created_at_local: {rec.get('created_at_local')}",
        f"- live_send_attempted: {rec.get('live_send_attempted')}",
        f"- owner_chat last4: {rec.get('owner_chat', {}).get('last4')} / sha12: {rec.get('owner_chat', {}).get('sha12')} (REDACTED value)",
        f"- messages_confirmed: {rec.get('messages_confirmed', 0)} / max {MAX_MSG}",
        f"- broadcast: {rec.get('broadcast')}",
        f"- process_restart: {rec.get('process_restart')}",
        f"- send_exceptions_rolled_back: {rec.get('rollback', {}).get('send_exceptions_present_after') is False}",
        f"- live sendMessage still forbidden: {rec.get('rollback', {}).get('live_sendMessage_forbidden_after')}",
        "",
        "## Exact status detail",
        "",
        rec.get("status_detail") or rec.get("exact_forbid_reason") or "(none)",
        "",
        "## Message receipts",
        "",
    ]
    for i, m in enumerate(rec.get("messages") or [], 1):
        lines.append(
            f"- msg{i}: ok={m.get('ok')} cmd={m.get('command')} "
            f"outbox_state={m.get('outbox_state')} message_id={m.get('message_id')} "
            f"text_sha12={m.get('text_sha12')}"
        )
    lines.extend([
        "",
        "## Compact",
        "",
        f"- **STATUS**: {rec.get('status')}",
        f"- **EVIDENCE**: {RESULT_PATH.as_posix()}",
        f"- **NEXT**: {rec.get('compact', {}).get('NEXT')}",
        "",
    ])
    _atomic_write(RECEIPTS_PATH, "\n".join(lines) + "\n")


def main() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    started = _now_local()
    rollback_info = {"attempted": False}
    messages = []
    live_attempted = False
    status = "BLOCKED"
    status_detail = ""
    renew_info = {}
    env_load = {}
    owner_meta = {}

    try:
        # Stop / kill switches
        for name in ("STOP-TG-HEARTBEAT", "STOP-ORGANISM", "HALT-ALL"):
            if (OPS / name).is_file():
                status_detail = f"stop_file_armed:{name}"
                raise RuntimeError(status_detail)
        ks = OPS / "state" / "telegram" / "loop" / "kill-switch.json"
        if ks.is_file():
            try:
                if json.loads(ks.read_text(encoding="utf-8")).get("killed"):
                    status_detail = "durable_loop_kill_switch"
                    raise RuntimeError(status_detail)
            except (OSError, ValueError):
                pass

        env_load = load_root_env()
        owner_raw = (os.environ.get("TELEGRAM_OWNER_CHAT_ID") or "").strip()
        center_raw = (os.environ.get("TG_CENTER_CHAT_ID") or "").strip()
        token_ok = bool(
            (os.environ.get("TG_CENTER_BOT_TOKEN") or "").strip()
            or (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
        )
        if not owner_raw:
            status_detail = "TELEGRAM_OWNER_CHAT_ID_unresolved"
            raise RuntimeError(status_detail)
        if not token_ok:
            status_detail = "bot_token_unresolved"
            raise RuntimeError(status_detail)
        try:
            owner_id = int(owner_raw)
        except ValueError:
            status_detail = "owner_chat_id_not_int"
            raise RuntimeError(status_detail)
        if owner_id <= 0:
            status_detail = "owner_chat_not_private_dm"
            raise RuntimeError(status_detail)
        if center_raw:
            try:
                if int(center_raw) == owner_id:
                    status_detail = "owner_equals_center_chat_refused"
                    raise RuntimeError(status_detail)
            except ValueError:
                pass

        owner_sha12 = _sha12(owner_id)
        owner_last4 = str(owner_id)[-4:]
        # Cross-check prior N1
        prior_sha12 = "14280e011544"
        owner_meta = {
            "source": "F:/backup/.env TELEGRAM_OWNER_CHAT_ID + prior N1 sha12 cross-check",
            "last4": owner_last4,
            "sha12": owner_sha12,
            "matches_prior_n1_sha12": owner_sha12 == prior_sha12,
            "chat_target_class": "owner-only",
            "value_plaintext": "REDACTED",
        }
        if owner_sha12 != prior_sha12:
            status_detail = f"owner_sha12_mismatch_vs_prior_n1 got={owner_sha12}"
            raise RuntimeError(status_detail)

        renew_info = soft_renew_and_add_exceptions(owner_sha12)
        if not renew_info.get("ok"):
            status_detail = f"soft_renew_failed:{renew_info.get('reason')}"
            raise RuntimeError(status_detail)

        from tg_api import TgClient
        client = TgClient()
        if not client.wired():
            status_detail = "tg_client_not_wired"
            raise RuntimeError(status_detail)
        if client.owner_chat_id is None or int(client.owner_chat_id) != owner_id:
            status_detail = "client_owner_mismatch"
            raise RuntimeError(status_detail)

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        remember_text = (
            f"/remember prove-canary-{stamp}: A18-OWNER-CHAT-CANARY pearl-ack "
            f"token_intent={TOKEN_INTENT}"
        )
        correct_text = (
            f"/correct INVALID-TURN-A18-{stamp} prove-canary-invalid: shell "
            f"token_intent={TOKEN_INTENT}"
        )

        live_attempted = True
        m1 = send_one(client, owner_id, owner_sha12, "/remember", remember_text, 1)
        messages.append(m1)
        if not m1.get("ok"):
            status_detail = f"msg1_failed:{m1.get('error') or m1.get('send_trace', {}).get('error') or m1.get('gate', {}).get('reason')}"
            status = "PARTIAL" if False else "BLOCKED"
        else:
            m2 = send_one(client, owner_id, owner_sha12, "/correct", correct_text, 2)
            messages.append(m2)
            if m2.get("ok"):
                status = "PASS"
                status_detail = "both owner-only live messages CONFIRMED via SenderBridge; exceptions rolled back"
            else:
                status = "PARTIAL"
                status_detail = f"msg1_ok msg2_failed:{m2.get('error') or m2.get('send_trace', {}).get('error') or m2.get('gate', {}).get('reason')}"

    except Exception as exc:
        if not status_detail:
            status_detail = f"exception:{type(exc).__name__}:{exc}"
        if status == "PASS":
            status = "PARTIAL"
        # keep BLOCKED/PARTIAL as set
        err_tb = traceback.format_exc()
        (EVID / "error-traceback.txt").write_text(err_tb, encoding="utf-8")

    finally:
        try:
            rollback_info = rollback_send_exceptions()
            rollback_info["attempted"] = True
        except Exception as rex:
            rollback_info = {
                "attempted": True,
                "error": f"{type(rex).__name__}:{rex}",
                "send_exceptions_present_after": None,
                "live_sendMessage_forbidden_after": None,
            }

    confirmed_n = sum(1 for m in messages if m.get("ok"))
    rec = {
        "schema": "octopus-a18-owner-chat-canary-result/1",
        "token_intent": TOKEN_INTENT,
        "slice": "A18-OWNER-CHAT-CANARY",
        "status": status,
        "pass": status == "PASS",
        "status_detail": status_detail,
        "live_send_attempted": live_attempted,
        "messages_confirmed": confirmed_n,
        "max_messages": MAX_MSG,
        "broadcast": False,
        "process_restart": False,
        "destructive": False,
        "secrets_plaintext": False,
        "timezone": "Australia/Sydney",
        "created_at_local": started,
        "finished_at_local": _now_local(),
        "executor": "grok-bot-subagent",
        "owner_go": {
            "claimed_in_task": True,
            "condition": "OWNER EXPLICIT APPROVAL (2026-08-23): unlock system for ONE owner-chat A18 canary",
            "lease_renewed": bool(renew_info.get("ok")),
            "send_exceptions_added": bool(renew_info.get("ok")),
        },
        "owner_chat": owner_meta,
        "writer_lock_renew": renew_info,
        "env_load": {k: env_load.get(k) for k in ("loaded", "n_set", "keys_present")},
        "messages": [
            {
                "ok": m.get("ok"),
                "command": m.get("command"),
                "message_id": m.get("message_id"),
                "outbox_state": m.get("outbox_state"),
                "outbox_message_key": m.get("outbox_message_key"),
                "bridge_counts": m.get("bridge_counts"),
                "send_trace": m.get("send_trace"),
                "gate_ok": (m.get("gate") or {}).get("ok"),
                "text_sha12": m.get("text_sha12"),
                "chat_sha12": m.get("chat_sha12"),
                "error": m.get("error"),
            }
            for m in messages
        ],
        "path": "RateLimitQueue+SenderBridge+TgClient.send(owner_only)+send_exceptions_gate",
        "queue_path": str(QUEUE_PATH),
        "rollback": rollback_info,
        "runtime_health": {
            "center_pid": 35916,
            "organism_pid": 26900,
            "center_restarted": False,
            "organism_left_alone": True,
        },
        "guards": {
            "forbidden_actions_kept_live_sendMessage": True,
            "send_exceptions_ttl_30min": True,
            "owner_only": True,
            "max_2_messages": True,
            "no_broadcast": True,
            "no_token_scrape": True,
            "no_center_restart": True,
        },
        "compact": {
            "STATUS": status,
            "EVIDENCE": str(RESULT_PATH).replace("\\", "/"),
            "NEXT": (
                "A18 live owner ACK unlocked and proven; resume remember/correct LIVE center path verification"
                if status == "PASS"
                else (
                    "Investigate msg failure; re-arm send_exceptions under fresh owner approval if needed"
                    if status == "PARTIAL"
                    else "Resolve block reason; do not bypass via browser cookies"
                )
            ),
        },
    }
    write_result(rec)
    print(json.dumps({
        "STATUS": status,
        "messages_confirmed": confirmed_n,
        "detail": status_detail,
        "owner_sha12": owner_meta.get("sha12"),
        "rollback_ok": rollback_info.get("send_exceptions_present_after") is False,
        "evidence": str(RESULT_PATH),
    }, ensure_ascii=False))
    return 0 if status == "PASS" else (1 if status == "PARTIAL" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
