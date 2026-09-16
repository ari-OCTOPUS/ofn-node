#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Heartbeat path invokes poller uniqueness in dry-run (no live Telegram)."""
from __future__ import annotations

import importlib
import json
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
    root = Path(tempfile.mkdtemp(prefix="doc-uniq-hb-"))
    state = root / "state"
    state.mkdir(parents=True, exist_ok=True)
    os.environ["OCTOPUS_STATE_DIR"] = str(state)
    os.environ["OCTOPUS_WIRE_DOCTOR_UNIQUENESS"] = "1"
    os.environ["CHRONO_DOCTOR_UNIQUENESS_EVERY_N_BEATS"] = "1"
    return root, state


def t_a_heartbeat_invokes_uniqueness_dry_run():
    import poller_uniqueness as pu
    import wiring

    pu = importlib.reload(pu)
    wiring = importlib.reload(wiring)
    wiring._EPOCH_STATE.clear()

    _, state = _fresh()
    pu.seed_uniqueness_fixture(state, center_pid=424242)

    # beat=1 with every_n=1 → epoch 1 fires
    out = wiring.doctor_uniqueness_beat(
        beat=1,
        state_dir=state,
        dry_run=True,
        center_pids=[424242],
        require_lock_pid_alive=False,
        scan_live_pids=False,
    )
    assert out is not None, "heartbeat returned None (cadence skip?)"
    assert out.get("live_send") is False
    assert out.get("dry_run") is True
    assert out.get("ok") is True, out
    uniq = out.get("poller_uniqueness") or {}
    assert uniq.get("ok") is True, uniq
    assert uniq.get("checks", {}).get("one_center_pid") is True
    assert uniq.get("checks", {}).get("one_active_lease") is True
    assert uniq.get("checks", {}).get("one_tg_poller_lock") is True
    assert uniq.get("checks", {}).get("pids_agree") is True

    latest = state / "doctor" / "poller-uniqueness-latest.json"
    assert latest.is_file(), latest
    rec = json.loads(latest.read_text(encoding="utf-8"))
    assert rec.get("schema") == "poller-uniqueness-receipt/1"
    assert rec.get("live_send") is False
    assert rec.get("ok") is True
    assert rec.get("source") == "doctor_uniqueness_beat"
    assert rec.get("beat") == 1

    log = state / "doctor" / "poller-uniqueness.jsonl"
    assert log.is_file()
    lines = [ln for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 1


def t_b_fail_closed_records_receipt():
    import poller_uniqueness as pu
    import wiring

    pu = importlib.reload(pu)
    wiring = importlib.reload(wiring)
    wiring._EPOCH_STATE.clear()

    _, state = _fresh()
    pu.seed_uniqueness_fixture(state, center_pid=111, extra_active_leases=1)

    out = wiring.doctor_uniqueness_beat(
        beat=1,
        state_dir=state,
        dry_run=True,
        center_pids=[111],
        require_lock_pid_alive=False,
        scan_live_pids=False,
    )
    assert out is not None
    assert out.get("live_send") is False
    assert out.get("ok") is False, out
    latest = state / "doctor" / "poller-uniqueness-latest.json"
    rec = json.loads(latest.read_text(encoding="utf-8"))
    assert rec.get("ok") is False
    assert rec.get("live_send") is False


def t_c_opt_out_flag_skips():
    import wiring

    wiring = importlib.reload(wiring)
    wiring._EPOCH_STATE.clear()
    _, state = _fresh()
    os.environ["OCTOPUS_WIRE_DOCTOR_UNIQUENESS"] = "0"
    out = wiring.doctor_uniqueness_beat(beat=1, state_dir=state, dry_run=True, center_pids=[1])
    assert out is None


def t_d_cadence_skips_same_epoch():
    import poller_uniqueness as pu
    import wiring

    pu = importlib.reload(pu)
    wiring = importlib.reload(wiring)
    wiring._EPOCH_STATE.clear()
    _, state = _fresh()
    os.environ["CHRONO_DOCTOR_UNIQUENESS_EVERY_N_BEATS"] = "60"
    pu.seed_uniqueness_fixture(state, center_pid=424242)
    first = wiring.doctor_uniqueness_beat(
        beat=60, state_dir=state, dry_run=True, center_pids=[424242],
        require_lock_pid_alive=False, scan_live_pids=False,
    )
    second = wiring.doctor_uniqueness_beat(
        beat=61, state_dir=state, dry_run=True, center_pids=[424242],
        require_lock_pid_alive=False, scan_live_pids=False,
    )
    assert first is not None
    assert second is None  # same epoch


def t_e_organism_source_calls_beat():
    src = (_OPS / "organism.py").read_text(encoding="utf-8")
    assert "doctor_uniqueness_beat" in src
    wsrc = (_OPS / "wiring.py").read_text(encoding="utf-8")
    assert "def doctor_uniqueness_beat(" in wsrc
    assert '_epoch_fire("doctor_uniqueness"' in wsrc


def t_f_no_live_send_symbols_in_heartbeat_module():
    src = (_DOC / "uniqueness_heartbeat.py").read_text(encoding="utf-8")
    for w in ("sendMessage", "Bot API", "api.telegram.org", "getUpdates"):
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
    print("\ntest_doctor_uniqueness_heartbeat: %d/%d" % (len(tests) - len(failed), len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
