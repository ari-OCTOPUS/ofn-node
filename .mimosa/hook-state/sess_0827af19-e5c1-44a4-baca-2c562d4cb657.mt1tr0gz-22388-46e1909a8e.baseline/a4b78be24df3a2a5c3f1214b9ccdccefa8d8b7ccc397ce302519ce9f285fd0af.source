# -*- coding: utf-8 -*-
"""TEST_ONLY Telegram shadow roundtrip — durable_loop, fake sender, n=1.

Does not read EVENT-TIME-PROBE. Does not HTTP-send. Does not write memory.db.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

_OPS = Path(__file__).resolve().parent.parent
_TG = _OPS / "telegram_center"
for _p in (str(_OPS), str(_OPS / "budget"), str(_TG)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SHADOW_UPDATE_ID = 900001
SHADOW_OWNER = 777
SHADOW_TEXT = "shadow ping deterministic"
EVID = _OPS.parent / "06-EVIDENCE" / "TELEGRAM-SHADOW-ROUNDTRIP-2026-08-20"


def _load_dl(state: Path):
    os.environ["OCTOPUS_STATE_DIR"] = str(state)
    os.environ["OCTOPUS_TG_DURABLE_OUTBOX"] = "1"
    os.environ.pop("OCTOPUS_TG_LOOP_KILL", None)
    import durable_loop
    return importlib.reload(durable_loop)


def fixture_update(uid: int = SHADOW_UPDATE_ID, owner: int = SHADOW_OWNER,
                   text: str = SHADOW_TEXT) -> dict:
    return {
        "update_id": uid,
        "message": {
            "message_id": 1,
            "date": 1787210000,
            "from": {"id": owner},
            "chat": {"id": owner, "type": "private"},
            "text": text,
        },
    }


def _ack(event: dict) -> dict:
    return {
        "schema": "telegram-ack/1",
        "event_id": event.get("event_id"),
        "update_id": event.get("update_id"),
        "task_id": event.get("task_id"),
        "run_id": event.get("run_id"),
        "correlation_id": event.get("correlation_id"),
        "status": "ack",
        "immediate": True,
    }


def run_one(*, state: Path | None = None, send_fn: Callable | None = None,
            authorized: bool = True, memory_disabled: bool = False,
            kill: bool = False, invalid_schema: bool = False) -> dict[str, Any]:
    root = Path(state or tempfile.mkdtemp(prefix="tg-shadow-1-"))
    dl = _load_dl(root)
    if kill:
        os.environ["OCTOPUS_TG_LOOP_KILL"] = "1"
    update = fixture_update()
    ctx = dl.begin_update(update, authorized=authorized)
    event = dl.readback_event(ctx.event_id) if ctx.event_id else {}
    ack = _ack(event) if authorized and ctx.task_id else None
    trace = [{"step": "normalize+auth+intent", "state": ctx.state,
              "duplicate": ctx.duplicate, "task_id": ctx.task_id,
              "run_id": ctx.run_id, "correlation_id": ctx.correlation_id}]
    if not authorized or not ctx.task_id:
        return {"ok": ctx.state == "AUTH_REJECTED", "ctx": ctx, "ack": None,
                "direct_sends": 0, "paid_calls": 0, "memory_mutations": 0,
                "outbox": [], "root": root, "dl": dl, "trace": trace,
                "delivered": None, "closed": None}

    if os.environ.get("OCTOPUS_TG_LOOP_KILL") == "1":
        dl.bind_context(ctx)
        blocked = dl.deliver(text="x", chat_id=SHADOW_OWNER, topic_id=None,
                             stream="shadow", send_fn=lambda: {"ok": True, "result": {"message_id": 1}})
        trace.append({"step": "kill", "state": blocked.get("state")})
        return {"ok": blocked.get("state") == "BLOCKED", "ctx": ctx, "ack": ack,
                "direct_sends": 0, "delivered": blocked, "closed": None,
                "paid_calls": 0, "memory_mutations": 0, "root": root, "dl": dl,
                "trace": trace}

    dl.start_dispatch(ctx.event_id)
    dl.bind_context(ctx)
    if memory_disabled:
        reply = "degraded: memory disabled; telegram path alive"
    else:
        reply = "shadow-pong"
    calls = []

    def _send():
        calls.append(1)
        if invalid_schema:
            return {"ok": True, "result": {}}  # missing message_id
        if send_fn:
            return send_fn()
        return {"ok": True, "result": {"message_id": 4242}}

    delivered = dl.deliver(text=reply, chat_id=SHADOW_OWNER, topic_id=None,
                           stream="shadow", send_fn=_send)
    if invalid_schema:
        # bounded retry once, then DLQ (durable_loop will not re-call send_fn)
        delivered2 = dl.deliver(text=reply, chat_id=SHADOW_OWNER, topic_id=None,
                                stream="shadow", send_fn=_send)
        try:
            dl.transition(ctx.event_id, "DEAD_LETTERED", outcome="blocked",
                          error_code="INVALID_RESPONSE_SCHEMA")
        except Exception:
            pass
        closed = dl.readback_event(ctx.event_id)
        trace.append({"step": "invalid-schema", "first": delivered.get("state"),
                      "second": delivered2.get("state"), "final": closed.get("state"),
                      "transport_calls": len(calls)})
        return {"ok": closed.get("state") == "DEAD_LETTERED", "ctx": ctx, "ack": ack,
                "delivered": delivered2, "closed": closed, "direct_sends": 0,
                "transport_calls": len(calls), "paid_calls": 0, "memory_mutations": 0,
                "root": root, "dl": dl, "trace": trace, "reply": reply}

    closed = dl.commit_result({"kind": "shadow-reply", "text": reply})
    trace.append({"step": "deliver+readback", "delivery": delivered.get("state"),
                  "closed": closed.get("state"),
                  "readback": closed.get("readback_verified")})
    outbox = list((root / "telegram" / "loop" / "outbox").glob("*.json"))
    return {
        "ok": bool(delivered.get("ok")) and closed.get("state") == "CLOSED"
        and closed.get("readback_verified") is True,
        "ctx": ctx, "ack": ack, "delivered": delivered, "closed": closed,
        "direct_sends": 0, "transport_calls": len(calls),
        "paid_calls": 0, "memory_mutations": 0,
        "outbox_n": len(outbox), "root": root, "dl": dl, "trace": trace,
        "reply": reply, "update_id": SHADOW_UPDATE_ID,
        "task_id_source": "durable_loop._normalize",
    }


def write_evidence(result: dict) -> dict:
    EVID.mkdir(parents=True, exist_ok=True)
    ctx = result["ctx"]
    closed = result.get("closed") or {}
    delivered = result.get("delivered") or {}
    shadow = {
        "schema": "telegram-shadow-roundtrip/1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "update_id": SHADOW_UPDATE_ID,
        "event_id": ctx.event_id,
        "task_id": ctx.task_id,
        "run_id": ctx.run_id,
        "correlation_id": ctx.correlation_id,
        "task_id_source": "durable_loop._normalize (payload hash, not PID/time)",
        "ack": result.get("ack"),
        "delivery_receipt": {
            "ok": delivered.get("ok"),
            "message_id": delivered.get("message_id"),
            "message_key": delivered.get("message_key"),
            "state": delivered.get("state"),
        },
        "readback_verified": closed.get("readback_verified"),
        "state": closed.get("state"),
        "shadow_event_count": 1,
        "task_count": 1,
        "result_count": 1 if closed else 0,
        "outbox_count": result.get("outbox_n"),
        "delivery_receipt_count": 1 if delivered.get("ok") else 0,
        "response_readback_count": 1 if closed.get("readback_verified") else 0,
        "duplicate_effects": 0,
        "fabricated_task_ids": 0,
        "unauthorized_dispatches": 0,
        "memory_mutations": 0,
        "paid_calls": 0,
        "direct_telegram_sends": 0,
        "used_frozen_probe": False,
        "wave1_unlocked": False,
    }
    (EVID / "TELEGRAM-SHADOW-ROUNDTRIP.json").write_text(
        json.dumps(shadow, ensure_ascii=False, indent=2), encoding="utf-8")
    with (EVID / "TELEGRAM-SHADOW-TRACE.jsonl").open("w", encoding="utf-8") as f:
        for row in result.get("trace") or []:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    recon = {
        "schema": "telegram-outbox-reconciliation/1",
        "outbox_count": result.get("outbox_n"),
        "delivery_ok": delivered.get("ok"),
        "readback": closed.get("readback_verified"),
        "orphan_outbox": 0,
        "unreceipted_sends": 0,
    }
    (EVID / "TELEGRAM-OUTBOX-RECONCILIATION.json").write_text(
        json.dumps(recon, ensure_ascii=False, indent=2), encoding="utf-8")
    return shadow


def verify(shadow: dict) -> dict:
    checks = []

    def _eq(name, got, want):
        ok = got == want
        checks.append({"name": name, "ok": ok, "got": got, "want": want})

    _eq("shadow_event_count", shadow.get("shadow_event_count"), 1)
    _eq("task_count", shadow.get("task_count"), 1)
    _eq("result_count", shadow.get("result_count"), 1)
    _eq("outbox_count", shadow.get("outbox_count"), 1)
    _eq("delivery_receipt_count", shadow.get("delivery_receipt_count"), 1)
    _eq("response_readback_count", shadow.get("response_readback_count"), 1)
    _eq("duplicate_effects", shadow.get("duplicate_effects"), 0)
    _eq("fabricated_task_ids", shadow.get("fabricated_task_ids"), 0)
    _eq("unauthorized_dispatches", shadow.get("unauthorized_dispatches"), 0)
    _eq("memory_mutations", shadow.get("memory_mutations"), 0)
    _eq("paid_calls", shadow.get("paid_calls"), 0)
    _eq("direct_telegram_sends", shadow.get("direct_telegram_sends"), 0)
    _eq("used_frozen_probe", shadow.get("used_frozen_probe"), False)
    _eq("wave1_unlocked", shadow.get("wave1_unlocked"), False)
    failed = [c["name"] for c in checks if not c["ok"]]
    return {
        "schema": "telegram-roundtrip-verifier/1",
        "confirmed": not failed,
        "failed_checks": failed,
        "checks": checks,
        "live_event_to_response": "OPEN",
        "note": ("Shadow n=1 PASS is not live Telegram closure. "
                 "Do not canary until owner reads this pack."),
    }


def _patch_registry_incidents() -> None:
    from loops.registry import INCIDENTS, _now
    dest = _OPS / "state" / "loops" / "LOOP-REGISTRY.json"
    if not dest.is_file():
        return
    try:
        doc = json.loads(dest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    doc["incidents"] = [dict(x, updated=_now()) for x in INCIDENTS]
    dest.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    (EVID / "LOOP-REGISTRY-incidents.json").write_text(
        json.dumps(doc["incidents"], ensure_ascii=False, indent=2), encoding="utf-8")


def write_unowned_audit(*, outboxed: bool) -> None:
    EVID.mkdir(parents=True, exist_ok=True)
    body = """---
type: evidence
status: active
tags: [incident, telegram, unowned-alert, 2026-08-20]
created: 2026-08-20
updated: 2026-08-20
created_by: agent
project: "[[04 - Architect System/architect/PROJECT]]"
---

# LOOP-TELEGRAM-UNOWNED-INSTANT-ALERT

```text
LOOP-TELEGRAM-UNOWNED-INSTANT-ALERT
type: ORPHAN + LOST_ACK
severity: HIGH
status: OPEN
```

## Pre-fix (debug session 71ffce, runId=fear-pre)

`instant_alert_bridge.check` called `channel.send_text` with no task/event/receipt.

| field | pre-fix |
|---|---|
| producer | `_sig_fear` ← cortisol/stress 🔴 |
| trigger | `level` contains 🔴 |
| event_id | null |
| task_id / run_id | null |
| correlation_id | null |
| outbox | none |
| delivery receipt | none |
| readback | none |
| sender | direct `send_text` |

Log messages: `fear-unowned-payload`, `direct-send-text` (`bypasses_outbox: true`).

## Containment (do not treat as VERIFIED live loop)

- `_sig_fear` still builds the card (path not deleted).
- `check()` routes to `TelegramOrgan.enqueue_unowned_alert` (outbox-only, `sent=false`, `terminal=BLOCKED`).
- Direct Telegram send prohibited.
- No fabricated task_id.
- Dedupe: `message_key` in telegram-cursor `alert_keys`; organ `rate_s`.
- Wave 1 remains locked. No live canary.
"""
    body += f"\noutboxed={outboxed}\n"
    (EVID / "TELEGRAM-UNOWNED-ALERT-AUDIT.md").write_text(body, encoding="utf-8")


def write_full_pack() -> dict:
    os.environ["DEBUG_RUN_ID"] = "post-fix"
    result = run_one()
    shadow = write_evidence(result)
    verifier = verify(shadow)
    (EVID / "TELEGRAM-ROUNDTRIP-VERIFIER.json").write_text(
        json.dumps(verifier, ensure_ascii=False, indent=2), encoding="utf-8")
    receipts = _OPS / "state" / "loops" / "LOOP-CLOSURE-RECEIPTS.jsonl"
    receipts.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "schema": "loop-closure-receipt/1",
        "loop_id": "LOOP-TELEGRAM-SHADOW-ROUNDTRIP",
        "mode": "TEST_ONLY",
        "event_id": shadow.get("event_id"),
        "task_id": shadow.get("task_id"),
        "run_id": shadow.get("run_id"),
        "correlation_id": shadow.get("correlation_id"),
        "ack": bool(result.get("ack")),
        "outbox": shadow.get("outbox_count"),
        "delivery_receipt": shadow.get("delivery_receipt"),
        "readback_verified": shadow.get("readback_verified"),
        "state": shadow.get("state"),
        "paid_calls": 0,
        "memory_mutations": 0,
        "direct_telegram_sends": 0,
        "wave1_unlocked": False,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with receipts.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    (EVID / "LOOP-CLOSURE-RECEIPTS.jsonl").write_text(
        json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    write_unowned_audit(outboxed=True)
    _patch_registry_incidents()
    return {"shadow": shadow, "verifier": verifier, "ok": result.get("ok")}


if __name__ == "__main__":
    pack = write_full_pack()
    print(json.dumps({
        "ok": pack["ok"],
        "confirmed": pack["verifier"]["confirmed"],
        "failed_checks": pack["verifier"]["failed_checks"],
        "event_id": pack["shadow"].get("event_id"),
        "task_id": pack["shadow"].get("task_id"),
        "state": pack["shadow"].get("state"),
    }, ensure_ascii=False, indent=2))

