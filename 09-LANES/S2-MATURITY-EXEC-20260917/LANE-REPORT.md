# LANE REPORT — S2-MATURITY-EXEC-20260917

GOV_VERSION=V8 · LADDER=L2 · 2026-09-17 · lane root `F:/backup/09-LANES/S2-MATURITY-EXEC-20260917/`
Charter: S2 handoff (`09-LANES/S2-ARCHITECT-HANDOFF-20260917/PROMPT-AND-DATA.md`); bundle verify HASHES_MATCH (66 files).
Worktree: `F:/wt-s2-maturity-20260917` branch `s2-maturity-20260917` (base 31a39ee6) — commit **c00eb554** (m7-prep fixes).

## Gate status after this session (MATURITY-GATES.json ids)

| Gate | Status this session | Evidence |
|---|---|---|
| M0 identity | **RECORDED_REVALIDATED** (partial: 5 nodes carried from handoff, wiring UNKNOWN) | `receipts/M0-IDENTITY.md` |
| M1 sensorium memory | **MEASURED-FAIL (the 02B defect, now with numbers) + soak RUNNING** | OOM-kill at T+16s, 1.5G peak under MemoryMax=1536M/SwapMax=0; PREREG `bin/PREREG-M1-SOAK.json`; journalctl `s2replica-soak.scope` 09:45:11–27Z; soak2 service `s2replica-soak2` sampling since 09:49Z |
| M2 witness | UNCHANGED (W1 sidecar PID 764170 running, window ends 2026-09-18T09:11:20Z; S1 frozen-window watcher also live) | 182 `/root/s1-maturity-w1-20260917/observations.jsonl` |
| M3 fleet self-model | NOT advanced (daemon deploy remains) | — |
| M4 budget | PARTIAL INDIRECT (broker idempotency + fail-closed observed in M6 drill: DUPLICATE_SETTLE, unknown→max-reservation); `canonical_budget` concurrency/crash tests **NOT_RUN** | `receipts/M6-DRILL.md` |
| M5 RevenueRun | NOT_RUN (no new real chain; release holds stand) | — |
| M6 restore/kill-switch | **SLICE MEASURED 3/3** — consumer-on-restored ✓, tamper-refused ✓, halt-oracle fail-closed ✓ (component-level, second host = 182) | `receipts/M6-DRILL.md`, 182 `/root/s2-m6-drill-20260917/M6-DRILL-RESULT.json` |
| M7 learning | **HYGIENE LAYER DONE RED-first** (3 defects fixed, 52 tests green); the causal holdout experiment itself NOT_RUN | worktree c00eb554, `receipts/M7-PREP.md` |
| M8 24h soak | NOT_RUN (depends on M1 final changes) | — |

## Key engineering results

1. **M1 measured failure (preserved, not hidden):** the candidate `snapshot.py`
   replay-from-empty path (`load_events(after_seq=0)`, also triggered internally by
   `replay_matches_current`) materializes all 3.08M events in RAM. Under the
   preregistered quota (MemoryMax 1610612736, SwapMax 0) the process was **OOM-killed
   in 16 s at ~1.5G peak** on the frozen real journal (425MB, sha d5d4d7f4…). First
   launch `s2replica-soak.scope` (invocation c1fb58dca9ca…) is the failure receipt;
   the relaunched `s2replica-soak2.service` measures the anchored path + hold and will
   hit the same bomb in Phase B (~T+20min) — by design, honestly. Implication: without
   a streaming/batched reader (or a much higher ceiling), **GAP-02B's memory bound
   cannot pass on this hardware**, independent of fsync batching.
2. **M6 drill (all inside `/root/s2-m6-drill-20260917/`, broker copy with only ROOT
   repointed):** restored ledger = byte-identical to live 138 (89 rows, sha 5d09c95c…);
   chain linkage + recomputed `bl_hash` valid; `status()`/`month_spend`/`window_caps`
   operate on restored state; reserve→settle round-trip extends the chain validly
   (91 rows, new head a601fbab…); replayed settle refused (`DUPLICATE_SETTLE`, 0 rows
   added); one-byte tamper → hash check FAILS at the tampered row; halt oracle
   (isolated opslib copy, attribute-repointed): clean→RUNNING, HALT-ALL flag→halted,
   env→halted, gated send REFUSED_HALTED.
3. **M7-prep (learning hygiene):** three S1-registered defects reproduced RED-first
   (5 failing assertions pre-fix) then fixed: `snapshot_sha256` now a real canonical
   content hash (was `now_iso()` — consumers in `ofn/learning/cli.py:51,72,79,88,97,101`
   were recording fake provenance); `sample_size` now the true contact denominator
   (was `max(n,1)` — poisoned the `n<3` underpowered gate in `experiments.py:57`);
   `ActionChainLinker.build` now sorts by event time (order-invariance test added).
   52 learning tests green post-fix.

## What remains (next independent actions)
- Collect soak2 output after ~2026-09-17T10:55Z (`~/s2-replica-20260917/soak-samples.jsonl`,
  verdict per PREREG rule — compute max VmRSS of last ten 60s samples; expect Phase-B OOM).
- M1 real fix direction (measured, not yet built): streaming/segmented reader so replay
  never materializes the full journal; batch consumer integration into app; full replica
  boot blocked list recorded in PREREG (nacl absent, identity forgery risk, NATS contamination).
- M4: write the concurrency/crash/currency tests for `ofn/kernel/canonical_budget.py`.
- M2 tamper tests for the sensorium witness path; M3 daemon deploy (Class B, witnessed).
- M7: freeze the 4-arm experiment (B0/B1/C1/C2) per EXPERIMENT-PROTOCOL.md and run the
  10-pair pilot; today's fixes are a prerequisite, not evidence of learning.

## Rollback
- Worktree: `git -C F:/wt-s2-maturity-20260917 revert c00eb554` (or drop branch).
- 138: `sudo -n systemctl stop s2replica-soak2` (transient, gone after stop); remove `~/s2-replica-20260917/`.
- 182: remove `/root/s2-m6-drill-20260917/` + `/root/s2-m6-drill-runner.py` (isolated copies only; nothing live touched).
- No production service was restarted, stopped, or reconfigured on either node. No secrets read or printed. No journal bytes rewritten.

## 3h AUDIT + CODE COMPLETION (2026-09-17T17:45Z)
- **PULSE FIX (root-caused + fixed + verified)**: 138 heartbeat `load1=None` gap was NOT a dead service —
  `octopus-138-pulse.sh` payload carried no load field. Patched via preimage+backup
  (`octopus-138-pulse.sh.bak-n15-*`) to include `load1` (+leaf=True) while keeping the 140B frame contract;
  verified: PULSE_SENT bytes=140 ok=True → canonical heartbeat now shows `138 load1=1.12`. leaf=None for 138
  remains and is CORRECT (commander, not a NATS leaf).
- **Two missing loops CODED + first runs**: `bin/loop_mirror_freshness.py` (FRESH, seq 1, age 9.3h, quarantine noted)
  and `bin/loop_fleet_pulse.py` (7 nodes parsed, 0 alerts, 0 silent) — evidence files written; schedule them
  from a fresh chat (one-automation-per-session limit).
- **Wide scan clean**: both worktrees zero drift; zero TODO/FIXME markers in touched learning/adapter code;
  138 disk 35% (37G free), 182 disk 46%; journal 3,088,523 lines (+9.6k/9h ≈ measured rate, nominal);
  failed units: 138={smartmontools(+2)}, 182={pre-existing informational}.
- Soak observer 358 samples/0 errors; W1 102 samples frozen; sensorium NRestarts=0 overnight.
