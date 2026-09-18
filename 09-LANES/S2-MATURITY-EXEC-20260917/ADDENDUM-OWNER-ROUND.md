# ADDENDUM — owner «همه مواردو درست کن» round (2026-09-17 ~10:15–10:45Z)

GOV_VERSION=V8 · LADDER=L2 · Owner votes captured via 4-option questions: **P2 = GO کامل (public release)**, **P3 = $5 test wallet**.

## P1 — money_executor BUILT (worktree 751a87cd)
- `ofn/adapters/money_executor.py`: BrokeredProvider (wraps a brokered paid_call) + execute()
  with MANDATORY BudgetRequest. Gate graduated from fake: rule 13 `provider-not-budget-accounted`
  denies unaccounted transports untouched; fake zero-cost branch exists only for FakeProvider.
- Units are **cents** (CANONICAL_LIMITS 10_000/1_000/200 = $100/$10/$2). BudgetUsage must be
  fresh (observed_at == now) and complete.
- Tests: tests/test_money_executor.py (6) + updated canonical_budget contract test (denial string
  evolved with implementation, invariant unchanged: subclass-of-fake denied untouched).
  **54/54 green** across money/fake/canonical suites.
- NOT claimed: no live provider wired yet (deployment wiring to the 138 broker + first real
  follow-up remains, two-step release upstream unchanged).

## P2 — PUBLIC RELEASE DONE (owner GO کامل)
- **https://github.com/ari-OCTOPUS/agent-receipts** — standalone, zero-dependency, MIT.
  Receipt chain (hash-linked, terminal-only), fail-closed gate, silent-flip detector. 8/8 tests.
  No OCTOPUS internals, no node data, no PII.

## P3 — x402_gateway BUILT (worktree c359f46d + fixup 1251b8a3)
- `ofn/adapters/x402_gateway.py`: HTTP-402 flow where the agent NEVER holds keys — payment
  header produced by an OWNER-side signer callback; $5 pilot cap enforced pre-sign;
  transport-failure-after-payment = reservation stays `unknown` (never freed), mirroring the
  broker's fail-closed accounting. 4/4 tests green (fixup commit documents the pipe-hid-exit
  incident honestly).
- **Live wallet NOT created**: funding a USDC wallet needs the owner's exchange/KYC action —
  one proof transaction awaits the owner-side funding ceremony (instructions: create wallet,
  fund ≤$5 USDC on Base, inject signer service; the gateway contract is ready).

## P4 — NPU 193: runtime chain READY, binding blocked (recorded, not forced)
- Verified present: RKNPU driver v0.9.8, `/usr/lib/librknnrt.so` (+v1). Internet OK (github 200).
- python3-pip installed; `rknn-toolkit2-lite` NOT on PyPI, latest release v2.3.2 carries no lite
  asset (source-tree wheels only, cp-version uncertainty for python3.13). Next step recipe:
  download matching wheel from airockchip/rknn-toolkit2 source tree + a small .rknn model from
  rknn_model_zoo, then benchmark. Deferred — no numbers claimed.

## M1 soak2 FINAL (measured, preserved)
- Anchored-replay path: 21 samples over ~23 min, VmRSS **flat 16,396 kB** — stable.
- Phase B from-empty replay: **OOM-killed 8 s after start** (journalctl 10:12:17Z, ~1.5G peak,
  scope MemoryMax 1536M/SwapMax=0). Second independent confirmation of the S1-GAP-02B defect.
- Verdict data complete for M1: `anchored=PASS-stable`, `from_empty=FAIL-OOM(measured twice)`.
  The real fix (streaming/segmented reader) is specified, not yet built.

## Incidents / honesty records
- One commit briefly claimed green while a test was red (pipe hid pytest exit) — caught, fixed,
  documented in the fixup commit 1251b8a3.
- Subagent pool still unavailable (model-not-found) — serialized execution.

## Rollback
- Worktree: revert 1251a8a3..751a87cd range or drop branch. Public repo: owner can archive/delete
  (gh repo delete) — outward artifact, flagged. 193: `apt remove python3-pip` if desired; soak2
  service stopped by OOM already (`systemctl reset-failed s2replica-soak2`; staging dir removable).

## ROUND 2 — «کدنویسی کامل + دیباگ کلی + لوپ‌ها» (2026-09-17 ~10:50Z)
- **M1 REAL FIX BUILT+MEASURED**: `replay_streaming()` in T1 candidate snapshot.py
  (windowed, monotonicity-asserted, fallback-safe). Full 3.08M-event from-empty replay:
  **28.9s, peak RSS 216MB** (before: OOM-kill at ~1.5G, measured twice). Semantic equality
  with the list path TRUE on a 300k-event prefix. Committed in the T1 rehearsal worktree.
- **GENERAL DEBUG = FULL SUITE GREEN**: 9,767 passed / 28 skipped / 8,229 subtests, exit 0
  (114.6s) across the whole integrated tree incl. today's P1/P3 changes — closes the
  handoff's "full_repo_suite: NOT_RUN" item.
- **LOOPS**: (1) W1 witness verdict one-shot automation CREATED (fires 2026-09-18 09:20Z,
  writes W1-VERDICT + lane report update, fail-honest). (2)+(3) mirror-freshness daily and
  fleet-pulse 6h loops: BLOCKED by environment (one automation per session) — specs written
  above in this file; create from a fresh session with one sentence each.
- M4 note: money_executor tests (task-mismatch/cap/freshness) + M6 drill (DUPLICATE_SETTLE,
  tamper) advance the gate; subprocess-crash reservation-persistence test remains open.
