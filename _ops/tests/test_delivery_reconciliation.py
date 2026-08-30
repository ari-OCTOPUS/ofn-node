#!/usr/bin/env python3
"""Delivery truth states + bounded reconciliation queue contract.

Owner ruling 2026-08-21 scenarios:
- timeout before transport attempt;
- timeout during transport call;
- response received but receipt commit crashes;
- restart during reconciliation;
- owner-observed evidence (no message_id invented);
- no automatic resend of uncertain effects;
- failed send never counted as answered.
All transports are fake; no network, no paid calls.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_TG = _OPS / "telegram_center"
for _p in (str(_OPS), str(_TG)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _fresh():
    root = Path(tempfile.mkdtemp(prefix="tg-delivery-rec-"))
    os.environ["OCTOPUS_STATE_DIR"] = str(root)
    os.environ["OCTOPUS_TG_DURABLE_OUTBOX"] = "1"
    os.environ.pop("OCTOPUS_TG_LOOP_KILL", None)
    import durable_loop
    import delivery_reconciliation
    dl = importlib.reload(durable_loop)
    dr = importlib.reload(delivery_reconciliation)
    return dl, dr, root


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


def _single_outbox(root: Path) -> dict:
    files = list((root / "telegram" / "loop" / "outbox").glob("*.json"))
    assert len(files) == 1, files
    return json.loads(files[0].read_text(encoding="utf-8"))


def _event(root: Path, event_id: str) -> dict:
    name = event_id.replace(":", "_")
    return json.loads((root / "telegram" / "loop" / "events" / (name + ".json"))
                      .read_text(encoding="utf-8"))


def t_a_timeout_before_transport_attempt_goes_uncertain():
    dl, dr, root = _fresh()
    calls = []

    def boom(*_a, **_k):
        calls.append(1)
        raise TimeoutError("no transport attempt happened")

    ctx = dl.begin_update(_update(), authorized=True)
    dl.bind_context(ctx)
    out = dl.deliver(text="reply", chat_id=777, topic_id=None,
                     stream="center", send_fn=boom)
    assert out["managed"] is True and out["ok"] is False
    assert out["state"] == "NEEDS_RECONCILIATION" and out["message_id"] is None
    ob = _single_outbox(root)
    assert ob["delivery_truth"] == "UNCERTAIN_SEND_OUTCOME"
    assert ob["state"] == "NEEDS_RECONCILIATION"
    q = dr.pending()
    assert len(q) == 1 and q[0]["truth"] == "UNCERTAIN_SEND_OUTCOME"
    assert q[0]["message_key"] == ob["message_key"]


def t_b_timeout_during_transport_call_goes_uncertain():
    dl, dr, root = _fresh()
    calls = []

    def boom(*_a, **_k):
        calls.append(1)
        raise TimeoutError("transport call timed out mid-flight")

    ctx = dl.begin_update(_update(uid=42), authorized=True)
    dl.bind_context(ctx)
    out = dl.deliver(text="reply", chat_id=777, topic_id=None,
                     stream="center", send_fn=boom)
    assert out["state"] == "NEEDS_RECONCILIATION"
    assert _single_outbox(root)["delivery_truth"] == "UNCERTAIN_SEND_OUTCOME"
    assert len(dr.pending()) == 1
    # never counted as answered: event must not be CLOSED/RESPONSE_CONFIRMED
    ev = _event(root, "tg:42")
    assert ev["state"] == "NEEDS_RECONCILIATION"
    assert ev["readback_verified"] is not True


def t_c_receipt_commit_crash_leaves_no_fake_confirmation():
    dl, dr, root = _fresh()
    calls = []

    def ok_fn(*_a, **_k):
        calls.append(1)
        return {"ok": True, "result": {"message_id": 777}}

    real_atomic = dl._atomic

    def crash_atomic(path, value):
        if value.get("state") == "CONFIRMED":
            raise OSError("receipt commit crashed")
        real_atomic(path, value)

    dl._atomic = crash_atomic
    ctx = dl.begin_update(_update(uid=43), authorized=True)
    dl.bind_context(ctx)
    crashed = False
    try:
        dl.deliver(text="reply", chat_id=777, topic_id=None,
                   stream="center", send_fn=ok_fn)
    except OSError:
        crashed = True
    assert crashed
    ob = _single_outbox(root)
    # the crash happened before the CONFIRMED write: no fake confirmation
    assert ob["state"] != "CONFIRMED"
    assert ob.get("message_id") is None
    # retry after crash must NOT produce a second external response
    dl._atomic = real_atomic
    out = dl.deliver(text="reply", chat_id=777, topic_id=None,
                     stream="center", send_fn=ok_fn)
    assert out["state"] == "NEEDS_RECONCILIATION"
    assert calls == [1], "send_fn must be called exactly once"


def t_d_restart_during_reconciliation_is_bounded():
    dl, dr, root = _fresh()
    dr.enqueue_uncertain(event_id="tg:44", message_key="k" * 64)
    dl = importlib.reload(dl)
    dr = importlib.reload(dr)
    r1 = dr.reconcile()
    assert r1["still_pending"] == 1 and r1["resolved"] == {
        "confirmed": 0, "owner_observed": 0, "dead_lettered": 0}
    r2 = dr.reconcile()
    assert r2["still_pending"] == 1
    r3 = dr.reconcile()
    assert r3["resolved"]["dead_lettered"] == 1
    assert r3["still_pending"] == 0
    last = dr.pending()
    assert last == []
    # never confirmed, never resent — the item is quarantined with the
    # DEAD_LETTERED truth
    rows = (root / "telegram" / "loop" / "reconciliation-queue.jsonl") \
        .read_text(encoding="utf-8").splitlines()
    final = json.loads(rows[-1])
    assert final["status"] == "dead_lettered"
    assert final["truth"] == "DEAD_LETTERED"


def t_e_owner_observed_evidence_never_invents_message_id():
    dl, dr, root = _fresh()
    key = "e" * 64
    dr.enqueue_uncertain(event_id="tg:45", message_key=key)
    dr.record_owner_observation(event_id="tg:45", message_key=key,
                                observed_by="owner", note="seen in chat")
    r = dr.reconcile()
    assert r["resolved"]["owner_observed"] == 1
    assert r["still_pending"] == 0
    rows = (root / "telegram" / "loop" / "owner-observed-evidence.jsonl") \
        .read_text(encoding="utf-8").splitlines()
    for line in rows:
        row = json.loads(line)
        assert row["kind"] == "OWNER_OBSERVED_UNCONFIRMED_API"
        assert "message_id" not in row, "owner observation must not invent a message_id"
    last = (root / "telegram" / "loop" / "reconciliation-queue.jsonl") \
        .read_text(encoding="utf-8").splitlines()[-1]
    resolved = json.loads(last)
    assert resolved["truth"] == "OWNER_OBSERVED_UNCONFIRMED_API"
    assert resolved["status"] == "resolved"


def t_f_no_automatic_resend_of_uncertain_effects():
    dl, dr, root = _fresh()
    calls = []

    def boom(*_a, **_k):
        calls.append(1)
        raise TimeoutError("boom")

    ctx = dl.begin_update(_update(uid=46), authorized=True)
    dl.bind_context(ctx)
    first = dl.deliver(text="reply", chat_id=777, topic_id=None,
                       stream="center", send_fn=boom)
    assert first["state"] == "NEEDS_RECONCILIATION"
    second = dl.deliver(text="reply", chat_id=777, topic_id=None,
                        stream="center", send_fn=boom)
    assert second["state"] == "NEEDS_RECONCILIATION"
    assert second["message_id"] is None
    assert calls == [1], "uncertain effect must never be automatically resent"


def t_g_failed_send_is_never_counted_as_answered():
    dl, dr, root = _fresh()
    calls = []

    def boom(*_a, **_k):
        calls.append(1)
        raise RuntimeError("send failed")

    ctx = dl.begin_update(_update(uid=47), authorized=True)
    dl.bind_context(ctx)
    out = dl.deliver(text="reply", chat_id=777, topic_id=None,
                     stream="center", send_fn=boom)
    assert out["ok"] is False
    ob = _single_outbox(root)
    assert ob["state"] == "NEEDS_RECONCILIATION"
    assert ob.get("message_id") is None
    ev = _event(root, "tg:47")
    assert ev["state"] == "NEEDS_RECONCILIATION"
    assert "CLOSED" not in str(ev.get("transitions") or [])
    assert dr.pending()[0]["truth"] == "UNCERTAIN_SEND_OUTCOME"


def t_h_truth_states_are_explicit():
    dl, dr, root = _fresh()
    expected = {"QUEUED", "ATTEMPTING", "DELIVERY_CONFIRMED", "DELIVERY_FAILED",
                "UNCERTAIN_SEND_OUTCOME", "OWNER_OBSERVED_UNCONFIRMED_API",
                "DEAD_LETTERED"}
    assert dr.TRUTH_STATES == expected



def t_i_event_path_normalize_colon_and_underscore_match():
    """Both logical (tg:) and on-disk (tg_) forms must resolve identically.

    Reproduces OCTOPUS-OUTBOX-RECONCILE-2026-08-23 blocker B5: reconcile
    looked up events/{event_id}.json with colon, but durable_loop stores
    events/tg_<id>.json. No live send; fixture-only transport evidence.
    """
    dl, dr, root = _fresh()
    assert dr._event_fs_name("tg:223883344") == "tg_223883344"
    assert dr._event_fs_name("tg_223883344") == "tg_223883344"
    assert dr._event_fs_name("tg:223883344") == dr._event_fs_name("tg_223883344")

    events = root / "telegram" / "loop" / "events"
    events.mkdir(parents=True, exist_ok=True)
    # On-disk form as durable_loop._event_path would write it
    ev_path = events / "tg_223883344.json"
    ev_path.write_text(json.dumps({
        "event_id": "tg:223883344",
        "state": "CLOSED",
        "readback_verified": True,
        "delivery_message_id": 999001,
    }), encoding="utf-8")

    key = "a" * 64
    dr.enqueue_uncertain(event_id="tg:223883344", message_key=key)
    found = dr._search_transport_evidence({
        "event_id": "tg:223883344",
        "message_key": key,
    })
    assert found is not None, "colon form must find underscore on-disk file"
    assert found["truth"] == "DELIVERY_CONFIRMED"

    found2 = dr._search_transport_evidence({
        "event_id": "tg_223883344",
        "message_key": key,
    })
    assert found2 is not None, "underscore form must also match"
    assert found2["truth"] == "DELIVERY_CONFIRMED"


def t_j_reconcile_confirms_via_normalized_event_path():
    """Full reconcile() pass: queue carries tg:, disk has tg_ -> CONFIRMED."""
    dl, dr, root = _fresh()
    events = root / "telegram" / "loop" / "events"
    events.mkdir(parents=True, exist_ok=True)
    (events / "tg_55.json").write_text(json.dumps({
        "event_id": "tg:55",
        "state": "CLOSED",
        "readback_verified": True,
        "delivery_message_id": 555,
    }), encoding="utf-8")
    key = "b" * 64
    dr.enqueue_uncertain(event_id="tg:55", message_key=key)
    r = dr.reconcile()
    assert r["resolved"]["confirmed"] == 1, r
    assert r["still_pending"] == 0
    # Must not dead-letter when transport evidence exists under normalized path
    assert r["resolved"]["dead_lettered"] == 0




def t_k_sync_owner_observed_to_dead_letter():
    """OWNER_OBSERVED queue resolution -> outbox+event DEAD_LETTERED (no send).

    Reproduces OCTOPUS-OUTBOX-RECONCILE B6: sanctioned reversible sync helper.
    """
    dl, dr, root = _fresh()
    key = "c" * 64
    event_id = "tg:66"
    # Seed outbox + event in NEEDS_RECONCILIATION (as live quarantine items)
    outbox = root / "telegram" / "loop" / "outbox"
    events = root / "telegram" / "loop" / "events"
    outbox.mkdir(parents=True, exist_ok=True)
    events.mkdir(parents=True, exist_ok=True)
    (outbox / f"{key}.json").write_text(json.dumps({
        "schema": "telegram-outbox/1",
        "message_key": key,
        "event_id": event_id,
        "state": "NEEDS_RECONCILIATION",
        "error_code": "UNCERTAIN_SEND_OUTCOME",
        "message_id": None,
    }), encoding="utf-8")
    (events / "tg_66.json").write_text(json.dumps({
        "schema": "telegram-durable-loop/1",
        "event_id": event_id,
        "state": "NEEDS_RECONCILIATION",
        "transitions": [],
        "readback_verified": False,
        "delivery_message_id": None,
    }), encoding="utf-8")
    dr.enqueue_uncertain(event_id=event_id, message_key=key)
    dr.record_owner_observation(event_id=event_id, message_key=key,
                                observed_by="owner", note="seen")
    assert dr.reconcile()["resolved"]["owner_observed"] == 1

    # Unrelated CONFIRMED outbox must be untouched
    other = "d" * 64
    (outbox / f"{other}.json").write_text(json.dumps({
        "schema": "telegram-outbox/1",
        "message_key": other,
        "event_id": "tg:67",
        "state": "CONFIRMED",
        "message_id": 123,
    }), encoding="utf-8")

    dry = dr.sync_owner_observed_to_dead_letter(message_keys=[key], dry_run=True)
    assert dry["synced"] == 1 and dry["items"][0]["action"] == "would_sync"
    assert json.loads((outbox / f"{key}.json").read_text(encoding="utf-8"))["state"] == "NEEDS_RECONCILIATION"

    live = dr.sync_owner_observed_to_dead_letter(message_keys=[key], dry_run=False)
    assert live["synced"] == 1 and live["items"][0]["action"] == "synced"
    ob = json.loads((outbox / f"{key}.json").read_text(encoding="utf-8"))
    ev = json.loads((events / "tg_66.json").read_text(encoding="utf-8"))
    assert ob["state"] == "DEAD_LETTERED"
    assert ob["delivery_truth"] == "DEAD_LETTERED"
    assert ob.get("message_id") is None
    assert ev["state"] == "DEAD_LETTERED"
    assert ev.get("delivery_message_id") is None
    other_ob = json.loads((outbox / f"{other}.json").read_text(encoding="utf-8"))
    assert other_ob["state"] == "CONFIRMED" and other_ob["message_id"] == 123
    # Journal has before-snapshot (reversible)
    journal = (root / "telegram" / "loop" / "owner-observed-dead-letter-sync-journal.jsonl")
    assert journal.is_file()
    jrow = json.loads(journal.read_text(encoding="utf-8").splitlines()[-1])
    assert jrow["kind"] == "OWNER_OBSERVED_DEAD_LETTER_SYNC"
    assert jrow["before"]["outbox"]["state"] == "NEEDS_RECONCILIATION"
    # Idempotent skip
    again = dr.sync_owner_observed_to_dead_letter(message_keys=[key], dry_run=False)
    assert again["synced"] == 0 and again["items"][0]["reason"] == "already_dead_lettered"
    # Filter refuses non-target
    refuse = dr.sync_owner_observed_to_dead_letter(message_keys=[other], dry_run=False)
    assert refuse["synced"] == 0
    assert other_ob == json.loads((outbox / f"{other}.json").read_text(encoding="utf-8"))

def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  OK  {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\ntest_delivery_reconciliation: {len(tests) - failed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
