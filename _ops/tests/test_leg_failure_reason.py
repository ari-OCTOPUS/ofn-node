#!/usr/bin/env python3
"""test_leg_failure_reason.py — T3 (2026-07-25): حلقهٔ self-healِ کور → باعلت.

گواه: selfheal-events.jsonl = ۶۶ ری‌استارت (۱۰۰٪ lead-naghshi)، ۳۸ فاصله در باندِ
۶۱ ثانیه، و هیچ‌جا علت ثبت نمی‌شد. این تست ادعا می‌کند:
  الف) مسیرِ phi-timeout (chrono): فایلِ state/legs/<leg>-last-failure.json ساخته
       می‌شود با reason=phi-timeout:no-ack و context کامل؛ ردیفِ selfheal-events
       فیلدِ reason/phi دارد؛ و restart_from_known_good همچنان صدا زده می‌شود
       (رفتارِ self-heal دست‌نخورده).
  ب) مسیرِ استثنا (wiring.leg_beat): لِگی که raise می‌کند →
       state/legs/<leg>-last-error.json با error_type + frame؛ و None برمی‌گردد
       (tick نمی‌میرد).
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

_TMP = Path(tempfile.mkdtemp(prefix="oct-t3-legs-"))
_FAKE_OPS = _TMP / "_ops"
_FAKE_STATE = _FAKE_OPS / "state"
_FAKE_STATE.mkdir(parents=True, exist_ok=True)

# sandbox کامل — همهٔ ثابت‌های مسیر که در import بایند شده‌اند
opslib.ORG_ROOT = _TMP
opslib.OPS = _FAKE_OPS
opslib.STATE_DIR = _FAKE_STATE
opslib.ALERTS_MD = _FAKE_OPS / "governor" / "governor-alerts.md"
opslib.STOP_ORGANISM = _FAKE_OPS / "STOP-ORGANISM"
opslib.STOP_METABOLIC = _FAKE_OPS / "STOP-METABOLIC"
opslib.HALT_ALL = _FAKE_OPS / "HALT-ALL"
opslib.STOP_ARCHITECT = _TMP / "04 - Architect System" / "STOP"
opslib.FREEZE_FLAG = _FAKE_OPS / "budget" / "FREEZE.flag"

import chrono  # noqa: E402
import wiring  # noqa: E402

fails = []


def check(cond, msg):
    if cond:
        print(f"  ✅ {msg}")
    else:
        fails.append(msg)
        print(f"  ❌ {msg}")


# ═══ الف) مسیرِ chrono: phi-timeout ═══════════════════════════════════════════
class _FakeLedger:
    def last_hash(self):
        return "0" * 64

    def last_age_tick(self):
        return 0


class _MockDoctor:
    def __init__(self):
        self.restarts = []

    def restart_from_known_good(self, leg, db):
        self.restarts.append(getattr(leg, "id", "?"))
        # رفتارِ واقعی: لِگ را به حالتِ زنده برمی‌گرداند
        leg.state = "alive"


_now = [1_700_000_000_000]


def _clock():
    return _now[0]


db = chrono.ChronoDB(_FAKE_STATE / "chrono.db")
bus = chrono.ChronoBus(_clock)
doctor = _MockDoctor()
pm = chrono.Pacemaker(db=db, bus=bus, period_s=60.0, clock=_clock,
                      doctor=doctor, ledger=_FakeLedger())
leg = bus.register_leg("test-leg")            # یک ackِ تولد (phi=0 در bootstrap)
bus.phi["test-leg"].heard(_now[0] + 1000)     # ack دوم → فاصلهٔ ۱s (پنجرهٔ باریک)
_now[0] += 10_000_000                          # سکونِ عظیم → phi بسیار بالا

os.environ["OCTOPUS_WIRE_SELFHEAL"] = "1"
try:
    pm.beat_once()
finally:
    os.environ.pop("OCTOPUS_WIRE_SELFHEAL", None)

ff = _FAKE_STATE / "legs" / "test-leg-last-failure.json"
check(ff.exists(), "last-failure.json ساخته شد (مسیرِ phi-timeout)")
if ff.exists():
    ctx = json.loads(ff.read_text("utf-8"))
    check(ctx.get("reason") == "phi-timeout:no-ack", "علتِ صادق: phi-timeout:no-ack")
    check(isinstance(ctx.get("phi"), (int, float)) and ctx["phi"] > 0, "phi ثبت شد")
    check(ctx.get("silence_ms") and ctx["silence_ms"] > 9_000_000,
          "silence_ms واقعی ثبت شد")
    check(ctx.get("beat") == 1, "beat ثبت شد")

she = _FAKE_STATE / "selfheal-events.jsonl"
check(she.exists(), "selfheal-events.jsonl نوشته شد")
if she.exists():
    rows = [json.loads(x) for x in she.read_text("utf-8").splitlines() if x.strip()]
    check(len(rows) == 1, "دقیقاً یک ردیفِ selfheal")
    if rows:
        check(rows[0].get("reason") == "phi-timeout:no-ack",
              "ردیفِ selfheal فیلدِ reason دارد (قبلاً فقط {leg,ts} بود)")
        check("phi" in rows[0], "ردیفِ selfheal فیلدِ phi دارد")
check(doctor.restarts == ["test-leg"], "restart_from_known_good صدا زده شد (رفتارِ self-heal دست‌نخورده)")

ev = _FAKE_STATE / "events.jsonl"
check(ev.exists(), "events.jsonl در sandbox نوشته شد (نه درختِ زنده)")
if ev.exists():
    evs = [json.loads(x) for x in ev.read_text("utf-8").splitlines() if x.strip()]
    blocked = [e for e in evs if e.get("event_name") == "task.blocked"]
    check(len(blocked) == 1, "یک رویدادِ task.blocked")
    if blocked:
        check("last-failure.json" in str(blocked[0].get("next_action", "")),
              "task.blocked به فایلِ علت اشاره می‌کند")
        check("phi=" in str(blocked[0].get("summary", "")),
              "خلاصهٔ task.blocked phi را دارد")

# ═══ ب) مسیرِ wiring: استثنا ═════════════════════════════════════════════════
class _FakePacket:
    leg_id = "boom-leg"


class _FakeLeg:
    packet = _FakePacket()


class _BadBus:
    def register_leg(self, leg_id):
        raise RuntimeError("bus exploded")


class _FakePM:
    bus = _BadBus()


os.environ["OCTOPUS_WIRE_LEAD_TICK"] = "1"
try:
    r = wiring.leg_beat(_FakeLeg(), pacemaker=_FakePM(), beat=5)
finally:
    os.environ.pop("OCTOPUS_WIRE_LEAD_TICK", None)

check(r is None, "leg_beat با لِگِ معیوب None برمی‌گردد (tick نمرد)")
ef = _FAKE_STATE / "legs" / "boom-leg-last-error.json"
check(ef.exists(), "last-error.json ساخته شد (مسیرِ استثنا)")
if ef.exists():
    ectx = json.loads(ef.read_text("utf-8"))
    check(ectx.get("error_type") == "RuntimeError", "error_type ثبت شد")
    check("bus exploded" in str(ectx.get("error", "")), "پیامِ خطا ثبت شد")
    check(isinstance(ectx.get("frame"), str) and "register_leg" in ectx["frame"],
          "آخرین فریمِ stack ثبت شد")

try:
    db.close()
except Exception:  # noqa: BLE001
    pass

print(f"\n{'PASS' if not fails else 'FAIL'} — test_leg_failure_reason")
for f in fails:
    print(f"  - {f}")
sys.exit(1 if fails else 0)
