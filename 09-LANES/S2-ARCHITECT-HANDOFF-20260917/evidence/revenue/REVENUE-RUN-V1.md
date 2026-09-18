# RevenueRun v1 — frozen local contract candidate

GOV_VERSION=V8 · LADDER=L2 · lane=S1-REVENUE-CONTRACT-20260917

Source task: S1-TRIDENT-FLEET T5/T8, owner D3/D4. Baseline:
`31a3aca70f593877add0f628189a5d07e71f54d4` in this isolated worktree.
Parent observed live 138 at `fe0c55e0a952e0048ff6bd3ddb8ab9419cd1dc0d`;
this candidate is not deployed or loaded there.

## Contract

`ofn.adapters.revenue_run.make_receipt` stamps stage observations using the
existing `ofn.adapters.receipt` canonical digest. `replay` independently
checks every record and requires a caller-supplied pinned policy hash.
No store, executor, scheduler, or authority framework is introduced.

Exact fields: schema, run_id, leg, stage, prev_receipt_sha, policy_sha,
evidence_sha, producer_id, recorded_at_epoch_s, mode, witness_id,
witness_receipt_sha, receipt_sha256. Missing and extra fields fail closed.
Opaque IDs exclude whitespace and personal labels. All receipt/policy hashes
are nonzero lowercase SHA256; only genesis predecessor is 64 zeroes.
`evidence_sha` binds the external source receipt bytes; it must be distinct
per stage. Referenced evidence itself is not fetched by this validator.

Leg is exactly ziman, painting, or studio. Sequence is exactly:

lead_captured → enriched → qualified → offer_drafted → owner_released →
dispatched → replied → quote_or_order → settled_cash.

Run ID, leg, mode, and policy are pinned throughout a run. Every predecessor
must equal the previous canonical receipt hash. Timestamps cannot move
backwards. Valid prefixes are accepted as incomplete. Missing, repeated,
reordered, tampered, or reused evidence fails closed.

Modes: dry_run or live_observation. A dry run cannot claim settled_cash.
A settled_cash observation needs a distinct witness identity and independent
receipt reference. These are structural requirements, not authentication.
All replay outputs retain `cash_verified=false`, `may_authorize=false`, and
`external_evidence_status=UNVERIFIED`, even for a structurally complete chain.
No numerical cash claim is produced.

Canonicalization is the existing receipt v1 algorithm: remove receipt_sha256,
JSON with ensure_ascii=False and sort_keys=True, SHA256 of UTF-8 bytes.

## Actual consumer and current limits

`python -m tools.replay_revenue_run PATH --policy-sha SHA` reads a single-run
JSONL stream without writing it. Exit 0 means STRUCTURE_VALID, not cash or
LIVE. Exit 2 means INVALID. Blank or corrupt entries are never skipped.
Error output omits the record content, preventing accidental PII exposure.

Existing producers have not been changed to emit this contract. Integration
into intake, owner release, provider dispatch, settlement, and witness is
still required, followed by real source read-back on the intended live HEAD.
External attestation cannot be established from self-supplied hashes.
Ziman hold_external remains true; two-step owner release remains mandatory.
The code has no external-effect path and does not implement a release gate.

Source/task/test hashes are in SOURCE-RECEIPT.json. Model digest is UNKNOWN:
no trustworthy model build digest is available in this run, so no provenance
claim substitutes a guessed model name or digest.

## Verification

55 tests passed: new negative/boundary cases plus existing receipt and
revenue-state regressions. `tests.xml` is the actual local JUnit evidence.
Grade E3 for this bounded contract. No E4/E5 or cash/run completion claim.
