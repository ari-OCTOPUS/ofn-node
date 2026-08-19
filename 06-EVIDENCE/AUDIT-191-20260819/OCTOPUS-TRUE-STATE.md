# OCTOPUS-TRUE-STATE — 2026-08-19T02:15Z

One page. Machine truth: `_ops/state/labels.json` (50 labels, generated 2026-08-19T01:22:49Z). Rendered by `_ops/scripts/render_now.py` → `docs/NOW.md` (in sync, verified).

## Operational truth (one line)

**Daemon healthy and local-only; learning UNVERIFIED with 0/30 primary valid pairs; scoring blocked solely by 1-of-4 judge-unreadable E2E cases (D-B); protocol not yet owner-frozen (PENDING_V2_FREEZE); FX pin expires 06:00Z today; spend trivial (~$0.017 AUD today); safety boundaries intact.**

## Proven (VERIFIED, runtime-evidence-backed)

| Fact | Evidence |
|---|---|
| 4d daemon alive: PID 18020, since 2026-08-18T13:08:39Z, cwd `4d_system`, 0 HALT, 0 errors, 1352+ ticks | Win32_Process + `daemon-launch4b.err.log` + `daemon_state.json` |
| Daemon local-only: `cloud_calls=0`; all 55 paid calls/24h are Live-4 pipeline (deepseek-v4-flash) | daemon_state.json + paid-calls.jsonl |
| TCB clean: 15/15 manifest digests recomputed and matching; preflight invariants all green | trust-boundary.json + preflight-invariant.txt |
| Prediction ledger genuinely append-only: 4 RAISE(ABORT) triggers, 0 dup IDs, 0 temporal violations, 109 predictions / 102 outcomes (40 hit, 17 miss, 46 void) | predictions.db sqlite_master + queries |
| Canonical memory gate is the single write path (508 rows: 500 ADMITTED / 1 PENDING / 7 RETRACTED); no bypass found | memory.db + code census |
| D-A baseline-arm defect FIXED (root cause: missing tier → local qwen; fix: explicit tier; 0 failures in last 8 calls) | LIVE4-DA-DB-E2E-REPORT.md + pairs jsonl |
| Freeze root-caused, released with receipt, flag archived (Errno 22 → catch-all freeze, 3 days) | FREEZE-ROOT-CAUSE.md + FREEZE-RELEASE-RECEIPT.json |
| Safety: /sh disarmed + fail-closed test; boards no-contact; scheduler unchanged; external PROPOSE_ONLY; no secrets in logs; .env never committed | CARD-A-DISARM + tests + R01/F1 evidence |
| Costs: today $0.0119 USD / $0.0167 AUD; all-time $0.4530 USD; 82/82 receipts complete on core fields | paid-calls.jsonl + cost-receipts.jsonl |

## Claimed (documented, not wired/proven)

- `CONTRADICTION_RADAR=ACTIVE` — radar exists but **no production writer connects it**; two-phase Admission imported only by a test.
- `SYSTEM_DETERMINISTIC_RULE` confidence separation — code path exists, **0 rows** demonstrate it.
- Judge independence — `judge_independence_limited` hardcoded True (same provider family); duplicate rationale_hash across E2E pairs.
- Live-4 protocol "FROZEN" (old NOW.md) — registry truth is **PENDING_V2_FREEZE**, null hash.
- "~140 ESP32 boards" — zero inventory evidence in vault; Orange Pi roles (.138/.180/.182) documented but unverified live (only laptop .191 verified).

## Blocked

- **Live-4 primary scoring** — `BLOCKED_JUDGE_UNREADABLE_1_OF_4`: six E2E runs, best 3/4 readable; D-B V2 JSON + re-ask insufficient so far.
- Wiring gaps (fail-closed promises unwired): `paid_blocked` never read in general path; FX-expiry unchecked outside Live-4; local-fallback leg unreceipted.

## Stale / time-critical

- **FX_PIN expires 2026-08-19T06:00Z** → all Live-4 paid evaluation blocks (validate_fx fail-closed). Owner must re-pin.
- PROVIDER_CAPACITY label expires 04:00Z; DAEMON labels expire 12:30Z (re-observe trivial).
- Receipt bug: `model_router.py:319` passes cost_usd as budget_before → **all 82 receipts show negative budget_after** (audit-trail wrong; enforcement unaffected).

## Unknown

- Live daemon's actual `OCTOPUS_TCB_MANIFEST_ENFORCE` env (launched without documented wrapper).
- Holdout membership has no separate hash.
- Daily-loop invocation model and FX auto-fetch prohibition not explicitly documented anywhere.

## One next unblock action

**Fix D-B judge readability to a real 4/4** (strict single-char/JSON contract + re-ask inside attempt cap), then run one fresh 4-case foreground E2E — that single gate release unblocks primary batch scoring (2×15) inside the existing reservation (124/200 attempts remain). Owner prerequisites in the same window: FX re-pin (before 06:00Z) + V2 protocol freeze ratification.
