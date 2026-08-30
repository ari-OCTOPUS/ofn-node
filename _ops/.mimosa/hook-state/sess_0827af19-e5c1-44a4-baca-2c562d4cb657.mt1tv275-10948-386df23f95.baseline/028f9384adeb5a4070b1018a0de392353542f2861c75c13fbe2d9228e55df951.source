#!/usr/bin/env python3
"""Unit 3 — orphan watchdog: detect alive-child/dead-parent without touching a healthy child."""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))


def _fresh():
    root = Path(tempfile.mkdtemp(prefix="orphan-watchdog-"))
    os.environ["OCTOPUS_STATE_DIR"] = str(root / "_ops" / "state")
    import orphan_watchdog as w
    w = importlib.reload(w)
    return w, root


def _rows(gateway_pid=100, gateway_parent=50, parent_alive=True):
    rows = []
    if parent_alive:
        rows.append({"Pid": 50, "Parent": 1, "Cmd": "launcher"})
    rows.append({"Pid": 100, "Parent": 50,
                 "Cmd": "python -X utf8 telegram_center\\miniapp_gateway.py"})
    return rows


def t_a_healthy_gateway_no_receipt_no_action():
    w, root = _fresh()
    rep = w.tick(rows=_rows(), state={}, now=1000.0)
    assert rep["states"] == {"HEALTHY": 1, "ORPHAN": 0}, rep
    assert rep["actions"] == [], rep
    assert not w.receipts_path().exists() or len(
        w.receipts_path().read_text(encoding="utf-8").splitlines()) == 0


def t_b_orphan_child_is_reported_never_restarted():
    w, root = _fresh()
    rep = w.tick(rows=_rows(parent_alive=False), state={}, now=1000.0)
    assert rep["states"] == {"HEALTHY": 0, "ORPHAN": 1}, rep
    kinds = [a["kind"] for a in rep["actions"]]
    assert "orphan_receipt" in kinds and "restart" not in kinds, rep
    assert "restart" not in str(rep), "healthy/orphan child must never be restarted"
    recs = [json.loads(x) for x in w.receipts_path().read_text(encoding="utf-8").splitlines()]
    assert recs and recs[0]["kind"] == "orphan_receipt"


def t_c_missing_gateway_restarts_within_budget():
    w, root = _fresh()
    # gateway absent from rows entirely (dead child)
    rows = [{"Pid": 50, "Parent": 1, "Cmd": "launcher"}]
    rep = w.tick(rows=rows, state={}, now=1000.0)
    kinds = [a["kind"] for a in rep["actions"]]
    assert "restart" in kinds, rep
    st = json.loads(w.state_path().read_text(encoding="utf-8"))
    assert st["restarts"] == 1


def t_d_budget_exhaustion_blocks_restart_storm():
    w, root = _fresh()
    rows = [{"Pid": 50, "Parent": 1, "Cmd": "launcher"}]
    state = {"window_start": 0.0, "restarts": w.RESTART_MAX,
             "last_restart_ts": 0.0, "cooldown_until": 0.0}
    rep = w.tick(rows=rows, state=state, now=2000.0)
    kinds = [a["kind"] for a in rep["actions"]]
    assert "restart_blocked" in kinds and "restart" not in kinds, rep
    assert rep["actions"][0]["reason"] == "budget_exhausted"


def t_e_cooldown_blocks_immediate_second_restart():
    w, root = _fresh()
    rows = [{"Pid": 50, "Parent": 1, "Cmd": "launcher"}]
    state = {"window_start": 0.0, "restarts": 1,
             "last_restart_ts": 0.0, "cooldown_until": 1500.0}
    rep = w.tick(rows=rows, state=state, now=1000.0)
    kinds = [a["kind"] for a in rep["actions"]]
    assert "restart_blocked" in kinds and "restart" not in kinds, rep
    assert rep["actions"][0]["reason"] == "cooldown"


def t_f_receipts_are_append_only_with_timestamp():
    w, root = _fresh()
    w.tick(rows=_rows(parent_alive=False), state={}, now=1000.0)
    w.tick(rows=_rows(parent_alive=False), state={}, now=1001.0)
    lines = w.receipts_path().read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["ts"] == 1000.0


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
    print(f"\ntest_orphan_watchdog: {len(tests) - failed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
