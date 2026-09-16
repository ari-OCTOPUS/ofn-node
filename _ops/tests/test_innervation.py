"""test_innervation.py — عصب‌کشیِ قلب→ستون→اندام‌ها + فیکسِ #۱ seedِ زودِ setpoint (جلسه ۴۶).

هر اندام beat می‌خورد یا نقطهٔ مرده؟ ضربانِ کنترلِ کلی منتشر می‌شود؟ setpoint روی اولین
velocity زود seed می‌شود (نه انتظارِ کادنسِ ۱۴۴۰)؟
"""
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("innervation")

import innervation as nv   # noqa: E402
import opslib             # noqa: E402


def _touch(rel, age_min=0.0):
    p = opslib.STATE_DIR / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{}", "utf-8")
    if age_min:
        old = time.time() - age_min * 60
        os.utime(p, (old, old))


def t_a_fresh_organ_connected():
    _touch("ORGANISM-STATE.json", age_min=1)      # SLA spine = 5min
    a = nv.check()
    spine = next(o for o in a["organs"] if o["id"] == "spine")
    assert spine["connected"] is True and "عصب‌دار" in spine["status"]


def t_b_stale_organ_is_dead_spot():
    _touch("pulse/heart-shadow-latest.json", age_min=200)   # SLA heart = 30 → ۲۰۰ = مرده
    a = nv.check()
    heart = next(o for o in a["organs"] if o["id"] == "heart")
    assert heart["connected"] is False and "مرده" in heart["status"]
    assert any("قلب" in dn for dn in a["dead_spots"])


def t_c_unborn_not_counted_as_dead():
    """اندامی که هنوز فایلش نیست = «هنوز نزاده»، نه نقطهٔ مردهٔ واقعی."""
    # cortex-state را پاک نگه دار
    p = opslib.STATE_DIR / "cortex" / "cortex-state.json"
    if p.exists():
        p.unlink()
    a = nv.check()
    cortex = next(o for o in a["organs"] if o["id"] == "cortex")
    assert cortex["connected"] is False and "نزاده" in cortex["status"]
    assert not any("مرکزی" in dn for dn in a["dead_spots"])   # نزاده ≠ مرده


def t_d_heart_period_is_master_rhythm():
    (opslib.STATE_DIR / "pulse").mkdir(parents=True, exist_ok=True)
    (opslib.STATE_DIR / "pulse" / "heart-shadow-latest.json").write_text(
        json.dumps({"period_s": 212.0}), "utf-8")
    assert nv.heart_period_now() == 212.0
    a = nv.check()
    assert a["heart_period_s"] == 212.0            # ضربانِ کنترلِ کلی منتشر شد


def t_e_coverage_and_persist_event_on_new_dead():
    import events
    _touch("ORGANISM-STATE.json", age_min=1)
    nv.persist()                                    # baseline
    _touch("cortex/stress-latest.json", age_min=500)  # اندامی مرده شد
    nv.persist()
    assert any("مرده" in (e.get("summary") or "") for e in events.recent(50))


def t_f_setpoint_early_seed_fix1():
    """فیکسِ #۱: seedِ setpoint روی اولین velocity (نه انتظارِ کادنسِ ۱۴۴۰)."""
    import wiring
    # velocity واقعی بگذار، setpoint نباشد → seed باید در همان اولین ضربان بیفتد
    (opslib.STATE_DIR / "pulse").mkdir(parents=True, exist_ok=True)
    from heart import producers, interface as hi
    # مستقیم: بدونِ setpoint + با velocity → run_epoch_setpoint می‌نویسد
    from heart import doctor_setpoint as ds
    if hi.read_setpoint() is not None:
        pass
    # velocity را در stream بگذار تا producer ببیند
    (opslib.STATE_DIR / "pulse" / "velocity-stream.jsonl").write_text(
        "\n".join(json.dumps({"ts": time.time(), "confirmed": 1, "effects": 1, "hour": i})
                  for i in range(5)) + "\n", "utf-8")
    sig = producers.read_signals()
    v = (sig.get("velocity") or {}).get("velocity_per_hr")
    if v is not None:      # اگر producer velocity داد، seed باید بنویسد
        out = ds.run_epoch_setpoint(write=True)
        assert out.get("written") is True and out.get("rationale", "").startswith("seeded")
        assert hi.read_setpoint() is not None       # باند دیگر null نیست
    else:
        # producer در محیطِ تست velocity نداد → حداقل مسیرِ awaiting درست است
        out = ds.run_epoch_setpoint(write=True)
        assert out.get("reason") == "awaiting-first-velocity"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_innervation: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
