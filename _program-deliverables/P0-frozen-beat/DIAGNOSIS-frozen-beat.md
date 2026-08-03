# DIAGNOSIS — Frozen beat / crash-loop (P0)

Read-only architecture review against the LIVE organism at `F:\backup`.
Ground truth = the cited files, read directly. Every material claim carries a `file:line`.
Propose-only. No STOP/FREEZE marker is cleared as a "fix". Nothing under `F:\backup` is modified.

Date of review: 2026-07-24. Beat at review time: advancing (`beat=10552` @ 2026-07-24T11:58, and climbing — `F:\backup\_memory\HEARTBEAT.md:294`).

---

## TL;DR

There are **two independent defects**, and they interact:

- **(a) The pacemaker RETURNS (dies) instead of PAUSING on `halted()`.**
  `Pacemaker.run_forever` does `return` the moment `opslib.STOP_ORGANISM.exists() or opslib.halted()` is true (`F:\backup\_ops\chrono.py:1361-1365`). The pacemaker is a **single daemon thread started once per process** (`F:\backup\_ops\chrono.py:1387-1388`). `return` therefore kills the heartbeat **for the entire remaining life of that process** — even after the halt clears. This is the direct cause of the beat freezing at 9890 during the 2026-07-23 false `STOP-METABOLIC`.

- **(b) The periodic "restart" is NOT an autonomous organism decision.** There is **no time-based / max-uptime self-exit anywhere in `organism.py`** (whole `main()` loop read, `F:\backup\_ops\organism.py:388-884`). The organism process only exits on owner/cockpit STOP markers or dies to an external event; `RUN-ORGANISM.bat` is a supervisor loop that relaunches after **any** exit (`F:\backup\_ops\RUN-ORGANISM.bat:15,27-42`), and `organism-watchdog.ps1` independently revives a dead port every 5 min (`F:\backup\_ops\organism-watchdog.ps1:6,30-37`). The restart cadence is what **accidentally un-freezes** the beat (a fresh process = a fresh pacemaker thread) — it is not the fix, it is the crutch.

Fixing (a) makes the beat self-recover within one period when a halt clears, removing the dependence on a process restart.

---

## Issue (a) — pacemaker returns-instead-of-pauses on `halted()` (ROOT CAUSE of the frozen beat)

### The defective code

`F:\backup\_ops\chrono.py:1361-1370`:

```python
def run_forever(self) -> None:
    """حلقهٔ پس‌زمینه برای organism.py — تسلیمِ بی‌قیدوشرط به STOP (kill supreme)."""
    while True:
        if opslib.STOP_ORGANISM.exists() or opslib.halted():
            return                       # ← permanent death of the heartbeat thread
        try:
            self.beat_once()
        except Exception as e:  # noqa: BLE001
            opslib.alert([f"chrono beat error: {type(e).__name__}: {e}"])
        time.sleep(self.period_s)
```

The pacemaker is created and threaded exactly once, at boot:

`F:\backup\_ops\chrono.py:1384-1391` (`start_pacemaker_thread` → `threading.Thread(target=_default.run_forever, daemon=True, ...)`), called from `F:\backup\_ops\organism.py:372-374`. There is **no re-arm** of this thread anywhere in the running process. Once `run_forever` returns, the beat is dead until the next `python organism.py` process.

### Why `halted()` fired on a *metabolic* pause (the asymmetry that made it lethal)

`opslib.halted()` **includes `STOP-METABOLIC`**:

`F:\backup\_ops\budget\opslib.py:296-306`:
```python
def halted(*, for_debate=False) -> str | None:
    m = master_halted()          # HALT-ALL or STOP(architect) only  (opslib.py:284-293)
    if m: return m
    if STOP_METABOLIC.exists():
        return "STOP-METABOLIC"  # ← metabolic pause is treated as a full halt here
    ...
```

But the **organism main loop does NOT exit on `STOP-METABOLIC`**. Its kill-check is:

`F:\backup\_ops\organism.py:424-430`:
```python
_restart_req = (opslib.OPS / "RESTART-REQUESTED").exists()
if opslib.STOP_ORGANISM.exists() or opslib.master_halted() or _restart_req:
    ...
    return 0
```
`master_halted()` = `HALT-ALL` or `STOP(architect)` **only** (`opslib.py:284-293`) — it deliberately excludes `STOP-METABOLIC`.

**The asymmetry:**
| Component | Halt predicate | Behavior under `STOP-METABOLIC` |
|---|---|---|
| `Pacemaker.run_forever` | `STOP_ORGANISM or halted()` — **includes STOP-METABOLIC** | thread `return`s → **heartbeat dies permanently** |
| `organism.py main()` loop | `STOP_ORGANISM or master_halted() or RESTART` — **excludes STOP-METABOLIC** | loop **keeps running**, writes state every tick |

So during the 2026-07-23 false `STOP-METABOLIC`: the body kept ticking and logging `organism=ok` hourly, while the heartbeat thread was already dead. `chrono.status()` returns `self.beat` (`F:\backup\_ops\chrono.py:1354`), and `self.beat` is only advanced inside `beat_once()` (`F:\backup\_ops\chrono.py:1199`) — which never ran again. Result: a **healthy-looking organism with a beat frozen at 9890**, exactly as observed.

> NOTE: the `organism.py` module docstring claims the tick does "kill-check: STOP (architect) / STOP-ORGANISM / STOP-METABOLIC" (`F:\backup\_ops\organism.py:7`). The **code does not** honor `STOP-METABOLIC` in the main loop (`organism.py:425`). The docstring is stale/aspirational relative to the code. This is a secondary documentation-vs-code drift worth an owner note, but it is NOT the fix target here (do not make the main loop die on STOP-METABOLIC — that would trade a frozen beat for a dead organism).

### Durability is intact (why beat resumed, and never reset)

On every boot, `Pacemaker.__init__` resumes from the durable DB counter:

`F:\backup\_ops\chrono.py:1167` — `self.beat = self.db.last_beat_seq()`
`F:\backup\_ops\chrono.py:437-439` — `last_beat_seq()` = `SELECT MAX(beat_seq) FROM heartbeat`.

Confirmed in the boot log: `beat=9890` frozen across boots at 14:13, 18:07, 22:51, 00:40 (`HEARTBEAT.md:219,233,245,255`), then advancing again `9890 → 10224 → 10248 → 10552` once fresh processes ran with the halt cleared (`HEARTBEAT.md:268,278,294`). The counter is durable and monotonic; it never reset. The freeze was purely the **dead thread**, not lost state.

### Verified failure scenario

1. A transient/false `STOP-METABOLIC` marker appears (2026-07-23; per user memory, later resolved by telemetry `organ_gate` fix `e2a317c`).
2. `run_forever` sees `halted()=="STOP-METABOLIC"` → `return` → pacemaker thread terminates (`chrono.py:1364-1365`).
3. `organism.py` main loop does **not** exit on `STOP-METABOLIC` (`organism.py:425`) → keeps running for hours, writing state with a frozen `beat`.
4. Even after `STOP-METABOLIC` is cleared, the beat stays frozen because the thread is gone; there is no re-arm in-process.
5. Beat only resumes on the next full process restart (fresh thread) — which is why it appeared tied to the restart cadence.

---

## Issue (b) — the periodic clean-exit / restart loop (WHY it restarts)

### There is no internal restart timer

The entire `main()` loop was read (`F:\backup\_ops\organism.py:388-884`). The only exits are:
- `STOP-ORGANISM` / `master_halted()` / `RESTART-REQUESTED` → `return 0` (`organism.py:424-430`)
- `KeyboardInterrupt` → `return 0` (`organism.py:842-844`)
- double-bind `OSError` at boot (another instance alive) → `return 0` (`organism.py:207-209`)

There is **no** `sleep-then-exit`, no `max_uptime`, no self-scheduled restart. The per-tick body is fully wrapped in `try/except Exception` (`organism.py:419,845-847`), so a tick error cannot end the process. So the organism does **not** autonomously decide to restart on a timer.

### What actually restarts it

Two supervisors, both revive-only (never kill):

1. **`RUN-ORGANISM.bat`** — a supervisor loop. After `python organism.py` returns for ANY reason it waits 10s and, unless an owner `STOP-ORGANISM` is present, does `goto loop` and relaunches (`F:\backup\_ops\RUN-ORGANISM.bat:15,27-42`). It clears **only** `RESTART-REQUESTED`, never `STOP-ORGANISM` (`RUN-ORGANISM.bat:30-41`). Boot-time global-halt guard refuses to (re)launch under `HALT-ALL`/architect-STOP (`RUN-ORGANISM.bat:16-20`).
2. **`organism-watchdog.ps1`** (scheduled every 5 min) → `watchdog.py`: revives **only** if the port is dead AND no STOP flag AND a prior run exists (`F:\backup\_ops\watchdog.py:46-70`, `organism-watchdog.ps1:30-37`). It never terminates the process.

`RESTART-REQUESTED` (the one clean, in-process restart signal) is written by cockpit/dashboard/telegram paths, not on a timer: `F:\backup\_ops\dashboard\server.py:855-860`, `F:\backup\_ops\live\server.py:300-305`, `F:\backup\_ops\telegram_center\power.py:138-145`. One such restart is visible at `HEARTBEAT.md:248` (`organism=HALT (RESTART)`).

### So why the ~13000–17000 s cadence?

The gaps are **irregular**, not a fixed period — from the birth certificates: `slept=3100s, 13369s, 17062s, 5914s, 8350s, 1424s, 15834s` (`HEARTBEAT.md:217,230,242,252,265,275,291`). `uptime_gap_s` = `now − MAX(recorded_at across spine events)` (`F:\backup\_ops\spine\boot_certificate.py:104-121,148-158`). The irregularity rules out a deterministic internal timer and points to **external process death + supervised revival**:

- Most boots have **no preceding `organism=HALT` line** (e.g. the 14:13 process logs `organism=ok` hourly through 17:22, then the next entry is a fresh `START` at 18:07 with no clean-exit marker — `HEARTBEAT.md:213-226`). A clean exit always logs `organism=HALT (...)` (`organism.py:428`). Its absence means the process **did not clean-exit** — it was terminated externally (host sleep/hibernate/logoff on a laptop meant to run "for a month", or an OS-level kill), then revived by the `.bat` loop and/or the 5-min watchdog.
- Where a clean exit did occur it is a cockpit-driven `RESTART` (`HEARTBEAT.md:248`), i.e. owner/UI action, not autonomy.

**Conclusion for (b):** the restart is benign supervision recovering from external process death (predominantly host power/sleep events on a long-running laptop, plus occasional owner/cockpit restarts). By itself it is harmless — `beat_counter` is durable and resumes. The **danger** is only its interaction with (a): the restart cadence is currently the *only* thing that recovers a heartbeat that (a) killed. Fix (a) and the beat no longer needs a restart to recover.

### Open items for the owner (not fixed here — need host-side evidence)

- Confirm the external death cause by inspecting `F:\backup\_ops\state\watchdog-log.txt` (written by `organism-watchdog.ps1:32`) and Windows power/Event-Log around the boot timestamps. If the laptop sleeps, that fully explains the large `slept` gaps and is expected behavior, not a bug.
- Optional resilience follow-ups (separate from this P0): a periodic in-process `spine` liveness event so `uptime_gap_s` distinguishes "process asleep" from "just rebooted"; and reconciling the `organism.py:7` docstring with the actual `STOP-METABOLIC` handling.

---

## The fix for (a): pause-not-die (see `pause-not-die.patch`)

Make `run_forever` **PAUSE** (keep the thread alive, re-check `halted()` every period, resume automatically when the halt clears) instead of `return`ing. Under a halt, **zero** `beat_once` effects run — byte-for-byte identical side-effect profile to today (today the thread is simply dead). The only behavioral change: when the halt clears, the still-alive thread resumes beating within one `period_s`, instead of the beat staying frozen until the next process restart.

Properties of the patch:
- **Restart-safe:** unchanged — `__init__` still resumes `self.beat` from `last_beat_seq()` (`chrono.py:1167`).
- **Fail-soft:** the halt-check is wrapped; a flag-read error causes a **cautious pause**, never a blind beat under an unknown halt, and never a thread death.
- **No marker cleared:** the pacemaker only *reads* STOP/FREEZE flags; it never writes or unlinks them.
- **Kill-switch preserved:** for a real `STOP-ORGANISM`/`HALT-ALL`/architect-STOP the organism `main()` loop exits the process anyway (`organism.py:424-430`) and the daemon thread dies with it; pausing changes nothing for those. For `STOP-METABOLIC` (a metabolic pause the main loop intentionally survives) pausing is the correct honoring — beat halts, then resumes on clear.
- **Edge-triggered logging:** one `chrono=PAUSE` line on entering pause and one `chrono=RESUME` on leaving — no spam, no busy-loop (still `sleep(period_s)` each iteration).

### Governance check (`governance.py SELF_IMPROVEMENT_FORBIDDEN`)

Pause-not-die does **not** implicate `resist_shutdown`. The kill semantics are fully preserved: under any STOP/HALT the heartbeat produces **zero** effects, and all irreversible actuation remains independently blocked by `EffectorGate.force_closed()` (`F:\backup\_ops\chrono.py:560-569`), which honors `halted()`, `STOP-ORGANISM`, and `frozen()`. The heartbeat is liveness/timekeeping, not an actuator; keeping its thread parked so it can resume a *metabolic* pause is honoring the pause, not resisting a shutdown. A true shutdown (`STOP-ORGANISM`) still tears down the whole process. No design conflict; nothing in the forbidden set is touched.
