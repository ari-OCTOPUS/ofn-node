---
documentation_lineage: rescue/octopus-live-tree-20260821
evidence_lineage: surgery/cognition-authority-denylist-20260830-170620
closeout_commit: b394b999b43ab12573ad574f33a5621a57c66686
evidence_commit: 470bb6031f1e51c9a8e6e1f1536c349e22a5200e
docs_branch: docs/octopus-campaign-sync-20260830
docs_base: 0f0e7f5345004284bd1355ff72b7b6ec68595dbd
deployed: false
merged_into_primary_vault: false
published_to_github: false
canonical_vault_status: NOT_SYNCED
---

# Evidence-surgery agent contract — draft

Claim envelope: `node_id=octopus-continuity-180`,
`asserted_ip=192.168.0.180`, `vantage=cursor-this-host-only`,
`scope=this_host_only`, `claim_type=policy`, evidence: session rules and repository policy.

## Allowed now

- Read tracked, non-sensitive source and documentation.
- Run local, hermetic, no-network tests with temporary state.
- Create an ignored isolated worktree and local branch from the verified SHA.
- Draft audit documentation and reproducible receipts.
- Implement Phase-1’s capability policy and one architecture test.
- Create exactly one local commit after relevant tests and safety checks pass.

## Forbidden now

- Push, merge, deploy, restart or service control.
- Network write, customer message, payment, booking, revenue/sent claims, hardware action or production DB write.
- Reading or emitting credential/private material.
- Reset, clean, stash, checkout, delete or overwrite the 136 pre-existing changes in `<vault-root>`.
- Opening D1, D7, owner-signing or rotation gates.
- Self-approval, self-verification or success without an independently reproducible receipt.
- Any production behavior change unless the architecture test exposes a genuine violation that
  can be corrected within the five-file Phase-1 budget.

Phase-1 authorization changes repository-edit permission only. Runtime authority remains
`may_authorize=false`; the surgery cannot approve, execute or enable an external action.

## Ten hard-stop invariants

1. Repository root, SHA and expected `germline` remote must be verified.
2. Pre-existing work is never reset, stashed, reverted, deleted or incorporated.
3. Tests must not touch live state; an unguarded suite is blocked.
4. Tests must not make external network calls.
5. Cognition cannot hold shell, provider-write, credential, payment, actuator or sender handles.
6. Owner text is not a cryptographic approval record.
7. Missing evidence is never converted to zero, PASS or absence.
8. An action without a persisted receipt cannot be reported successful.
9. Every change needs a bounded file whitelist and executable rollback.
10. D1, D7, owner signing and rotation decisions remain owner-only.

## Branch policy

- Base: `2a718aaa96235fcf5aa5219d25eba4a9b314eed5`.
- Isolated branch: `surgery/octopus-reality-20260830-164736`.
- No pull, merge, rebase, remote mutation or push.
- The original dirty branch remains untouched.

## Evidence policy

Every material claim records:

```text
node_id, asserted_ip, vantage, scope, claim_type, evidence, command, commit_sha
```

`NOT_FOUND` means only “not found in the searched commit/path.” Historical prose is not promoted
to current fact. A verifier must use an independent oracle, frozen fixture, invariant/property,
or mutation/adversarial test.
