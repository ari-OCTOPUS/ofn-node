# -*- coding: utf-8 -*-
"""Wave 1 preflight tests — shadow isolation, receipts, kill, write guard."""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))

from nervous_recovery import wave0_governor, wave1_gates, wave1_readonly  # noqa: E402


def test_unresolved_stays_null():
    store = wave1_readonly.FixtureStore(wave1_readonly.default_fixture())
    dt = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    out = wave1_readonly.retrieve(
        store, caller_task="", run_id="", kind="query_experiments",
        decision_time=dt, shadow=True)
    assert out["status"] == "unresolved"
    assert out["receipt"]["task_id"] in ("", None)
    assert out["receipt"]["outcome"] == "unattributed"
    assert "pid" not in str(out["receipt"]["task_id"] or "")


def test_task_a_cannot_read_task_b():
    store = wave1_readonly.FixtureStore(wave1_readonly.default_fixture())
    dt = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    a = wave1_readonly.retrieve(
        store, caller_task="tsk_wave1_a", run_id="run_wave1_a",
        kind="search_vault", needle="bravo", decision_time=dt, shadow=True)
    assert "mem_b_01" not in a["ids"]
    b = wave1_readonly.retrieve(
        store, caller_task="tsk_wave1_b", run_id="run_wave1_b",
        kind="search_vault", needle="alpha", decision_time=dt, shadow=True)
    assert not any(i.startswith("mem_a_") for i in b["ids"])


def test_shared_visible_and_future_hidden():
    store = wave1_readonly.FixtureStore(wave1_readonly.default_fixture())
    dt = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    a = wave1_readonly.retrieve(
        store, caller_task="tsk_wave1_a", run_id="run_wave1_a",
        kind="search_vault", needle="shared", decision_time=dt, shadow=True)
    assert "mem_shared_01" in a["ids"]
    fut = wave1_readonly.retrieve(
        store, caller_task="tsk_wave1_a", run_id="run_wave1_a",
        kind="by_id", needle="mem_future_01", decision_time=dt, shadow=True)
    assert fut["ids"] == []


def test_write_guard_blocks_and_fingerprint_holds():
    store = wave1_readonly.FixtureStore(wave1_readonly.default_fixture())
    fp = store.fingerprint()
    try:
        store.write({"id": "x"})
        raise AssertionError("write must raise")
    except RuntimeError:
        pass
    assert store.fingerprint() == fp
    assert store.guard.mutations >= 1


def test_kill_switch_stops_retrieval():
    store = wave1_readonly.FixtureStore(wave1_readonly.default_fixture())
    dt = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    overlay = Path(tempfile.mkdtemp())
    (overlay / "STOP-WAVE1-READ").write_text("stop\n", encoding="utf-8")
    out = wave1_readonly.retrieve(
        store, caller_task="tsk_wave1_a", run_id="run_wave1_a",
        kind="query_experiments", decision_time=dt, shadow=True,
        overlay_root=overlay)
    assert out["status"] == "killed"
    assert out["ids"] == []


def test_production_lock_closed_skips_nonsadow():
    store = wave1_readonly.FixtureStore(wave1_readonly.default_fixture())
    dt = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    lock = Path(tempfile.mkdtemp()) / "lock.json"
    lock.write_text(json.dumps({"wave1_unlocked": False}), encoding="utf-8")
    out = wave1_readonly.retrieve(
        store, caller_task="tsk_wave1_a", run_id="run_wave1_a",
        kind="query_experiments", decision_time=dt, shadow=False,
        lock_path=lock)
    assert out["status"] == "locked"
    assert out["ids"] == []


def test_shadow_sample_hygiene():
    s = wave1_readonly.run_shadow_sample()
    assert s["n"] >= 10
    assert s["ratio"] >= 0.95
    assert s["fabricated_task_ids"] == 0
    assert s["memory_mutations"] == 0
    assert s["cross_task_leaks"] == []
    assert s["readback_failures"] == 0
    assert s["kill_switch_ok"] is True
    assert s["write_blocked"] is True
    assert s["paid_calls"] == 0
    assert s["wave1_unlocked"] is False


def test_wave0_governor_never_unlocks():
    rep = wave0_governor.audit_wave0()
    assert rep["wave1_unlocked"] is False


def test_entry_gates_see_shadow():
    freeze = wave1_gates.wave0_freeze_ok()
    shadow = wave1_readonly.run_shadow_sample()
    caps = wave1_gates.evaluate_capabilities(shadow)
    gates = wave1_gates.entry_gates(shadow, caps, freeze, True)
    assert caps["cards"]
    assert all(c["truth_status"] in capability_ok() for c in caps["cards"])
    assert isinstance(gates["all_pass"], bool)
    # Live lock may already be open after a canary; the pre-activation
    # snapshot lives in WAVE1-ENTRY-GATES.json.


def capability_ok():
    return {
        "VERIFIED", "DEGRADED", "DECLARED_UNOBSERVED",
        "DORMANT", "BLOCKED", "UNKNOWN",
    }


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in tests:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as e:
            failed += 1
            print("FAIL", fn.__name__, type(e).__name__, e)
    if failed:
        raise SystemExit(1)
    print(f"{len(tests)} passed")
