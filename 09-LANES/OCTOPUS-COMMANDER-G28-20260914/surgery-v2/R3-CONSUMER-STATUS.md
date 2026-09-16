# R3 — Consumer Chain Status (2026-09-14 13:40Z)

## Finding (honest, from bytes)

The consumer (`consume_decisions` in staged TRIO `9e157b4d`) does:
1. Read `owner_decision.v1.jsonl` rows
2. Match `bound_request_payload_sha256` to `decision_tasks.json` by exact hash
3. Transition task state `awaiting_ack` → `resumed` (atomic write, crash-safe)
4. Write `DECISION_CONSUMED` receipt

**What it does NOT do (and no downstream reader exists for):**
- No scheduler, worker, or dispatcher reads `decision_tasks.json` for tasks with `state == "resumed"` and continues their execution
- The coding_worker's `park/unpark` mechanism is for ITS OWN blocked tasks (dependency-based), not for decision_tasks
- The ops_agent goal_engine generates goals from observations but doesn't consume decision_tasks
- No other file in `ofn/` or `state/` mentions `decision_tasks` (grep across all Python: only the 3 TRIO preimages)

## Honest chain status

```
owner_decision.v1.jsonl → consumer → state flip (awaiting_ack→resumed) → ✋ GATE: no downstream executor
```

**The chain stops at the state flip.** `DECISION_CONSUMED` records "awaiting flag cleared only" — accurate but the flag being cleared has no consequence yet. The task is in a limbo state `resumed` that nothing reads.

## What "continued" means (and what ACK_SEEN permits)

Per the contract: `ACK_SEEN` proves the owner SAW the card. It does NOT:
- select an option (no APPROVE semantics)
- authorize any external effect
- unlock money or customer communication

So the legitimate continuation for an ACK_SEEN-only task is: the internal next step that was gated on "owner has seen this" becomes eligible. For example:
- a monitoring task that was waiting for owner awareness can now log/escalate
- a blocked task whose park reason was "needs owner attention" can now retry its internal work
- a report can now include the acknowledgment timestamp

## What must be built (W3 continuation)

The **next consumer** — a mechanism that reads `decision_tasks.json` for `state == "resumed"` and executes the task's `resume_action`:

1. `resume_action` must be a typed enum from a closed set (e.g., `"unpark_in_worker"`, `"mark_seen_in_report"`, `"enable_internal_step"`) — never free-form text
2. The action must map to a REAL existing mechanism in the worker/scheduler
3. The action's effect must be internally verifiable (file change, state change, receipt)
4. Idempotency: task `state` transitions to a terminal (`"completed"` or `"failed"`) only after the resume_action has actually been executed and verified — never before

## Deployment readiness

The consumer (as built in TRIO) can safely deploy even without the next consumer, because:
- `DECISION_NO_TASK` disposition handles the case where no task is registered
- the STRATA-CHOICE first-bind row will get `DECISION_NO_TASK` (no task registered for its payload hash)
- no card is re-pended; no state is destroyed

The next consumer can be added in a follow-up package with its own dependency on TRIO's deployed bytes.
