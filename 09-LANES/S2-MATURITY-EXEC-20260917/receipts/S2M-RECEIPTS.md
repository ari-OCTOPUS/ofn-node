# S2-MATURITY-EXEC-20260917 — Receipts (consolidated)

Receipt id convention: `S2M-<UTC>-<sha256(INTENT)[:12]>`.

## M0 — identity/scope
`receipts/M0-IDENTITY.md` (written 2026-09-17 ~10:00Z). Nodes 138/182 fresh-authenticated;
five others carried from handoff with wiring UNKNOWN. No authority expansion; D1–D5 honored.

## M6 — restore/kill-switch drill slice (182, isolated)
- INTENT: `S2M-20260917T1005Z-<see file>` — prove consumer-operates-on-restored-state,
  tamper-refusal, halt-oracle fail-closed; isolated copies only.
- Result file: `/root/s2-m6-drill-20260917/M6-DRILL-RESULT.json` — verdict 3/3 true.
- Key numbers: restored ledger 89 rows sha 5d09c95c… (byte-equal live); chain ok both passes;
  round-trip head a601fbab…; DUPLICATE_SETTLE rows-delta 0; tamper → bad_hash [0];
  halt: clean=null, flag=halt-flag:…, env=HALT_SURVIVAL_LOOP=1, gated_send_flag=REFUSED_HALTED.
- Scope honesty: component-level (single broker module + oracle), second host = 182 itself;
  full effect-path checkpoint map and a 138-side consumer run remain for the gate.

## M1 — replay-path memory soak (138, quota-caged)
- PREREG (before launch): `bin/PREREG-M1-SOAK.json` — candidate snapshot sha 48cfac2e…,
  2-line path adaptation (replica snapshot bytes sha 86f885064da89323…), frozen journal
  sha d5d4d7f4…/445,138,480 B, snapshots 52,312,962 B, MemoryMax=1610612736, SwapMax=0,
  60s×65 sampling, pass rule frozen.
- **Measured failure (preserved):** `s2replica-soak.scope` invocation c1fb58dca9ca4375abe4c66214e13faa7d —
  started 09:45:11Z, **OOM-killed 09:45:27Z** (16.065s CPU, ~1.5G peak). Cause: from-empty
  materialization (via replay_matches_current) of 3.08M events.
- Relaunch: `s2replica-soak2.service` (invocation df0ec0c0d4af413d8244a4ff7a000a7d) active since
  09:49:23Z; sample 0 boot VmRSS 16,396 kB. Phase B (one from-empty) will re-measure the bomb.
- Full-app-boot blockers (recorded, not bypassed): nacl absent on 138 system python;
  identity/registry copy = role forgery risk; NATS contamination risk.

## M7-prep — learning hygiene (worktree c00eb554)
- Repro RED: 5 failed assertions (hash-not-hex, same-second-stability, denom-0→1,
  order-dependence ×2) — `tests/test_learning_s2_repro.py` pre-fix run.
- Fix GREEN: 52 passed (new 7 + existing 45 across feeder/economic-loop/hash-chain suites).
- Consumer traces: snapshot_sha256 → ofn/learning/cli.py:51,72,79,88,97,101;
  sample_size → ofn/learning/experiments.py:57,63 + cli.py:87,166.
- NOT claimed: any runtime learning benefit (experiment NOT_RUN).

## Tool limitation record
Subagent pool unavailable this session (`model-not-found` GLM-5-Turbo) — D5 parallelism
degraded to serialized single-writer lanes; not an owner blocker.

## Compliance
Zero API spend; no OCTOPUS_WIRE_*/OFN_WIRE_* flags; no production service lifecycle changes;
no journal rewrites; failures preserved (OOM, RED tests); no gate or criterion altered —
M1's prereg was frozen before launch and the OOM is reported as FAIL evidence, not excused.
