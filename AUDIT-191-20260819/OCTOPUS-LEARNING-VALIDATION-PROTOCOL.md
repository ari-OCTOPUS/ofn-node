# OCTOPUS-LEARNING-VALIDATION-PROTOCOL — Live-4 preregistered protocol (consolidated)

Consolidates the **already-owner-approved** criterion (TASK-CLASS-TAXONOMY.json, sha256 `8d33263f…`, sidecar hash present) with the audit's corrections. Status per item reflects 2026-08-19T02:20Z. This document does not change any threshold — it makes the existing one explicit, machine-checkable, and honest about what is not yet frozen.

## 0. Current standing

`MEMORY_LIVE_LEARNING_UNVERIFIED` — correct and mandatory until §5 is satisfied. `LIVE4_PROTOCOL_VERSION = PENDING_V2_FREEZE`: **the V2 freeze ratification is the only prerequisite the owner personally owns before the first counted primary pair.**

## 1. Arms and pairing

- Question Q drawn per pair from the frozen task taxonomy; **baseline arm** answers Q without retrieved memory; **conditioned arm** answers Q + retrieved evidence rows (canonical, eligible, provenance-carrying, mem_-ids recorded).
- Both arms MUST run on the same paid provider/model route (`tier="primary"` → deepseek/deepseek-v4-flash). Asymmetric arms (local vs paid) are VOID by definition (D-A lesson, now enforced: 0 baseline failures in last 8 calls).
- A/B placement: seeded RNG decides `cond_position` **before** the judge call; mapping recorded in the pair record. (Limitation: no cryptographic sealing; acceptable, disclosed.)
- Local fallback, freeze-blocked, deferred or free-tier results: `evaluation_eligible=false` — never score.

## 2. Judge contract (V2)

- Judge input: the two anonymized answers; judge output accepted **only** as machine-readable `{"verdict":"A"|"B"|"TIE","rationale_hash":"<64-hex>"}` (strict `judge_json`); anything else = `UNREADABLE` → VOID. One re-ask allowed inside the attempt cap; a second failure stays VOID.
- The lenient `parse_judge` path must not be used by any scored run (fg_runner uses judge_json; the original driver still imports the lenient parser — retire it from scored paths in the V2 freeze).
- Judge independence: currently same provider family as arms (`judge_independence_limited=true`, hardcoded, disclosed in every report). A different-family judge is an owner option, not a requirement.
- VOID = neither win nor loss; provider failures, unreadable judging, exceptions → VOID with reason code (observed vocabulary: `exc:IntegrityError`, `exc:KeyError`, `judge`, `base=False/fugu cond=deepseek-v4-flash`).

## 3. Sample structure

| Phase | Cases | Counted toward primary? | Current |
|---|---|---|---|
| Pilot (batch 1) | 15 | NO | 3 valid (label LIVE4_PILOT_VALID_PAIRS=3) |
| E2E gate (batch 9) | 4, repeatable | NO | best 3/4 — **gate not passed** |
| **Primary** | 2 batches × 15 = 30 | YES | **0** |
| Confirmatory (batches 3-4) | up to 30 more (31–60) | replication only | 0 |

**Hard rule:** the primary threshold is never altered after observing any result, including confirmatory. Confirmatory exists to replicate, not to rescue. Pilot results enter the primary sample only if protocol version, route, prompt contract, eligibility and judge contract are identical and were frozen before counting — they are not (pilot predates D-A/D-B fixes), hence pilot=3 stays out (already enacted via VALID_PAIRS 3→0 supersession, owner decision LIVE4-DEFECT-CLOSURE-AND-E2E-01).

## 4. Primary success criterion (frozen numbers)

Pass LIVE-4 primary iff ALL:
1. ≥ **30 valid paired cases** (2 batches × ≥15);
2. ≥ **10 evidence-conditioned wins per batch**;
3. ≥ **20 evidence-conditioned wins total**;
4. complete metadata + complete paid receipts for every counted pair;
5. VOID accounting published (count + reason per batch).

Learning upgrade (`LEARNING_VERIFIED`) additionally requires the evaluator's conditions: Brier improvement `(b0 − b1) > 0` on frozen task classes AND provenance coverage ≥ 0.9 AND the owner's condition ④ (valid evidence-conditioned pairs per this protocol).

## 5. Entry gate (must hold before first counted pair)

- [ ] E2E foreground gate: one run of 4 sequential cases with `valid_pairs_increment=4, baseline_failure=0, judge_unreadable=0`, complete receipts, unique pair IDs — **asserted by test, not by narrative** (add to `test_e2e_fixture.py`).
- [ ] Owner ratifies LIVE4_PROTOCOL_VERSION V2 freeze (timestamp + hash, non-null evidence_hash).
- [ ] FX pin fresh (<24h, hash-valid) at scoring time; provider capacity probed same-session.
- [ ] Reservation active with sufficient attempts (caps: 200 attempts/60 pairs/90-min window).

## 6. Reporting contract (every scored run)

Report side-by-side: valid_pairs · VOID count+reasons · provider availability · baseline-arm reliability · judge readability · metadata completeness · Brier/calibration where relevant · cost per valid pair · cost per evidence-conditioned win · conditioned-vs-baseline result · limitations/confounders (composition-shift caveat applies to any Brier comparison across runs).

## 7. Falsification conditions (what would DISPROVE the learning claim)

1. ≤ 20 conditioned wins in 30 valid pairs under this protocol;
2. Brier delta ≤ 0 on identical task classes/eligibility with coverage ≥ 0.9;
3. Gains explained by dataset composition shift rather than memory conditioning;
4. Voids statistically associated with the conditioned arm (bias audit);
5. Judge readability < 100% of counted pairs (each counted pair needs a machine-readable verdict);
6. Provenance coverage < 0.9 on counted pairs.

## 8. Cost discipline (verified figures)

Live-4 to date: 132 paid calls, $0.006473 AUD total → ≈ $0.000049/call, ≈ $0.0022/valid-pair, ≈ $0.0032/win (E2E-era conservative figures). Caps in force: 30 AUD/day, 24 AUD hard stop, 1 AUD/call, enforced in driver. At current unit costs, a full 60-case run costs well under $0.50 AUD — **budget is not the constraint; readability and protocol freeze are.**

## 9. What is NOT allowed

Counting local fallback as an arm · padding valid pairs with pilot/E2E cases · post-hoc threshold edits · re-asking judges beyond the one allowed re-ask · treating provider quota failures as losses · using confirmatory results to modify the primary rule · freezing the protocol after seeing primary results.
