# PC_WORKER_REPLY_PATCH_RESULT
**received:** 2026-08-27 11:28 AEST
**from:** PC_worker (5071c1ec-6aef-4eef-b712-a68501283b89)
**pc_disposition:** REFERENCE_ONLY. Handed to 182 as oracle candidate. 138 review-only. 180 must not apply to production.

```text
PC_WORKER_REPLY_PATCH_RESULT
WORKTREE=F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\pc-worker\worktree
BASE_COMMIT=441af7632dd6e248ccdb4b95f08aebf4f0cca2d6
BUG_REPRODUCED=YES (BuggyWorker: process marks INPUT_PROCESSED then send; send fail -> retry DupBlocked; lost-probe class 16fc28ed)
PATCH_COMMIT=557b6b485a8dfbf671800970a94e6b4a452c5fac
STATE_MACHINE=CLAIMED>PROCESSING>RESPONSE_FROZEN>REPLY_PENDING>TRANSMITTING>REPLY_ACKED>INPUT_PROCESSED
DURABLE_OUTBOX=sqlite jobs table WAL+FULL; frozen bytes+hash+idempotency_key survive reopen
ORPHAN_SCANNER=YES (REPLY_PENDING|TRANSMITTING|RESPONSE_FROZEN -> retry frozen, no model rerun)
START_LIMIT_FIX=run_once exits 0 on no_event and duplicate_blocked
TESTS_TOTAL=24
TESTS_PASS=24
TESTS_FAIL=0
SECRET_SCAN=CLEAN
PRODUCTION_MUTATIONS=0
ROLLBACK=git -C worktree checkout 441af7632dd6e248ccdb4b95f08aebf4f0cca2d6
STATUS=REFERENCE_ONLY not 30f60773; not 180 production; 180 disk untouched
CLAIMED_30f60773=NO
END_RESULT
```

Checkpoint A still OPEN: needs 180 official result + 182 verdict + 138 settle of the official path.
