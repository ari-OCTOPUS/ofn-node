---
type: report
status: closed_residue_accepted
tags: [octopus, ex1, criterion]
updated: 2026-09-07
---

# MP-EX1-CRITERION-20260907 — LANE-REPORT

GOV_VERSION=V8 · LADDER=L2 · V7-locks retained  
kind=`advisor_proposal` · may_authorize=false  
owner answer recorded as `owner_chat_answer` (not `owner_ruling`).

## What was done

- Evaluated existing EX1 receipts locally (`evaluate_ex1_criteria.py`). Work-order hash rematch: `ca736a4724ddac884fd39108dc6089e907fba6f1439ba61ff71cc7681cdaa4e3`.
- Did not re-run the board EX1 SSH test. Did not drop 194298/194329 from baseline. Did not declare EX1 PASS. Did not start EX3.
- After the owner chat answer: registered three layers in `THREE-RESULTS.json` (log `H-G`). Wrote exact contradiction table. Wrote EX3 precondition note. Wrote unadopted v3.1 draft. Wrote unapplied EX2 direction proposal.

## Three results (owner-requested split)

1. Existence/content: MEASURED only for keys actually present on receipts. 194298: event/reason/seq/calib_tail. 194329: event/reason/seq; `owner_go_id` open (receipt vs debug filter).
2. Halt and mint modes: both observed once. Not a rate, stability, or quality claim.
3. EX1 original contract: **NOT_PASSED**. Unmet: `reason_code`, per-record trio, `mint_evidence.calib_tail` on 194329, specified `verify_chain` OK.

## What remains

- v3.1 draft not adopted. EX2 direction proposal not applied. Source lineage / loaded revision / node182 / RuntimeTruthRow unchanged.
- EX3 blocked: v3.0 PASS unmet; row timestamps UNKNOWN (probe filter). See `EX3-PRECONDITIONS.md`.
- Owner declined EX2 code work this session: leave the local candidate uncommitted and unaligned. New go required before any EX2 mutation.

## What failed

- Literal EX1 v3.0 expect remains false (`CRITERION-EVAL.json` `literal_ex1_pass=false`). Expected under the frozen contract.

## Evidence

`CURRENT-STATUS.md` · `STALE-POINTERS.md` · `STALE-POINTER-CHECK.json` · `THREE-RESULTS.json` · `F:/backup/debug-df323e.log` (`runId=stale-pointers`)

## Rollback

Delete this lane's new files and additive handoff/pin. Do not delete MP-DEBUG / MP-EXEC receipts or the two ledger seqs.

## Non-actions

SSH=0 · EX3=0 · worktree=0 · commit/push/deploy=0 · verifier/threshold unchanged=yes · service/flag/secret/message/purchase=0
