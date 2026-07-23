#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_beat_scheduler.py — C5: یک ضربان — virtual-time + restart + isolation + no-double-actuation.

پوشش (معیارهای موفقیتِ C5):
  1. ترتیبِ فازِ قطعی: SENSE→…→HEAL صرف‌نظر از ترتیبِ ثبت
  2. every_n_beats: organ فقط در beatهای درست اجرا می‌شود
  3. bounded: overrunِ budget علامت می‌خورد؛ overrunِ مکرر → circuit-breaker quarantine
  4. organ failure isolation: fail یک organ ضربان را نمی‌ایستاند؛ بقیه اجرا می‌شوند
  5. restart continuity: beat_counter durable؛ scheduler نو از beatِ **بعدی** ادامه می‌دهد (نه دوباره)
  6. HALT: زیرِ HALT فقط SENSE/RECORD/HEAL؛ ACT هرگز (fail-closed)
  7. zero double-actuation: فازِ ACT پیش‌فرض dry-run (بدونِ ACT_ARMED)
$0 آفلاین؛ صفر شبکه؛ virtual clock؛ state در sandbox.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("beat-scheduler")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import beat_scheduler as bs  # noqa: E402
import opslib  # noqa: E402

_STATE = Path(str(opslib.STATE_DIR))


class _VClock:
    """virtual-time: زمان فقط با advance جلو می‌رود (قطعی، بدونِ sleep)."""
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t += s


def _sched(tag, clock=None, halted=None):
    sp = _STATE / "pulse" / f"beat-{tag}.json"
    if sp.exists():
        sp.unlink()
    return bs.BeatScheduler(state_path=sp, clock=clock or (lambda: 1000.0),
                            spine=None, halted_fn=halted or (lambda: None)), sp


def _rec(log, name):
    def h(**kw):
        log.append((name, kw["beat"], kw["dry_run"], kw["halt"]))
        return {"ran": name}
    return h


# ── ۱: ترتیبِ فازِ قطعی ──────────────────────────────────────────────────────────
def t_deterministic_phase_order():
    os.environ.pop(bs.ACT_ARMED_FLAG, None)
    sch, _ = _sched("t1")
    log = []
    # عمداً بی‌ترتیب ثبت می‌کنیم
    sch.register_organ("healer", "HEAL", _rec(log, "healer"))
    sch.register_organ("sensor", "SENSE", _rec(log, "sensor"))
    sch.register_organ("thinker", "THINK", _rec(log, "thinker"))
    r = sch.tick()
    assert r["phase_order"] == ["sensor", "thinker", "healer"], r["phase_order"]


# ── ۲: every_n_beats ─────────────────────────────────────────────────────────────
def t_every_n_beats():
    sch, _ = _sched("t2")
    log = []
    sch.register_organ("fast", "THINK", _rec(log, "fast"), every_n_beats=1)
    sch.register_organ("slow", "HEAL", _rec(log, "slow"), every_n_beats=3)
    for _ in range(3):
        sch.tick()
    fast_beats = [b for (n, b, _, _) in log if n == "fast"]
    slow_beats = [b for (n, b, _, _) in log if n == "slow"]
    assert fast_beats == [1, 2, 3] and slow_beats == [3], f"{fast_beats} / {slow_beats}"


# ── ۳: bounded + circuit breaker ────────────────────────────────────────────────
def t_budget_and_circuit_breaker():
    vc = _VClock()
    sch, _ = _sched("t3", clock=vc)

    def slow_handler(**kw):
        vc.advance(2.0)   # ۲۰۰۰ms > budget 100ms → overrun هر بار
        return {}
    sch.register_organ("laggard", "THINK", slow_handler, budget_ms=100)
    quarantined_at = None
    for i in range(1, 7):
        r = sch.tick()
        res = r["results"].get("laggard", {})
        if res.get("skipped") == "quarantined":
            quarantined_at = i
            break
    assert quarantined_at is not None, "overrunِ مکرر باید quarantine شود (circuit breaker)"
    assert quarantined_at <= 5, f"باید تا beat 5 quarantine شود: {quarantined_at}"


# ── ۴: organ failure isolation ──────────────────────────────────────────────────
def t_failure_isolation():
    sch, _ = _sched("t4")
    log = []

    def boom(**kw):
        raise RuntimeError("organ exploded")
    sch.register_organ("bomb", "THINK", boom)
    sch.register_organ("survivor", "LEARN", _rec(log, "survivor"))
    r = sch.tick()
    assert r["results"]["bomb"]["ok"] is False, "organ باید fail کند"
    assert ("survivor", 1, False, None) in log, "ضربان باید ادامه دهد (survivor اجرا شد)"
    assert r["beat"] == 1, "ضربان کامل شد (نایستاد)"


# ── ۵: restart continuity ───────────────────────────────────────────────────────
def t_restart_continuity():
    sch, sp = _sched("t5")
    sch.register_organ("s", "SENSE", lambda **k: None)
    sch.tick(); sch.tick(); sch.tick()   # beats 1,2,3
    assert sch.beat_counter == 3
    # «restart»: scheduler نو با همان state_path
    sch2 = bs.BeatScheduler(state_path=sp, clock=lambda: 1000.0, spine=None,
                            halted_fn=lambda: None)
    log = []
    sch2.register_organ("s", "SENSE", _rec(log, "s"))
    r = sch2.tick()
    assert r["beat"] == 4, f"باید از beatِ بعدی (4) ادامه دهد، نه دوباره 1: {r['beat']}"
    assert log[0][1] == 4, "organ در beat 4 اجرا شد (beat 1-3 دوباره اجرا نشد)"


# ── ۶: HALT — فقط فازهای امن ─────────────────────────────────────────────────────
def t_halt_only_safe_phases():
    sch, _ = _sched("t6", halted=lambda: "HALT-ALL")
    log = []
    sch.register_organ("sensor", "SENSE", _rec(log, "sensor"))
    sch.register_organ("actor", "ACT", _rec(log, "actor"))
    sch.register_organ("healer", "HEAL", _rec(log, "healer"))
    r = sch.tick()
    ran = {n for (n, *_ ) in log}
    assert "sensor" in ran and "healer" in ran, "فازهای امن باید زیرِ HALT اجرا شوند"
    assert "actor" not in ran, "ACT هرگز زیرِ HALT اجرا نمی‌شود (fail-closed)"
    assert r["halted"] == "HALT-ALL"


# ── ۷: zero double-actuation (ACT dry-run پیش‌فرض) ──────────────────────────────
def t_act_is_dry_run_by_default():
    os.environ.pop(bs.ACT_ARMED_FLAG, None)
    sch, _ = _sched("t7")
    seen = {}

    def actor(**kw):
        seen["dry_run"] = kw["dry_run"]
        return {}
    sch.register_organ("effector", "ACT", actor)
    sch.tick()
    assert seen.get("dry_run") is True, "بدونِ ACT_ARMED فازِ ACT باید dry-run باشد (صفر double-actuation)"
    # با ACT_ARMED → واقعی
    os.environ[bs.ACT_ARMED_FLAG] = "1"
    sch.tick()
    assert seen.get("dry_run") is False, "با ACT_ARMED باید واقعی شود"
    os.environ.pop(bs.ACT_ARMED_FLAG, None)


# ── ۸: watchdog — تشخیصِ stall/غیابِ ضربان ─────────────────────────────────────
def t_heartbeat_stall_watchdog():
    sch, sp = _sched("t8", clock=lambda: 5000.0)
    sch.register_organ("s", "SENSE", lambda **k: None)
    sch.tick()   # last_beat_at = 5000
    h1 = bs.BeatScheduler.heartbeat_health(sp, stall_after_s=900, now=5100.0)
    assert h1["alive"] and not h1["stall"] and h1["beat"] == 1, h1
    h2 = bs.BeatScheduler.heartbeat_health(sp, stall_after_s=900, now=9000.0)   # ۴۰۰۰s بعد
    assert h2["stall"] and not h2["alive"], f"باید stall تشخیص دهد: {h2}"
    h3 = bs.BeatScheduler.heartbeat_health(_STATE / "pulse" / "nonexistent.json")
    assert h3["stall"] and "never beat" in h3["reason"], h3


if __name__ == "__main__":
    failed = harness.run([
        ("[۸] watchdog stall detection", t_heartbeat_stall_watchdog),
        ("[۱] ترتیبِ فازِ قطعی", t_deterministic_phase_order),
        ("[۲] every_n_beats", t_every_n_beats),
        ("[۳] bounded + circuit breaker", t_budget_and_circuit_breaker),
        ("[۴] organ failure isolation", t_failure_isolation),
        ("[۵] restart continuity (beatِ بعدی، نه دوباره)", t_restart_continuity),
        ("[۶] HALT — فقط فازهای امن", t_halt_only_safe_phases),
        ("[۷] zero double-actuation (ACT dry-run)", t_act_is_dry_run_by_default),
    ])
    sys.exit(1 if failed else 0)
