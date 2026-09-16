#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ONE live owner canary for EXPEDITED_BOUNDED_LIVE_ROLLOUT.

Authorization: OCTOPUS-OWNER-CANARY-20260822-N1
Bounds: exactly one message to TELEGRAM_OWNER_CHAT_ID via RateLimitQueue+SenderBridge.
Never prints tokens or raw chat ids.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"F:/backup")
OPS = ROOT / "_ops"
EVID = ROOT / "06-EVIDENCE" / "OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22"
LOCK_PATH = OPS / "state" / "locks" / "octopus-writer.lock"
OUT_JSON = EVID / "CANARY-N1.json"
QUEUE_PATH = OPS / "state" / "telegram" / "canary-n1-rate-limit.sqlite3"
CANARY_TOKEN = "OCTOPUS-LIVE-CANARY-N1-2026-08-22"
AUTH_ID = "OCTOPUS-OWNER-CANARY-20260822-N1"
AGENT = "grok-ari-single-writer"
SESSION = "sess_830e364e-8cd7-4046-ade3-9862f40ec726"
AEST = timezone(timedelta(hours=10))

sys.path.insert(0, str(OPS))
sys.path.insert(0, str(OPS / "telegram_center"))
sys.path.insert(0, str(OPS / "tests"))


def _sha12(v: object) -> str:
    return hashlib.sha256(str(v).encode("utf-8", "replace")).hexdigest()[:12]


def _sha256(v: object) -> str:
    return hashlib.sha256(str(v).encode("utf-8", "replace")).hexdigest()


def _now_local() -> str:
    return datetime.now(AEST).isoformat(timespec="milliseconds")


def _atomic_write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def write_blocked(reason: str, **extra) -> dict:
    rec = {
        "schema": "octopus-owner-canary-n1/1",
        "authorization_id": AUTH_ID,
        "mode": "EXPEDITED_BOUNDED_LIVE_ROLLOUT",
        "builder": AGENT,
        "verdict_label": "BUILDER_VERIFIED",
        "independent_verification": False,
        "canary_token": CANARY_TOKEN,
        "sent": False,
        "live_send": False,
        "message_id": None,
        "chat_target_class": "owner-only",
        "chat_id_hash_ok": False,
        "chat_id_sha12": None,
        "outbox_path": str(QUEUE_PATH),
        "readback_confirm": None,
        "timestamp_local_aest": _now_local(),
        "blocked": True,
        "block_reason": reason,
        **extra,
    }
    _atomic_write(OUT_JSON, rec)
    return rec


def renew_heartbeat() -> dict:
    from live_state_guard import allow_live_write  # noqa: WPS433

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("agent_id") != AGENT or lock.get("session_id") != SESSION:
        return {"ok": False, "reason": "not_holder", "agent": lock.get("agent_id")}
    remain_h = (float(lock.get("expires_at") or 0) - time.time()) / 3600.0
    with allow_live_write("canary-n1-writer-heartbeat"):
        lock["heartbeat_at"] = time.time()
        lock["renewed_at"] = round(time.time(), 3)
        lock["renewed_at_local"] = _now_local()
        # remaining >= 2h: heartbeat only, do not extend expires_at
        tmp = LOCK_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(lock, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, LOCK_PATH)
    return {"ok": True, "remaining_hours": remain_h, "ttl_extended": False}


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
    return {"loaded": True, "n_set": n, "keys_present": present}


def main() -> int:
    # Idempotency: never a second canary
    if OUT_JSON.is_file():
        prev = json.loads(OUT_JSON.read_text(encoding="utf-8"))
        if prev.get("sent") or prev.get("live_send"):
            print(json.dumps({
                "result": "ALREADY_SENT",
                "message_id": prev.get("message_id"),
                "evidence": str(OUT_JSON),
            }, ensure_ascii=False))
            return 0
        if prev.get("blocked"):
            # allow retry only if previous was blocked (not sent)
            pass

    hb = renew_heartbeat()
    if not hb.get("ok"):
        rec = write_blocked("writer_lock_not_held", heartbeat=hb)
        print(json.dumps({"result": "BLOCKED", "reason": rec["block_reason"]}, ensure_ascii=False))
        return 2

    env_load = load_root_env()
    owner_raw = (os.environ.get("TELEGRAM_OWNER_CHAT_ID") or "").strip()
    center_raw = (os.environ.get("TG_CENTER_CHAT_ID") or "").strip()
    token_ok = bool(
        (os.environ.get("TG_CENTER_BOT_TOKEN") or "").strip()
        or (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    )
    if not owner_raw:
        rec = write_blocked("TELEGRAM_OWNER_CHAT_ID_unresolved", env_load=env_load, heartbeat=hb)
        print(json.dumps({"result": "BLOCKED", "reason": rec["block_reason"]}, ensure_ascii=False))
        return 2
    if not token_ok:
        rec = write_blocked("bot_token_unresolved", env_load=env_load, heartbeat=hb)
        print(json.dumps({"result": "BLOCKED", "reason": rec["block_reason"]}, ensure_ascii=False))
        return 2

    try:
        owner_id = int(owner_raw)
    except ValueError:
        rec = write_blocked("owner_chat_id_not_int", env_load=env_load, heartbeat=hb)
        print(json.dumps({"result": "BLOCKED", "reason": rec["block_reason"]}, ensure_ascii=False))
        return 2

    # Owner-only: private DM (positive). Reject groups / center chat.
    if owner_id <= 0:
        rec = write_blocked(
            "owner_chat_not_private_dm",
            chat_id_sha12=_sha12(owner_id),
            env_load=env_load,
            heartbeat=hb,
        )
        print(json.dumps({"result": "BLOCKED", "reason": rec["block_reason"]}, ensure_ascii=False))
        return 2
    if center_raw:
        try:
            if int(center_raw) == owner_id:
                rec = write_blocked(
                    "owner_equals_center_chat_refused",
                    chat_id_sha12=_sha12(owner_id),
                    env_load=env_load,
                    heartbeat=hb,
                )
                print(json.dumps({"result": "BLOCKED", "reason": rec["block_reason"]}, ensure_ascii=False))
                return 2
        except ValueError:
            pass

    # Stop / kill switches
    for name in ("STOP-TG-HEARTBEAT", "STOP-ORGANISM", "HALT-ALL"):
        if (OPS / name).is_file():
            rec = write_blocked(f"stop_file_armed:{name}", heartbeat=hb)
            print(json.dumps({"result": "BLOCKED", "reason": rec["block_reason"]}, ensure_ascii=False))
            return 2
    ks = OPS / "state" / "telegram" / "loop" / "kill-switch.json"
    if ks.is_file():
        try:
            if json.loads(ks.read_text(encoding="utf-8")).get("killed"):
                rec = write_blocked("durable_loop_kill_switch", heartbeat=hb)
                print(json.dumps({"result": "BLOCKED", "reason": rec["block_reason"]}, ensure_ascii=False))
                return 2
        except (OSError, ValueError):
            pass

    chat_hash = _sha256(owner_id)
    text = (
        f"{CANARY_TOKEN}\n"
        f"authorization_id={AUTH_ID}\n"
        f"mode=EXPEDITED_BOUNDED_LIVE_ROLLOUT\n"
        f"builder={AGENT}\n"
        f"verdict_label=BUILDER_VERIFIED (not SIG-IV)\n"
        f"owner-only canary · no broadcast · one message"
    )
    payload_hash = _sha256(text)
    message_key = _sha256(f"canary-n1|{AUTH_ID}|{chat_hash}|{payload_hash}")[:40]

    from live_state_guard import allow_live_write  # noqa: WPS433
    import rate_limit_queue as rlq  # noqa: WPS433
    from sender_bridge import SenderBridge  # noqa: WPS433
    from tg_api import TgClient  # noqa: WPS433

    client = TgClient()
    if not client.wired():
        rec = write_blocked(
            "tg_client_not_wired",
            chat_id_sha12=_sha12(owner_id),
            env_load=env_load,
            heartbeat=hb,
            token_source=getattr(client, "_token_source", None),
        )
        print(json.dumps({"result": "BLOCKED", "reason": rec["block_reason"]}, ensure_ascii=False))
        return 2
    if client.owner_chat_id is None or int(client.owner_chat_id) != owner_id:
        rec = write_blocked(
            "client_owner_mismatch",
            chat_id_sha12=_sha12(owner_id),
            client_owner_sha12=_sha12(client.owner_chat_id) if client.owner_chat_id is not None else None,
            env_load=env_load,
            heartbeat=hb,
        )
        print(json.dumps({"result": "BLOCKED", "reason": rec["block_reason"]}, ensure_ascii=False))
        return 2

    # Hard bound: send_fn only accepts our owner chat_hash and only sends to owner_id
    send_trace = {"attempts": 0, "message_id": None, "error": None}

    def send_fn(item: dict) -> dict:
        send_trace["attempts"] += 1
        if str(item.get("chat_hash") or "") != chat_hash:
            send_trace["error"] = "chat_hash_mismatch"
            return {"ok": False}
        if send_trace["attempts"] > 1:
            send_trace["error"] = "second_attempt_refused"
            return {"ok": False}
        # stream label for receipts; chat_id forced to owner only
        mid = client.send(text, chat_id=owner_id, stream="owner-canary-n1")
        if mid is None:
            send_trace["error"] = "send_returned_none"
            return {"ok": False}
        send_trace["message_id"] = int(mid)
        return {"ok": True, "message_id": int(mid)}

    with allow_live_write("OCTOPUS-OWNER-CANARY-20260822-N1 live owner canary via SenderBridge"):
        q = rlq.RateLimitQueue(QUEUE_PATH)
        client.attach_defer_queue(q)
        enq = q.enqueue(
            message_key=message_key,
            chat_hash=chat_hash,
            payload_hash=payload_hash,
            priority=100,
        )
        if enq.get("state") == "REJECTED_QUEUE_FULL":
            rec = write_blocked("queue_full", heartbeat=hb, enqueue=enq)
            print(json.dumps({"result": "BLOCKED", "reason": rec["block_reason"]}, ensure_ascii=False))
            return 2
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
    mid = int(row["message_id"]) if confirmed else None

    rec = {
        "schema": "octopus-owner-canary-n1/1",
        "authorization_id": AUTH_ID,
        "mode": "EXPEDITED_BOUNDED_LIVE_ROLLOUT",
        "builder": AGENT,
        "verdict_label": "BUILDER_VERIFIED",
        "independent_verification": False,
        "canary_token": CANARY_TOKEN,
        "sent": bool(confirmed),
        "live_send": bool(confirmed),
        "message_id": mid,
        "chat_target_class": "owner-only",
        "chat_id_hash_ok": True,
        "chat_id_sha12": _sha12(owner_id),
        "chat_hash_sha12": chat_hash[:12],
        "outbox_path": str(QUEUE_PATH),
        "outbox_message_key": message_key,
        "outbox_state": (row or {}).get("state") if isinstance(row, dict) else None,
        "bridge_counts": out,
        "readback_confirm": {
            "queue_state": (row or {}).get("state") if isinstance(row, dict) else None,
            "message_id_match": bool(confirmed and mid == send_trace.get("message_id")),
            "delivery_attempts": (row or {}).get("delivery_attempts") if isinstance(row, dict) else None,
            "send_attempts": send_trace["attempts"],
            "send_error": send_trace.get("error"),
        },
        "timestamp_local_aest": _now_local(),
        "blocked": not confirmed,
        "block_reason": None if confirmed else (send_trace.get("error") or "send_not_confirmed"),
        "env_load": env_load,
        "heartbeat": hb,
        "token_source": getattr(client, "_token_source", None),
        "path": "RateLimitQueue+SenderBridge+TgClient.send(owner_only)",
        "paid_calls": 0,
        "webhook_mutated": False,
        "broadcast": False,
        "groups": False,
        "second_canary": False,
    }
    with allow_live_write("canary-n1-evidence-write"):
        _atomic_write(OUT_JSON, rec)

    print(json.dumps({
        "result": "SENT" if confirmed else "FAILED",
        "message_id": mid,
        "evidence": str(OUT_JSON),
        "bridge": out,
        "block_reason": rec.get("block_reason"),
        "chat_sha12": rec["chat_id_sha12"],
    }, ensure_ascii=False))
    return 0 if confirmed else 1


if __name__ == "__main__":
    raise SystemExit(main())
