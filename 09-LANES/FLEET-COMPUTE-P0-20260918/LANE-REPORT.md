# LANE REPORT — FLEET-COMPUTE-P0-20260918

GOV_VERSION=V8 · LADDER=L2 · one lane, one worktree · Class A (internal, non-TCB, reversible)

## Goal this lane answers

The Deep GitHub Scan on fleet CPU utilisation concluded that `main` "is not
presently wired to pool CPU across seven Orange Pi boards plus a laptop", and
prescribed a staged project: read-only census and telemetry, a durable task
contract, capability-driven placement, a restricted worker with cgroup limits,
then canary → three boards → seven boards → laptop.

This lane turns that report into a running, receipted system. It found that the
scan's conclusion was **still true today**, and then built the missing half.

## What was already there (measured, not assumed)

Two prior lanes had built real transport, and this lane verified it live rather
than trusting the notes:

- NATS JetStream hub on the laptop with a leaf on all 7 boards; the vault matrix
  `06-EVIDENCE/FLEET-HEARTBEAT-CANONICAL.md` pulses every node.
- `state/fleet-jobs/fleet_jobs.jsonl` with a real cross-board job
  (`model_infer`, commander 138 → worker 193, state CLOSED) and a capability
  registry `state/fleet-scheduler/node-capabilities.json`.

But reading the scheduler source showed the gap is bigger than it looks:

- `fleet_scheduler.py`'s job body is `echo 'retrieve-executed-on-100'` — it
  moves JSON and proves SSH works; it consumes no CPU.
- `lease_expiry` is parked at `2099-01-01`, so leases never expire.
- Worker choice never looks at load, temperature, memory or disk.
- No cgroup limits anywhere, no worker agent, no retry budget, no drain.
- The job bus is `SHADOW_LOCAL_JSONL` with 0 consumers — not replayable.

So the fleet had a message bus, not a computer.

## What this lane built

### Phase 0 — read-only census and telemetry (`tools/fleet_probe.py`)

Nonce-verified fan-out probe: 7/7 boards answered with per-zone thermal, per-core
CPU%, memory, disk, frequencies, cooling states, failed units and service health.
Liveness is *proven*, not assumed: each round carries a random nonce and the node
echoes `sha256(nonce)`, so a stale or copied record fails the check.

Baseline is running at ~9 s cadence for 24 h (2128 samples at the time of this
report). `tools/baseline_report.py` summarises it.

### Control plane on 138 (`tools/compute_core.py`, `tools/compute_scheduler.py`)

- SQLite in WAL mode: `tasks`, `leases`, `events`, with the append-only event log
  written in the same transaction as every state change.
- Real expiring leases. `reclaim_expired()` returns the exact rows it cleared so
  the caller can tear down the abandoned work.
- Fail-closed admission: missing measurement, stale telemetry, thermal, memory,
  load, CPU, disk, spare-core and quarantine rules all produce explicit reason
  codes. **Nothing measurable → no lease.**
- Exactly-once settlement: a duplicate or late result cannot re-settle a task.
- Retry budget, parking (decline without consuming an attempt), cancel, and an
  owner-pause flag file.
- Placement scoring is thermal-weighted, and only among already-admitted nodes,
  so a score can never override a refusal.
- Capability-driven: a node with no capability record is not dispatchable.

### Worker agent (`tools/compute_worker.py`, v1.1.0)

Deployed inert to 114/160/100/193 (it does nothing until invoked). Executes only
pre-registered profiles (`cpu_bench` v2, `sha256_manifest` v1); `params` is data
and is never interpolated into a shell string. Hard timeout, output cap, clean
SIGTERM cancellation, and a capability record the control plane reads instead of
guessing roles.

**The cgroup is not the agent.** The control plane launches it through
`systemd-run --scope -p CPUQuota=… -p MemoryMax=…`, and the agent reports the
cgroup directory it actually ran in. The control plane then *verifies* the
envelope file-by-file; a mismatch fails the task and stops the scope. A receipt
that merely shows a scope path is a claim, not proof, and is rejected as
`UNVERIFIED`.

## The failure this lane found (and fixed)

The first sustained canary leaked three simultaneous 8-worker scopes on node 114.
The chain, all three confirmed live and now covered by regression tests:

1. **Pool children inherited the parent's soft SIGTERM handler.** `Pool.terminate()`
   sends SIGTERM; the children ignored it, so `join()` never returned and the
   scope never exited. Replaced multiprocessing.Pool with explicit processes that
   terminate, then kill, under a hard deadline; children reset signal handlers.
2. **`params.seconds` could exceed the envelope's `max_seconds`.** A 120 s request
   arrived with `max_seconds=110`, so the workload outlived its own lease and the
   control plane declared a timeout against a task still executing. Now clamped,
   with the clamp reported in the receipt.
3. **Scope names came from the task id alone**, so a retry collided with a
   still-loaded unit (`Unit ... was already loaded or has a fragment file`).
   Now `octopus-compute-<id>-a<attempt>`, deterministic so reclaim can stop it.

Every failure path now also stops the scope, and lease reclaim stops the scope it
abandoned. Evidence that the fix is real: the three tasks that previously died at
`rc=124`/`rc=1` were re-run by the fixed stack and all three **SUCCEEDED** with
`cgroup_envelope: VERIFIED`.

## Measured results

| Item | Measurement | Source |
|---|---|---|
| Fleet | 7 boards × 8 cores = 56 cores, all reachable | census |
| Idle headroom | 114/160/100/193 at ~0.2–0.5 % CPU, 6.7–7.1 % mem, 23–29 °C | baseline |
| Busy nodes | 138 load1 p95 14.8; 182 at 76.5 % memory | baseline |
| Identity | 7/7 stable machine-id and boot-id, 1 each, clock skew ≤ 6 s | baseline |
| Thermal quantisation | all boards step in ~0.93 °C increments | baseline |
| Canary envelope | `cpu_max = 400000 100000` verified in-scope, 8/8 workers | receipt |
| Sustained 4-core load | hottest median 27.8 °C, max 29.6 °C, cooldown 25.0 °C | sustained run |
| Throughput | ~375–393 k SHA-256 ops/s aggregate at 4-core quota | receipts |
| SSH latency under load | median 472 ms, max 3.8 s | sustained run |
| Process overhead | 8 workers ≈ +17 s on a 90 s task | receipts |
| Load average vs quota | 8 procs at ~50 % CPU each while `load1` read 0.66 | live check |

That last row matters for any future scheduler: **throttled tasks are not counted
as runnable, so `load1` badly understates utilisation under a cgroup quota.**
`cpu_pct` from `/proc/stat` stays trustworthy. This is recorded in
`DEFAULT_POLICY` so the next agent does not re-learn it.

## Acceptance status

| Phase | Criterion | Status |
|---|---|---|
| 0 | stable identities, fresh telemetry, no stale records | **PASS** (24 h run continuing) |
| 0 | collect for 24 h at 10–15 s | IN PROGRESS (~9 s cadence, 296 rounds so far) |
| 1 | no placement on stale/hot/memory-pressured nodes | **PASS** (tests) |
| 1 | deterministic replay from one snapshot | **PASS** (tests) |
| 1 | owner pause blocks all new leases | **PASS** (live, task PARKED at attempt 0) |
| 1 | 24 h of shadow decisions before promotion | IN PROGRESS (timer live, 5-min cadence) |
| 2 | single canary, cgroup-limited, envelope proven | **PASS** (114, verified) |
| 2 | 24 h without watchdog restart / throttle / latency regression | NOT YET (needs wall clock) |
| 3–5 | three boards, seven boards, laptop | NOT STARTED |

## What failed / honest limits

- The first sustained canary leaked work; root-caused and fixed, not retried away.
- Two tasks are `FAILED_FINAL` from that window and stay failed in the store. They
  are the honest record of the bug, not noise to be cleaned.
- Three never-dispatched tasks were `CANCELLED` explicitly so a future promotion
  does not fire phantom work.
- `per_worker_ops` spreads ~2.3× between workers — consistent with RK3588
  big.LITTLE scheduling, not measured as a controlled result.
- The sustained run's own script had a trailing `NameError` after data collection;
  fixed. Its "task N/M dispatched" label was misleading too: the scheduler drains
  FIFO, so it executed older queued tasks while the freshly enqueued ones stayed
  queued. The dispatch results are real; the label was not.
- Thermal headroom at 4-core load is large (≈30 °C), but a 24 h soak has not been
  done, so no fleet-wide threshold is asserted yet.

## Evidence paths

- `09-LANES/FLEET-COMPUTE-P0-20260918/evidence/telemetry.jsonl` — census ledger
- `09-LANES/FLEET-COMPUTE-P0-20260918/FLEET-CENSUS.md` — generated summary
- `09-LANES/FLEET-COMPUTE-P0-20260918/evidence/canary-run-{1,2}.json` — first canary, then envelope-verified
- `09-LANES/FLEET-COMPUTE-P0-20260918/evidence/canary-fresh.json` — clean fresh task
- `09-LANES/FLEET-COMPUTE-P0-20260918/evidence/owner-pause-engaged.json` — pause blocks leases
- `09-LANES/FLEET-COMPUTE-P0-20260918/evidence/multicore-*.json`, `calib-*.json` — quota calibration
- `09-LANES/FLEET-COMPUTE-P0-20260918/evidence/sustained-canary-*.jsonl` — sustained run
- `09-LANES/FLEET-COMPUTE-P0-20260918/evidence/deploy-receipts.jsonl` — digest-verified pushes
- on 138: `/home/ari/ofn/state/fleet-compute/{compute_tasks.db,decisions.jsonl,receipts.jsonl,cockpit.json}`
- on 138 units: `/etc/systemd/system/octopus-compute-shadow.{service,timer}`

## Rollback

1. Stop the control plane: `sudo systemctl disable --now octopus-compute-shadow.timer`
2. Remove units: `sudo rm /etc/systemd/system/octopus-compute-shadow.{service,timer} && sudo systemctl daemon-reload`
3. Remove code: `rm /home/ari/ofn/tools/{compute_core,compute_scheduler,fleet_probe}.py`
4. Remove the worker agent from each board: `rm /usr/local/bin/compute_worker.py`
5. Stop any live scope: `systemctl stop 'octopus-compute-*.scope'`
6. State is additive and never overwrites existing fleet state: delete
   `/home/ari/ofn/state/fleet-compute/` to remove the task store and logs.
   The pre-existing `state/fleet-jobs`, `state/fleet-scheduler` and NATS units
   were **not modified** by this lane.

## Phase 2 soak — ARMED

The canary is now an unattended timer on 138, not a manual command:

- `octopus-compute-canary.timer` — every 10 min, `octopus-compute-canary.service`
- mode `canary`, `allowed_nodes: ["114"]`, `CPUQuota=200%`, 30 s task, 8 workers
- **Soak start: 2026-09-18T01:00:00Z** (first timer fire 00:57:57Z, manual
  verification fire 00:58:30Z, both `status=0/SUCCESS`)

Acceptance is evaluated from evidence, not recollection:

```
python tools/canary_acceptance.py --since 2026-09-18T01:00:00Z
```

It checks eight criteria against the live control plane and the local telemetry
ledger: no service restart, no thermal throttling (cooling-device `cur_state`
all zero), no queue corruption (no task holding two open leases), exactly-once
settlement, proven cgroup envelope for every dispatch **in the window**, no work
outliving its lease (no in-flight task, no open scope, no stray worker process),
node never rebooted, and the 24 h window actually elapsed.

One honesty note it enforces: a 1-hour dry run of that evaluator reports the
envelope criterion as **FAIL** (`VERIFIED: 12, UNVERIFIED: 4, NONE: 1`) because
dispatches from the pre-fix agent are inside that window. That is the correct
verdict — those four runs genuinely could not prove their limits — and it is why
the criterion is scoped to the soak window rather than all history.

## Next actions (in dependency order)

1. Let the 24 h baseline and 24 h of shadow decisions finish; then compare
   predicted placement against observed headroom and promote the canary.
2. Arm the canary as a timer on 138 (mode `canary`, `allowed_nodes: ["114"]`) so
   Phase 2's 24 h acceptance runs unattended.
3. Add a real multi-node workload for Phase 3 — `sha256_manifest` is built and
   tested but a useful corpus has not been placed on the boards yet.
4. Keep 182 out of compute permanently: it holds the witness/audit-latch role.
