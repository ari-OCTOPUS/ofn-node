# Restart attempt 2 — 2026-08-20 RESULT: OK

script: `_ops/RESTART-ALL.ps1`
ATTEMPT2_START: 2026-08-20T11:42:46+10:00
ATTEMPT2_END: 2026-08-20T11:50:26+10:00
ATTEMPT2_EXIT: 0

## Raw stdout (trimmed to RESULT)

```
=== PREFLIGHT ===
  beat         : 42778
  cortex       : pid=19352   started 03:52:09
  organism     : pid=10028   started 03:52:09

=== RESTART cortex ===
AFTER  : pid=25284 started 11:44:30
OK: restarted with fresh code.

=== RESTART center ===
AFTER  : pid=25372 started 11:45:06
OK: restarted with fresh code.

=== RESTART gateway ===
AFTER  : pid=9120 started 11:45:15
OK: gateway restarted with fresh code.

=== RESTART live ===
AFTER  : pid=27124 started 11:45:17
OK: restarted with fresh code.

=== RESTART organism ===
AFTER  : pid=7096 started 11:47:04
OK: organism running with fresh code.

=== ACCEPTANCE GATE ===
  OK   cortex    pid 19352 -> 25284
  OK   center    pid 18536 -> 25372
  OK   gateway   pid 10504 -> 9120
  OK   live      pid 20180 -> 27124
  OK   organism  pid 10028 -> 7096
  OK   no markers left behind
  WARN flag drift across restarted limbs: center=340 cortex=340 live=345 organism=345
  OK   fresh state (boot=2026-08-20T11:47:04) at 2026-08-20T11:50:24
  OK   beat 42778 -> 42780

RESULT: OK - every limb restarted, verified, and beating.
ATTEMPT2_EXIT=0
```

Attempts this work-order: 2. Attempt 1 PARTIAL fail-closed. Attempt 2 OK.

Post-boot life-currency: `life-currency-latest.post.json` · ts 11:47:25 · beat 42780 · daily_cap=30.0 · unit=life_credit · min tokens=0.003 · any_zero=false
