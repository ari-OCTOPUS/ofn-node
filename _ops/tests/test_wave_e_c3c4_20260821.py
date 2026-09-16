#!/usr/bin/env python3
"""Wave E — C3/C4 wiring verification (owner order 2026-08-21).

Proves the durable deferral + single-owner sender bridge contract:
- full retry_after preserved (no cap; huge values deferred in full)
- restart at retry_after-1 must NOT send; at retry_after the item is due
- SenderBridge full cycle: due -> admit -> mark_delivery_attempt -> send_fn
  -> confirm(message_id) / defer(full retry_after) / DLQ(failed)
- crash after transport attempt -> UNCERTAIN_SEND_OUTCOME in DLQ; a second
  run_once never auto-resends it
- duplicate message key -> single delivery
- live attachment stays default-off (center does not import sender_bridge;
  TgClient has no defer queue until attach_defer_queue is called)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "telegram_center"))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402
ENV = harness.setup("wave-e-c3c4")
_STATE = Path(tempfile.mkdtemp(prefix="wave-e-c3c4-"))
os.environ["OCTOPUS_STATE_DIR"] = str(_STATE / "_ops" / "state")

import rate_limit_queue as rlq  # noqa: E402
from sender_bridge import SenderBridge  # noqa: E402

T0 = 1_785_500_000.0
CLOCK = {"now": T0}


def _clock() -> float:
    return CLOCK["now"]


def _fresh_queue(name: str) -> rlq.RateLimitQueue:
    q = rlq.RateLimitQueue(str(_STATE / f"{name}.sqlite3"), clock=_clock, jitter=lambda: 0.0)
    q.reset() if hasattr(q, "reset") else None
    return q


def _mk(key: str, chat: str = "c1") -> dict:
    return {"message_key": key, "chat_hash": chat,
            "payload_hash": f"ph:{key}", "priority": 0}


def test_full_retry_after_preserved_no_cap():
    CLOCK['now'] = T0
    q = _fresh_queue("full-ra")
    huge = 10 ** 9  # any value must be preserved verbatim (no min(ra, cap))
    q.enqueue(message_key="m1", chat_hash="c1", payload_hash="p1")
    q.defer("m1", retry_after=huge)
    row = q.get("m1")
    assert row["state"] == "DEFERRED"
    # retry_not_before = now + huge + jitter(0)
    assert row["retry_not_before"] >= T0 + huge
    # nothing is due before the boundary
    assert q.due() == []


def test_restart_at_retry_after_minus_1_does_not_send():
    CLOCK['now'] = T0
    # durable queue survives a "restart" (new queue object, same sqlite file)
    q1 = _fresh_queue("ra-boundary")
    q1.enqueue(message_key="m1", chat_hash="c1", payload_hash="p1")
    q1.defer("m1", retry_after=60.0)          # prohibited until T0+60
    q2 = rlq.RateLimitQueue(str(_STATE / "ra-boundary.sqlite3"), clock=_clock, jitter=lambda: 0.0)
    CLOCK["now"] = T0 + 59.0                  # restart at retry_after - 1
    assert q2.due() == [], "restart before the boundary must NOT make the item due"
    sends = []
    SenderBridge(q2, lambda item: sends.append(item) or {"ok": True, "message_id": 1}).run_once()
    assert sends == [], "no send before retry_after"


def test_restart_at_retry_after_sends():
    CLOCK['now'] = T0
    q1 = _fresh_queue("ra-due")
    q1.enqueue(message_key="m1", chat_hash="c1", payload_hash="p1")
    q1.defer("m1", retry_after=60.0)
    q2 = rlq.RateLimitQueue(str(_STATE / "ra-due.sqlite3"), clock=_clock, jitter=lambda: 0.0)
    CLOCK["now"] = T0 + 60.0                  # restart exactly at the boundary
    sends = []
    out = SenderBridge(q2, lambda item: sends.append(item) or {"ok": True, "message_id": 7}).run_once()
    assert len(sends) == 1
    assert out["sent"] == 1
    row = q2.get("m1")
    assert row["state"] == "CONFIRMED" and row["message_id"] == 7


def test_bridge_full_cycle_confirm_defer_dlq():
    CLOCK['now'] = T0
    q = _fresh_queue("cycle")
    # one item per chat so the local CHAT_1_PER_SECOND policy admits all three
    q.enqueue(message_key="ok1", chat_hash="c1", payload_hash="p1")
    q.enqueue(message_key="ra1", chat_hash="c2", payload_hash="p2")
    q.enqueue(message_key="fail1", chat_hash="c3", payload_hash="p3")
    def send_fn(item):
        key = item["message_key"]
        if key == "ok1":
            return {"ok": True, "message_id": 99}
        if key == "ra1":
            return {"ok": False, "retry_after": 120.0}
        return {"ok": False}                  # failed without retry_after
    bridge = SenderBridge(q, send_fn)
    out = bridge.run_once()
    assert out["sent"] == 1 and out["deferred"] == 1 and out["dlq"] == 1, out
    assert q.get("ok1")["state"] == "CONFIRMED"
    row = q.get("ra1")
    assert row["state"] == "DEFERRED"
    assert row["retry_not_before"] >= T0 + 120.0, "full retry_after preserved"
    assert q.get("fail1")["state"] == "DLQ"


def test_crash_after_attempt_goes_uncertain_never_resends():
    CLOCK['now'] = T0
    q = _fresh_queue("crash")
    q.enqueue(message_key="m1", chat_hash="c1", payload_hash="p1")
    attempts = []
    def send_fn(item):
        attempts.append(item["message_key"])
        raise RuntimeError("crash after transport attempt")
    bridge = SenderBridge(q, send_fn)
    out = bridge.run_once()
    assert out["dlq"] == 1
    row = q.get("m1")
    assert row["state"] == "DLQ"
    assert row["last_error"] == "UNCERTAIN_SEND_OUTCOME"
    # second pass must NOT resend the uncertain item
    out2 = bridge.run_once()
    assert out2["due"] == 0 and out2["sent"] == 0
    assert len(attempts) == 1, "uncertain outcome must never auto-resend"


def test_duplicate_message_key_single_delivery():
    CLOCK['now'] = T0
    q = _fresh_queue("dupkey")
    r1 = q.enqueue(message_key="k1", chat_hash="c1", payload_hash="p1")
    r2 = q.enqueue(message_key="k1", chat_hash="c1", payload_hash="p1")
    assert r1["duplicate"] is False and r2["duplicate"] is True
    sends = []
    out = SenderBridge(q, lambda item: sends.append(item) or {"ok": True, "message_id": 5}).run_once()
    assert len(sends) == 1 and out["sent"] == 1
    out2 = SenderBridge(q, lambda item: sends.append(item) or {"ok": True, "message_id": 6}).run_once()
    assert out2["due"] == 0, "confirmed item must not be redelivered"


def test_live_attachment_stays_default_off():
    # the live Center must not import the bridge (owner gate: attach explicitly)
    center_src = (_OPS / "telegram_center" / "center.py").read_text(encoding="utf-8")
    assert "import sender_bridge" not in center_src
    assert "from sender_bridge" not in center_src
    # TgClient has no defer queue until attach_defer_queue arms it
    import tg_api  # noqa: WPS433
    client = tg_api.TgClient("123:ABC", owner_chat_id=1)
    assert client._defer_queue is None
    assert client._defer == client._default_defer


def main() -> int:
    failed = []
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in tests:
        try:
            fn()
            print(f"  ok  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(fn.__name__)
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
