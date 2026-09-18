---
type: policy-proposal
id: MIRROR-001
status: proposed
requires: owner_decision
may_authorize: false
as_of: 2026-09-04
lane: Q-180-DECISION-CRITIQUE-20260904
---

# PROPOSED — MIRROR-001

This file is a draft. It is not registered until the owner signs
`07-HANDOFF/GO-MIRROR-DRILL-OWNER-SLIP-2026-09-04.md`.

## Purpose

Keep `origin/main` on `github.com/ari-OCTOPUS/ofn-node` a fast-forward
audit mirror of node138 `/home/ari/ofn` `main`. The packet states the
PR path is not the remaining independent audit trail
(`09-LANES/M-MIGRATION-TRANSFER-20260904/MIGRATION-EXECUTION-PACKET.md`
Phase 5 item 1).

## Push rule

1. Preflight on node138 only, with `GIT_OPTIONAL_LOCKS=0`.
2. If `HEAD..origin/main` is not empty: stop. Do not merge, rebase, or force.
3. If `HEAD..origin/main` is empty: push rescue branch `138-main-20260904`
   to `origin` first, then fast-forward `main`.
4. Force is forbidden. `germline` is forbidden. Only `origin`.
5. Do not stage untracked state. Packet observation:
   `untracked_source_entries_observed: 28`
   (`09-LANES/M-MIGRATION-TRANSFER-20260904/MIGRATION-FACTS.json`).

## Warning threshold (proposed, not measured tonight)

Inbound draft said: lag greater than 3 commits **or** greater than 24 hours.
Source of that threshold: owner chat 2026-09-04, not a prior vault file.
`status: unverified` as an adopted number until the owner signs this text.

## Observed lag pair — do not pick one

| value | source | status |
|---|---|---|
| origin/main `e00c8ed5be7ec6609c600bb7a5bc3b99ace3c3e9`; source ahead **5** | `MIGRATION-FACTS.json` `source_mirror` | open |
| at least three named local commits `c75473af`, `1c81bdf`, `2cd67aa` | owner chat 2026-09-04 | open |
| GitHub date `2026-09-04T04:27:13Z` | owner chat 2026-09-04 | unverified on this host; no network fetch |

Fresh preflight on node138 outranks both.

## Registration meaning

Writing this file, plus an owner-signed slip, registers the policy in the
vault. A GitHub push is a separate action and is not required before
drill option A.
