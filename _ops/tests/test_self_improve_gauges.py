#!/usr/bin/env python3
"""test_self_improve_gauges — vitals دروغِ «همیشه سبز» نمی‌سازند."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("self-improve-gauges")

from pathlib import Path as _P  # noqa: E402
_CORTEX = str(_P(__file__).resolve().parent.parent / "cortex")
if _CORTEX not in sys.path:
    sys.path.insert(0, _CORTEX)

import opslib  # noqa: E402
import self_improve_gauges as g  # noqa: E402


NOW = datetime(2026, 8, 16, 5, 0, tzinfo=timezone.utc)


def _write_verdicts(rows):
    p = opslib.STATE_DIR / "test_cycle" / "verdicts.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", "utf-8")


def t_all_fail_is_zero_not_green():
    """کنترل منفی: ۲۴ FAIL نباید rate_pct>0 یا n_keys_passed>0 بدهد."""
    g._STATE = opslib.STATE_DIR
    _write_verdicts([
        {"schema": "cycle_verdict.v1", "ts": "2026-08-16T00:00:00+00:00",
         "goal_key": "abc", "verdict": "FAIL"},
        {"schema": "cycle_verdict.v1", "ts": "2026-08-16T12:00:00+00:00",
         "goal_key": "abc", "verdict": "FAIL"},
    ])
    close = g.goal_loop_close_7d(NOW)
    moved = g.internal_goals_moved_7d(NOW)
    assert close["n"] == 2 and close["n_pass"] == 0 and close["rate_pct"] == 0.0
    assert moved["n_keys_passed"] == 0


def t_a_pass_moves_the_gauge():
    g._STATE = opslib.STATE_DIR
    _write_verdicts([
        {"schema": "cycle_verdict.v1", "ts": "2026-08-16T00:00:00+00:00",
         "goal_key": "abc", "verdict": "FAIL"},
        {"schema": "cycle_verdict.v1", "ts": "2026-08-16T12:00:00+00:00",
         "goal_key": "abc", "verdict": "PASS"},
    ])
    close = g.goal_loop_close_7d(NOW)
    moved = g.internal_goals_moved_7d(NOW)
    assert close["n_pass"] == 1 and close["rate_pct"] == 50.0
    assert moved["n_keys_passed"] == 1


def t_old_verdicts_are_outside_the_window():
    g._STATE = opslib.STATE_DIR
    old = (NOW - timedelta(days=20)).isoformat()
    _write_verdicts([
        {"schema": "cycle_verdict.v1", "ts": old, "goal_key": "abc",
         "verdict": "PASS"},
    ])
    close = g.goal_loop_close_7d(NOW)
    assert close["n"] == 0 and close["rate_pct"] is None


def t_snapshot_is_read_only():
    g._STATE = opslib.STATE_DIR
    before = list((opslib.STATE_DIR).rglob("*"))
    g.snapshot(now=NOW)
    after = list((opslib.STATE_DIR).rglob("*"))
    assert after == before


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_self_improve_gauges: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
