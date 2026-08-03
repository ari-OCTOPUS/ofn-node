# OWNER-GATE CARD — P0: pause-not-die heartbeat fix

**Proposal:** Change `Pacemaker.run_forever` in `_ops/chrono.py` so the heartbeat **pauses** under STOP/HALT instead of permanently killing its thread.

**What you are approving**
- Apply `pause-not-die.patch` (one method rewritten + one small helper `_halt_reason` added) to `F:\backup\_ops\chrono.py`.
- After apply, the pacemaker daemon thread, on any halt (`STOP-ORGANISM`, `HALT-ALL`, architect `STOP`, or `STOP-METABOLIC`), will **stop beating but stay alive**, re-check the halt each period, and **automatically resume** beating when the halt clears — instead of `return`ing and freezing the beat until the next process restart (root cause of the beat=9890 freeze on 2026-07-23).

**What this does NOT change / does NOT do**
- Does **not** clear, weaken, or bypass any STOP/FREEZE/HALT marker. The pacemaker only *reads* the flags.
- Does **not** change side-effects under halt: zero `beat_once` effects run while halted — identical to today. All irreversible actuation stays blocked by `EffectorGate.force_closed()` (unchanged).
- Does **not** touch the durable `beat_counter` (still resumes from `last_beat_seq()`), the genome, `.env`, budget state, `_ops/OCTOPUS-flags.cmd`, or any kill-switch file.
- Does **not** touch issue (b) (the periodic restart): that is external process death + supervised revival, benign on its own; no code change proposed for it here (only owner-side host/power-log verification suggested).
- No governance boundary is implicated: this is not `resist_shutdown` — a real `STOP-ORGANISM` still tears down the whole process via the `organism.py` main loop; only the *metabolic pause* path gains auto-resume.

**Scope of change:** exactly one file, one method + one helper. `git apply --check` = clean; result parses as valid Python (verified against a copy; nothing under `F:\backup` was modified during review).

**Verification after apply (owner)**
1. Restart the organism once so the new `run_forever` is loaded.
2. Write a test `STOP-METABOLIC` marker → expect one `chrono=PAUSE beat=<n>` heartbeat line and the beat to stop advancing (no thread death).
3. Delete the `STOP-METABOLIC` marker → expect one `chrono=RESUME beat=<n>` line and the beat to advance again **without any process restart**. This is the behavior that was broken.

**Rollback:** `git apply -R pause-not-die.patch` (or `git checkout -- _ops/chrono.py`), then restart the organism. Zero data migration; the change is pure control-flow in one method, so reverting is instant and stateless.

**Residual risk:** minimal. Worst case if `opslib.halted()` raises, the helper fail-**safe**s to a pause (never a blind beat, never a thread death). The only new persistent effect is two edge-triggered heartbeat log lines (PAUSE/RESUME).
