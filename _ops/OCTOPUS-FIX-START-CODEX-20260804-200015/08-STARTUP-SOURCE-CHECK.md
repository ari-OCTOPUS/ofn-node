# 08 — Startup source check

Read `_ops/RUN-ORGANISM.bat` in full (57 lines). Line 26:

```bat
if exist "F:\backup\_ops\OCTOPUS-flags.cmd" call "F:\backup\_ops\OCTOPUS-flags.cmd"
python -X utf8 organism.py
```

This `call` happens **immediately before** `python organism.py` launches, and happens again
on every loop iteration (`:loop` label) — so a restart-triggered relaunch (via
`RESTART-REQUESTED`) also re-sources the flags file with whatever is on disk at that moment.

## Verdict

**FLAGS_EFFECTIVE_ON_NEXT_BOOT: yes.** Startup genuinely reads `OCTOPUS-flags.cmd`; this is
not a case of "flags written but never read" (the failure mode the master instruction asked
us to check for). The only gap is time, not wiring: the *currently running* process was
already alive before today's flag edits, so it is running with whatever env it captured at
its own boot — not today's values — until it is restarted. See `10-SAFE-RESTART-PLAN.md`.
