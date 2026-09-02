---
type: reference
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, surgery, decisions, governance]
created: 2026-08-30
updated: 2026-08-30
created_by: agent
sources:
  - "[[CHECKPOINT]]"
  - "[[00-CONCEPT-MAP]]"
---

# Surgery 1 decisions

## S1-D01 — Result classification

`TEST_ONLY_GUARD` is final. Production behavior changes equal zero.

## S1-D02 — Verifier wording

`27/27` means 27 checks executed by one verifier. The claim that these were
27 independent verifiers is `CONTRADICTED` and must not be restored.

## S1-D03 — Cognition boundary

Narrow cognition separation is `VERIFIED` only for the policy’s enumerated
source paths. This is not a system-wide claim.

## S1-D04 — Provider boundary

Cortex → provider is `SAFE_INFERENCE_BOUNDARY`. Provider adapters may retain
model-network and provider-credential capability because they expose inference
responses, not approval or executor authority.

## S1-D05 — Executor boundary

`code_brain → code_autonomy` is `APPROVED_EXECUTOR_BOUNDARY`, not provider-only.
Proposal generation does not imply owner approval.

## S1-D06 — Gate namespaces

OFN `secret_rotation` remains distinct from rotation-vault mechanisms. Surgery 1
does not change either.

## S1-D07 — Provenance

The parent manifest, surgery receipt, resulting manifest and Git commit remain
separate immutable provenance values listed in [[CHECKPOINT]].

## S1-D08 — Operations

No push, merge, deployment, runtime restart, provider call, external effect or
owner-gate modification is authorized or recorded by this synchronization.

## S2-D01 — Lab gateway

The gateway is `ISOLATED_LAB_ONLY`. Presence of a provider credential is not
authorization. The gate is checked before key status, budget or client creation.

## S2-D02 — Explicit admission

Admission requires all of: explicit lab mode, runtime zone `lab|test`, an
allowlisted lab entrypoint, `executable=false`, and `external_action=false`.
No environment variable was added as a generic bypass.

## S2-D03 — Inventory

Every known provider caller must be classified as router-fenced, adapter-fenced,
lab-gated or choke primitive. Residual callers remain forbidden.

## S2-D04 — GitHub publication

No push or PR is permitted from this lineage: `github/main` and the local vault
branch have no merge base. Repair requires an explicit repository migration,
not force push, merge, rebase or history rewrite.

## S3-D01 — Hermetic default

The default runner is offline except loopback, strips provider/sender credentials,
forces outbound flags off, and redirects state/artifacts to a temporary root.

## S3-D02 — Live tests

Live tests remain present. They are not part of the hermetic default and require
both `--live` and `OCTOPUS_ALLOW_LIVE_TESTS=1`. Neither was used.

## S3-D03 — Capability marker

Default and `--only` hermetic runs do not refresh or revoke the runtime capability
marker. Persistent marker behavior remains available only for explicit isolated
or `--live-state` execution.

## S3-D04 — Cortex import

The test imports `cortex.cortex` explicitly. Path-order manipulation is no longer
used to choose between the package and module.

## S4-D01 — Observatory lineage

The implementation and runtime claim stores are `NOT_FOUND_IN_CURRENT_LINEAGE`.
This does not assert that they never existed.

## S4-D02 — Historical metrics

Historical values including 0.80, 0.99, n=114 and Brier tables are narrative
artifacts until reproduced from actual claim records. They cannot score current
measurement quality.

## S4-D03 — No resurrection from prose

No strategy, verifier or database is reconstructed by copying formulas or values
from documentation. Replacement begins from a versioned fixture and independent
producer/scorer/verifier boundaries.

## S5-D01 — Contract beside parser

The new `observation.v1` record lives in `observation_record.py`. The USGS/HN
`parse_body` adapter remains unchanged.

## S5-D02 — Replay only

Fake and replay adapters may not emit an unlabeled physical observation. A real
sensor is out of campaign scope.

## S5-D03 — Local vault branch publication remains forbidden

`ari-OCTOPUS/ofn-node` is PUBLIC and has no merge base with this vault. Pushing
the surgery or rescue branch would publish vault history.

## S5-D04 — Selective public export is PR 6

Canonical export: https://github.com/ari-OCTOPUS/ofn-node/pull/6
PR 5 is `CLOSED_SUPERSEDED`. Merge remains `NOT_AUTHORIZED`.

## S6-D01 — Publication is no longer forbidden
S2-D04 and S5-D03 are SUPERSEDED. ari-OCTOPUS/ofn-node main and the working
lineage were reconciled by PR #11 (merged 2026-08-31). Direct branch push plus
in-repo PR is the normal path. Force-push, history rewrite and vault-history
publication remain forbidden.

## S6-D02 — Canonical claim model
ClaimRecord (obs_fixture.py, owner decision Q5=A) is canonical. claim.v1 is a
serialization shape reached only through claim_adapter. Strict time rule
resolved_at > observed_at applies to both. outcome is int 0/1.

## S6-D03 — predicted_p is not a claim field
Prediction values do not live on the claim row and stay excluded from
provenance_hash. Until piece 3 removes the field, it is validated before the
resolved/unresolved branch, never after.

## S6-D04 — Superseded pull requests
PR #1, #2, #3, #4 are CLOSED_SUPERSEDED by the PR #11 reconciliation or target
a non-main base. Closing them is bookkeeping, not a content decision.

## S6-D05 — Merge is not single-signature
main accepts merges from more than one collaborator account. The owner queue is
not the only gate at the GitHub layer. Any claim that "nothing reaches main
without the owner" must be stated as a process intent, not a mechanism.

## S6-D06 — Admin-merge is a mechanism, not a gate (registered 2026-09-01)
The four docs PRs (#12, #14, #13, #15) and later docs merges were merged
with administrator privileges while repository checks were not satisfied,
under owner ruling Q8. This is the concrete mechanism behind S6-D05's
warning that the owner queue is not the only gate — admin override can
bypass repository checks entirely. It is registered here so the process
intent ("owner review before main") is not mistaken for a mechanism. Any
future admin-merge should be owner-ruled and referenced to this entry.

## S6-D07 — Brier contradiction resolved with one canonical bundle (2026-09-01)
Three contradictory historical records (0.346 vs 0.259; 0.237 vs 0.259;
0.34565 vs 0.286113) are closed by a single reproducible measurement at a
pinned commit: strategy 0.237387 CI95 [0.182603, 0.292171] vs persistence
0.258498 CI95 [0.220513, 0.296484], n=35 resolved, seed 20260830, all
verifier checks green. The 0.237 record is CONFIRMED; the other two are
STALE (older fixture/scorer versions). CIs overlap, so no superiority claim
is made — consistent with the receipt's own superiority_claim: None.
Bundle: docs/octopus-surgery/receipts/BRIER-CANONICAL-20260901.json.
This also unblocks the vault manifest's Q1_host ("current independent Brier
score and confidence interval"): the answer now exists with provenance.
official_n remains unset; this is a fixture measurement, not an official
announcement. run_observatory.py / bayesian_strategy.py / verify_live_store.py
remain absent at HEAD; fixture_run.run_pipeline is their canonical successor.

## S6-D08 — P001 stop-command superseded (owner, 2026-09-01)
The 24h megaprompt's stop-after-P001 gate is superseded by the owner's
same-day commands ("...ابسیدین و گیت هابم اپدیتکن" and "do both parallel"):
phases 2-6 data/doc mutations and their GitHub merges are authorized.
Board138 deploy/runtime mutation stays DEPLOY_BLOCKED; paid calls and
external business effects stay out of scope. Receipt:
receipts/S6-D08-SUPERSESSION-20260901.json.
## S6-D09 — D0_BLOCKED context hygiene (2026-09-01)
Per the three-model audit: (1) the PR #27/#28 merges are registered as a
supersession under S6-D08's standing owner order, so no future audit counts
them as undetected mutations; (2) the market score deltas 74/73 are WITHDRAWN
as post-hoc — canonical scores revert to 72/69/61 INTERNAL_FIT_SCORE while
the owner-native market LEVELS stand; (3) the restore-drill 'local env
failure' was root-caused to a real guard_target bug (drive-root prefix check)
and the test is now a host-independent negative-control. The D-program state
is untouched: THIRD_PARTY_FAILED_STOP / D0_BLOCKED / D1 = NOT_STARTED.
Receipt: receipts/S6-D09-D0BLOCKED-CONTEXT-20260901.json.

## S6-D10 — governance rules generalized; admin merges registered per S6-D06 (2026-09-01)
Three standing rules from the owner's verdict: (1) NO_POST_HOC_RUBRIC — no
criterion is created or re-tuned after seeing the evidence it scores (Brier
superiority withheld; market deltas withdrawn); (2) SAFETY_GATE_LOCAL_FAILURE_
STAYS_OPEN — a local failure of a safety-gate test is never closed by "CI is
green"; it stays OPEN until the differing parameter is found (guard_target:
cwd-parent-is-drive-root). Green CI on an uncovered parameter space is the
more dangerous case. (3) externally unobservable claims stay
LOCAL_RECEIPT_CLAIM until verified from the repo. The full admin-merge
register (which PRs, under what state, per S6-D06) lives in
receipts/S6-D10-GOVERNANCE-RULES-20260901.json.

## S6-D11 — survival-loop ratified as the next execution frame; nothing started (2026-09-01)
The owner's bounded-autonomy plan is the frame for what comes next:
freedom-to-discover automated (A0-A4), freedom-to-affect envelope/owner-gated
(A5-A8); north star verified_cash_collected; L0-L7 ladder targeting L5;
revenue/resource caps 60/25/10/5. Hard gates before any loop runs: the
20-test mandatory battery, 7 shadow days, observatory runtime re-proven.
Wave-1: seeded truth-audit benchmark (>=80% recall / <10% FP before any
public repo), narrow-green CI detector with mutant proof, painting loop,
rescue-as-truth-audit, capped nightly self-audit. Board deploy stays
DEPLOY_BLOCKED; no A5+ activity starts without a campaign envelope.
Receipt: receipts/S6-D11-SURVIVAL-LOOP-FRAME-20260901.json.

## S6-D12 — outbox hardening + process honesty (2026-09-01)
The deep audit's findings are accepted and registered: seven PRs at a mean
lifetime under ten minutes is self-certification, not review; PR #29 mixed
two unrelated decisions (anti-pattern for a reversibility project);
'CI green' never meant 'reviewed'. Brier's NOT_PROVEN is restated precisely:
UNDECIDED, not refuted — n=35 with a 0.021 difference is underpowered, a
no-signal result. The outbox was re-measured (stronger than claimed) and
hardened: composite (tenant, idem_key) primary key, raw keys with the
seven composition sites removed, idempotent legacy migration, plus TEN
negative controls on the real machine — the guard_target lesson applied.
Commitments: one decision per PR; branch protection with required approvals
enabled immediately after this PR merges, making sub-15-minute self-merges
impossible going forward. Receipt: receipts/S6-D12-OUTBOX-AND-PROCESS-20260901.json.

## S6-D13 — D-26 owner ratification of STAGE-01 package (2026-09-01)

The owner said: take the whole senior-agent package and register it on
behalf of owner and partners, then: they all signed. This is a
**record**, not wave-1 start, merge, deploy, or WIRE. Owner attests
all three partners signed; this vantage still did not hear them
(`owner_attests_all_signed=true`,
`partner_voices_independently_observed=false`). Canonical split:
business=`ofn-node`, architecture=vault, mesh after edge contract.
Receipt: `stage-01-lineage-scan/2026-09-01/OWNER-RATIFICATION.json`.

## S6-D14 — D-27 unlock (2026-09-02)

Owner + senior-agent: authorization fields of D-26 become true, with
caps (25 sends/day, 50 AUD/day, per-board budget 0) and kill-switch
`OFN_EXTRA_CLOSED_GATES`. Propose-only ends. Four facts stay outside
decree: partner voices, Saba consent record, real secret rotation,
platform ToS. C-009 closed as identity. O-3 and S-04 move later→open.
`OFN_KEEP_GATES_OPEN` and `OFN_WIRE_OUTBOUND` are not defaulted on.
Receipt: `stage-01-lineage-scan/2026-09-01/D-27-OWNER-DIRECTIVE.json`.

## S6-D15 — D-28 rule-edge; three fields unforged (2026-09-02)

Partner voices do not block painting. Observation stays false until
three `media_sha256` receipts exist **and** a verifier has accessed
each file. 2026-09-02 Windows hashes are recorded under
`attestations/receipts/`; `sume` is not Abbas; observation stays
false. Saba consent is
`record_release` only. Secret rotation on this host is
`risk_accepted_unrotated`. `GATE_OPEN_UNTIL_UTC=2026-09-16`.
Platform matrix filled to the ToS edge. Advisor gate stays
parameterless. Receipt:
`stage-01-lineage-scan/2026-09-01/D-28-OWNER-DIRECTIVE.json`.
