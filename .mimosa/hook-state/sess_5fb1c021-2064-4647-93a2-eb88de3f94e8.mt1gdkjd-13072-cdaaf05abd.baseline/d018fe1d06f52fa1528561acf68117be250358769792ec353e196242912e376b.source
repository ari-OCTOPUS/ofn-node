#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_circuit_reset_not_recovery — invariant «ریست ≠ ریکاوری» (2026-08-16).

شواهد زندهٔ 6h-report: orchestr با state=closed ولی opened_at_ts پر (۱۳:۲۵)،
last_ok_ts=2026-08-12 و پنجرهٔ 20/20 شکست — closeِ واقعی (record_success)
همیشه opened_at را خالی می‌کند؛ این شکل = نوشتهٔ بیرونی/ریستِ جزئی.
فیکس: _target_entry چنین حالتی را به half_open تنزل می‌دهد تا ریکاوری با
تماسِ موفق واقعی اثبات شود.
"""
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("circuit-reset-not-recovery")
sys.path.insert(0, str(ENV["ops"] / "budget"))

import circuit_breaker as cb  # noqa: E402

STATE = Path(tempfile.mkdtemp()) / "circuit-state.json"


def _write_orchestr(state, opened, last_ok="2026-08-12T07:52:59"):
    import json
    STATE.write_text(json.dumps({
        "targets": {"orchestr": {
            "state": state, "fail_count": 0, "success_count": 0,
            "last_fail_ts": None, "last_ok_ts": last_ok,
            "opened_at_ts": opened, "half_open_attempts": 0,
            "consecutive_opens": 0,
            "recent_outcomes": [False] * 20,
        }}}), encoding="utf-8")


def t_reset_shape_demoted_to_half_open():
    _write_orchestr("closed", opened=time.time())
    cb.STATE_PATH = STATE
    r = cb.check("orchestr")
    assert r["state"] == "half_open", r     # نه allow-as-closed
    assert r["allow"] is True, r            # یک probe مجاز — اثبات با تماس


def t_genuine_close_still_works():
    _write_orchestr("closed", opened=None, last_ok="2026-08-16T03:00:00")
    cb.STATE_PATH = STATE
    r = cb.check("orchestr")
    assert r["state"] == "closed" and r["allow"] is True, r


def t_recovery_must_be_proven_by_success():
    _write_orchestr("closed", opened=time.time())
    cb.STATE_PATH = STATE
    cb.check("orchestr")                       # تنزل به half_open
    cb.record_failure("orchestr", "probe failed")
    r = cb.check("orchestr")
    assert r["state"] in ("open", "half_open"), r   # شکستِ probe ⇒ باز، نه closed
    # جریان واقعی ریکاوری: cooldown بگذرد → half_open → دو موفقیت ⇒ close اثباتی
    import json, ast

    def _read_t():
        d = json.loads(STATE.read_text(encoding="utf-8"))
        t = d["targets"]["orchestr"]
        return ast.literal_eval(t) if isinstance(t, str) else t

    def _write_t(t):
        d = json.loads(STATE.read_text(encoding="utf-8"))
        was_str = isinstance(d["targets"]["orchestr"], str)
        d["targets"]["orchestr"] = repr(t) if was_str else t
        STATE.write_text(json.dumps(d), encoding="utf-8")

    t = _read_t()
    t["opened_at_ts"] = time.time() - 7200     # cooldown گذشته
    _write_t(t)
    cb.check("orchestr")                       # open → half_open
    cb.record_success("orchestr")
    cb.record_success("orchestr")
    t2 = _read_t()
    assert t2["state"] == "closed", t2
    assert t2["opened_at_ts"] is None, t2
    assert str(t2["last_ok_ts"] or "").startswith("2026-08-1"), t2


def t_idempotent_rederivation():
    _write_orchestr("closed", opened=time.time())
    cb.STATE_PATH = STATE
    for _ in range(3):
        r = cb.check("orchestr")
        assert r["state"] == "half_open", r   # هر بار همان استنتاج، بدون جهش


CHECKS = [
    ("شکلِ ریست ⇒ half_open (نه allow-as-closed)", t_reset_shape_demoted_to_half_open),
    ("closeِ واقعی دست‌نخورده", t_genuine_close_still_works),
    ("ریکاوری فقط با تماسِ موفق اثبات می‌شود", t_recovery_must_be_proven_by_success),
    ("استنتاج idempotent", t_idempotent_rederivation),
]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    sys.exit(1 if failed else 0)
