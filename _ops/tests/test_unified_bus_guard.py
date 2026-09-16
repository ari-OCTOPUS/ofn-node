#!/usr/bin/env python3
"""Offline, hermetic test for M4 (now_moves/unified_bus_guard).

Stdlib-only · no network · no ledger. Uses a fake bus (records publish) and a fake
guard (injected via P._default_guard) to verify: non-human passthrough (guard not
consulted), human allowed → is_human preserved, human denied → downgraded to
is_human=False, guard absent → fail-soft passthrough, transparent delegation of
other attrs, wrap(None) is None. Standalone (exit 0/1) per run_all.py.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
for _p in (str(OPS / "now_moves"), str(OPS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unified_bus_guard as P                            # noqa: E402


class FakeBus:
    def __init__(self):
        self.calls = []
        self.marker = "real-bus"

    def publish(self, event_type, payload, actor="system", is_human=False, beat=False):
        self.calls.append({"event_type": event_type, "actor": actor,
                           "is_human": is_human, "beat": beat})
        return {"hash": "x", "is_human": 1 if is_human else 0}

    def subscribe(self, fn):
        return "subscribed"


class FakeGuard:
    def __init__(self, allow):
        self.allow = allow
        self.calls = []

    def authorize(self, event_type, is_human, *, token=None, approval_id=None):
        self.calls.append((event_type, is_human, token))
        return (self.allow, "test")


def _use_guard(g):
    P._default_guard = (lambda: g)


def test_non_human_passthrough():
    bus = FakeBus(); guard = FakeGuard(True); _use_guard(guard)
    gb = P.wrap(bus)
    gb.publish("OBSERVE", {"a": 1}, actor="pump", is_human=False)
    assert bus.calls[-1]["is_human"] is False, bus.calls
    assert guard.calls == [], "guard must NOT be consulted for non-human"
    print("  ok non-human publish     -> passthrough, guard not consulted")


def test_human_allowed_preserved():
    bus = FakeBus(); _use_guard(FakeGuard(True))
    gb = P.wrap(bus)
    gb.publish("APPROVAL", {"v": "yes"}, actor="human", is_human=True, token="tok")
    assert bus.calls[-1]["is_human"] is True, bus.calls
    print("  ok human + guard allows  -> is_human preserved")


def test_human_denied_downgraded():
    bus = FakeBus(); _use_guard(FakeGuard(False))
    gb = P.wrap(bus)
    gb.publish("APPROVAL", {"v": "yes"}, actor="human", is_human=True)   # no valid token
    assert bus.calls[-1]["is_human"] is False, bus.calls
    print("  ok human + guard denies  -> downgraded to machine append")


def test_guard_absent_failsoft():
    bus = FakeBus(); _use_guard(None)
    gb = P.wrap(bus)
    gb.publish("APPROVAL", {"v": "yes"}, actor="human", is_human=True)
    assert bus.calls[-1]["is_human"] is True, "missing guard must never break the bus"
    print("  ok guard absent          -> fail-soft passthrough")


def test_transparent_delegation():
    bus = FakeBus(); _use_guard(FakeGuard(True))
    gb = P.wrap(bus)
    assert gb.marker == "real-bus", "attribute must delegate to the real bus"
    assert gb.subscribe(lambda e: None) == "subscribed", "method must delegate"
    print("  ok delegation            -> non-publish attrs/methods pass through")


def test_wrap_none():
    assert P.wrap(None) is None
    print("  ok wrap(None)            -> None (factory returned no bus)")


def _run():
    tests = [test_non_human_passthrough, test_human_allowed_preserved,
             test_human_denied_downgraded, test_guard_absent_failsoft,
             test_transparent_delegation, test_wrap_none]
    print("test_unified_bus_guard (M4) — offline, hermetic")
    for t in tests:
        t()
    print(f"PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    try:
        _run()
    except AssertionError as e:
        print("FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print("ERROR:", type(e).__name__, e); sys.exit(1)
    sys.exit(0)
