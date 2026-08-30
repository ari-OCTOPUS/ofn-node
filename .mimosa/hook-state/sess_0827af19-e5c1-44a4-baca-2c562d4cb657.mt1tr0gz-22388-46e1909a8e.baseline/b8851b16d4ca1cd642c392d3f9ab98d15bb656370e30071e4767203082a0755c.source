#!/usr/bin/env python3
"""test_selfheal_ok_field — continuous-F: رویدادِ خودترمیمی فیلدِ ok دارد.

قبل: ۸۳ ردیف زنده، صفرتای آن‌ها `ok` داشتند؛ مقدار برگشتی
restart_from_known_good نادیده گرفته می‌شد و task.completed حتی روی شکست
ادعا می‌شد. None از mockهای قدیمی همچنان موفقیت است (رگرسیون phi-reset).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
sys.path.insert(0, str(OPS))
sys.path.insert(0, str(OPS / "budget"))

import opslib  # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="oct-selfheal-ok-"))
_FAKE_OPS = _TMP / "_ops"
_FAKE_STATE = _FAKE_OPS / "state"
_FAKE_STATE.mkdir(parents=True, exist_ok=True)

opslib.ORG_ROOT = _TMP
opslib.OPS = _FAKE_OPS
opslib.STATE_DIR = _FAKE_STATE
opslib.ALERTS_MD = _FAKE_OPS / "governor" / "governor-alerts.md"
opslib.ALERTS_MD.parent.mkdir(parents=True, exist_ok=True)

import chrono  # noqa: E402

fails: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        fails.append(msg)


class _FakeLedger:
    def last_hash(self):
        return "0" * 64

    def last_age_tick(self):
        return 0


class _Doctor:
    def __init__(self, ret):
        self.ret = ret
        self.n = 0

    def restart_from_known_good(self, leg, db):
        self.n += 1
        if self.ret is not False:
            leg.state = "alive"
        return self.ret


def _one_fail_cycle(ret):
    t0 = 1_000_000.0
    clk = [t0]
    db = chrono.ChronoDB(_FAKE_STATE / f"chrono-{id(ret)}.db")
    bus = chrono.ChronoBus(lambda: clk[0])
    doctor = _Doctor(ret)
    pm = chrono.Pacemaker(db=db, bus=bus, period_s=60.0, clock=lambda: clk[0],
                          doctor=doctor, ledger=_FakeLedger())
    bus.register_leg("loop-leg")
    bus.phi["loop-leg"].heard(clk[0] + 1000)
    clk[0] += 10_000_000
    os.environ["OCTOPUS_WIRE_SELFHEAL"] = "1"
    try:
        pm.beat_once()
    finally:
        os.environ.pop("OCTOPUS_WIRE_SELFHEAL", None)
    try:
        db.close()
    except Exception:  # noqa: BLE001
        pass
    p = _FAKE_STATE / "selfheal-events.jsonl"
    rows = []
    if p.exists():
        rows = [json.loads(l) for l in p.read_text("utf-8").splitlines() if l.strip()]
        p.unlink()
    return doctor.n, rows


n_none, rows_none = _one_fail_cycle(None)
check(n_none == 1, "None (mock قدیمی) همچنان restart را صدا می‌زند")
check(len(rows_none) == 1, f"یک رویداد برای None، شد {len(rows_none)}")
check(rows_none and rows_none[-1].get("ok") is True,
      f"None → ok=True (سازگاری)، شد {rows_none}")

n_true, rows_true = _one_fail_cycle(True)
check(n_true == 1 and rows_true and rows_true[-1].get("ok") is True,
      f"True → ok=True، شد {rows_true}")

n_false, rows_false = _one_fail_cycle(False)
check(n_false == 1, "False هم restart را صدا می‌زند")
check(rows_false and rows_false[-1].get("ok") is False,
      f"False → ok=False، شد {rows_false}")

print(f"\n{'PASS' if not fails else 'FAIL'} — test_selfheal_ok_field")
for f in fails:
    print(f"  - {f}")
sys.exit(1 if fails else 0)
