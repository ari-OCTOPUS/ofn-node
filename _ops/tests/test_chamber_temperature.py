#!/usr/bin/env python3
"""تست Blueprint Phase 5 — دمای Chamber (اکتشاف/پالایش). RED: فقط sandbox.

پوشش:
  - T همیشه در [t_min, t_max] روی تاریخچه‌های مصنوعی (خالی/همه-رد/همه-merge/رکود/مخلوط)
  - خالی → خنثی (وسطِ بازه)؛ رکود → T بالاتر (یکنوا)؛ merge_rate بالا → T پایین‌تر
  - determinism، تقدمِ ctor بر env بر پیش‌فرض، persist fail-soft
  - rounds_for و run_chamber: سقفِ مطلق MAX_ROUNDS=3، رفتارِ identical با temperature=None
  - ساختاری: zero-auto-merge (grep رشته‌های ممنوع)، فلگ OCTOPUS_WIRE_CHAMBER_T در doctor
  - doctor: مصرفِ pop_rfc_verdicts از کانال (fail-soft، MagicMock)
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("chamber-temperature")

_REAL_DOCTOR = Path(r"F:\backup\_ops\doctor")
if str(_REAL_DOCTOR) not in sys.path:
    sys.path.insert(0, str(_REAL_DOCTOR))

import json  # noqa: E402
import os  # noqa: E402
import time  # noqa: E402
from types import SimpleNamespace  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from temperature import TemperatureController  # noqa: E402
from chamber import run_chamber, MAX_ROUNDS  # noqa: E402


# ─── ابزار: db فیک منطبق بر کوئریِ calibration.get_verdict_history ─────────────
class FakeDB:
    """ردیف‌های duration_marker با label=JSON — دقیقاً شکلی که get_verdict_history می‌خواند."""

    def __init__(self, verdicts: list[str]):
        self._rows = [(json.dumps({"rfc_id": f"rfc-{i}", "verdict": v,
                                   "bottleneck_key": "", "effect": {}, "ts": i},
                                  ensure_ascii=False),)
                      for i, v in enumerate(verdicts)]

    def q(self, sql, params=()):
        assert "duration_marker" in sql and "verdict-" in sql
        return list(self._rows)


class BoomDB:
    def q(self, sql, params=()):
        raise RuntimeError("db exploded")


def _tc(verdicts=None, **kw):
    db = FakeDB(verdicts) if verdicts is not None else None
    kw.setdefault("persist_path", ENV["ops"] / "state" / "t-test.json")
    return TemperatureController(db=db, **kw)


_TRACE = {"errors": [{"organ": "X", "msg": "boom"}]}
# بدونِ rollback → Red-Critic هر دور concern می‌دهد → توقفِ زودهنگام رخ نمی‌دهد
_RFC_LONG = {"bottleneck": "b", "fix": "a sufficiently long real fix",
             "expected_lift": "fewer errors"}


# ═══ ۱ · بازهٔ T روی تاریخچه‌های مصنوعی ═══════════════════════════════════════

def t_range_all_synthetic_histories():
    """T همیشه در [t_min,t_max] — خالی/همه-رد/همه-merge/رکود بلند/مخلوط/ignored."""
    histories = [[], ["rejected"] * 30, ["merged"] * 30,
                 ["merged"] + ["ignored"] * 40,
                 (["merged", "rejected", "ignored"] * 10),
                 ["ignored"] * 7, ["rejected", "merged"] * 3]
    for h in histories:
        for (lo, hi) in ((0.2, 1.5), (0.4, 0.6)):
            t = _tc(h, t_min=lo, t_max=hi).current()
            assert lo <= t <= hi, f"T={t} خارج از [{lo},{hi}] برای history={h[:5]}…"


def t_empty_history_neutral_midrange():
    """تاریخچهٔ خالی (یا db=None) → دمای خنثی = وسطِ بازه."""
    mid = 0.2 + (1.5 - 0.2) * 0.5
    assert abs(_tc([]).current() - mid) < 1e-9
    assert abs(_tc(None).current() - mid) < 1e-9   # db=None → همان خنثی


def t_db_exception_neutral():
    """db خراب → fail-soft → خنثی (نه crash)."""
    tc = TemperatureController(db=BoomDB(),
                               persist_path=ENV["ops"] / "state" / "t-boom.json")
    assert abs(tc.current() - 0.85) < 1e-9


def t_all_rejected_hits_tmax():
    """همه-رد + رکودِ کامل → explore=1 → T=t_max."""
    assert abs(_tc(["rejected"] * 30).current() - 1.5) < 1e-9


def t_all_merged_hits_tmin():
    """همه-merge (رکود صفر، merge_rate=1) → explore=0 → T=t_min."""
    assert abs(_tc(["merged"] * 30).current() - 0.2) < 1e-9


def t_stagnation_raises_T_monotonic():
    """رکودِ طولانی‌تر (merge_rate ثابت=1 با ignored) → T اکیداً بالاتر."""
    t0 = _tc(["merged"] * 5).current()
    t3 = _tc(["merged"] * 5 + ["ignored"] * 3).current()
    t6 = _tc(["merged"] * 5 + ["ignored"] * 6).current()
    t12 = _tc(["merged"] * 5 + ["ignored"] * 12).current()
    assert t0 < t3 < t6 < t12, (t0, t3, t6, t12)


def t_high_merge_rate_lowers_T():
    """با رکودِ برابر (۴)، merge_rate بالاتر → T پایین‌تر."""
    low_mr = _tc(["rejected"] * 3 + ["merged"] + ["rejected"] * 4).current()
    high_mr = _tc(["merged"] * 3 + ["merged"] + ["rejected"] * 4).current()
    assert high_mr < low_mr, (high_mr, low_mr)


def t_window_limits_lookback():
    """window فقط رکوردهای آخر را می‌بیند: mergeهای قدیمیِ بیرونِ پنجره اثر ندارند."""
    h = ["merged"] * 30 + ["rejected"] * 20
    t_windowed = _tc(h, window=20).current()      # فقط ۲۰ ردِ آخر → t_max
    assert abs(t_windowed - 1.5) < 1e-9


# ═══ ۲ · determinism / env / persist ═══════════════════════════════════════════

def t_deterministic():
    """همان تاریخچه → همان T (بدونِ هیچ randomness)."""
    h = ["merged", "rejected", "ignored", "rejected"] * 4
    vals = {_tc(h).current() for _ in range(5)}
    assert len(vals) == 1, vals


def t_env_override_then_ctor_precedence():
    """آرگومانِ سازنده > env > پیش‌فرض (الگوی _env_float در bcm)."""
    os.environ["OCTOPUS_CHAMBER_T_MIN"] = "0.5"
    os.environ["OCTOPUS_CHAMBER_T_MAX"] = "1.0"
    os.environ["OCTOPUS_CHAMBER_T_WINDOW"] = "5"
    try:
        env_tc = _tc([])
        assert (env_tc.t_min, env_tc.t_max, env_tc.window) == (0.5, 1.0, 5)
        ctor_tc = _tc([], t_min=0.3, t_max=0.9, window=7)
        assert (ctor_tc.t_min, ctor_tc.t_max, ctor_tc.window) == (0.3, 0.9, 7)
    finally:
        for k in ("OCTOPUS_CHAMBER_T_MIN", "OCTOPUS_CHAMBER_T_MAX",
                  "OCTOPUS_CHAMBER_T_WINDOW"):
            os.environ.pop(k, None)


def t_persist_writes_snapshot():
    """persist اتمی: فایل با کلیدهای ts/T/explore/merge_rate/stagnation نوشته می‌شود."""
    p = ENV["ops"] / "state" / "t-persist.json"
    _tc(["rejected"] * 4, persist_path=p).current()
    data = json.loads(p.read_text(encoding="utf-8"))
    for k in ("ts", "T", "explore", "merge_rate", "stagnation"):
        assert k in data, f"کلید {k} در persist نیست: {data}"
    assert data["stagnation"] == 4


def t_persist_fail_soft():
    """مسیرِ persist خراب (والد = فایل) → current همچنان float معتبر برمی‌گرداند."""
    blocker = ENV["ops"] / "state" / "t-blocker"
    blocker.write_text("i am a file", encoding="utf-8")
    tc = _tc(["rejected"] * 8, persist_path=blocker / "x.json")
    t = tc.current()
    assert isinstance(t, float) and 0.2 <= t <= 1.5


# ═══ ۳ · rounds_for — سقفِ مطلق ۳ ═══════════════════════════════════════════════

def t_rounds_for_mapping():
    """0.2→1، 1.5→3، 99→3 — و کرانِ سخت [1,3] روی کلِ بازه اثبات می‌شود."""
    tc = _tc([])
    assert tc.rounds_for(0.2) == 1
    assert tc.rounds_for(1.5) == 3
    assert tc.rounds_for(99) == 3
    assert tc.rounds_for(0.0) == 1
    assert tc.rounds_for(-5.0) == 1
    for i in range(0, 400):
        r = tc.rounds_for(i * 0.05)
        assert 1 <= r <= MAX_ROUNDS, f"rounds_for({i*0.05})={r} خارج از [1,3]"


# ═══ ۴ · run_chamber با دما ═════════════════════════════════════════════════════

def t_chamber_temperature_none_identical():
    """temperature=None → رفتار بایت‌به‌بایت مثلِ قبل؛ result['temperature'] None."""
    r1 = run_chamber(trace=dict(_TRACE), initial_rfc=dict(_RFC_LONG))
    r2 = run_chamber(trace=dict(_TRACE), initial_rfc=dict(_RFC_LONG), temperature=None)
    assert r1 == r2
    assert r1["temperature"] is None and r2["temperature"] is None
    # None نباید max_rounds پاس‌شده را دستکاری کند
    r3 = run_chamber(trace=dict(_TRACE), initial_rfc=dict(_RFC_LONG),
                     max_rounds=2, temperature=None)
    assert r3["rounds_run"] == 2


def t_chamber_high_temp_bounded():
    """T=1.5 (و حتی T=99) با traceای که طولانی می‌دود → rounds_run ≤ MAX_ROUNDS=3."""
    r = run_chamber(trace=dict(_TRACE), initial_rfc=dict(_RFC_LONG), temperature=1.5)
    assert r["rounds_run"] <= MAX_ROUNDS == 3
    assert r["rounds_run"] == 3   # این trace بدونِ rollback تا سقف می‌دود
    r99 = run_chamber(trace=dict(_TRACE), initial_rfc=dict(_RFC_LONG), temperature=99.0)
    assert r99["rounds_run"] <= 3, "سقفِ مطلق شکست"


def t_chamber_low_temp_one_round():
    """T=0.2 → حداکثر یک دور (پالایش)."""
    r = run_chamber(trace=dict(_TRACE), initial_rfc=dict(_RFC_LONG), temperature=0.2)
    assert r["rounds_run"] == 1


def t_chamber_result_carries_temperature():
    """دیکشنریِ خروجی temperature را حمل می‌کند (audit)."""
    r = run_chamber(trace=dict(_TRACE), initial_rfc=dict(_RFC_LONG), temperature=0.7)
    assert r["temperature"] == 0.7


def t_chamber_still_propose_only():
    """با دما هم propose-only می‌ماند: هیچ کلیدِ اثر/ادغام در خروجی نیست."""
    r = run_chamber(trace=dict(_TRACE), initial_rfc=dict(_RFC_LONG), temperature=1.0)
    for forbidden in ("merged", "applied", "settled", "effect"):
        assert forbidden not in r, f"کلیدِ ممنوع {forbidden} در خروجیِ Chamber"
    assert "rfc" in r


# ═══ ۵ · ساختاری — zero-auto-merge ══════════════════════════════════════════════

def t_structural_temperature_no_forbidden_strings():
    """خطِ قرمز: temperature.py هیچ ردی از gate/effector/کانال ندارد."""
    import temperature as _t
    src = open(_t.__file__, encoding="utf-8").read()
    forbidden = ["organ_gate", "money_gate", "capability_gate", "budget_gate",
                 "EffectorGate", "settle", "submit_for_approval", "sendMessage"]
    for f in forbidden:
        assert f not in src, f"خطِ قرمز نقض شد: '{f}' در temperature.py"


def t_structural_doctor_has_wire_flag():
    """doctor.py پشتِ flag سیم‌کشی شده: OCTOPUS_WIRE_CHAMBER_T در سورس."""
    import doctor as _d
    src = open(_d.__file__, encoding="utf-8").read()
    assert "OCTOPUS_WIRE_CHAMBER_T" in src


# ═══ ۶ · doctor — مصرفِ verdict از کانال (fail-soft) ════════════════════════════

def _mk_doctor(channel=None, db=None):
    from doctor import Doctor
    sd = ENV["ops"] / "state"
    sd.mkdir(parents=True, exist_ok=True)
    return Doctor(state_dir=str(sd), knowledge_dir=str(ENV["ops"] / "ki"),
                  approval_channel=channel, db=db)


def t_doctor_consumes_rfc_verdicts():
    """کانال با pop_rfc_verdicts → run_cycle بدونِ crash مصرف می‌کند و record_verdict می‌زند."""
    channel = MagicMock()
    channel.pop_rfc_verdicts.return_value = [("rfc-x", "merge-approved")]
    db = MagicMock()
    doc = _mk_doctor(channel=channel, db=db)
    res = doc.run_cycle(beat=1, trace={}, use_calibration=False, use_chamber=False)
    assert res is None                       # trace خالی → گلوگاهی نیست
    assert channel.pop_rfc_verdicts.called
    assert db.ex.called                      # record_verdict نوشت (INSERT duration_marker)


def t_doctor_verdict_updates_registry_status():
    """merge-approved→human-merged، denied→human-rejected، ناشناخته→skip."""
    channel = MagicMock()
    channel.pop_rfc_verdicts.return_value = [
        ("rfc-x", "merge-approved"), ("rfc-y", "denied"), ("rfc-z", "weird")]
    doc = _mk_doctor(channel=channel, db=MagicMock())
    now = time.time()
    for rid in ("rfc-x", "rfc-y", "rfc-z"):
        doc._rfcs[rid] = SimpleNamespace(status="submitted", created_ts=now)
    doc.run_cycle(beat=2, trace={}, use_calibration=False, use_chamber=False)
    assert doc._rfcs["rfc-x"].status == "human-merged"
    assert doc._rfcs["rfc-y"].status == "human-rejected"
    assert doc._rfcs["rfc-z"].status == "submitted"   # verdict ناشناخته دست نمی‌خورد


def t_doctor_verdict_consumption_fail_soft():
    """pop_rfc_verdicts منفجر شود → cycle نمی‌میرد (alert fail-soft)."""
    channel = MagicMock()
    channel.pop_rfc_verdicts.side_effect = RuntimeError("channel boom")
    doc = _mk_doctor(channel=channel, db=MagicMock())
    res = doc.run_cycle(beat=3, trace={}, use_calibration=False, use_chamber=False)
    assert res is None                       # زنده ماند و مسیرِ عادی را رفت


def t_doctor_no_channel_method_skips():
    """کانالِ بدونِ pop_rfc_verdicts (hasattr-guard) → مسیرِ قدیمی، بدونِ crash."""
    class Bare:                              # نه MagicMock — واقعاً attr ندارد
        pass
    doc = _mk_doctor(channel=Bare(), db=None)
    assert doc.run_cycle(beat=4, trace={}, use_calibration=False,
                         use_chamber=False) is None


if __name__ == "__main__":
    failed = harness.run([
        # بازهٔ T
        ("[T] T در بازه روی همهٔ تاریخچه‌های مصنوعی", t_range_all_synthetic_histories),
        ("[T] خالی → خنثی وسطِ بازه", t_empty_history_neutral_midrange),
        ("[T] db خراب → خنثی (fail-soft)", t_db_exception_neutral),
        ("[T] همه-رد → t_max", t_all_rejected_hits_tmax),
        ("[T] همه-merge → t_min", t_all_merged_hits_tmin),
        ("[T] رکود → T یکنوا بالا", t_stagnation_raises_T_monotonic),
        ("[T] merge_rate بالا → T پایین", t_high_merge_rate_lowers_T),
        ("[T] window فقط رکوردهای آخر", t_window_limits_lookback),
        # determinism / env / persist
        ("[D] deterministic", t_deterministic),
        ("[D] ctor > env > default", t_env_override_then_ctor_precedence),
        ("[D] persist snapshot اتمی", t_persist_writes_snapshot),
        ("[D] persist fail-soft", t_persist_fail_soft),
        # rounds_for
        ("[R] rounds_for: نگاشت + کرانِ سخت [1,3]", t_rounds_for_mapping),
        # run_chamber با دما
        ("[C] temperature=None = رفتارِ قبلی", t_chamber_temperature_none_identical),
        ("[C] T بالا → rounds_run ≤ 3 (سقفِ مطلق)", t_chamber_high_temp_bounded),
        ("[C] T پایین → یک دور", t_chamber_low_temp_one_round),
        ("[C] خروجی temperature را حمل می‌کند", t_chamber_result_carries_temperature),
        ("[C] propose-only حفظ شد", t_chamber_still_propose_only),
        # ساختاری
        ("[S] zero-auto-merge: رشته‌های ممنوع غایب", t_structural_temperature_no_forbidden_strings),
        ("[S] doctor پشتِ OCTOPUS_WIRE_CHAMBER_T", t_structural_doctor_has_wire_flag),
        # doctor verdict consumption
        ("[V] مصرفِ verdict از کانال", t_doctor_consumes_rfc_verdicts),
        ("[V] نگاشت و به‌روزرسانیِ registry", t_doctor_verdict_updates_registry_status),
        ("[V] fail-soft: کانالِ خراب", t_doctor_verdict_consumption_fail_soft),
        ("[V] hasattr-guard: کانالِ بدونِ متد", t_doctor_no_channel_method_skips),
    ])
    sys.exit(1 if failed else 0)
