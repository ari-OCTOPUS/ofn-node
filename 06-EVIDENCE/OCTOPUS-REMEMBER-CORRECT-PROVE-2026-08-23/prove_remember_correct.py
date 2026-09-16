# -*- coding: utf-8 -*-
"""OCTOPUS remember/correct prove — local invoke + isolated durable ACK.
No Telegram sendMessage. No process restart. No deletes. No secrets in artifacts.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"F:\backup").resolve()
EVID = ROOT / "06-EVIDENCE" / "OCTOPUS-REMEMBER-CORRECT-PROVE-2026-08-23"
ISOLATED = EVID / "isolated-loop"
MEM = ROOT / "research" / "full_loop" / "state" / "memory.jsonl"
LOCK = ROOT / "_ops" / "state" / "locks" / "octopus-writer.lock"
SYD = timezone(timedelta(hours=10))

for p in (str(ROOT / "_ops"), str(ROOT / "_ops" / "owner_console"),
          str(ROOT / "_ops" / "telegram_center")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["OCTOPUS_TG_DURABLE_OUTBOX"] = "1"
os.environ.pop("OCTOPUS_TG_LOOP_KILL", None)
os.environ["OCTOPUS_STATE_DIR"] = str(ISOLATED)


def _now_local() -> str:
    return datetime.now(SYD).isoformat(timespec="seconds")


def _sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip())


def _boom(*_a, **_k):
    raise AssertionError("model must not be called")


def main() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    ISOLATED.mkdir(parents=True, exist_ok=True)
    (ISOLATED / "telegram" / "loop" / "outbox").mkdir(parents=True, exist_ok=True)
    (ISOLATED / "telegram" / "loop" / "events").mkdir(parents=True, exist_ok=True)

    before = {
        "memory_lines": _line_count(MEM),
        "memory_sha256": _sha256_file(MEM),
        "memory_bytes": MEM.stat().st_size if MEM.exists() else 0,
        "center_pid_35916_alive": False,
        "lock": None,
        "captured_at_local": _now_local(),
    }
    try:
        import psutil  # type: ignore
        before["center_pid_35916_alive"] = psutil.pid_exists(35916)
    except Exception:
        # fallback via os — Windows
        before["center_pid_35916_alive"] = (
            os.system('tasklist /FI "PID eq 35916" 2>NUL | find "35916" >NUL') == 0
        )
    if LOCK.exists():
        try:
            ld = json.loads(LOCK.read_text(encoding="utf-8"))
            before["lock"] = {
                "agent_id": ld.get("agent_id"),
                "expires_at": ld.get("expires_at"),
                "expired": float(time.time()) > float(ld.get("expires_at") or 0),
                "renewed_at_local": ld.get("renewed_at_local"),
            }
        except Exception as exc:
            before["lock"] = {"error": type(exc).__name__}

    from owner_console import local_commands
    import durable_loop as dl
    importlib.reload(dl)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    remember_text = f"prove-canary-{stamp}: pearl-ack"
    rem = local_commands.handle_local(
        f"/remember {remember_text}", model_fn=_boom, memory_store=MEM
    )
    rem_dict = rem.as_dict()
    # strip any long payload echoes for evidence
    rem_safe = {
        "handled": rem.handled,
        "kind": rem.kind,
        "receipt": rem.receipt,
        "memory_id": rem.memory_id,
        "text_has_memory_id": bool(rem.memory_id and rem.memory_id in (rem.text or "")),
        "text_len": len(rem.text or ""),
        "ack_in_reply_text": bool(rem.memory_id and rem.memory_id in (rem.text or "")),
    }

    inv = local_commands.handle_local(
        "/correct not-a-real-id prove-canary-invalid: shell",
        model_fn=_boom,
        memory_store=MEM,
    )
    inv_safe = {
        "handled": inv.handled,
        "kind": inv.kind,
        "receipt": inv.receipt,
        "memory_id": inv.memory_id,
        "text_len": len(inv.text or ""),
        "mentions_unknown": "unknown turn_id" in (inv.text or ""),
    }

    after_mem_lines = _line_count(MEM)
    after_sha = _sha256_file(MEM)
    mem_grew = after_mem_lines == before["memory_lines"] + 1  # remember only; invalid must not grow extra
    # correct-invalid must NOT append
    invalid_no_write = after_mem_lines == before["memory_lines"] + (1 if rem.memory_id else 0)

    # Confirm last line is remember canary (hash id only in evidence)
    last_id = None
    last_prov = None
    if MEM.exists():
        rows = [json.loads(x) for x in MEM.read_text(encoding="utf-8").splitlines() if x.strip()]
        if rows:
            last_id = rows[-1].get("id")
            last_prov = rows[-1].get("provenance")

    # Isolated durable ACK (fake transport) — same path as tests / tg_api
    update = {
        "update_id": 900000000 + int(time.time()) % 100000,
        "message": {
            "message_id": 1,
            "date": int(time.time()),
            "chat": {"id": 777, "type": "private"},
            "from": {"id": 777, "is_bot": False},
            "text": f"/remember {remember_text}",
        },
    }
    ctx = dl.begin_update(update, authorized=True)
    dl.bind_context(ctx)
    dl.start_dispatch(ctx.event_id)
    seen = []

    def fake_send():
        rows = list((ISOLATED / "telegram" / "loop" / "outbox").glob("*.json"))
        assert rows, "outbox row missing before send"
        queued = json.loads(rows[-1].read_text(encoding="utf-8"))
        assert queued["state"] == "SENDING"
        seen.append(queued.get("message_key"))
        return {"ok": True, "result": {"message_id": 4242}}

    ack_out = dl.ack_local_result(
        rem, chat_id=777, topic_id=None, stream="owner-reply", send_fn=fake_send
    )
    snap = dl.readback_event(ctx.event_id)
    outbox_files = sorted((ISOLATED / "telegram" / "loop" / "outbox").glob("*.json"))
    confirmed = json.loads(outbox_files[-1].read_text(encoding="utf-8")) if outbox_files else {}
    # redact chat content — only structural fields
    confirmed_safe = {
        k: confirmed.get(k)
        for k in (
            "schema", "state", "delivery_truth", "event_id", "message_key",
            "message_id", "stream", "attempts", "confirmed_at", "created_at",
        )
        if k in confirmed
    }
    event_safe = {
        k: snap.get(k)
        for k in (
            "schema", "state", "readback_verified", "event_id", "reply_receipt_id",
            "closed_at", "delivery_message_id",
        )
        if snap and k in snap
    }

    # Live outbox sample (read-only) — latest CONFIRMED existence
    live_outbox = ROOT / "_ops" / "state" / "telegram" / "loop" / "outbox"
    live_events = ROOT / "_ops" / "state" / "telegram" / "loop" / "events"
    live_ob = sorted(live_outbox.glob("*.json"), key=lambda p: p.stat().st_mtime)
    live_ev = sorted(live_events.glob("*.json"), key=lambda p: p.stat().st_mtime)
    live_latest = {}
    if live_ob:
        raw = json.loads(live_ob[-1].read_text(encoding="utf-8"))
        live_latest = {
            "path": str(live_ob[-1].relative_to(ROOT)),
            "state": raw.get("state"),
            "delivery_truth": raw.get("delivery_truth"),
            "mtime_epoch": live_ob[-1].stat().st_mtime,
            "note": "pre-existing live receipt; not from this prove (no Telegram owner msg)",
        }

    blockers = []
    # Full live center outbox for THIS remember requires owner Telegram message
    blockers.append({
        "id": "A18-LIVE-TELEGRAM-OWNER-ACK",
        "severity": "partial",
        "detail": (
            "Local handle_local + isolated durable ACK proven. "
            "End-to-end LIVE outbox/events row from center PID 35916 for this "
            "/remember still needs an owner-only Telegram message "
            "(TELEGRAM_OWNER_CHAT_ID unset in shell; live sendMessage forbidden by lease)."
        ),
    })

    status = "PASS"
    checks = {
        "remember_handled": bool(rem.handled and rem.receipt == "local-remember" and rem.memory_id),
        "remember_ack_in_text": rem_safe["ack_in_reply_text"],
        "remember_persisted": last_id == rem.memory_id and last_prov == "owner_direct",
        "correct_invalid_receipt": inv.receipt == "local-correct-invalid",
        "correct_invalid_no_memory_id": inv.memory_id is None,
        "correct_invalid_no_extra_write": invalid_no_write,
        "durable_ack_confirmed": (
            ack_out.get("deliver", {}).get("state") == "CONFIRMED"
            and confirmed.get("state") == "CONFIRMED"
            and confirmed.get("delivery_truth") == "DELIVERY_CONFIRMED"
        ),
        "durable_event_closed": bool(snap and snap.get("state") == "CLOSED" and snap.get("readback_verified")),
        "center_alive": bool(before["center_pid_35916_alive"]),
        "lock_not_expired": bool(before.get("lock") and not before["lock"].get("expired")),
    }
    if not all(checks.values()):
        status = "PARTIAL" if any(checks.values()) else "BLOCKED"
    # With intentional A18 live-telegram blocker, overall is PARTIAL even if local PASS
    if status == "PASS":
        status = "PARTIAL"  # pending live Telegram owner ACK for full A18 unlock

    result = {
        "schema": "octopus-remember-correct-prove/1",
        "status": status,
        "captured_at_local": _now_local(),
        "branch": "rescue/octopus-live-tree-20260821",
        "head": "d07c9ad",
        "center_pid": 35916,
        "method": {
            "remember_correct": "owner_console.local_commands.handle_local → LIVE memory.jsonl",
            "durable_ack": "durable_loop.ack_local_result + fake_send under isolated OCTOPUS_STATE_DIR",
            "telegram_live_send": False,
            "process_restart": False,
            "deletes": False,
        },
        "before": before,
        "after": {
            "memory_lines": after_mem_lines,
            "memory_sha256": after_sha,
            "memory_bytes": MEM.stat().st_size if MEM.exists() else 0,
            "last_memory_id": last_id,
            "last_provenance": last_prov,
        },
        "receipts": {
            "local_remember": rem_safe,
            "local_correct_invalid": inv_safe,
            "isolated_outbox_confirmed": confirmed_safe,
            "isolated_event_closed": event_safe,
            "live_outbox_latest_readonly": live_latest,
            "live_outbox_count": len(live_ob),
            "live_events_count": len(live_ev),
        },
        "checks": checks,
        "paths": {
            "memory_store": str(MEM),
            "evidence": str(EVID),
            "isolated_loop": str(ISOLATED / "telegram" / "loop"),
            "isolated_outbox": str(ISOLATED / "telegram" / "loop" / "outbox"),
            "isolated_events": str(ISOLATED / "telegram" / "loop" / "events"),
            "live_outbox": str(live_outbox),
            "live_events": str(live_events),
        },
        "blockers": blockers,
        "next_action": {
            "id": "A18-OWNER-TG-REMEMBER-CANARY",
            "reversible": True,
            "step": (
                "Owner sends one /remember and one /correct <bad-id> ... in owner chat only; "
                "then verify new LIVE outbox CONFIRMED + events CLOSED referencing local-remember / local-correct-invalid; "
                "then update CURRENT-TRUTH A18 if both prove."
            ),
        },
    }

    (EVID / "RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (EVID / "receipts-summary.json").write_text(
        json.dumps(result["receipts"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": status, "checks": checks, "memory_id": rem.memory_id,
                      "inv_receipt": inv.receipt, "confirmed": confirmed.get("state"),
                      "event": snap.get("state") if snap else None}, ensure_ascii=False))
    return 0 if checks["remember_handled"] and checks["correct_invalid_receipt"] and checks["durable_ack_confirmed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
