#!/usr/bin/env python3
"""test_phi_reset_on_restart.py — لوپِ ری‌استارتِ بی‌فایدهٔ lead-naghshi.

گواهِ باگ: selfheal-events.jsonl نشان می‌داد lead-naghshi در سه beatِ پشتِ سرِ
هم failed شد (phi ۱۹.۸ → ۲۵.۶ → ۳۱.۹) با وجودِ restart در هر بار — چون
`restart_from_known_good` فقط `leg.state` را ریست می‌کرد و `PhiAccrual.arrivals`
(تاریخچهٔ ackِ مسموم) را دست نمی‌زد. beatِ بعد phi را از همان arrivals محاسبه
می‌کرد و leg بلافاصله دوباره failed می‌شد.

این تست ادعا می‌کند:
  الف) `PhiAccrual.reset()` تاریخچه را پاک می‌کند و phi به ۰ (bootstrap) برمی‌گردد.
  ب) بعد از یک restartِ واقعی در `beat_once`، beatِ بعد phi را از تاریخچهٔ پاک‌شده
     محاسبه می‌کند → leg در همان سکوتِ قبلی alive می‌ماند (نه failed).
  ج) doctor.restarts فقط یک‌بار ثبت می‌شود (نه لوپ).
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

_TMP = Path(tempfile.mkdtemp(prefix="oct-phi-reset-"))
_FAKE_OPS = _TMP / "_ops"
_FAKE_STATE = _FAKE_OPS / "state"
_FAKE_STATE.mkdir(parents=True, exist_ok=True)

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

fails = []


def check(cond, msg):
    if cond:
        print(f"  ✅ {msg}")
    else:
        fails.append(msg)
        print(f"  ❌ {msg}")


# ═══ الف) PhiAccrual.reset() ════════════════════════════════════════════════
acc = chrono.PhiAccrual(window=20)
t0 = 1_700_000_000_000
acc.heard(t0)
acc.heard(t0 + 1000)               # دو ack → phi قابل‌محاسبه
_now = t0 + 10_000_000
phi_before = acc.phi(_now)
check(phi_before > 0, f"phi قبل از reset بالا است (phi={phi_before:.1f})")

acc.reset(t0 + 10_000_000)          # ریست + یک ackِ تولدِ جدید
phi_after = acc.phi(t0 + 10_000_000 + 500)
check(phi_after == 0.0, f"phi بعد از reset صفر است (bootstrap، phi={phi_after})")
check(len(acc.arrivals) == 1, "arrivals فقط یک ackِ تولد دارد بعد از reset")


# ═══ ب/ج) beat_once: restart → beatِ بعد alive ═════════════════════════════
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
        leg.state = "alive"
        leg.hlc = (0, 0)


_clk = [t0]
db = chrono.ChronoDB(_FAKE_STATE / "chrono.db")
bus = chrono.ChronoBus(lambda: _clk[0])
doctor = _MockDoctor()
pm = chrono.Pacemaker(db=db, bus=bus, period_s=60.0, clock=lambda: _clk[0],
                      doctor=doctor, ledger=_FakeLedger())
leg = bus.register_leg("loop-leg")
bus.phi["loop-leg"].heard(_clk[0] + 1000)        # ack دوم → پنجرهٔ باریک
_clk[0] += 10_000_000                              # سکونِ عظیم

os.environ["OCTOPUS_WIRE_SELFHEAL"] = "1"
try:
    pm.beat_once()                                 # beat 1 → failed + restart
finally:
    os.environ.pop("OCTOPUS_WIRE_SELFHEAL", None)

check(doctor.restarts == ["loop-leg"], "beat 1: یک restart صدا زده شد")

# روستِ مدعی: بدونِ فیکس، arrivals هنوز قدیمی است و phi دوباره بالا → failed.
# با فیکس، arrivals پاک شده + یک ackِ تولد → phi=0 → alive.
leg_state_after_beat1 = bus.legs["loop-leg"].state
_clk[0] += 10_000_000                              # سکوتِ بزرگِ دیگر
try:
    pm.beat_once()                                 # beat 2
except Exception:
    pass

leg_state_after_beat2 = bus.legs["loop-leg"].state
check(leg_state_after_beat2 == "alive",
      f"beat 2: leg بعد از restart زنده ماند (state={leg_state_after_beat2})")
check(doctor.restarts == ["loop-leg"],
      "beat 2: دوباره restart نشد (لوپ شکست — فقط یک restart کلِ تاریخچه)")

try:
    db.close()
except Exception:  # noqa: BLE001
    pass

print(f"\n{'PASS' if not fails else 'FAIL'} — test_phi_reset_on_restart")
for f in fails:
    print(f"  - {f}")
sys.exit(1 if fails else 0)
