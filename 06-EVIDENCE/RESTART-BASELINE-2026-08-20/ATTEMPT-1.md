# Restart attempt 1 — 2026-08-20 (fail-closed / partial)

script: `_ops/RESTART-ALL.ps1`
started_at: 2026-08-20T11:19:54Z (~11:20 +10)
preflight_beat: 42770
preflight_pids: organism 10028 · cortex 19352 · center 20816 · gateway 15440 · live 26008

## Raw (from script stdout)

```
=== RESTART cortex ===
TIMEOUT: old process still alive. Nothing relaunched.
  runner exit code 2 for 'cortex'

=== RESTART center ===
AFTER  : pid=18536 started 11:29:20
OK: restarted with fresh code.

=== RESTART gateway ===
AFTER  : pid=10504 started 11:29:31
OK: gateway restarted with fresh code.

=== RESTART live ===
AFTER  : pid=20180 started 11:29:43
OK: restarted with fresh code.

=== RESTART organism ===
STOP-ORGANISM + RESTART-REQUESTED written - waiting up to 300s...
```

Terminal session ended before `RESULT:` / `ATTEMPT1_EXIT=` (file later UNLOCATED). Live inspect after:

| limb | PID after | started | verdict |
|---|---:|---|---|
| cortex | 19352 | 03:52:09 | NOT restarted (timeout, fail-closed, no double) |
| center | 18536 | 11:29:20 | restarted |
| gateway | 10504 | 11:29:31 | restarted |
| live | 20180 | 11:29:43 | restarted |
| organism | 10028 | 03:52:09 | NOT restarted |

ORGANISM-STATE at 11:33:00: beat 42778 · started still 03:52:10 · **stop_organism=true** · halted null · frozen false · arbiter GREEN 114.74s

life-currency-latest 11:35:41 beat 42779 · **daily_cap=1000.0** · unit field absent · tokens all 0.097 · no zeros

markers: none on disk after inspect.

Attempt 1 = PARTIAL. Same class as morning fail-closed. Attempt 2 authorized by work-order T4.
