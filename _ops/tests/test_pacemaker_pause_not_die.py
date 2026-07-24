#!/usr/bin/env python3
"""pause-not-die: STOP-METABOLIC = توقفِ برگشت‌پذیر، kill supreme = خروجِ دائم.

پس‌زمینه (رفعِ frozen-beat ۲۰۲۶-۰۷-۲۳): `chrono.Pacemaker.run_forever` روی `opslib.halted()`
برای همیشه return می‌کرد؛ چون `halted()` برای STOP-METABOLIC هم truthy است، یک STOP-METABOLICِ
کاذب نخِ ضربان را برای همیشه می‌کشت (beat روی 9890 یخ زد) در حالی که پروسهٔ organism زنده بود
(organism.py فقط روی master_halted() خارج می‌شود، نه STOP-METABOLIC).

اثبات‌ها:
  1. تصمیمِ هر تیک: default→beat · STOP-METABOLIC→pause (نه stop) · kill supreme→stop.
  2. kill supreme بر STOP-METABOLIC مقدم است.
  3. رفتارِ حلقه: زیرِ STOP-METABOLIC هیچ beat نمی‌خورد ولی حلقه return نمی‌کند؛ با رفعِ شرط
     خودکار دوباره می‌تپد؛ با kill supreme خارج می‌شود. همه $0، آفلاین، بدونِ sleepِ واقعی."""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("pacemaker_pause")
import opslib  # noqa: E402
import chrono  # noqa: E402


def _pm():
    clock = lambda: 1_000_000  # noqa: E731 — ساعتِ ثابتِ تزریقی
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-pause.db")
    return chrono.Pacemaker(db=db, bus=chrono.ChronoBus(clock), clock=clock)


def _clear():
    for f in (opslib.STOP_ORGANISM, opslib.HALT_ALL, opslib.STOP_ARCHITECT, opslib.STOP_METABOLIC):
        try:
            f.unlink()
        except OSError:
            pass


def _raise(flag, text="x"):
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.write_text(text, "utf-8")


# ─── ۱) تصمیمِ هر تیک ──────────────────────────────────────────────────────────
def t_default_beats():
    _clear()
    assert _pm()._tick_decision() == "beat"


def t_metabolic_pauses_not_stops():          # هستهٔ فیکس
    _clear()
    _raise(opslib.STOP_METABOLIC, "false-alarm")
    assert _pm()._tick_decision() == "pause"


def t_metabolic_clears_resumes():
    _clear()
    _raise(opslib.STOP_METABOLIC)
    pm = _pm()
    assert pm._tick_decision() == "pause"
    opslib.STOP_METABOLIC.unlink()
    assert pm._tick_decision() == "beat"      # همان instance، بدونِ restart


def t_stop_organism_kills():
    _clear()
    _raise(opslib.STOP_ORGANISM, "kill")
    assert _pm()._tick_decision() == "stop"


def t_halt_all_kills():
    _clear()
    _raise(opslib.HALT_ALL, "panic")
    assert _pm()._tick_decision() == "stop"


def t_architect_stop_kills():
    _clear()
    _raise(opslib.STOP_ARCHITECT, "architect")
    assert _pm()._tick_decision() == "stop"


def t_kill_supreme_precedes_metabolic():
    _clear()
    _raise(opslib.STOP_METABOLIC)
    _raise(opslib.STOP_ORGANISM, "kill")
    assert _pm()._tick_decision() == "stop"


# ─── ۲) رفتارِ حلقهٔ run_forever (بدونِ sleepِ واقعی) ────────────────────────────
def _run_forever_scripted(pm, script):
    """run_forever را اجرا کن؛ به‌جای sleepِ واقعی، `script(n)` را صدا بزن (n=شمارهٔ تیک).
    شمارشِ beatها را برمی‌گرداند. sleepِ ماژول را موقتاً fake می‌کند (بدونِ لمسِ stdlib)."""
    beats = {"n": 0}
    pm.beat_once = lambda: (beats.__setitem__("n", beats["n"] + 1), {})[1]  # شمارنده، بدونِ DB
    calls = {"n": 0}
    saved = chrono.time

    def fake_sleep(_s):
        calls["n"] += 1
        script(calls["n"])
    chrono.time = types.SimpleNamespace(sleep=fake_sleep, time=lambda: 0.0)
    try:
        pm.run_forever()
    finally:
        chrono.time = saved
    return beats["n"], calls["n"]


def t_run_forever_metabolic_suppresses_beats_until_kill():
    """زیرِ STOP-METABOLICِ ماندگار: صفر beat، ولی حلقه نمی‌میرد — تا kill supreme خارجش کند."""
    _clear()
    _raise(opslib.STOP_METABOLIC)
    pm = _pm()

    def script(n):
        if n >= 3:                     # پس از ۳ تیکِ pause، مالک kill می‌زند
            _raise(opslib.STOP_ORGANISM, "kill")
    beats, ticks = _run_forever_scripted(pm, script)
    assert beats == 0, f"در pause نباید بتپد؛ beats={beats}"     # اثباتِ suppress
    assert ticks >= 3, ticks                                     # حلقه زنده ماند (نمرد)
    # و در نهایت خارج شد (اگر نمی‌شد، اینجا نمی‌رسیدیم = تعلیقِ بی‌نهایت)


def t_run_forever_resumes_after_metabolic_clears():
    """STOP-METABOLIC رفع شود → همان نخ دوباره می‌تپد (اثباتِ رفعِ frozen-beat)."""
    _clear()
    _raise(opslib.STOP_METABOLIC)
    pm = _pm()

    def script(n):
        if n == 2:
            opslib.STOP_METABOLIC.unlink()          # رفعِ شرطِ کاذب
        if n == 4:
            _raise(opslib.STOP_ORGANISM, "kill")    # سپس خاتمهٔ حلقه
    beats, ticks = _run_forever_scripted(pm, script)
    assert beats >= 1, f"پس از رفعِ metabolic باید دوباره بتپد؛ beats={beats}"  # اثباتِ resume


def t_run_forever_stop_organism_exits_immediately():
    """رفتارِ kill supreme دست‌نخورده: با STOP-ORGANISM بلافاصله خارج، صفر beat."""
    _clear()
    _raise(opslib.STOP_ORGANISM, "kill")
    pm = _pm()
    beats, ticks = _run_forever_scripted(pm, lambda n: None)
    assert beats == 0 and ticks == 0, (beats, ticks)   # همان تیکِ اول return


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("t_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
            passed += 1
        except Exception:  # noqa: BLE001
            print(f"FAIL  {fn.__name__}")
            traceback.print_exc()
    print(f"\n{passed}/{len(fns)} pass")
    sys.exit(0 if passed == len(fns) else 1)
