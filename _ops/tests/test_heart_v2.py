#!/usr/bin/env python3
"""test_heart_v2.py — Gate 1: HeartStore + FSM + kernel + runtime + continuity.

همه در sandbox harness؛ هیچ state زنده نوشته نمی‌شود.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("heart-v2")
_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "heart"), str(_OPS / "cortex"),
           str(_OPS / "memory")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
from heart import state_machine as fsm  # noqa: E402
from heart import kernel as hk          # noqa: E402


# ═══ HeartStore ═══
def _store():
    from heart import store as st
    return st.HeartStore(opslib.STATE_DIR / "chrono.db")


def t_genesis_once_and_idempotent():
    s = _store()
    g1 = s.genesis()
    g2 = s.genesis()
    assert g1.get("genesis") in (True, False)      # بوت دوباره → already
    assert g2["genesis"] is False and g2["already_present"] is True
    c = s.counts()
    assert c["max_beat"] >= 0
    row = s.reader().execute(
        "SELECT beat, status, mode FROM heart_beat WHERE beat=0").fetchone()
    assert row and row[0] == 0 and row[1] == "COMMITTED" and row[2] == "GENESIS"
    s.close()


def t_beat_lifecycle_and_unique_per_run():
    s = _store()
    assert s.begin_beat(1) is True
    assert s.begin_beat(1) is False            # تکرار در همان run رد می‌شود
    assert s.commit_beat(1, mode="RUNNING", period_advisory_s=96.4) is True
    assert s.commit_beat(1, mode="RUNNING") is False   # دوباره commit نمی‌شود
    assert s.commit_beat(2, mode="RUNNING") is False   # بدون reserve
    s.close()


def t_event_idempotency():
    s = _store()
    a = s.emit(1, "x.y", {"k": 1}, idempotency_key="fixed")
    b = s.emit(1, "x.y", {"k": 1}, idempotency_key="fixed")
    assert a is not None and b is None
    s.close()


def t_outbox_claim_confirm_dlq():
    s = _store()
    oid = s.enqueue(1, "notify", {"m": "hi"})
    assert oid is not None
    items = s.claim_outbox()
    assert any(i["id"] == oid for i in items)
    assert all(i["id"] != oid for i in s.claim_outbox())   # lease گرفته
    s.confirm_outbox(oid)
    s.confirm_outbox(oid, dlq=True)            # CONFIRMED → DLQ مجاز (بازبینی دستی)
    assert s.counts()["outbox"].get("DLQ") == 1
    s.close()


def t_time_model_seq_ordering():
    s = _store()
    s.begin_beat(3); s.commit_beat(3, mode="RUNNING")
    rows = s.reader().execute(
        "SELECT seq, run_id, boot_id FROM heart_run JOIN heart_beat "
        "USING(run_id) WHERE beat=3").fetchall()
    assert rows and rows[0][1] and rows[0][2]
    ev = s.reader().execute(
        "SELECT COUNT(*) FROM heart_event WHERE idempotency_key='genesis'").fetchone()
    assert ev[0] == 1
    s.close()


# ═══ FSM ═══
def t_no_threat_to_capability_edge_exists():
    # COMA هیچ یال مستقیم به توان بالاتر ندارد؛ DORMANT terminal است؛
    # بازگشت SAFE/DEGRADED فقط از مسیر streak-gatedِ assess_transition است
    # (تست جداگانهٔ t_recovery_needs_streak).
    assert not fsm.can_transition("COMA", "RUNNING")
    assert not fsm.can_transition("DORMANT", "RUNNING")
    assert not fsm.can_transition("DORMANT", "WARMUP")
    assert not fsm.can_transition("GENESIS", "RUNNING")   # فقط از BOOTING
    m, _ = fsm.assess_transition("COMA", green_streak=99)
    assert m == "COMA"                                     # بدون coma_recovered
    assert fsm.can_transition("BOOTING", "WARMUP")


def t_kill_supreme_from_every_state():
    for cur in fsm.STATES:
        mode, why = fsm.assess_transition(cur, kill=True)
        assert mode == "DORMANT", (cur, mode)


def t_recovery_needs_streak():
    m, why = fsm.assess_transition("SAFE", red=False, green_streak=1)
    assert m == "SAFE"
    m, _ = fsm.assess_transition("SAFE", red=False, green_streak=fsm.RECOVERY_STREAK)
    assert m == "RUNNING"
    m, _ = fsm.assess_transition("DEGRADED", degraded_inputs=False, green_streak=0)
    assert m == "DEGRADED"          # بدون streak برنمی‌گردد
    m, _ = fsm.assess_transition("DEGRADED", green_streak=fsm.RECOVERY_STREAK)
    assert m == "RUNNING"


def t_red_goes_safe_journal_failure_coma():
    assert fsm.assess_transition("RUNNING", red=True)[0] == "SAFE"
    assert fsm.assess_transition("RUNNING", journal_failure=True)[0] == "COMA"
    assert fsm.assess_transition("WARMUP", journal_failure=True)[0] == "COMA"


# ═══ Kernel ═══
def _obs(**over):
    base = [
        {"metric": "organism.beat", "value": 100, "unit": "count",
         "age_s": 5.0, "quality": "VALID", "source": "t"},
        {"metric": "organism.halted", "value": None, "unit": "flag",
         "age_s": 5.0, "quality": "VALID", "source": "t"},
        {"metric": "organism.sleep_s", "value": 96.0, "unit": "s",
         "age_s": 5.0, "quality": "VALID", "source": "t"},
        {"metric": "pulse.effective_period_s", "value": 96.0, "unit": "s",
         "age_s": 5.0, "quality": "VALID", "source": "t"},
        {"metric": "vitals.stress", "value": 0.2, "unit": "0..1",
         "age_s": 5.0, "quality": "VALID", "source": "t"},
        {"metric": "disk.write_failures_1h", "value": 0, "unit": "count",
         "age_s": 0.0, "quality": "VALID", "source": "t"},
    ]
    for k, v in over.items():
        for o in base:
            if o["metric"] == k:
                o.update(v if isinstance(v, dict) else {"value": v})
    return base


def t_kernel_boot_to_running_then_stable():
    o1 = hk.assess(_obs(), current_mode="BOOTING", beat=1)
    assert o1["mode"] in ("WARMUP", "RUNNING")
    o2 = hk.assess(_obs(), current_mode="WARMUP", beat=hk.WARMUP_MIN_BEATS + 1)
    assert o2["mode"] == "RUNNING"
    o3 = hk.assess(_obs(), current_mode="RUNNING", beat=99)
    assert o3["mode"] == "RUNNING" and o3["green_streak"] >= 1
    assert o3["period_advisory_s"] == 96.0     # advisory فقط گزارش می‌دهد
    assert o3["wake_brain"] is False or o3["wake_reasons"]


def t_kernel_missing_is_not_zero_and_degraded():
    o = _obs()
    o[3]["quality"] = "MISSING"
    o[3]["value"] = None
    out = hk.assess(o, current_mode="RUNNING", beat=10)
    assert out["n_missing"] == 1 and out["degraded_inputs"] is False  # آستانه ۲
    o2 = _obs()
    o2[2]["quality"] = "MISSING"; o2[2]["value"] = None
    o2[3]["quality"] = "MISSING"; o2[3]["value"] = None
    out2 = hk.assess(o2, current_mode="RUNNING", beat=10)
    assert out2["degraded_inputs"] is True


def t_kernel_write_failures_red_and_journal():
    out = hk.assess(_obs(**{"disk.write_failures_1h": hk.RED_WRITE_FAILURES}),
                    current_mode="RUNNING", beat=10)
    assert out["red"] is True and out["mode"] == "SAFE"
    out2 = hk.assess(_obs(**{"disk.write_failures_1h": 99}),
                     current_mode="RUNNING", beat=11)
    assert out2["mode"] == "COMA"


def t_kernel_wake_is_event_driven_not_every_beat():
    o = hk.assess(_obs(), current_mode="RUNNING", beat=50, prev_wake_beat=49)
    assert o["wake_brain"] is False            # نه هر beat
    o2 = hk.assess(_obs(), current_mode="RUNNING", beat=50 + hk.BRAIN_WAKE_EVERY_N)
    assert o2["wake_brain"] is True and any("periodic" in r for r in o2["wake_reasons"])
    o3 = hk.assess(_obs(**{"vitals.stress": 0.8}), current_mode="RUNNING", beat=5)
    assert o3["wake_brain"] is True
    o4 = hk.assess(_obs(), current_mode="SAFE", beat=5 + hk.BRAIN_WAKE_EVERY_N)
    assert o4["wake_brain"] is False           # زیر SAFE بیداری شناختی نیست


def t_kernel_kill_halt_dormant():
    out = hk.assess(_obs(**{"organism.halted": "HALT-ALL"}),
                    current_mode="RUNNING", beat=9)
    assert out["mode"] == "DORMANT"


# ═══ Runtime (scheduler واحد) ═══
def t_runtime_flag_off_noop_and_on_registers():
    from heart import runtime as hrt
    import os
    os.environ.pop(hrt.FLAG_ENV, None)
    if hrt.FLAG_FILE.exists():
        hrt.FLAG_FILE.unlink()
    assert hrt.enabled() is False and hrt.get_scheduler() is None
    os.environ[hrt.FLAG_ENV] = "1"
    try:
        sched = hrt.get_scheduler()
        assert sched is not None
        names = {o.name for o in sched._organs}
        assert {"heart-sense", "heart-assess", "heart-brain",
                "heart-memory", "heart-heal"} <= names
        assert not any(o.phase == "ACT" for o in sched._organs)   # صفر اثر خارجی
        r = hrt.tick()
        assert r is not None and r.get("committed") in (True, False)
        latest = hrt.read_latest()
        assert latest.get("schema") == "heart-v2/1"
        assert latest.get("advisory_only") is True
    finally:
        os.environ.pop(hrt.FLAG_ENV, None)


def t_runtime_respects_stop():
    from heart import runtime as hrt
    import os
    os.environ[hrt.FLAG_ENV] = "1"
    try:
        opslib.STOP_ORGANISM.write_text("stop", "utf-8")
        assert hrt.tick() is None
    finally:
        opslib.STOP_ORGANISM.unlink(missing_ok=True)
        os.environ.pop(hrt.FLAG_ENV, None)


# ═══ Brain (advisory-only) ═══
def t_brain_parser_forces_non_executable_and_caps():
    import heart_brain as hb
    parsed = hb._parse_model_json(
        'noise {"assessment":"ok","questions":[],"proposals":[{"capability":"x"}]} tail')
    assert parsed and parsed["proposals"][0]["executable"] is False
    assert hb._parse_model_json("not json at all") is None


def t_brain_skips_when_not_woken():
    import heart_brain as hb
    rec = hb.wake({"wake_brain": False}, [], beat=1)
    assert rec["status"] == "SKIPPED"


# ═══ Continuity ═══
def t_continuity_backup_drill_and_projection():
    from memory import continuity as hc
    # hermetic (نشت 2026-08-25T12:30 به _memory واقعی): پروجکشن فقط در sandbox
    hc.MEM_DIR = Path(opslib.STATE_DIR).parent / "_memory" / "OCTOPUS"
    # یک chrono کوچک برای backup
    import sqlite3
    src = opslib.STATE_DIR / "chrono.db"
    if not src.exists():
        con = sqlite3.connect(str(src)); con.execute(
            "CREATE TABLE IF NOT EXISTS x(a)"); con.commit(); con.close()
    snap = hc.BACKUP_DIR / "chrono-test-1.db"
    res = hc.backup_db(snap)
    assert res["ok"] and res.get("sha256")
    assert hc._drill_restore(snap)["ok"] is True
    proj = hc.project({"ts": "2026-08-25T12:00:00", "beat": 5, "mode": "RUNNING",
                       "mode_prev": "WARMUP", "green_streak": 2,
                       "period_advisory_s": 96.0,
                       "brain_stats": {"ok": 1, "degraded": 0},
                       "store_counts": {"beats": 5, "events": 2}})
    assert "NOW.md" in proj["projected"]
    now_md = (hc.MEM_DIR / "NOW.md").read_text("utf-8")
    assert "RUNNING" in now_md and "بازنویسی" not in now_md.split("ماشین‌نوشت")[0]
    ab = hc.MEM_DIR / "AUTOBIOGRAPHY" / str(__import__("datetime").date.today().year)
    assert ab.exists()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_heart_v2: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
