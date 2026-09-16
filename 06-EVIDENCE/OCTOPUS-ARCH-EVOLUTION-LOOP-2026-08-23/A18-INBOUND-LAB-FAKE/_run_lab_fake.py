# -*- coding: utf-8 -*-
"""A18 inbound Full Loop — LAB FAKE (no live Telegram)."""
from __future__ import annotations

import importlib
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"F:\backup").resolve()
EVID = ROOT / "06-EVIDENCE" / "OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23" / "A18-INBOUND-LAB-FAKE"
ISOLATED = EVID / "isolated-loop"
MEM = EVID / "lab-memory.jsonl"
SYD = timezone(timedelta(hours=10))

for p in (str(ROOT / "_ops"), str(ROOT / "_ops" / "owner_console"), str(ROOT / "_ops" / "telegram_center")):
    if p not in sys.path:
        sys.path.insert(0, p)


def now_local() -> str:
    return datetime.now(SYD).isoformat(timespec="seconds")


def boom(*_a, **_k):
    raise AssertionError("model must not be called in lab fake")


def _sending_row() -> dict:
    found = []
    for pth in (ISOLATED / "telegram" / "loop" / "outbox").glob("*.json"):
        row = json.loads(pth.read_text(encoding="utf-8"))
        if row.get("state") == "SENDING":
            found.append(row)
    assert len(found) == 1, found
    return found[0]


def scrub(d: dict, keys: tuple) -> dict:
    return {k: d.get(k) for k in keys if k in d}


def main() -> int:
    os.environ["OCTOPUS_TG_DURABLE_OUTBOX"] = "1"
    os.environ.pop("OCTOPUS_TG_LOOP_KILL", None)
    os.environ["OCTOPUS_STATE_DIR"] = str(ISOLATED)

    EVID.mkdir(parents=True, exist_ok=True)
    for sub in ("outbox", "events"):
        d = ISOLATED / "telegram" / "loop" / sub
        d.mkdir(parents=True, exist_ok=True)
        for f in d.glob("*"):
            if f.is_file():
                f.unlink()
    MEM.write_text("", encoding="utf-8")

    from owner_console import local_commands
    import durable_loop as dl
    importlib.reload(dl)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    remember_text = f"a18-lab-fake-{stamp}: inbound-pearl"

    rem = local_commands.handle_local(f"/remember {remember_text}", model_fn=boom, memory_store=MEM)
    inv = local_commands.handle_local(
        "/correct not-a-real-lab-id a18-lab-fake-invalid: shell",
        model_fn=boom,
        memory_store=MEM,
    )

    rem_ok = bool(rem.handled and rem.receipt == "local-remember" and rem.memory_id)
    inv_ok = bool(inv.handled and inv.receipt == "local-correct-invalid" and inv.memory_id is None)
    mem_lines = [ln for ln in MEM.read_text(encoding="utf-8").splitlines() if ln.strip()]
    mem_grew_once = len(mem_lines) == 1

    def run_durable(result_obj, update_id: int, message_id: int, fake_mid: int):
        update = {
            "update_id": update_id,
            "message": {
                "message_id": message_id,
                "date": int(time.time()),
                "chat": {"id": 778, "type": "private"},
                "from": {"id": 778, "is_bot": False},
                "text": "lab-fake",
            },
        }
        ctx = dl.begin_update(update, authorized=True)
        dl.bind_context(ctx)
        dl.start_dispatch(ctx.event_id)

        def fake_send():
            _sending_row()
            return {"ok": True, "result": {"message_id": fake_mid}}

        ack = dl.ack_local_result(
            result_obj, chat_id=778, topic_id=None, stream="owner-reply", send_fn=fake_send
        )
        snap = dl.readback_event(ctx.event_id)
        ok = (
            ack.get("deliver", {}).get("state") == "CONFIRMED"
            and bool(snap and snap.get("state") == "CLOSED" and snap.get("readback_verified"))
        )
        return ok, ack, snap, ctx.event_id

    uid = 910000000 + int(time.time()) % 100000
    durable_ok, ack, snap, eid1 = run_durable(rem, uid, 11, 88018)
    durable2_ok, ack2, snap2, eid2 = run_durable(inv, uid + 1, 12, 88019)

    # outbox confirmed for remember (any CONFIRMED with message_id 88018)
    confirmed = {}
    for pth in (ISOLATED / "telegram" / "loop" / "outbox").glob("*.json"):
        row = json.loads(pth.read_text(encoding="utf-8"))
        if row.get("message_id") == 88018:
            confirmed = row
            break

    lab_pass = all([rem_ok, inv_ok, mem_grew_once, durable_ok, durable2_ok])

    result = {
        "schema": "octopus-a18-inbound-lab-fake/1",
        "stamp_local": now_local(),
        "timezone": "Australia/Sydney",
        "status": "PASS" if lab_pass else "FAIL",
        "constraints": {
            "no_live_sendMessage": True,
            "no_unlock": True,
            "no_secrets": True,
            "isolated_state_only": True,
            "live_memory_untouched": True,
        },
        "method": {
            "inbound": "fake update dict (no getUpdates / no Telegram network)",
            "commands": "owner_console.local_commands.handle_local",
            "durable": "durable_loop.begin_update → ack_local_result + fake_send",
            "sot_class": "isolated loop/outbox+events under evidence (lab SoT for this prove)",
        },
        "checks": {
            "remember_local_remember": rem_ok,
            "correct_local_correct_invalid": inv_ok,
            "lab_memory_one_row": mem_grew_once,
            "remember_durable_CONFIRMED_CLOSED": durable_ok,
            "correct_invalid_durable_CONFIRMED_CLOSED": durable2_ok,
        },
        "receipts": {
            "local_remember": {"receipt": rem.receipt, "memory_id": rem.memory_id, "handled": rem.handled},
            "local_correct_invalid": {"receipt": inv.receipt, "memory_id": inv.memory_id, "handled": inv.handled},
            "remember_outbox": scrub(
                confirmed,
                ("schema", "state", "delivery_truth", "event_id", "message_key", "message_id", "stream"),
            ),
            "remember_event": scrub(
                snap or {},
                ("schema", "state", "readback_verified", "event_id", "delivery_message_id"),
            ),
            "correct_event": scrub(
                snap2 or {},
                ("schema", "state", "readback_verified", "event_id", "delivery_message_id"),
            ),
        },
        "paths": {
            "evidence": str(EVID),
            "lab_memory": str(MEM),
            "isolated_outbox": str(ISOLATED / "telegram" / "loop" / "outbox"),
            "isolated_events": str(ISOLATED / "telegram" / "loop" / "events"),
        },
        "remaining_gap": {
            "id": "A18-LIVE-OWNER-INBOUND",
            "status": "OPEN",
            "detail": (
                "Lab fake proves local_commands + durable_loop SoT path to CONFIRMED/CLOSED. "
                "LIVE Full Loop still requires real owner Telegram inbound /remember + /correct "
                "through live center durable loop/outbox (not canary sqlite). See C05 contract."
            ),
        },
        "pytest": {"file": "_ops/tests/test_a18_inbound_lab_fake.py"},
        "compact": {
            "STATUS": "PASS" if lab_pass else "FAIL",
            "LAB": "fake inbound → CONFIRMED/CLOSED",
            "REMAINING": "real owner inbound for LIVE Full Loop",
            "EVIDENCE": str(EVID / "RESULT.json"),
        },
    }
    (EVID / "RESULT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    gaps_path = ROOT / "06-EVIDENCE" / "OCTOPUS-GAP-INVENTORY-2026-08-23" / "IOS-GAPS.json"
    if gaps_path.exists():
        gaps = json.loads(gaps_path.read_text(encoding="utf-8"))
        for g in gaps.get("gaps", []):
            if g.get("id") == "A18-INBOUND-FULL-LOOP":
                g["status"] = "LAB_FAKE_PASS_LIVE_OPEN" if lab_pass else "LAB_FAKE_FAIL"
                g["note"] = ((g.get("note") or "") + " | 2026-08-23 lab fake; LIVE owner inbound still OPEN")[-500:]
                g["evidence"] = list(dict.fromkeys((g.get("evidence") or []) + [str(EVID / "RESULT.json")]))
        gaps_path.write_text(json.dumps(gaps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (gaps_path.parent / "GAPS.json").write_text(gaps_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(json.dumps(result["compact"], ensure_ascii=False))
    return 0 if lab_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
