"""test_heart_work.py — HH-P9: پمپِ کار (ضربان→کارِ واقعی) + زنجیرهٔ boot.

کوپل به periodِ سایه، ردهٔ paid پشتِ live-gate، kill-switch، plan-seed،
حافظه (log+state)، و گاردهای ساختاری. deterministic (زمانِ تزریقی).
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("heart-work")

import heart.work_pump as wp   # noqa: E402
import wiring                  # noqa: E402
import opslib                  # noqa: E402

T0 = dt.datetime(2026, 7, 10, 12, 0, 0)


def t_a_plan_seeded_on_first_use():
    """اولین استفاده planِ پیش‌فرض را seed می‌کند — نقشهٔ درونی ماشین‌خوان."""
    plan = wp.load_plan()
    assert plan["schema"] == "work-plan.v1"
    kinds = [t["kind"] for t in plan["templates"]]
    assert kinds == ["health", "gap_report", "web_research", "search", "llm_learn"]
    assert wp.PLAN_PATH.exists()
    on_disk = json.loads(wp.PLAN_PATH.read_text("utf-8"))
    assert [t["kind"] for t in on_disk["templates"]] == kinds


def t_b_kill_switch_and_freeze_first():
    opslib.STOP_ORGANISM.write_text("stop", "utf-8")
    try:
        assert wp.pump_step(1, 60.0, now=T0) == {"skipped": "kill-switch"}
    finally:
        opslib.STOP_ORGANISM.unlink()
    opslib.FREEZE_FLAG.parent.mkdir(parents=True, exist_ok=True)
    opslib.FREEZE_FLAG.write_text("t", "utf-8")
    try:
        assert wp.pump_step(1, 60.0, now=T0) == {"skipped": "FREEZE"}
    finally:
        opslib.FREEZE_FLAG.unlink()


def t_c_first_window_runs_health_and_remembers():
    """اولین پنجره: health اجرا، log ثبت، state به‌روز — حافظهٔ کار."""
    r = wp.pump_step(beat=10, period_s=60.0, now=T0)
    assert r.get("kind") == "health" and r.get("ok") is True, r
    assert wp.HEALTH_PATH.exists()
    log = wp.read_log()
    assert log and log[-1]["kind"] == "health" and log[-1]["beat"] == 10
    st = json.loads(wp.STATE_PATH.read_text("utf-8"))
    assert st["last_run"]["health"] > 0


def t_d_cadence_follows_shadow_period():
    """کوپلِ ضربان↔کار: تا periodِ سایه نگذشته پنجرهٔ نو باز نمی‌شود؛
    قلبِ در استراحت (۹۰۰s) پنجره‌های کمتری می‌دهد."""
    r1 = wp.pump_step(beat=11, period_s=60.0, now=T0 + dt.timedelta(seconds=30))
    assert r1.get("idle") == "not-due"                     # ۳۰s < ۶۰s
    r2 = wp.pump_step(beat=12, period_s=60.0, now=T0 + dt.timedelta(seconds=61))
    assert r2.get("kind") == "gap_report" and r2.get("ok") is True, r2   # taskِ بعدی
    st = json.loads(wp.STATE_PATH.read_text("utf-8"))
    last = st["last_window_ts"]
    r3 = wp.pump_step(beat=13, period_s=900.0,
                      now=T0 + dt.timedelta(seconds=61 + 400))
    assert r3.get("idle") == "not-due"                     # با قلبِ آرام: ۴۰۰s < ۹۰۰s
    assert json.loads(wp.STATE_PATH.read_text("utf-8"))["last_window_ts"] == last


def t_e_paid_search_live_locked_today():
    """ردهٔ paid (سرچ): امروز skipِ صادق با دلیلِ live-locked — نه اجرای خاموش.
    (مستقیمِ لِینِ paid — مستقل از ترتیبِ انتخابِ پمپ، که حالا web_researchِ $0 هم دارد.)"""
    tpl = {"kind": "search", "paid": True}
    r = wp._exec_paid_lane("search", tpl)
    assert r.get("ok") is False and "live-locked" in r.get("skipped", ""), r


def t_f_paid_llm_learn_live_locked_today():
    """ردهٔ paid (یادگیریِ LLM): همان گیتِ دوقفله؛ سندِ unlock در خروجی.
    rollover 2026-07-21: قراردادِ «پیش از تاریخ» با پینِ LIVE_GATE_DATE سنجیده می‌شود."""
    _real_gate = opslib.LIVE_GATE_DATE
    opslib.LIVE_GATE_DATE = dt.date(2099, 1, 1)
    try:
        r = wp._exec_paid_lane("llm_learn", {"kind": "llm_learn", "paid": True})
        assert r.get("ok") is False and "live-locked" in r.get("skipped", ""), r
        assert "ACTIVATION-WORK-LLM" in r.get("unlock", "")
        # گیتِ دوقفله: بدونِ ACTIVATION-GO-LIVE، سپرِ تاریخ بسته است
        ok, why = opslib.live_gate_open(wp.ACT_WORK_LLM)
        assert ok is False and "live locked" in why
    finally:
        opslib.LIVE_GATE_DATE = _real_gate


def t_g_wiring_flag_off_no_work_key():
    """WIRE_HEART روشن ولی WIRE_HEART_WORK خاموش → خروجیِ heart_beat کلیدِ work ندارد."""
    os.environ["OCTOPUS_WIRE_HEART"] = "1"
    os.environ.pop("OCTOPUS_WIRE_HEART_WORK", None)
    try:
        wiring._HEART_STATE["last_epoch"] = 0
        out = wiring.heart_beat(beat=10)
        assert out is not None and "work" not in out
    finally:
        os.environ.pop("OCTOPUS_WIRE_HEART", None)


def t_h_wiring_flag_on_pumps_with_shadow_period():
    """هر دو flag روشن → work داخلِ خروجیِ ضربان (کوپلِ کامل، fail-soft)."""
    os.environ["OCTOPUS_WIRE_HEART"] = "1"
    os.environ["OCTOPUS_WIRE_HEART_WORK"] = "1"
    try:
        wiring._HEART_STATE["last_epoch"] = 0
        out = wiring.heart_beat(beat=20)
        assert out is not None and "work" in out, out
    finally:
        os.environ.pop("OCTOPUS_WIRE_HEART", None)
        os.environ.pop("OCTOPUS_WIRE_HEART_WORK", None)


def t_i_structural_no_toplevel_money_and_bounded():
    """I2: هیچ importِ پولی سطحِ ماژول؛ paid-lane مستند به organ_gate؛ هر پنجره ≤۱ کار."""
    src = Path(wp.__file__).read_text("utf-8")
    head = src.split("def pump_step")[0]
    for bad in ("import organ_gate", "from organ_gate", "import money_gate",
                "import budget_gate"):
        assert bad not in head
    assert "organ_gate" in src                 # قرارداد در paid-lane مستند است
    assert src.count("picked = tpl") == 1      # حداکثر یک task per پنجره (ضدِ طوفان)


def t_i2_beat_path_does_not_leak_syspath():
    """نشتِ 2026-07-24: مسیرهای per-beat با sys.path.insert بی‌گارد هر ضربان یک ورودیِ
    تکراری اضافه می‌کردند (۵۰ ضربان = ۵۲ تکراری) و در پروسهٔ چندروزه هر import را کند
    می‌کرد. حالا idempotent: ۵۰ ضربان = صفر رشد."""
    import sys as _s
    before = len(_s.path)
    for i in range(50):
        wiring.heartstate_beat(beat=i)          # فلگ خاموش → no-op، فقط مسیرِ import
        wp._emit_event("task.probe", "test/probe", summary="p")
    # سنجه = رشدِ صفر در مسیرِ ضربان (تکراری‌های موجود از setupِ خودِ harness/تست‌اند)
    assert len(_s.path) == before, f"sys.path رشد کرد: {before} → {len(_s.path)}"
    # ساختاری: هر insertِ درون-تابعیِ باقی‌مانده باید بلافاصله پشتِ گاردِ «not in ...path» باشد
    for mod in (wp, wiring):
        lines = Path(mod.__file__).read_text("utf-8").splitlines()
        assert "def _syspath" in "\n".join(lines)
        for i, ln in enumerate(lines):
            if ln.startswith((" ", "\t")) and "path.insert(0," in ln:
                prev = lines[i - 1] if i else ""
                assert "not in" in prev and "path" in prev, \
                    f"{mod.__name__}:{i + 1} insertِ بی‌گارد: {ln.strip()}"


def t_j_watchdog_runner_exists_and_owner_gated():
    """runnerِ boot: ps1 موجود، به watchdog.py وکالت می‌دهد، ثبتِ تسک = دستورِ مالک."""
    ps1 = Path(__file__).resolve().parents[1] / "organism-watchdog.ps1"
    assert ps1.exists()
    src = ps1.read_text("utf-8")
    assert "watchdog.py" in src and "RUN-ORGANISM.bat" in src
    assert "schtasks /Create" in src           # فقط مستند — ایجنت اجرا نمی‌کند
    assert "REVIVE" in src
    import watchdog
    should, reason = watchdog.should_revive(port_alive=True)
    assert should is False                     # ارگانیسمِ زنده → هرگز دوباره‌روشن


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_heart_work: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
