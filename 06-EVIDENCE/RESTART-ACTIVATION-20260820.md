# RESTART + ACTIVATION EVIDENCE — 2026-08-20

- **Owner approval:** «ری‌استارت کن» (AskUserQuestion answers, 2026-08-19)
- **Runbook:** `_ops/RESTART-ALL.ps1` (delegated by `_ops/RESTART-ALL.bat`; includes per-limb acceptance gate)
- **Attempt 1 (~00:23–00:29 local):** partial — gateway/live restarted; cortex/center/organism stayed on old PIDs (stop markers not observed within 300s; fail-closed, no double-launch). Markers cleaned.
- **Attempt 2 (~00:40–00:48 local):** FULL SUCCESS.

## Before → After (PIDs)

| Limb | Before | After | Status |
|---|---:|---:|---|
| organism | 1196 (15:22:46) | 26892 (00:45:34) | OK |
| cortex | 3516 | 4564 | OK |
| center | 5484 | 9204 | OK |
| gateway | 14852 → 28324 (attempt 1) | 28396 | OK |
| live | 14864 → 10768 (attempt 1) | 14572 | OK |

## Acceptance gate (RESTART-ALL.ps1 output, attempt 2)

```
OK cortex 3516 -> 4564 · OK center 5484 -> 9204 · OK gateway 28324 -> 28396
OK live 10768 -> 14572 · OK organism 1196 -> 26892
OK no markers left behind · OK fresh state (boot=2026-08-20T00:45:34)
OK beat 42159 -> 42165
WARN flag drift: center=340 cortex=340 live=345 organism=345 (pre-existing pattern; live/organism always loaded 345)
RESULT: OK
```

## Post-restart live verification (path + method + timestamp + grade)

| Check | Result | Evidence |
|---|---|---|
| Novelty gate verdict active | True | `novelty_gate_enabled()` reads `verdicts.wire_novelty_gate=1` (2026-08-20T00:49, VERIFIED) |
| B1 life-currency live allocation | daily_cap=1000.0 · 11 members · beat_pool=1.246 | `_ops/state/pulse/life-currency-latest.json` beat 42165 (OBSERVED) |
| Web UI | HTTP 200 | `http://127.0.0.1:8771/` (OBSERVED) |
| CURRENT-TRUTH | coherence 0.985 · beat 42163 · HEAD 5a1c22d | `OCTOPUS/CURRENT-TRUTH.md` (OBSERVED) |

## Meaning

- For the first time since `life-currency.v1` existed, the live organism allocates a non-zero daily pool (1000/day → ~1.25/beat → 11 members). Root cause (missing `daily_cap`) fixed by B1 fallback; rollback documented in `02-DECISIONS/PROPOSAL-B1-cardiac-dailycap-wiring-2026-08-19.md`.
- The debate novelty gate is armed via owner verdict; fail-soft, reversible (`value: 0`).
- K=9 pilot result stands: RS_AB=RS_BA=1.0 at K=9 → CONSISTENT/STABLE; 20 calls, 0 VOID, cost micro (receipts in `_ops/state/pipeline/pilot-k9-receipts.jsonl`).
- Owner-key.enc: still UNVERIFIED (no path provided yet) — separate open item.
