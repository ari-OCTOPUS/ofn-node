# LANE-REPORT — L2

## What was done
Retained D8-02 as v1. Wrote v2 from season file. No live winner. Criterion a15a5166.

## What remains
Synthetic blind test blocked. L3-L6 stay blocked on that gate.

## What failed
Matrix synthetic test vs AGENTS.md. Blocked honest. Baselines not beaten.

## Evidence paths
| Claim | Value | Source path | Grade | Status |
|---|---|---|---|---|
| criterion | a15a5166 | 09-LANES/L2/PASS-CRITERION.md | E2 | verified |
| v1 STRATEGY_BRIER | 0.34565 | metrics/recorded_replay_brier.v1.md | E2 | verified |
| v2 STRATEGY_BRIER | 0.237387 | metrics/recorded_replay_brier.v2.md | E2 | verified |

## Rollback steps
Archive v2 and 09-LANES/L2 to 99-ARCHIVE/. Keep v1. No rm -rf.
