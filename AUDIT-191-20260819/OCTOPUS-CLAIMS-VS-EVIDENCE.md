# OCTOPUS-CLAIMS-VS-EVIDENCE — every material claim and its evidentiary grade

Grades: **VERIFIED** (runtime/machine evidence recomputed or reproduced) · **OBSERVED** (seen live but not independently recomputed) · **CLAIMED** (documented, not wired/proven) · **STALE** (was true, no longer) · **VOID** (mechanism absent) · **UNKNOWN** (no evidence either way). Audit close 2026-08-19T02:07Z.

## System & runtime

| Claim (source) | Grade | Decisive evidence |
|---|---|---|
| "4d daemon running, PID 18020" (labels/NOW.md) | **VERIFIED** | Live Win32_Process match; cmdline `python -X utf8 -m brain.daemon`; log appending at 01:09:35Z+ |
| "Daemon healthy, no HALT since restart" (impl. from labels) | **VERIFIED** | 0 HALT hits across all daemon+watchdog logs since 08-18T13:08Z; 0 errors in daemon_state.json |
| "Daemon is learning/producing" | **OBSERVED-weaker** | 1356 tasks, 608 memory reads, 106 ideas (358 deduped) — but **0 predictions, 0 hypotheses, 0 proposals** this run; local-only (cloud_calls=0) |
| "TCB clean, no drift" (labels) | **VERIFIED** | 15/15 manifest digests recomputed and matching; preflight invariants clean |
| "TCB enforcement active in the daemon" | **UNKNOWN** | Flag exists in OCTOPUS-flags.cmd:1500 but daemon launched without the documented wrapper; live env uninspected |
| "Boards no-contact, scheduler unchanged, /sh disarmed, external PROPOSE_ONLY" (labels) | **VERIFIED** | R01/F1 evidence, archived disarmed flag, fail-closed test without shell exec, code grep |
| ".env credentials never leaked to git" | **VERIFIED** | `git log --all -- .env` = 0 commits |
| "Old credentials remain in git history (mail_credentials.py)" | **VERIFIED-OPEN** | D3 decision text; risk label OPEN; rewrite forbidden |
| "~140 idle ESP32 boards available" (owner lore) | **CLAIMED** | Zero inventory evidence anywhere in the vault |
| "Orange Pi .138/.180/.182 operational roles" | **CLAIMED/OBSERVED-mixed** | Only docs; no live verification in scope; .180 explicitly never started |

## Registry & documentation

| Claim | Grade | Decisive evidence |
|---|---|---|
| "labels.json is the sole machine truth" | **OBSERVED** | Live-updating (47→50 labels during audit); but 5 labels lack evidence_hash; hash widths inconsistent (64- vs 16-hex) |
| "label-history is hash-linked append-only" | **VOID** (hash-link) / **VERIFIED** (append-only) | No prev_hash/entry_hash fields exist; parse+chronology clean |
| "NOW.md mirrors the registry" | **STALE** | Generated 01:04:06Z vs registry 01:22:49Z; 6 labels missing; VALID_PAIRS/LIVE4_STATE/LIVE4_PROTOCOL values outdated |
| "Owner decisions all recorded" | **OBSERVED-gap** | 2 of the referenced decision IDs have no decision files |
| 00-INDEX "CURRENT-TRUTH verified" | **STALE** | Index generated 08-15; page not updated since |

## Memory & learning

| Claim | Grade | Decisive evidence |
|---|---|---|
| "Memory admission gate ACTIVE" | **VERIFIED** | Single insert path gate.py:182; all writers gate-wrapped; no bypass found |
| "Contradiction radar ACTIVE" (NOW.md) | **CLAIMED** | Radar + gate hooks exist but **no production writer connects it**; two-phase Admission imported only by a test |
| "Canonical/raw separation" | **VERIFIED** | admission.py semantics; raw jsonl trails lack gate fields |
| "42 historical no-confidence rows excluded, unaltered" | **VERIFIED** | Query-time exclusion (REQUIRED_ROW + WHERE clause); rows intact |
| "Retrieval is provenance-carrying and causal" | **VERIFIED** | memories_used (id/sha/trust) + live4 evidence_ids injected into conditioned prompts |
| "MEMORY_LIVE_LEARNING_UNVERIFIED" | **VERIFIED** | LEARNING-VERDICT.md; evaluator conditions unmet; 0 primary valid pairs |
| "SYSTEM_DETERMINISTIC_RULE confidence separated" | **CLAIMED** | Code path exists; **0 such rows** exist to demonstrate it |

## Predictions & calibration

| Claim | Grade | Decisive evidence |
|---|---|---|
| "Prediction ledger append-only, tamper-proof" | **VERIFIED** | 4 RAISE(ABORT) triggers in sqlite_master; INSERT-only code; 0 duplicate IDs; 0 temporal violations |
| "Brier improved Live-2 0.1195 → Live-3 0.026" | **VERIFIED** | Reports + run-report JSON; n=20→30 |
| "Group-B calibration not 'perfect'" | **VERIFIED** | UNDERCONFIDENT_OR_INCONCLUSIVE with n=8 insufficiency note |
| "Composition-shift caveat acknowledged" | **VERIFIED** | CORRECTION-CALIBRATION.md:4 |
| "Holdout membership frozen+hashed" | **UNKNOWN** | No separate hash exists |

## Live-4

| Claim | Grade | Decisive evidence |
|---|---|---|
| "Protocol frozen" (NOW.md) | **STALE/CLAIMED** | Registry: PENDING_V2_FREEZE, null hash; taxonomy self-label is not a freeze proof |
| "Primary criterion = 30 valid / 2×15 / 10+10 / 20 wins" | **VERIFIED** | TASK-CLASS-TAXONOMY.json (sha256 sidecar) |
| "D-A fixed (baseline arm)" | **VERIFIED** | Root cause (missing tier → local qwen) reproduced from traces; explicit tier fix; 0 baseline failures in last 8 calls |
| "D-B fixed by contract+tests" | **VERIFIED-code / OBSERVED-live** | judge_json + 8 tests pass — but live E2E still 3/4 (1 UNREADABLE in 6 consecutive runs) |
| "Judge blind & randomized" | **VERIFIED-seeded** | Seeded RNG pre-judge, mapping in-record; no cryptographic sealing (limitation) |
| "Judge independent" | **CLAIMED-limited** | `judge_independence_limited` hardcoded True (same provider family); duplicate rationale_hash across pairs |
| "Malformed judge output always UNREADABLE→VOID" | **VERIFIED** | contract/json paths; **but** the lenient `parse_judge` still exists in the original driver path |
| "E2E gate = 4 clean cases" | **OBSERVED-failing** | Six runs, best 3/4; no fixture-level assertion of judge_unreadable=0 |
| "Local/freeze fallback never scores" | **VERIFIED** | evaluation_eligible=false defaults + PAID_PATH_BLOCKED_BY_FREEZE annotation + TIER-ROUTING-CONTRACT |
| "Pilot vs primary isolated" | **OBSERVED-procedural** | Separate labels, **same pairs file**, no mechanical firewall |

## Provider, cost, freeze

| Claim | Grade | Decisive evidence |
|---|---|---|
| "Every paid call fully receipted" | **VERIFIED** | 82/82 receipts, 12 core fields 100%; gap: fx fields 0/82 (REPORTED method) |
| "Budget caps enforced (30/24/1 AUD)" | **VERIFIED-for-Live-4 / PARTIAL-general** | Driver enforces 30/24/1; general path 2/day+30/month, and `budget_ok()` never called in router |
| "Receipt budget accounting correct" | **VOID** | model_router.py:319 bug → **all 82 receipts show negative budget_after** (enforcement unaffected, audit trail wrong) |
| "COST_UNOBSERVABLE blocks future paid calls" | **CLAIMED** | Flag set but never read outside Live-4 driver |
| "FX pin valid & fresh" | **VERIFIED → STALE at 06:00Z** | Hash recomputed and matching; expires 2026-08-19T06:00Z; general path lacks expiry check |
| "Freeze root-caused, released with receipt, flag archived" | **VERIFIED** | Errno 22 → catch-all freeze; FREEZE-RELEASE-RECEIPT.json; renamed flag file |
| "Reservation defers ordinary paid work visibly" | **VERIFIED** | Pre-dispatch gate; 1 DEFERRED receipt, cost 0 |
| "Quota reset observed" | **UNKNOWN** | QUOTA-RESET-OBSERVATION.json never written; override bypassed it |
| "Spend today ≈ trivial" | **VERIFIED** | $0.0119 USD / $0.0167 AUD (AUSEST day), computed from paid-calls + receipts |

## Strongest claim-vs-evidence gaps (summary)

1. **"Contradiction radar ACTIVE"** — not wired (honesty debt in the memory core).
2. **"Protocol FROZEN"** — actually PENDING_V2_FREEZE with null hash.
3. **"Receipts show budget before/after"** — mechanically wrong on all 82 receipts (negative).
4. **"Fail-closed on cost-unknown"** — promised in comment, unwired in general path.
5. **NOW.md as sole truth** — stale by 6 labels including the headline metric supersession (3→0).
