#!/usr/bin/env python3
"""Canary window guard — strict sequence, duplicates never advance."""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "telegram_center"))


def _fresh():
    root = Path(tempfile.mkdtemp(prefix="canary-window-"))
    os.environ["OCTOPUS_STATE_DIR"] = str(root / "_ops" / "state")
    import canary_window as cw
    cw = importlib.reload(cw)
    return cw, root


def t_a_open_window_mints_nonce_and_id():
    cw, root = _fresh()
    w = cw.open_window("CANARY-TEST")
    assert w["ok"] and w["canary_id"] == "CANARY-TEST" and len(w["nonce"]) == 16
    again = cw.open_window("CANARY-X")
    assert again["ok"] is False and again["reason"] == "window_already_open"


def t_b_strict_sequence_advances():
    cw, root = _fresh()
    cw.open_window("CANARY-TEST")
    for i, cmd in enumerate(cw.SEQUENCE):
        r = cw.observe(f"{cmd} something", update_id=100 + i, now=1000 + i)
        assert r["decision"] == "ACCEPTED", (cmd, r)
        assert r["row"]["update_id"] == 100 + i
    st = cw.window_status()
    assert st["completed"] is True and st["open"] is False


def t_c_duplicate_is_recorded_and_does_not_advance():
    cw, root = _fresh()
    cw.open_window("CANARY-TEST")
    first = cw.observe("CANARY-01 STATUS", update_id=1, now=1.0)
    assert first["decision"] == "ACCEPTED"
    dup = cw.observe("CANARY-01 STATUS", update_id=2, now=2.0)
    assert dup["decision"] == "DUPLICATE" and dup["ok"] is False
    st = cw.window_status()
    assert st["next_index"] == 1 and st["next_expected"] == "CANARY-02"


def t_d_out_of_order_is_rejected_without_advance():
    cw, root = _fresh()
    cw.open_window("CANARY-TEST")
    r = cw.observe("CANARY-03 MEMORY-STATUS", update_id=3, now=1.0)
    assert r["decision"] == "OUT_OF_ORDER" and r["row"]["expected"] == "CANARY-01"
    st = cw.window_status()
    assert st["next_index"] == 0


def t_e_unlabelled_text_is_unknown_no_advance():
    cw, root = _fresh()
    cw.open_window("CANARY-TEST")
    r = cw.observe("hello free text", update_id=4, now=1.0)
    assert r["decision"] == "UNKNOWN"
    assert cw.window_status()["next_index"] == 0


def t_f_no_window_rejects():
    cw, root = _fresh()
    r = cw.observe("CANARY-01 STATUS", update_id=5, now=1.0)
    assert r["decision"] == "NO_WINDOW"


def t_g_repeated_update_id_is_duplicate_no_advance():
    cw, root = _fresh()
    cw.open_window("CANARY-TEST")
    first = cw.observe("CANARY-01 STATUS", update_id=1, now=1.0)
    assert first["decision"] == "ACCEPTED"
    replay = cw.observe("CANARY-02 LOOPS", update_id=1, now=2.0)
    assert replay["decision"] == "DUPLICATE"
    assert replay["row"]["reason"] == "repeat_update_id"
    st = cw.window_status()
    assert st["next_index"] == 1 and st["next_expected"] == "CANARY-02"


def t_h_skipped_03_is_out_of_order_then_03_accepted():
    cw, root = _fresh()
    cw.open_window("CANARY-TEST")
    assert cw.observe("CANARY-01 STATUS", update_id=1, now=1.0)["decision"] == "ACCEPTED"
    assert cw.observe("CANARY-02 LOOPS", update_id=2, now=2.0)["decision"] == "ACCEPTED"
    skip = cw.observe("CANARY-04 RECEIPT-CHECK", update_id=4, now=3.0)
    assert skip["decision"] == "OUT_OF_ORDER" and skip["row"]["expected"] == "CANARY-03"
    ok = cw.observe("CANARY-03 MEMORY-STATUS", update_id=3, now=4.0)
    assert ok["decision"] == "ACCEPTED"
    assert cw.window_status()["next_index"] == 3


def t_i_repeated_04_is_duplicate_no_advance():
    cw, root = _fresh()
    cw.open_window("CANARY-TEST")
    for i, cmd in enumerate(["CANARY-01 STATUS", "CANARY-02 LOOPS",
                             "CANARY-03 MEMORY-STATUS", "CANARY-04 RECEIPT-CHECK"]):
        assert cw.observe(cmd, update_id=100 + i, now=1000 + i)["decision"] == "ACCEPTED"
    dup = cw.observe("CANARY-04 RECEIPT-CHECK", update_id=200, now=2000.0)
    assert dup["decision"] == "DUPLICATE" and dup["row"]["reason"] == "repeat_command"
    st = cw.window_status()
    assert st["next_index"] == 4 and st["next_expected"] == "CANARY-05"


def t_j_restart_after_step_02_resumes_durably():
    cw, root = _fresh()
    cw.open_window("CANARY-TEST")
    assert cw.observe("CANARY-01 STATUS", update_id=1, now=1.0)["decision"] == "ACCEPTED"
    assert cw.observe("CANARY-02 LOOPS", update_id=2, now=2.0)["decision"] == "ACCEPTED"
    # restart: module reload with the same durable state dir
    import importlib
    cw = importlib.reload(cw)
    assert cw.window_status()["next_index"] == 2
    assert cw.observe("CANARY-03 MEMORY-STATUS", update_id=3, now=3.0)["decision"] == "ACCEPTED"
    assert cw.observe("CANARY-04 RECEIPT-CHECK", update_id=4, now=4.0)["decision"] == "ACCEPTED"
    assert cw.observe("CANARY-05 CLOSE", update_id=5, now=5.0)["decision"] == "ACCEPTED"
    st = cw.window_status()
    assert st["completed"] is True and st["open"] is False


def t_k_close_before_completion_is_out_of_order():
    cw, root = _fresh()
    cw.open_window("CANARY-TEST")
    r = cw.observe("CANARY-05 CLOSE", update_id=5, now=1.0)
    assert r["decision"] == "OUT_OF_ORDER" and r["row"]["expected"] == "CANARY-01"
    st = cw.window_status()
    assert st["open"] is True and st["completed"] is False and st["next_index"] == 0


def t_l_event_after_window_closure_is_no_window():
    cw, root = _fresh()
    cw.open_window("CANARY-TEST")
    for i, cmd in enumerate(cw.SEQUENCE):
        assert cw.observe(cmd, update_id=100 + i, now=1000 + i)["decision"] == "ACCEPTED"
    r = cw.observe("CANARY-01 STATUS", update_id=200, now=2000.0)
    assert r["decision"] == "NO_WINDOW"


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
    print(f"\ntest_canary_window: {len(tests) - failed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
