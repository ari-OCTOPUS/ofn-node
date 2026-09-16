# OCTOPUS-OWNER-DECISIONS-NEXT — decisions that cannot safely be inferred

Everything else is executable under standing authority (CORE-AUTO-DEBUG: non-TCB, reversible, tested, receipted). Sorted by deadline.

## Time-critical (today)

| # | Decision | Deadline | If deferred |
|---|---|---|---|
| **ODN-1** | **Re-pin FX** (RBA AUD_USD of the day → FX-RECORD.json + hash + new pin ID) | **2026-08-19T06:00Z** | All Live-4 paid evaluation blocks (validate_fx fail-closed). Recurs ~daily until an owner-approved FX workflow exists — auto-fetch stays forbidden. |
| **ODN-2** | **Ratify LIVE4_PROTOCOL_VERSION V2 freeze** (timestamp + hash; null-hash label becomes VERIFIED) | before first counted primary pair | Primary pairs collected under an unfrozen protocol are contestable; the run should not start. |

## This week

| # | Decision | Options | Recommendation |
|---|---|---|---|
| **ODN-3** | **Judge provider policy** — if the next D-B iteration still fails 4/4 | (a) keep same-family judge + stricter format; (b) one different-family judge for E2E/scoring; (c) accept 3/4 with disclosed VOID | (b) — also resolves the duplicate-rationale-hash smell; keeps VOID policy unchanged |
| **ODN-4** | **Wire-or-retire the orphan estate** (ConsolidationCycle 4d twin, 18 weighty `_ops` modules, councils) | wire with caller / mark STATUS retired (no deletion) / leave | retire-by-annotation now; wire individually only when a phase needs them |
| **ODN-5** | **Math-TCB guard ceremony** (DARE ZeroDivision guard + I_pred anchor in run_self_test, then re-sign trust-boundary) | approve TCB ceremony / defer | approve — removes a real divergence between organism math and brain math |
| **ODN-6** | **Reservation re-arm policy** — start_override resets all counters; windows are 90 min | accept reset semantics / ask for cumulative counters first | accept for now; ask for cumulative counters if batches span multiple windows |

## This month

| # | Decision | Context |
|---|---|---|
| **ODN-7** | **D3 git-history credentials** — purge old mail_credentials.py versions (rewrite) vs rotate-and-accept | Rewrite is the highest-irreversibility action in the repo; rotation + risk-acceptance is the safe default |
| **ODN-8** | **http.server :8765 zombie** — identify+kill (after cwd check) or adopt into the manifest | Undeclared listening member since 08-14 |
| **ODN-9** | **Windows-task launcher fixes** (`py` → absolute python.exe for Poisoning Watch / Consolidation Tick / LiveDataRefresh) | Task Scheduler mutation is owner territory per standing rules; the fix is zero-logic |
| **ODN-10** | **Hardware scope for Phase 5** — approve inventory-only work now; park all contact/purchase/pilot decisions | Zero verified hardware inventory exists today; nothing to infer from |

## Standing confirmations (no action needed unless you disagree)

- Budget stays 30/24/1 AUD; foreground-only execution; boards no-contact; PROPOSE_ONLY; shell disarmed; scheduler unchanged; two-agent agreement never VERIFIED; VOID never scored.
- The autonomy ruling of 2026-07-16 (free vs important) remains the metacontrol baseline.

**Minimum viable owner session today: ODN-1 + ODN-2 — two acts, minutes of work, and the entire primary scoring path is legally and operationally unblocked.**
