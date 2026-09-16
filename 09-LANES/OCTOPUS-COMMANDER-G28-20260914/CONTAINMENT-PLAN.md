# CONTAINMENT PLAN — G8/W24 producer-binder transition (2026-09-14, lane OCTOPUS-COMMANDER-G28-20260914)

GOV_VERSION=V8 · LADDER=L2 · hold_external=true · customer_send=false · GO-B4=false

## Facts the plan is built on (all read-back this session)

- Live: glass_runner ddee3da4 (timer `octopus-glass.timer`, oneshot, cwd `/home/ari/ofn/ofn/agents`); binder 00dd4ef3 (timer `octopus-go-b3-bind.timer`, oneshot, same cwd, `poll` arg).
- Glass cursor 732409709 (frozen behind); **binder cursor 732409744 (ahead)** — the binder is the *effective receiver* today and the FIRST-BIND event (2026-09-14T05:13Z) proves it works end-to-end.
- Telegram `getUpdates(offset=K)` confirms every id < K for **whichever** consumer calls it; ids ≤732409743 are already server-side gone (consumed by the binder into `go_b3_tg_spool.jsonl` + decisions — preserved history, not lost).
- Quota: 2 class-B slots in 24 h age out at **2026-09-15T01:56:08Z** and **02:34:47Z** respectively → G8 deploys first, W24 only at the *second* slot (never both at the first).
- Money-gate containment: `state/revenue-drive/owner_reply.py` = **f8187600** verified live (bare «بفرست»→0 calls, ambiguity→0 calls, named card→1 call — prior regression).

## Transition states and who owns receive/ACK

| State | glass bytes | binder bytes | Ingress owner | Unpersisted-message risk |
|---|---|---|---|---|
| A (now) | old ddee3da4 (frozen-behind, idle) | old 00dd4ef3 (poller, ahead) | binder | binder's G13-fixed spool write receipts failures; FIRST-BIND proven |
| B (post-G8 slot 1) | new 8da9471c (durable, polls from 732409710) | old 00dd4ef3 still polling | binder (glass on standby) | none NEW: glass receives nothing (binder keeps consuming); if the binder dies in the window, glass automatically picks up every update ≥732409710 — durable-first, so no loss |
| C (post-W24 slot 2) | new 8da9471c, sole poller | new b9c504f8 (spool consumer only, never polls) | glass → `go_b3_inbox.jsonl` → binder | governed by G27v2 contract (T1–T10 proven) |

Why B→C cannot strand the producer behind the gap: the new glass polls with `offset=732409710`; Telegram returns everything ≥ that offset, so new owner messages arrive the moment the old binder stops consuming them; the glass cursor then jumps to the new max id. The consumed gap 732409710–732409743 is preserved in the old binder's spool/decisions.

## Failure modes covered

1. **Second deploy (W24) fails** → system stays in B: the old binder keeps receiving (FIRST-BIND-proven holding state). Retry at the next quota slot. Nothing is unwired by a failed W24.
2. **Producer rollback** (G8 revert to ad34b138 pre-image) → reintroduces the known leak (every owner message → revenue lane). Containment = money gates f8187600 MUST be verified live immediately before any rollback. This precondition is now written INTO the queued request's `rollback` field; the repackage script asserts the gate bytes before it will even re-queue.
3. **Old process still alive during deploy** → both units are oneshot: a running invocation finishes its current poll (its offset is already the most advanced — it can only confirm what it itself durably spooled); the next timer tick executes the new bytes. Verify post-deploy via journalctl last-invocation + on-disk sha (the "DEPLOYED_AND_RUN_BY_ONESHOT" rule).
4. **Simultaneous restart** → two short-lived oneshots may overlap once; both write only their own durable lanes; cross-lane update_id dedupe (G27v2) absorbs any double-write.

## Proof obligations after each slot (owner of the check: next commander tick / this lane)

- After slot 1: `glass_runner.py` sha == 8da9471c… (read-back bytes, not filename); journalctl shows the new invocation; next B3-shaped owner message lands in `go_b3_inbox.jsonl` (producer side) while the old binder still binds (state B).
- After slot 2: `go_b3_owner_bind.py` sha == b9c504f8…; **process/timer trace proof that only glass calls getUpdates** (journalctl + tcp/egress trace or strace on one timer invocation — not merely "getUpdates absent from the binder file"); binder consumes `go_b3_inbox.jsonl` via its cursor.
- Then: prepare ONE fresh financially-inert card (explicit id + expiry, zero money effect) for a REAL owner inbound test. STRATA-CHOICE is consumed and must not be re-pended. The owner's send is never faked.

## Out of scope / not claimed

- No drill executed against the REAL bot (would touch production ingress); state-matrix mechanics were proven with the stateful file-backed transport + real subprocess crashes (g27b battery T1–T10).
- The old binder's internals were not re-tested (deployed, FIRST-BIND-proven; out of this lane's scope).
