#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Doctor / EveLab poller-uniqueness fail-closed probe — fixture only."""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_DOC = _OPS / "doctor"
for _p in (str(_OPS), str(_DOC), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _fresh():
    root = Path(tempfile.mkdtemp(prefix="poller-uniq-"))
    state = root / "state"
    state.mkdir(parents=True, exist_ok=True)
    os.environ["OCTOPUS_STATE_DIR"] = str(state)
    return root, state


def t_a_fixture_one_one_one_passes():
    import poller_uniqueness as pu
    pu = importlib.reload(pu)
    _, state = _fresh()
    pu.seed_uniqueness_fixture(state, center_pid=424242)
    out = pu.check_poller_uniqueness(
        state_dir=state,
        center_pids=[424242],
        require_lock_pid_alive=False,
        scan_live_pids=False,
    )
    assert out["ok"] is True, out
    assert out["checks"]["one_center_pid"] is True
    assert out["checks"]["one_active_lease"] is True
    assert out["checks"]["one_tg_poller_lock"] is True
    assert out["checks"]["pids_agree"] is True
    assert out["live_send"] is False


def t_b_two_active_leases_fails():
    import poller_uniqueness as pu
    pu = importlib.reload(pu)
    _, state = _fresh()
    pu.seed_uniqueness_fixture(state, center_pid=111, extra_active_leases=1)
    out = pu.check_poller_uniqueness(
        state_dir=state,
        center_pids=[111],
        require_lock_pid_alive=False,
        scan_live_pids=False,
    )
    assert out["ok"] is False, out
    assert out["checks"]["one_active_lease"] is False
    assert out["active_lease_count"] == 2


def t_c_two_center_pids_fails():
    import poller_uniqueness as pu
    pu = importlib.reload(pu)
    _, state = _fresh()
    pu.seed_uniqueness_fixture(state, center_pid=222)
    out = pu.check_poller_uniqueness(
        state_dir=state,
        center_pids=[222, 333],
        require_lock_pid_alive=False,
        scan_live_pids=False,
    )
    assert out["ok"] is False, out
    assert out["checks"]["one_center_pid"] is False


def t_d_two_locks_fails():
    import poller_uniqueness as pu
    pu = importlib.reload(pu)
    _, state = _fresh()
    pu.seed_uniqueness_fixture(state, center_pid=444, extra_locks=1)
    out = pu.check_poller_uniqueness(
        state_dir=state,
        center_pids=[444],
        require_lock_pid_alive=False,
        scan_live_pids=False,
    )
    assert out["ok"] is False, out
    assert out["checks"]["one_tg_poller_lock"] is False


def t_e_pid_mismatch_fails():
    import poller_uniqueness as pu
    pu = importlib.reload(pu)
    _, state = _fresh()
    pu.seed_uniqueness_fixture(state, center_pid=555)
    out = pu.check_poller_uniqueness(
        state_dir=state,
        center_pids=[999],
        require_lock_pid_alive=False,
        scan_live_pids=False,
    )
    assert out["ok"] is False, out
    assert out["checks"]["pids_agree"] is False


def t_f_lab_call_doctor_check_includes_uniqueness():
    import lab_bridge
    lab_bridge = importlib.reload(lab_bridge)
    _, state = _fresh()
    result = lab_bridge.lab_call_doctor_check(state_dir=state, dry_run=True)
    assert result.get("live_send") is False
    assert result.get("ok") is True, result
    names = {c["name"]: c for c in result.get("checks") or []}
    assert "poller_uniqueness" in names, names.keys()
    assert names["poller_uniqueness"]["ok"] is True, names["poller_uniqueness"]
    assert names["poller_uniqueness"].get("fixture") is True
    assert names["poller_uniqueness"]["center_pid_count"] == 1
    assert names["poller_uniqueness"]["active_lease_count"] == 1
    assert names["poller_uniqueness"]["tg_poller_lock_count"] == 1


def t_g_no_secrets_in_module_source():
    src = (_DOC / "poller_uniqueness.py").read_text(encoding="utf-8")
    banned = ("BOT_TOKEN", "api.telegram.org", "sendMessage", "getUpdates")
    for w in banned:
        assert w not in src, w


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    failed = []
    for fn in tests:
        try:
            fn()
            print("  OK  " + fn.__name__)
        except Exception as exc:
            failed.append(fn.__name__)
            print("  FAIL " + fn.__name__ + ": " + type(exc).__name__ + ": " + str(exc))
    print("\ntest_poller_uniqueness_doctor: %d/%d" % (len(tests) - len(failed), len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
