#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow roundtrip + unowned-alert containment. Fake transport. No paid calls."""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
_TG = _OPS / "telegram_center"
for _p in (str(_OPS), str(_OPS / "budget"), str(_TG), str(_OPS / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from loops import shadow_roundtrip as sr  # noqa: E402
import instant_alert_bridge as ib  # noqa: E402
import opslib  # noqa: E402


def t1_same_update_id_three_times_one_task():
    r = sr.run_one()
    dl, ctx = r["dl"], r["ctx"]
    ids = {ctx.task_id}
    for _ in range(2):
        again = dl.begin_update(sr.fixture_update(), authorized=True)
        ids.add(again.task_id)
        assert again.duplicate is True
    assert len(ids) == 1
    assert r["outbox_n"] == 1
    closed = dl.readback_event(ctx.event_id)
    assert closed.get("state") == "CLOSED"


def t2_same_payload_different_update_id_is_new_event():
    r = sr.run_one()
    dl = r["dl"]
    other = dl.begin_update(sr.fixture_update(uid=900002), authorized=True)
    assert other.duplicate is False
    assert other.task_id != r["ctx"].task_id
    decision = {"policy": "update_id is idempotency key; payload_hash collision is AUDIT not merge",
                "first": r["ctx"].event_id, "second": other.event_id}
    assert decision["first"] != decision["second"]


def t3_unauthorized_zero_dispatch_zero_outbox():
    r = sr.run_one(authorized=False)
    assert r["ctx"].state == "AUTH_REJECTED"
    assert r["ctx"].task_id is None
    assert not list((r["root"] / "telegram" / "loop" / "outbox").glob("*.json"))


def t4_crash_after_intent_resumes_same_task():
    root = Path(tempfile.mkdtemp())
    dl = sr._load_dl(root)
    first = dl.begin_update(sr.fixture_update(), authorized=True)
    dl = importlib.reload(dl)
    resumed = dl.begin_update(sr.fixture_update(), authorized=True)
    assert resumed.resumed is True
    assert resumed.task_id == first.task_id


def t5_crash_after_result_before_delivery_retries_outbox_once():
    root = Path(tempfile.mkdtemp())
    dl = sr._load_dl(root)
    ctx = dl.begin_update(sr.fixture_update(), authorized=True)
    dl.bind_context(ctx)
    dl.commit_result({"kind": "pre-delivery"})
    snap = dl.readback_event(ctx.event_id)
    assert snap["state"] == "RESULT_COMMITTED"
    dl = importlib.reload(dl)
    ctx2 = dl.begin_update(sr.fixture_update(), authorized=True)
    dl.bind_context(ctx2)
    calls = []
    out = dl.deliver(text="shadow-pong", chat_id=sr.SHADOW_OWNER, topic_id=None,
                     stream="shadow",
                     send_fn=lambda: calls.append(1) or {"ok": True, "result": {"message_id": 7}})
    assert out.get("ok") is True
    assert calls == [1]


def t6_sender_restart_no_resend_if_confirmed():
    r = sr.run_one()
    dl, ctx = r["dl"], r["ctx"]
    calls = []
    dl = importlib.reload(dl)
    replay = dl.begin_update(sr.fixture_update(), authorized=True)
    dl.bind_context(replay)
    second = dl.deliver(text="shadow-pong", chat_id=sr.SHADOW_OWNER, topic_id=None,
                        stream="shadow",
                        send_fn=lambda: calls.append(1) or {"ok": True, "result": {"message_id": 99}})
    assert second.get("ok") is True
    assert second.get("message_id") == 4242
    assert calls == []


def t7_invalid_schema_dead_lettered():
    r = sr.run_one(invalid_schema=True)
    assert r["transport_calls"] <= 2
    assert (r.get("closed") or {}).get("state") == "DEAD_LETTERED"


def t8_sig_fear_cannot_bypass_outbox():
    state = Path(tempfile.mkdtemp())
    prev_state = getattr(opslib, "STATE_DIR", None)
    prev_env = os.environ.get("OCTOPUS_STATE_DIR")
    prev_flag = os.environ.get(ib.FLAG)
    os.environ["OCTOPUS_STATE_DIR"] = str(state)
    opslib.STATE_DIR = state
    (state / "cortex").mkdir(parents=True, exist_ok=True)
    (state / "cortex" / "cortisol-state.json").write_text(
        json.dumps({"level": "🔴 ترس", "in_fear": ["legs"]}), encoding="utf-8")
    (state / "cortex" / "stress-latest.json").write_text(
        json.dumps({"level": "🟢", "in_fear": []}), encoding="utf-8")
    os.environ[ib.FLAG] = "1"
    ch_sent = []

    class Chan:
        def send_text(self, *a, **k):
            ch_sent.append(1)
            return True

    try:
        r = ib.check(Chan(), min_interval_s=0.0)
        assert ch_sent == []
        assert r.get("direct_sends") == 0
        assert "fear" in (r.get("outboxed") or r.get("sent") or [])
        ob = state / "loops" / "telegram-outbox.jsonl"
        assert ob.is_file()
        row = json.loads(ob.read_text(encoding="utf-8").splitlines()[0])
        assert row["kind"] == "unowned_alert"
        assert row["sent"] is False
        assert row["task_id"] is None
        assert row.get("correlation_id")
        assert row["loop_id"] == "LOOP-TELEGRAM-UNOWNED-INSTANT-ALERT"
    finally:
        if prev_flag is None:
            os.environ.pop(ib.FLAG, None)
        else:
            os.environ[ib.FLAG] = prev_flag
        if prev_env is None:
            os.environ.pop("OCTOPUS_STATE_DIR", None)
        else:
            os.environ["OCTOPUS_STATE_DIR"] = prev_env
        if prev_state is not None:
            opslib.STATE_DIR = prev_state


def t9_memory_disabled_degraded_response_survives():
    os.environ["OCTOPUS_MEMORY_DISABLED"] = "1"
    try:
        r = sr.run_one(memory_disabled=True)
        assert r["ok"] is True
        assert "degraded" in (r.get("reply") or "")
        assert r["closed"]["state"] == "CLOSED"
    finally:
        os.environ.pop("OCTOPUS_MEMORY_DISABLED", None)


def t10_kill_switch_blocks_dispatch():
    try:
        r = sr.run_one(kill=True)
        assert (r.get("delivered") or {}).get("state") == "BLOCKED"
        assert not list((r["root"] / "telegram" / "loop" / "outbox").glob("*.json"))
    finally:
        os.environ.pop("OCTOPUS_TG_LOOP_KILL", None)


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t") and callable(v)]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  PASS {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"{'PASS' if not failed else 'FAIL'} {len(tests) - failed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
