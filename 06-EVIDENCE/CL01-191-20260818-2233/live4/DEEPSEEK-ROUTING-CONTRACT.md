# DEEPSEEK-ROUTING-CONTRACT — DEEPSEEK-AUTOMATIC-ROUTING-01 (executed state)

Effective: 2026-08-19T02:23Z · Decision: `02-DECISIONS/DEEPSEEK-AUTOMATIC-ROUTING-01-2026-08-19.md`

## Route (observed runtime fact)

| Item | Value |
|---|---|
| primary paid route | DeepSeek · `deepseek-v4-flash` (metered) |
| tier map | local=ollama/qwen2.5:1.5b · secondary/primary=deepseek-v4-flash (`model_router.py:116-138`) — matches owner TIER-ROUTING-CONTRACT post-INC-2 |
| Live-4 arms | both arms `tier="primary"` → same provider+model (D-A fix enforced) |
| Judge | DeepSeek (no GLM introduced) — D-B/V3, see below |
| Non-DeepSeek route | requires receipt-visible reason (fugu quota path remains for free-tier internal work, marked FREE_OR_UNBILLED) |
| Silent local fallback | prohibited for paid/evaluation; freeze/fallback annotated (`PAID_PATH_BLOCKED_BY_FREEZE`, `evaluation_eligible=false`) |

## Hard stops in force (all verified live this session)

key_present ✓ · provider reachable ✓ (37 ok calls 12:31–12:38 local) · reservation policy ✓ (window expired → pass-through, no deferral; counters preserved) · cost receipts completable ✓ (COST-OBS-1 inline, 82+ receipts COMPLETE) · FX fresh ✓ (pin FX-PIN-20260819-01, valid to 2026-08-19T06:00Z — **re-pin still required before expiry**) · budget ✓ (session spend ≈ $0.0011 AUD of 24 hard stop) · no FREEZE/HALT/TCB mismatch ✓.

## D-B V3 judge contract — IMPLEMENTED & GATE PASSED

- Payload: exactly `{"choice":"A"}` | `{"choice":"B"}` | `{"choice":"TIE"}` — single-key; anything else → UNREADABLE → VOID. Winner only from position mapping, never guessed.
- Prompt V3.1: format instruction at the END with explicit example (recency; the observed failure mode was 700-char prose, not bare letters).
- Re-ask: exactly one, receipted (`JUDGE_REASK` receipt per occurrence); second unreadable = VOID.
- Parser: `live4_harness.judge_choice_v3` (schema `judge-choice-v3/1`, raw_output_sha256 recorded).
- Unit tests: `test_judge_v3.py` — **19/19 PASS** (valid A/B/TIE both positions, V2-payload rejected, extra-key rejected, invalid value, malformed, empty, markdown-without-JSON, embedded-JSON, prompt shape, seeded randomization, re-ask policy).
- Rollback: `V3-ROLLBACK.patch` (124 lines) + `*.pre-v3` byte-copies; non-TCB (evidence-dir harness, not in trust-boundary.json).

## E2E foreground gate — 4/4 PASS (first time, 2026-08-19T02:36–02:38Z, trace `cl1-live4-023601`)

| pair | valid | cond_won | cond_position | judge verdict | re-ask |
|---|---|---|---|---|---|
| 1 | ✓ | WIN | B | B | 1 (receipted, then readable) |
| 2 | ✓ | WIN | A | A | 0 |
| 3 | ✓ | WIN | B | B | 0 |
| 4 | ✓ | WIN | A | A | 0 |

`valid_pairs_increment=4 · baseline_failure=0 · judge_unreadable=0 · voids=0 · positions balanced {A,A,B,B} · receipts COMPLETE per pair · spent=$0.0005 AUD`

Prior same-session run (V3.0 prompt, trace `cl1-live4-023218`): 2/4 — two judge outputs were 698/765-char prose; root-caused to prompt-format compliance; fixed by V3.1 prompt (no parser/contract weakening). Void raws now captured to `live4-judge-raws.jsonl` for future diagnosis (observability gap closed).

## Automatic-use scope now active

planner / research / synthesis / memory analysis / hypothesis work / evidence-conditioned proposals / baseline proposals / blind judging → automatic DeepSeek, subject to the hard stops above. Free/local fallback only for non-evaluation internal work, labelled `provider_actual=local`, `evaluation_eligible=false`, explicit `fallback_reason`.

## What this does NOT unblock

Primary batch scoring still awaits owner acts: **(1)** LIVE4_PROTOCOL_VERSION V2 freeze ratification (ODN-2), **(2)** FX re-pin before 2026-08-19T06:00Z (ODN-1). The E2E gate condition of the Learning-Validation-Protocol §5 is now satisfied; the protocol-freeze and FX conditions are not.

## Trace IDs (this session)

`cl1-live4-023218-b9-01..04` (V3.0 run, 2/4) · `cl1-live4-023601-b9-01..04` (V3.1 run, 4/4 PASS) · receipts in `API-RECEIPTS.jsonl` · cost receipts in `_ops/state/cortex/cost-receipts.jsonl` (REPORTED/COMPLETE) · paid calls in `_ops/state/paid-calls.jsonl` 12:31–12:38 local.
