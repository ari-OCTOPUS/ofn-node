#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_circuit_demote_persist_errorhunt — تنزلِ ریست باید روی دیسک بماند.

ERRORHUNT 2026-08-16: `_target_entry` شکلِ closed+opened_at را به half_open
تنزل می‌داد ولی فایل را نمی‌نوشت ⇒ `circuit-state.json` و `status()` دروغِ
«سالم» می‌گفتند. این تست persist را قفل می‌کند. ثبت در run_all: گزارش شود
(WORKLOCK — این فایل خودش را ثبت نمی‌کند).
"""
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("circuit-demote-persist-errorhunt")
sys.path.insert(0, str(ENV["ops"] / "budget"))

import circuit_breaker as cb  # noqa: E402

STATE = Path(tempfile.mkdtemp()) / "circuit-state.json"


def _write_orchestr(state, opened, last_ok="2026-08-12T07:52:59"):
    STATE.write_text(json.dumps({
        "targets": {"orchestr": {
            "state": state, "fail_count": 0, "success_count": 0,
            "last_fail_ts": "2026-08-15T13:25:40", "last_ok_ts": last_ok,
            "opened_at_ts": opened, "half_open_attempts": 0,
            "consecutive_opens": 0,
            "recent_outcomes": [False] * 20,
        }}}), encoding="utf-8")


def _disk_state():
    return json.loads(STATE.read_text(encoding="utf-8"))["targets"]["orchestr"]["state"]


def t_check_persists_demotion_to_disk():
    _write_orchestr("closed", opened=time.time())
    cb.STATE_PATH = STATE
    r = cb.check("orchestr")
    assert r["state"] == "half_open", r
    assert _disk_state() == "half_open", _disk_state()


def t_status_also_persists_demotion():
    _write_orchestr("closed", opened=time.time())
    cb.STATE_PATH = STATE
    snap = cb.status("orchestr")
    assert snap["state"] == "half_open", snap
    assert _disk_state() == "half_open", _disk_state()


def t_second_check_stays_half_open_no_reclose():
    _write_orchestr("closed", opened=time.time())
    cb.STATE_PATH = STATE
    cb.check("orchestr")
    r2 = cb.check("orchestr")
    assert r2["state"] == "half_open", r2
    assert _disk_state() == "half_open"


def t_genuine_close_file_untouched():
    _write_orchestr("closed", opened=None, last_ok="2026-08-16T03:00:00")
    cb.STATE_PATH = STATE
    r = cb.check("orchestr")
    assert r["state"] == "closed" and r["allow"] is True, r
    assert _disk_state() == "closed"


CHECKS = [
    ("check ⇒ half_open روی دیسک", t_check_persists_demotion_to_disk),
    ("status ⇒ half_open روی دیسک", t_status_also_persists_demotion),
    ("چک دوم فایل را به closed برنمی‌گرداند", t_second_check_stays_half_open_no_reclose),
    ("close واقعی بدون opened_at دست‌نخورده", t_genuine_close_file_untouched),
]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    sys.exit(1 if failed else 0)
