# 07 Test Plan — A02 Runtime Investigator (CONSOLIDATED)

For later waves; **nothing was executed this run — READ_ONLY**. Sandbox/throwaway-copy tests marked; the live system must not be touched without owner approval.

## From the parallel observer

### T-A02-1 — Heartbeat soak (A15 verification)
Observe ORGANISM-STATE.json for ≥30 min: beat strictly monotonic, no regression of `started`, ts within ±2 s of host clock each sample, identity_health recomputed (touch nothing; value may legitimately stay equal).

### T-A02-2 — Kill-switch fail-closed (sandbox copy only, owner-approved)
In a throwaway copy (not the live tree): create STOP-ORGANISM / HALT-ALL flags, run one beat, assert only SENSE/RECORD/HEAL phases execute (beat_scheduler.py:212-213 contract).

### T-A02-3 — propose_only invariant
Static test: for every entry in effector_registry with propose_only falsy, assert no leg beat function calls it while its own state dict declares propose_only True. (Fails today by construction — document, then fix per recommendation #3.)

### T-A02-4 — Ledger liveness + integrity
Read-only: recompute ledger_hash chain over checkpoint table (N rows); assert continuity 1..N and that the newest row's hash matches running state. Establishes whether "tamper-evident" is earned.

### T-A02-5 — CURRENT-TRUTH freshness
Assert auto-block timestamp ≤30 min old whenever cortex is running; assert HEAD field == git HEAD at write time.

### T-A02-6 — Channel-status truthfulness
Test that the channel-status writer refreshes or tombstones dashboard entries; assert no `true` for a port with no listener (8790/8770 today).

### T-A02-7 — brain_core comparator
Feed identical old/new samples in a test harness; assert matched increments. If the old-side producer is dead, the soak metric must be reported as N/A, not 0.

### T-A02-8 — identity_health determinism
Given a frozen input-signals file, identity_equations.evaluate() must reproduce 0.542 exactly (locks the formula against silent drift).

## From the primary observer

### T-A02-9 — OFF-heartbeat with a dormant module (sandbox)
In a test env with exactly one module flag off (e.g. OCTOPUS_WIRE_CHORD_SHADOW=0), run 10 beats, assert exactly one `module.heartbeat` `status=OFF` event with trace/correlation/idempotency keys in events.jsonl. Today this is untestable live because zero modules are dormant (F-20).

### T-A02-10 — Config precedence regression
Unit test the full chain: (a) flags.cmd value beats .env for same key; (b) .env fills only unset keys; (c) auto-knobs fill only unset keys AND reject out-of-bounds values (outside improve.py AUTO_KNOBS ranges); (d) defaults apply last (F-22).

### T-A02-11 — Tunnel tombstone contract
Kill cloudflared in a test env; assert miniapp-url.json is blanked (`url:"", pid:0`) within the keepalive window and the gateway refuses to serve on a stale URL (F-03).

### T-A02-12 — board_cp fail-closed surface
Against a test instance: unauthenticated GET /api/board-cp/pull → 401/403; unknown path → 404; flag off or Gate 0 closed → 503 and zero commands leave; assert Authorization never appears in logs (F-04).

### T-A02-13 — Boot-hash drift detection
After implementing recommendation #10: boot, record hash in ORGANISM-STATE; edit a module; assert a drift alarm raises without restart (F-23).

### T-A02-14 — Timestamp convention lint
CI check: no artifact writes naive datetimes; every `Z`-suffixed ts must equal UTC (would have caught the math-control 10 h mislabel) (F-24).

### T-A02-15 — Arbiter advisory-only contract
Assert arbiter snapshots always carry advisory_only=true and that effective_period_s is never consumed as the organism beat period (naming-trap regression, C-7).

Not runnable this wave: all require either live-system mutation or test execution — outside READ_ONLY mode.
