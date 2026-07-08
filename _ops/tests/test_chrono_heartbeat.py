#!/usr/bin/env python3
"""تست Phase 1 · Chrono substrate (P-Chrono-1,2,3,5,6,7).
اثبات: ضربانِ یکنواختِ اکید + پیوستگی پس از restart · پاها ساعتِ دیواری نمی‌خوانند
(TINV-5، ساختاری) · ترتیبِ علّیِ HLC بینِ دو پا (TINV-1) · گذارِ phi-accrual
alive→suspected→failed در آستانه‌های درست + قلابِ دکتر (TINV-4) · experience_rate
کران‌دار [0,cap] و coupling متابولیکِ یکنواخت و دو-ساعت (age_tick بی‌حرکت — TINV-6)
· scheduler بر حسبِ نبض نه ساعتِ دیواری (F19) · effect-gate: بدونِ append settle
ممنوع؛ kill گیت را force-close می‌کند (TINV-7). همه $0 آفلاین."""
import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("chrono")
import opslib  # noqa: E402
import chrono  # noqa: E402


class FakeClock:
    """زمانِ فیزیکیِ تزریقی — تست بدونِ sleep، مستقل از ساعتِ دیواریِ واقعی."""

    def __init__(self, t_ms: int = 1_000_000):
        self.t = t_ms

    def __call__(self) -> int:
        return self.t

    def advance(self, ms: int) -> int:
        self.t += ms
        return self.t


def _pm(name: str, **kw):
    clock = FakeClock()
    db = chrono.ChronoDB(ENV["ops"] / "state" / f"chrono-{name}.db")
    bus = chrono.ChronoBus(clock)
    pm = chrono.Pacemaker(db=db, bus=bus, clock=clock, **kw)
    return pm, clock, db


def t_beat_monotonic_and_continuity():
    pm, clock, db = _pm("beat")
    seqs = []
    for _ in range(5):
        clock.advance(60_000)
        seqs.append(pm.beat_once()["beat"])
    assert seqs == [1, 2, 3, 4, 5], seqs
    rows = [r[0] for r in db.q("SELECT beat_seq FROM heartbeat ORDER BY beat_seq")]
    assert rows == [1, 2, 3, 4, 5], rows
    # پیوستگی: pacemaker نو روی همان db از آخرین نبض ادامه می‌دهد (نه از صفر)
    pm2 = chrono.Pacemaker(db=db, bus=chrono.ChronoBus(clock), clock=clock)
    clock.advance(60_000)
    assert pm2.beat_once()["beat"] == 6


def t_legs_never_read_wall_clock():
    # اثباتِ ساختاری TINV-5: کدِ leg-facing هیچ منبعِ ساعتِ دیواری ندارد
    src = inspect.getsource(chrono.LegHandle)
    for banned in ("time.time", "_utc_ms", "datetime", "clock()"):
        assert banned not in src, f"LegHandle reads wall-clock via {banned}"
    # و رفتاری: پا فقط beat + hlc + present می‌بیند
    pm, clock, _ = _pm("tinv5")
    leg = pm.bus.register_leg("A")
    clock.advance(60_000)
    pm.beat_once()
    msg = leg.inbox[-1]
    assert set(msg.keys()) == {"beat", "hlc", "present"}, msg.keys()


def t_hlc_causal_ordering_two_legs():
    pm, clock, _ = _pm("hlc")
    a = pm.bus.register_leg("A")
    b = pm.bus.register_leg("B")
    h_a = a.event("evt-a1")
    assert h_a > chrono.GENESIS_HLC
    clock.advance(60_000)
    pm.beat_once()                        # broadcast → merge به B (قاعدهٔ receive)
    h_b = b.event("evt-b1")
    assert h_b > h_a, (h_b, h_a)          # علیّت: b بعد از دیدنِ اکنونِ مشترک
    # یکنواختیِ اکید در ساعتِ منجمد: physical ثابت → logical فقط بالا می‌رود
    h1 = a.event()
    h2 = a.event()
    assert h2 > h1 and h2[0] == h1[0] and h2[1] == h1[1] + 1, (h1, h2)


def t_phi_transitions_and_doctor_hook():
    calls = []

    class DoctorStub:
        def restart_from_known_good(self, leg, db):
            calls.append(leg.id)

    pm, clock, _ = _pm("phi", doctor=DoctorStub())
    leg = pm.bus.register_leg("A")
    for _ in range(5):                    # تاریخچهٔ منظم: ack هر 60s
        clock.advance(60_000)
        pm.bus.ack("A")
    t_last = clock.t
    clock.t = t_last + 70_000             # phi≈1.3 < 8
    pm.beat_once()
    assert leg.state == "alive", leg.state
    clock.t = t_last + 100_000            # phi≈11 → مشکوک
    pm.beat_once()
    assert leg.state == "suspected", leg.state
    assert calls == []                    # suspected هنوز restart نمی‌گیرد
    clock.t = t_last + 120_000            # phi≈23 → مرده
    pm.beat_once()
    assert leg.state == "failed", leg.state
    assert calls == ["A"], calls          # قلابِ Phase 2 دقیقاً یک‌بار


def t_experience_bounded_coupling_two_clock():
    lg = opslib.genome_ledger()
    chrono.on_human_judgment({"verdict": "baseline"}, ledger=lg)   # age → 1
    age_before = lg.last_age_tick()
    pm, clock, db = _pm("xp")
    busy = pm.bus.register_leg("BUSY")
    pm.bus.register_leg("IDLE")
    clock.advance(60_000)
    pm.beat_once()                        # ضربانِ اول = مبدأ dt (لنگرِ wall)
    for _ in range(1000):                 # هزار رویداد در یک ضربان
        busy.event()
    clock.advance(1_000)                  # dt=1s → نرخِ خام 1000 ev/s
    pm.beat_once()
    rows = dict((r[0], r[1]) for r in
                db.q("SELECT leg_id, rate FROM experience_meter WHERE beat_seq=2"))
    assert rows["BUSY"] == chrono.XP_RATE_CAP, rows      # سقفِ پلانک‌آنالوگ
    assert rows["IDLE"] == 0.0, rows                     # کف = 0 (خواب)
    wear = dict(db.q("SELECT leg_id, wear FROM metabolic_age"))
    assert wear["BUSY"] > wear["IDLE"] > 0, wear         # coupling یکنواخت
    # دو-ساعت: پیریِ متابولیک حرکت کرد ولی فلشِ میرا بی‌حرکت ماند
    assert lg.last_age_tick() == age_before == 1


def t_anticipation_fires_by_beat_not_wall():
    pm, clock, db = _pm("sched")
    fired = []
    pm.dispatcher = fired.append
    pm.schedule("followup", "task-x", in_beats=3)        # سررسید = نبضِ ۳
    clock.advance(999_999_999)                            # جهشِ عظیمِ ساعتِ دیواری
    assert pm.beat_once()["beat"] == 1 and fired == []
    clock.advance(1)                                      # تقریباً هیچ زمانِ دیواری
    pm.beat_once()
    assert fired == []
    clock.advance(1)
    pm.beat_once()                                        # نبضِ ۳
    assert [f["task_ref"] for f in fired] == ["task-x"], fired
    assert fired[0]["fired_beat"] == 3
    assert db.q("SELECT COUNT(*) FROM anticipation_queue")[0][0] == 0


def t_duration_marker():
    pm, clock, _ = _pm("dur")
    clock.advance(60_000)
    pm.beat_once()
    pm.mark_duration("evt-1", "شروع")
    clock.advance(120_000)
    pm.beat_once()
    d_hlc, d_wall = pm.duration_since("evt-1")
    assert d_hlc > 0 and d_wall >= 120_000, (d_hlc, d_wall)


def t_effect_gate_refuses_without_append():
    pm, clock, db = _pm("gate1")
    gate = chrono.EffectorGate(db)
    eid = gate.request("send", "msg-001", beat=pm.beat)
    assert gate.settle(eid) is False                      # هیچ appendی نیست → ممنوع
    entry = chrono.on_human_judgment({"verdict": "approve msg-001"}, gate=gate)
    assert entry["is_human"] == 1 and entry["age_tick"] >= 1
    assert gate.settle(eid) is True                       # حالا settle مجاز
    assert db.q("SELECT status FROM gated_effect WHERE effect_id=?",
                (eid,))[0][0] == "settled"


def t_kill_switch_force_closes_gate():
    pm, clock, db = _pm("gate2")
    gate = chrono.EffectorGate(db)
    eid = gate.request("publish", "post-001")
    chrono.on_human_judgment({"verdict": "approve post-001"}, gate=gate)
    opslib.STOP_ORGANISM.write_text("kill", "utf-8")      # kill supreme
    try:
        assert gate.force_closed() == "STOP-ORGANISM"
        assert gate.settle(eid) is False                  # حتی releasable هم رد
    finally:
        opslib.STOP_ORGANISM.unlink()
    # FREEZE (I3) هم گیت را می‌بندد — fail-closed
    eid2 = gate.request("sync", "sync-001")
    chrono.on_human_judgment({"verdict": "approve sync-001"}, gate=gate)
    opslib.freeze("تستِ گیت")
    try:
        assert gate.settle(eid2) is False
    finally:
        opslib.FREEZE_FLAG.unlink()
    assert gate.settle(eid2) is False                     # refused ماند — برگشت‌ناپذیر


if __name__ == "__main__":
    failed = harness.run([
        ("ضربان یکنواختِ اکید + پیوستگی پس از restart", t_beat_monotonic_and_continuity),
        ("TINV-5: پاها ساعتِ دیواری نمی‌خوانند (ساختاری+رفتاری)", t_legs_never_read_wall_clock),
        ("TINV-1/2: ترتیبِ علّیِ HLC بینِ دو پا", t_hlc_causal_ordering_two_legs),
        ("TINV-4: phi-accrual alive→suspected→failed + قلابِ دکتر", t_phi_transitions_and_doctor_hook),
        ("TINV-6: نرخ کران‌دار + coupling متابولیک + دو-ساعت", t_experience_bounded_coupling_two_clock),
        ("F19: سررسید بر حسبِ نبض، نه ساعتِ دیواری", t_anticipation_fires_by_beat_not_wall),
        ("حسِ مدت (duration_marker)", t_duration_marker),
        ("TINV-7: بدونِ append هیچ settleی", t_effect_gate_refuses_without_append),
        ("kill/FREEZE گیت را force-close می‌کند", t_kill_switch_force_closes_gate),
    ])
    sys.exit(1 if failed else 0)
