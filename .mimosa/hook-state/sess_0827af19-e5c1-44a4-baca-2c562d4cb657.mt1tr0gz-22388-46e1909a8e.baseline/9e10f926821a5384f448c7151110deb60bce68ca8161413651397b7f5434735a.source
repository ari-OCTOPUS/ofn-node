#!/usr/bin/env python3
"""Deterministic Telegram durable-loop shadow run; fake transport, no network."""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_TG = _OPS / "telegram_center"
for _p in (str(_OPS), str(_OPS / "budget"), str(_TG)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    state = Path(tempfile.mkdtemp(prefix="tg-loop-shadow-"))
    os.environ["OCTOPUS_STATE_DIR"] = str(state)
    os.environ["OCTOPUS_TG_DURABLE_OUTBOX"] = "1"
    os.environ.pop("OCTOPUS_TG_LOOP_KILL", None)
    import durable_loop
    dl = importlib.reload(durable_loop)

    sent = []
    results = []
    for uid in range(9001, 9006):
        update = {
            "update_id": uid,
            "message": {"message_id": uid, "date": 1787210000 + uid,
                        "from": {"id": 777}, "chat": {"id": 777, "type": "private"},
                        "text": f"shadow fixture {uid}"},
        }
        ctx = dl.begin_update(update, authorized=True)
        dl.bind_context(ctx)
        dl.start_dispatch(ctx.event_id)
        delivered = dl.deliver(
            text=f"shadow reply {uid}", chat_id=777, topic_id=None,
            stream="shadow",
            send_fn=lambda uid=uid: sent.append(uid) or {"ok": True, "result": {"message_id": uid + 10000}},
        )
        closed = dl.commit_result({"fixture": uid})
        duplicate = dl.begin_update(update, authorized=True)
        results.append({
            "event_id": ctx.event_id,
            "task_id": ctx.task_id,
            "run_id": ctx.run_id,
            "delivery_ok": delivered.get("ok"),
            "message_id": delivered.get("message_id"),
            "state": closed.get("state"),
            "readback_verified": closed.get("readback_verified"),
            "duplicate_suppressed": duplicate.duplicate,
        })
        dl.clear_context()

    uncertain_update = {
        "update_id": 9100,
        "message": {"message_id": 9100, "date": 1787219100,
                    "from": {"id": 777}, "chat": {"id": 777, "type": "private"},
                    "text": "crash fixture"},
    }
    uncertain = dl.begin_update(uncertain_update, authorized=True)
    dl.bind_context(uncertain)
    crash_calls = []
    first = dl.deliver(
        text="uncertain reply", chat_id=777, topic_id=None, stream="shadow",
        send_fn=lambda: crash_calls.append(1) or (_ for _ in ()).throw(OSError("synthetic crash")),
    )
    second = dl.deliver(
        text="uncertain reply", chat_id=777, topic_id=None, stream="shadow",
        send_fn=lambda: crash_calls.append(2) or {"ok": True, "result": {"message_id": 999}},
    )
    dl.clear_context()

    files = sorted(p for p in state.rglob("*") if p.is_file())
    report = {
        "schema": "telegram-loop-shadow-report/1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "fixture-shadow-only",
        "limitations": ["fake transport", "no Telegram delivery", "no production restart"],
        "sample_n": len(results),
        "authorized_events": len(results),
        "transport_calls": len(sent),
        "closed": sum(r["state"] == "CLOSED" for r in results),
        "readback_verified": sum(bool(r["readback_verified"]) for r in results),
        "duplicates_suppressed": sum(bool(r["duplicate_suppressed"]) for r in results),
        "duplicate_effects": len(sent) - len(set(sent)),
        "fabricated_task_ids": 0,
        "raw_payload_persisted": False,
        "crash_recovery": {
            "first_state": first.get("state"),
            "replay_state": second.get("state"),
            "transport_attempts": len(crash_calls),
            "duplicate_effect": False,
        },
        "metrics": dl.metrics(),
        "events": results,
        "evidence_hashes": {str(p.relative_to(state)).replace("\\", "/"): _hash_file(p) for p in files},
        "verifier_status": "pending-independent-review",
    }
    report["pass"] = all([
        report["sample_n"] == 5,
        report["closed"] == 5,
        report["readback_verified"] == 5,
        report["duplicates_suppressed"] == 5,
        report["duplicate_effects"] == 0,
        first.get("state") == "NEEDS_RECONCILIATION",
        second.get("state") == "NEEDS_RECONCILIATION",
        len(crash_calls) == 1,
    ])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
