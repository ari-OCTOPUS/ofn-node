# Stage D — Live Limbs / Restart Decision

- Verdict: **PASS — restart not required**
- Reason: all five limbs have fresh 21:09–21:10 start times, fresh per-process flag snapshots, open service ports, and organism state continued updating through beat 31734 at 22:36:55.
- No restart marker was created; no process was interrupted.

## Live conditions

- APPLY=`0`, PROPOSAL=`1` in center/cortex/live/gateway/organism boot snapshots.
- Organism PID: 15916; `started=2026-08-11T21:10:38`.
- Fresh state: `ts=2026-08-11T22:36:55`, `beat=31734`.
- `protective_skip=false`; current-beat `protective_proposal=None` (normal low-pain beat).

## Synthetic high-pain contract

Tested in an isolated subprocess with APPLY=0 / PROPOSAL=1:

```text
pain.level=0.95
→ action=protective_proposal
→ executable=false
→ override=false
→ shadow_alert=true
```

This proves high neural pain remains a proposal/SHADOW alert and cannot directly set the organism skip/halt path.

## Controlled restart after Stage F additive runtime fixes

A restart became necessary after the owner-console intent/cap patches so center/gateway would load fresh code.

| Limb | Before PID | After PID |
|---|---:|---:|
| cortex | 22976 | 5680 |
| center | 21968 | 14272 |
| gateway | 14904 | 13292 |
| live | 21528 | 16448 |
| organism | 15916 | 9476 |

`RESTART-ALL.ps1` acceptance confirmed all five fresh PIDs, no leftover markers, and 316 equal flags per limb. Its 120-second freshness gate timed out before the organism's next cadence tick (known false-negative class). The independent post-wait proof succeeded:

```text
8771 listening: pid 9476
8774 listening: pid 13292
state started=2026-08-11T22:56:57
state ts=2026-08-11T22:59:53
beat=31754
protective_skip=false
APPLY=0 / PROPOSAL=1 in all 5 snapshots (316 flags each)
```

Final restart verdict: **PASS (acceptance freshness timeout independently resolved)**.
Log: `restart-after-fixes.log`.
