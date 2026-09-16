# OCTOPUS-NEXT-24H-ACTIONS — max 10, ordered by impact

Window: 2026-08-19T02:07Z → 2026-08-20T02:07Z. Owner timezone AUSEST (UTC+10). Source: OCTOPUS-FULL-AUDIT.md.

| # | Action (owner/agent) | Why first | Concrete done-criterion | Deadline (UTC) |
|---|---|---|---|---|
| 1 | **Fix D-B to a real 4/4**: make the judge output strictly machine-readable (single-char contract or forced-JSON) and exercise the allowed re-ask **inside the attempt cap**; then run a fresh 4-case foreground E2E | Sole blocker of primary scoring; six failed runs already burned ~30 attempts of the 200 reserved | One E2E run with `valid_pairs_increment=4, baseline_failure=0, judge_unreadable=0`, complete receipts, unique pair IDs | before window lapses |
| 2 | **Add the missing gate assertions** to `test_e2e_fixture.py`: `judge_unreadable==0`, `baseline_failure==0`, `valid_pairs_increment==4`, duplicate-pair-ID rejection | Turns the manual 4/4 gate into a repeatable machine gate (E14/E20 finding) | Fixture test asserting all four conditions passes/fails deterministically | with #1 |
| 3 | **Owner: re-pin FX before 06:00Z** (fetch RBA 2026-08-19 AUD_USD manually, write FX-RECORD.json, recompute fx_hash, new pin ID) | Otherwise `validate_fx` blocks ALL Live-4 paid evaluation from 06:00Z | New FX-RECORD.json with fresh timestamp + valid hash + owner pin id | **06:00Z** |
| 4 | **Owner: ratify + hash-freeze LIVE4_PROTOCOL_VERSION V2** before any primary pair is scored | Preregistration integrity: primary sample must run under a frozen protocol (currently PENDING_V2_FREEZE, null hash) | Protocol label VERIFIED with non-null evidence_hash and freeze timestamp | before batch 1 primary |
| 5 | **Regenerate NOW.md from labels.json and check in a generator script** (`_ops/scripts/render_now.py`) | Sole-truth page is 6 labels stale incl. VALID_PAIRS 3→0 supersession | NOW.md byte-consistent with labels.json; script committed | 24h |
| 6 | **Fix the receipt-budget bug + two wiring gaps** (non-TCB, CORE-AUTO-DEBUG eligible, tests+rollback): `model_router.py:319` budget_before must be remaining budget; read `paid_blocked` before next paid call; FX-expiry check in general paid path | All 82 receipts currently show negative budget_after; fail-closed promises not wired (F7/F11/F18) | Patch + test + rollback artifact under 06-EVIDENCE per promotion rules | 24h |
| 7 | **Wire two-phase Admission + contradiction radar into production writers** (or downgrade `CONTRADICTION_RADAR` to CLAIMED in labels) | NOW.md claims ACTIVE/VERIFIED but no writer sets the checker — an honesty debt at the heart of the memory system | Radar invoked on the live admission path with a quarantined-on-contradiction example, or label downgraded | 24h |
| 8 | **Write the two missing decision files** (`LIVE4-DEFECT-CLOSURE-AND-E2E-01`, `CONTINUE-LIVE4-DA-DB-CLOSURE-02`) with ID/timestamp/evidence links | Label-history references owner decisions that exist nowhere as records | Both files in 02-DECISIONS/ with evidence paths | 24h |
| 9 | **Fix F3 via auto-debug** (MemoryStore.insert required-metadata enforcement) | Best-bounded next self-debug target; closes the metadata-eligibility hole that excludes 42 historical rows | Patch + 11/11-style test run + rollback + manifest under 06-EVIDENCE | 24h |
| 10 | **After 1+3+4 succeed: run primary batches 1-2 (2×15) in one reservation window**, reporting `valid_pairs` **with `PROVIDER_CAPACITY` side-by-side**, void reasons counted | The actual goal: move PRIMARY_VALID_PAIRS from 0 toward 30/20 | First primary batch report with structured metric table | when unblocked |

**Not in the top 10 but time-sensitive if window lapses**: re-arm reservation via a new owner override (current window 90 min, ~33 min elapsed at audit check; counters reset on restart — G11).

**Explicitly NOT to do in this window**: any board/SSH contact, .180 activation, git-history rewrite, ESP32 purchases, cap raise, TCB edits, automatic FX fetching.
