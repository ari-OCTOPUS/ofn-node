# LANE-REPORT - L8

## What was done
Wrote pass criterion first (`09-LANES/L8/PASS-CRITERION.md` sha 96206c74). Read-only outside `09-LANES/L8/`. Extracted one real hash chain from `.cursor/hook-ledger.jsonl` (sha 78443439, 1409 bytes, 5 JSONL rows). chain_ok True this session (python walk: each prev_hash equals prior this_hash; genesis prev_hash 64 zeros). Causal chain (kind -> this_hash-12): egress_denied a0513652dc97 -> destructive_denied 979446a8542a -> secret_read_denied 3aa48384456c -> INCIDENT_flag_enable_attempt 60a096f3c4b0 -> mcp_denied_unknown_server 2777bf4d150a. All timestamps 2026-09-01T23:33:11+1000 or 2026-09-01T23:33:12+1000 on that file. L1 dependency present (`09-LANES/L1/LANE-REPORT.md` sha 9df6f4ea). contradictions.csv used as a second topology (29 data rows, 30 lines, sha cf4ab342): dual-valued open rows, no winner picked. Graph build is a proposal only: do not write `ledger/`; optional later job could emit a node-edge JSON from the jsonl hash pointers.

## What remains
- Ledger has only the install smoke five rows; later session actions are not in this jsonl (information not present, not inferred).
- Graph builder not implemented (deferred).
- Baselines: persistence beaten for chain walk vs "unverified". prior-only: L1 findings are context, not a new ledger chain. random: not used, not beaten.

## What failed
- Information loss named from files, not repaired:
  1. Schema drift across the five rows (keys differ: command/reason vs file_path vs matches vs server/tool). Source: per-row keys listed from hook-ledger.jsonl.
  2. No `reason` on egress, secret, flag, or mcp rows (only destructive_denied has reason).
  3. jsonl does not record the Cursor session id or git HEAD, so the chain cannot be joined to `07-HANDOFF/contradictions.csv` L0-GIT-HEAD without an extra join key (missing).
  4. gitwrite.lock absent now while GITWRITE-FAILED.flag remains (`_ops/backup/GITWRITE-FAILED.flag` sha 75e59b45); lock-file causal edge is gone from disk.
  5. contradictions.csv status remains open on sampled L0 rows; no resolved runtime source in those first four rows.

## Evidence paths
| Claim | Value | Source path | Grade | Status |
|---|---|---|---|---|
| criterion hash | 96206c74 | 09-LANES/L8/PASS-CRITERION.md | E2 | verified |
| ledger sha / rows | 78443439 / 5 | .cursor/hook-ledger.jsonl | E2 | verified |
| chain_ok | True | python walk this session on that jsonl | E2 | verified |
| csv lines | 30 (29 data) | 07-HANDOFF/contradictions.csv | E2 | verified |
| gitwrite flag | 40 attempts, 2026-09-01_045025 | _ops/backup/GITWRITE-FAILED.flag sha 75e59b45 | E2 | verified |
| gitwrite.lock | absent | Test-Path F:\backup\_ops\backup\gitwrite.lock | E2 | verified |
| post-install ledger completeness | unverified | n/a | E0 | unverified |

## Rollback steps
Move `09-LANES/L8/` to `99-ARCHIVE/` with `archive_` prefix. Do not rm -rf. Do not write `ledger/` or `src/`. Leave `.cursor/hook-ledger.jsonl` and `07-HANDOFF/contradictions.csv` untouched.