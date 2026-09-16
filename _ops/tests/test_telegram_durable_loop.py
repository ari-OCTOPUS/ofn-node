#!/usr/bin/env python3
"""Durable Telegram loop contract. All transports are fake; no network or paid calls."""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_TG = _OPS / "telegram_center"
for _p in (str(_OPS), str(_OPS / "budget"), str(_TG)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _fresh():
    root = Path(tempfile.mkdtemp(prefix="tg-durable-loop-"))
    os.environ["OCTOPUS_STATE_DIR"] = str(root)
    os.environ["OCTOPUS_TG_DURABLE_OUTBOX"] = "1"
    os.environ.pop("OCTOPUS_TG_LOOP_KILL", None)
    import durable_loop
    return importlib.reload(durable_loop), root


def _update(uid=41, owner=777, text="owner private text"):
    return {
        "update_id": uid,
        "message": {
            "message_id": 9,
            "date": 1787210000,
            "from": {"id": owner},
            "chat": {"id": owner, "type": "private"},
            "text": text,
        },
    }


def t_a_event_is_normalized_without_raw_payload():
    dl, root = _fresh()
    ctx = dl.begin_update(_update(), authorized=True)
    assert ctx.duplicate is False
    assert ctx.event_id == "tg:41"
    assert ctx.task_id and ctx.run_id and ctx.correlation_id
    snap = json.loads((root / "telegram" / "loop" / "events" / "tg_41.json").read_text("utf-8"))
    blob = json.dumps(snap, ensure_ascii=False)
    assert "owner private text" not in blob
    assert snap["payload_hash"] and snap["state"] == "INTENT_COMMITTED"


def t_b_duplicate_update_creates_no_second_task():
    dl, _ = _fresh()
    first = dl.begin_update(_update(), authorized=True)
    dl.start_dispatch(first.event_id)
    second = dl.begin_update(_update(), authorized=True)
    assert second.duplicate is True
    assert second.task_id == first.task_id
    assert dl.metrics()["telegram_duplicates_suppressed_total"] == 1


def t_b2_crash_after_intent_resumes_same_task():
    dl, _ = _fresh()
    first = dl.begin_update(_update(), authorized=True)
    dl = importlib.reload(dl)
    resumed = dl.begin_update(_update(), authorized=True)
    assert resumed.duplicate is False and resumed.resumed is True
    assert resumed.task_id == first.task_id and resumed.run_id == first.run_id
    dl.start_dispatch(resumed.event_id)


def t_b3_crash_after_dispatch_requires_reconciliation():
    dl, _ = _fresh()
    first = dl.begin_update(_update(), authorized=True)
    dl.start_dispatch(first.event_id)
    dl = importlib.reload(dl)
    replay = dl.begin_update(_update(), authorized=True)
    assert replay.duplicate is True
    assert replay.state == "NEEDS_RECONCILIATION"


def t_c_outbox_is_durable_before_transport_and_read_back():
    dl, root = _fresh()
    ctx = dl.begin_update(_update(), authorized=True)
    dl.bind_context(ctx)
    seen = []

    def fake_send():
        rows = list((root / "telegram" / "loop" / "outbox").glob("*.json"))
        assert len(rows) == 1
        queued = json.loads(rows[0].read_text("utf-8"))
        assert queued["state"] == "SENDING"
        seen.append(queued["message_key"])
        return {"ok": True, "result": {"message_id": 123}}

    result = dl.deliver(text="reply", chat_id=777, topic_id=None,
                        stream="owner-reply", send_fn=fake_send)
    assert result["ok"] is True and result["message_id"] == 123
    assert len(seen) == 1
    assert dl.commit_result({"kind": "reply"})["state"] == "CLOSED"
    snap = dl.readback_event(ctx.event_id)
    assert snap["state"] == "CLOSED" and snap["readback_verified"] is True


def t_d_restart_never_resends_confirmed_message():
    dl, _ = _fresh()
    ctx = dl.begin_update(_update(), authorized=True)
    dl.bind_context(ctx)
    calls = []
    first = dl.deliver(text="reply", chat_id=777, topic_id=None,
                       stream="owner-reply",
                       send_fn=lambda: calls.append(1) or {"ok": True, "result": {"message_id": 88}})
    assert first["ok"] and calls == [1]
    dl.clear_context()
    dl = importlib.reload(dl)
    replay = dl.begin_update(_update(), authorized=True)
    assert replay.duplicate is True
    dl.bind_context(replay)
    second = dl.deliver(text="reply", chat_id=777, topic_id=None,
                        stream="owner-reply",
                        send_fn=lambda: calls.append(2) or {"ok": True, "result": {"message_id": 99}})
    assert second["ok"] and second["message_id"] == 88
    assert calls == [1]


def t_e_unknown_send_outcome_is_quarantined_not_retried():
    dl, _ = _fresh()
    ctx = dl.begin_update(_update(), authorized=True)
    dl.bind_context(ctx)
    calls = []

    def crash_after_attempt():
        calls.append(1)
        raise OSError("synthetic uncertain network boundary")

    first = dl.deliver(text="reply", chat_id=777, topic_id=None,
                       stream="owner-reply", send_fn=crash_after_attempt)
    assert first["ok"] is False and first["state"] == "NEEDS_RECONCILIATION"
    second = dl.deliver(text="reply", chat_id=777, topic_id=None,
                        stream="owner-reply",
                        send_fn=lambda: calls.append(2) or {"ok": True, "result": {"message_id": 2}})
    assert second["ok"] is False and second["state"] == "NEEDS_RECONCILIATION"
    assert calls == [1]


def t_f_auth_failure_has_zero_dispatch_and_zero_outbox():
    dl, root = _fresh()
    ctx = dl.begin_update(_update(owner=999), authorized=False)
    assert ctx.state == "AUTH_REJECTED"
    assert not list((root / "telegram" / "loop" / "outbox").glob("*.json"))
    assert dl.metrics()["telegram_updates_rejected_total"] == 1


def t_g_kill_switch_blocks_before_outbox_and_transport():
    dl, root = _fresh()
    ctx = dl.begin_update(_update(), authorized=True)
    dl.bind_context(ctx)
    os.environ["OCTOPUS_TG_LOOP_KILL"] = "1"
    calls = []
    out = dl.deliver(text="reply", chat_id=777, topic_id=None,
                     stream="owner-reply", send_fn=lambda: calls.append(1))
    assert out["state"] == "BLOCKED" and calls == []
    assert not list((root / "telegram" / "loop" / "outbox").glob("*.json"))


def t_h_invalid_transition_is_rejected_durably():
    dl, _ = _fresh()
    ctx = dl.begin_update(_update(), authorized=True)
    try:
        dl.transition(ctx.event_id, "CLOSED")
    except dl.InvalidTransition:
        pass
    else:
        raise AssertionError("invalid transition must fail closed")
    assert dl.readback_event(ctx.event_id)["state"] == "INTENT_COMMITTED"


def t_i_tg_client_routes_update_reply_through_outbox():
    dl, _ = _fresh()
    import tg_api
    tg_api = importlib.reload(tg_api)
    ctx = dl.begin_update(_update(), authorized=True)
    dl.bind_context(ctx)
    posts = []

    def post(url, body, timeout_s=10.0):
        posts.append((url, body))
        return {"ok": True, "result": {"message_id": 501}}

    client = tg_api.TgClient(token="fake-token", owner_chat_id=777,
                             center_chat_id=None, post_fn=post)
    assert client.send("reply", chat_id=777, stream="owner-reply") == 501
    assert len(posts) == 1
    dl.clear_context()
    dl = importlib.reload(dl)
    replay = dl.begin_update(_update(), authorized=True)
    dl.bind_context(replay)
    assert client.send("reply", chat_id=777, stream="owner-reply") == 501
    assert len(posts) == 1


def t_j_multiple_messages_have_independent_receipts():
    dl, _ = _fresh()
    ctx = dl.begin_update(_update(), authorized=True)
    dl.bind_context(ctx)
    calls = []
    one = dl.deliver(text="first", chat_id=777, topic_id=None,
                     stream="owner-reply",
                     send_fn=lambda: calls.append("first") or {"ok": True, "result": {"message_id": 1}})
    two = dl.deliver(text="second", chat_id=777, topic_id=None,
                     stream="owner-reply",
                     send_fn=lambda: calls.append("second") or {"ok": True, "result": {"message_id": 2}})
    closed = dl.commit_result({"kind": "two-replies"})
    assert one["ok"] and two["ok"] and calls == ["first", "second"]
    assert closed["state"] == "CLOSED"
    assert len(closed["reply_receipt_ids"]) == 2


def t_k_failed_send_is_never_counted_as_answered():
    import tg_receipts
    inbound = [{"update_id": 41, "ts": "2026-08-20T12:00:00", "kind": "message"}]
    failed_send = [{"update_id": 41, "ts": 1787227201.0, "state": "sent", "ok": False}]
    result = tg_receipts.collect(inbound=inbound, sends=failed_send)
    assert result["counts"].get("ANSWERED", 0) == 0
    assert result["rows"][0]["verdict"] != "ANSWERED"


def t_l_durable_begin_is_inside_dead_letter_guard():
    import ast
    center_path = _TG / "center.py"
    tree = ast.parse(center_path.read_text("utf-8", errors="replace"))
    run_once = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "run_once")

    def calls(nodes):
        return {getattr(c.func, "attr", getattr(c.func, "id", ""))
                for node in nodes for c in ast.walk(node) if isinstance(c, ast.Call)}

    guarded = []
    for node in ast.walk(run_once):
        if not isinstance(node, ast.Try):
            continue
        body = calls(node.body)
        handlers = calls(node.handlers)
        final = calls(node.finalbody)
        if "_begin_durable" in body and "_dead_letter" in handlers \
                and "_bind_send_correlation" in final:
            guarded.append(node)
    assert guarded, "durable intent failure must dead-letter and clear correlation"


def t_m_receipt_truth_labels():
    import tg_receipts
    inbound = [{"update_id": 61, "ts": "2026-08-20T12:00:00", "kind": "message"},
               {"update_id": 62, "ts": "2026-08-20T12:01:00", "kind": "message"},
               {"update_id": 63, "ts": "2026-08-20T12:02:00", "kind": "message"}]
    sends = [{"update_id": 61, "ts": 1787227201.0, "state": "sent", "ok": True},
             {"update_id": 62, "ts": 1787227261.0, "state": "sent", "ok": False},
             {"update_id": 63, "ts": 1787227321.0, "state": "sent"}]
    result = tg_receipts.collect(inbound=inbound, sends=sends)
    conf = {r["update_id"]: r.get("confirmation") for r in result["rows"]}
    assert conf[61] == "DELIVERY_CONFIRMED", conf
    assert conf[62] == "DELIVERY_FAILED", conf
    assert conf[63] == "LEGACY_UNCONFIRMED", conf
    c = result.get("confirmation_counts") or {}
    assert c.get("DELIVERY_CONFIRMED") == 1
    assert c.get("DELIVERY_FAILED") == 1
    assert c.get("LEGACY_UNCONFIRMED") == 1
    assert result.get("confirmation_denominator") == 3


def t_n_remember_local_result_durable_ack():
    """Disk commit + durable ACK of LocalCommandResult; fake transport only."""
    dl, root = _fresh()
    ops = str(Path(__file__).resolve().parents[1])
    for extra in (ops, str(Path(ops) / "owner_console")):
        if extra not in sys.path:
            sys.path.insert(0, extra)
    from owner_console import local_commands  # noqa: WPS433

    store = root / "memory.jsonl"

    def _boom(*_a, **_k):
        raise AssertionError("model must not be called")

    res = local_commands.handle_local("/remember fixture-ack: pearl",
                                      model_fn=_boom, memory_store=store)
    assert res.handled and res.memory_id and res.memory_id.startswith("mem-")
    disk = store.read_text(encoding="utf-8")
    assert res.memory_id in disk

    ctx = dl.begin_update(_update(text="/remember fixture-ack: pearl"), authorized=True)
    dl.bind_context(ctx)
    seen = []

    def fake_send():
        rows = list((root / "telegram" / "loop" / "outbox").glob("*.json"))
        assert len(rows) == 1
        queued = json.loads(rows[0].read_text(encoding="utf-8"))
        assert queued["state"] == "SENDING"
        seen.append(queued["message_key"])
        return {"ok": True, "result": {"message_id": 4242}}

    out = dl.ack_local_result(res, chat_id=777, topic_id=None,
                              stream="owner-reply", send_fn=fake_send)
    assert out["deliver"]["ok"] is True
    assert out["deliver"]["message_id"] == 4242
    assert out["deliver"]["state"] == "CONFIRMED"
    assert out["commit"]["state"] == "CLOSED"
    assert len(seen) == 1
    snap = dl.readback_event(ctx.event_id)
    assert snap["state"] == "CLOSED" and snap["readback_verified"] is True
    confirmed = json.loads(next((root / "telegram" / "loop" / "outbox").glob("*.json")).read_text(encoding="utf-8"))
    assert confirmed["state"] == "CONFIRMED"
    assert confirmed.get("delivery_truth") == "DELIVERY_CONFIRMED"




def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    failed = []
    for fn in tests:
        try:
            fn()
            print(f"  OK  {fn.__name__}")
        except Exception as exc:
            failed.append(fn.__name__)
            print(f"  FAIL {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\ntest_telegram_durable_loop: {len(tests) - len(failed)}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
