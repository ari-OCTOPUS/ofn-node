# PC_WAVE0_PLAN

**author:** PC (Lead Architect)
**date:** 2026-08-27 11:22 AEST
**source:** START-HERE-GROK-FIVE-BOT-OCTOPUS.md (owner-attached)
**mutations:** 0
**runtime:** DEGRADED until Checkpoint A + B

```text
PC_WAVE0_PLAN
LIVE_STATE_RECONCILED=partial_from_start_here_plus_session
PRIMARY_BLOCKER=180_reply_lost_processed_before_ack
TASK_180_REPAIR_STATE=official_prefix_30f60773_unclaimed_by_pc
PC_WORKER_ASSIGNMENT=isolated_worktree_repro_patch_24_tests
WITNESS_ASSIGNMENT=182_independent_oracle_no_prod_write
COCKPIT_PARALLEL_WORK=M1_RO_only_ofn/cockpit-v2-20260827
FILES_AT_RISK=180_reply_path;180_outbox;180_disk_90pct;/opt/cellframe-node_untouched
CONFLICTS=none_yet;worktrees_isolated
OWNER_DECISIONS=pc_lead;hold_new_cycles;no_tg_prod;no_biz_effect;no_same_file
NEXT_CHECKPOINT=A_reply_repair_pass
MUTATIONS=0
STATUS=WAVE0_PLAN_READY_DISPATCHING
END_RESULT
```

## LIVE_STATE_RECONCILED

Reconciled from owner START-HERE (2026-08-27) plus this session's live notes. Live SSH/systemd reads are the boards' job, not PC.

Confirmed / accepted as current:

- Architecture: 138 commander/router/reconciler; 180 cognitive brain; 182 independent witness; PC lead architect; PC_worker implementation only.
- Transport/bridge three-board active. TTL 60s bug fixed.
- policy.json 3-board hash: `eee2812d7663721d3256f8c819ada8f5ee86699d0040d7acdd0d78fd742701aa`
- agent roles 3-board hash: `c0ebb5f0bda1e0934578c894bad7c77b345faa0f753b58f102c2e49defac803f`
- 180 correction + deployment PASS. 182 adoption PASS. Canary A/B/C complete/correct.
- Claim-level calibration 3 cycles, scores ~0.9.
- 11 new units GREEN, legacy services untouched, external actions 0.
- Cockpit M0 complete on `ofn/cockpit-v2-20260827@cc7a65b`. Old panel kept. Owner Control API incomplete. Telegram production OFF.
- Auto-wake 180 worked (~36s claim/process, model only on event, duplicate blocked). Reply lost: input marked processed, reply not durable/ACKed, retry could not resend frozen bytes.
- Official repair task prefix: `30f60773`. Lost probe: `16fc28ed`.
- 180 disk ~90%. `/opt/cellframe-node` ~41.7GB, do not touch. No heavy model/package/dataset/clone on 180.
- Session infra already done (do not re-open as Wave 0 work): 138 heartbeat start-limit drop-in applied; 182 MemoryMax=2048M applied; WAVE0 hardware still ARMED=false.
- Isolation dirs exist on laptop vault:
  `F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\`
  - `WAVE0\` (PC only: this file)
  - `pc-worker\`
  - `oracle-182\`
  - `settle-138\`

Not independently re-probed by PC this turn: live queue depth on 138, live TTL/claim state of `30f60773`, live 180 worker PID. 138/180 must report those.

## PRIMARY_BLOCKER

180 processes input **before** ACK. On send failure the response is lost. Retry cannot transmit the same frozen bytes. Internal loop is therefore open. Runtime stays `DEGRADED`. Scheduler stays `HOLD_NEW_CYCLES`. No Telegram production. No business external effects.

Contract:

```text
PROCESS ONCE
→ FREEZE RESPONSE
→ DURABLE REPLY_PENDING
→ IDEMPOTENT TRANSMIT
→ ACK
→ INPUT_PROCESSED
```

State machine required on 180:

`CLAIMED → PROCESSING → RESPONSE_FROZEN → REPLY_PENDING → TRANSMITTING → REPLY_ACKED → INPUT_PROCESSED`

## TASK_180_REPAIR_STATE

- Official production task prefix `30f60773` is 180's to find and claim **once if still valid**.
- PC does not claim it. PC_worker does not claim it.
- If expired: 180 must not mutate it; request resend from 138.
- Forensic required on lost probe `16fc28ed`.
- Until 180 reports claim/expiry + 24 green tests + real ACK from 138: repair is OPEN.

## Assignments (no shared write)

### PC_WORKER_ASSIGNMENT

Isolated worktree only. Reproduce reply-retry bug. Propose patch: state machine, durable outbox, `reply_pending`, ACK-before-processed, deterministic idempotency, orphan scanner, start-limit flapping. 24 failure-injection tests. Deliver diff / tests / hashes / rollback to PC and 138 as **reference**, not production.

Forbidden: claim `30f60773`, overwrite production worker, enable/restart units, secrets, systemd, LAN listeners, external actions.

Write only under: `F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\pc-worker\`
Output block: `PC_WORKER_REPLY_PATCH_RESULT`

### 180 assignment

Official repair owner. Find `30f60773`. Claim once if valid. Forensic `16fc28ed`. Implement contract above. Retry must reuse frozen bytes/hash/idempotency key. No model rerun on retry. `no_event` and `duplicate_blocked` exit success. 24 failure-injection tests. Complete only after real ACK from 138.

If task expired: do not touch; ask 138 to resend.

No new business tasks until repair done. No production write outside 180's own runtime/cognition path.

Output block: `REPLY_RETRY_REPAIR_180_RESULT`

### WITNESS_ASSIGNMENT (182)

Independent test oracle. Do not change 180 production code. Do not write outcomes onto 180/138 production. Falsify: frozen immutability, ACK-before-processed, send failure, ACK lost, SIGKILL before/after send, no model rerun, duplicate receiver, orphan recovery, start-limit, no listener/external effect.

Verdict only: `confirmed | disputed | unresolved`.

Write only under: `F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\oracle-182\`
Output block: `WITNESS_REPLY_REPAIR_RESULT`

### 138 assignment

Keep `scheduler=HOLD_NEW_CYCLES`. Keep heartbeat/router/control/audit ON. Watch queue growth. Settle `30f60773` and its reply. Treat PC_worker patch as review/reference only; canonical repair is the official 180 task. Take 182 verdict.

After Checkpoint A PASS, run Fresh E2E (Wave 1) with **zero manual sessions**:

138 → auto-claim 180 → durable reply → auto-dispatch verify → auto-claim 182 → verdict → auto-settle 138

Plus one injected send failure with retry and `MODEL_RERUNS_DURING_RETRY=0`.

Set `RUNTIME_MODE=PERSISTENT_GREEN` only if that loop is fully automatic.

Cockpit M1 read-only may continue on `ofn/cockpit-v2-20260827` in parallel. No command/effect endpoints.

Write only under: `F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\settle-138\`

## COCKPIT_PARALLEL_WORK

Allowed now, own branch only: Cockpit V2 M1 read-only (`ofn/cockpit-v2-20260827`). Read-model API, `/cockpit-v2/` beside old panel, same port/origin, current Telegram Mini App auth. No command endpoints. Old panel unchanged.

Not allowed until Checkpoint B: Owner Control API, Telegram production push, standing business policies, inbound-to-cash.

## FILES_AT_RISK

- 180 worker reply / outbox / ACK path (canonical writer: 180)
- PC_worker isolated worktree (writer: PC_worker only)
- 180 disk ~90% — no large clones, models, packages, datasets
- `/opt/cellframe-node` (~41.7GB) — do not touch
- 138 heartbeat drop-in already applied this session — do not rewrite unless 182/138 prove it is the start-limit bug under test
- 182 MemoryMax=2048M already applied — do not raise again
- Secrets, credentials, TFN — never in prompt/log/Git
- Signed envelopes — no hand-edit
- Audit / evidence / rejected / expired — no delete

## CONFLICTS

None yet. Isolation rule: no two bots write the same file or worktree. If collision: one writer, other reviews, 138 merges.

## OWNER_DECISIONS (locked)

1. PC is Lead Architect. Mutations on production = 0 for PC and PC_worker.
2. Wave 0 order is absolute: 180 durable reply → PC_worker independent patch → 182 independent verify → 138 settle + fresh E2E. Cockpit M1 RO parallel only.
3. `may_authorize=false` for all agents. Owner approval only via Owner Control API / Telegram (not yet live).
4. No Telegram production, no external customer/payment/publish, no new LAN listener, no wildcard systemctl.
5. Quote/booking/invoice ≠ verified cash. Cash path is Checkpoint F, after A–E.
6. Physical WAVE0 e-stop still deferred. Hardware unlock not in this wave.

## NEXT_CHECKPOINT

**A — Reply repair PASS**

Required evidence:

- 180: `REPLY_RETRY_REPAIR_180_RESULT` with 24/24 tests and real 138 ACK
- PC_worker: `PC_WORKER_REPLY_PATCH_RESULT` (reference)
- 182: `WITNESS_REPLY_REPAIR_RESULT` verdict `confirmed` (or documented `disputed` that 138 must resolve)
- 138: settle receipt for `30f60773`

Then PC opens Wave 1 / Checkpoint B (Fresh E2E GREEN). Do not pull the team into Cockpit commands, Telegram prod, policies, or cash before A and B close.

## Report format (all bots)

```text
BOT=
ROLE=
TASK_ID=
RUN_ID=
BASE_COMMIT=
OBSERVATIONS=
INFERENCES=
MUTATIONS=
FILES_CHANGED=
TESTS=
HASHES=
RISKS=
ROLLBACK=
EXTERNAL_ACTIONS=
MAY_AUTHORIZE=false
STATUS=
NEXT=
BLOCKER=
END_REPORT
```

Long raw dumps stay in isolation dirs. PC will summarize.

## PC actions this turn

- Wrote this file only. `MUTATIONS=0`.
- Dispatch isolated role prompts to PC_worker, 180, 182, 138.
- No production deploy, no systemd, no secrets, no fake owner approval.
