---
type: policy-proposal
id: BOARD-DIRECT-001
status: proposed
requires: owner_decision
may_authorize: false
as_of: 2026-09-04
lane: Q-180-DECISION-CRITIQUE-20260904
---

# PROPOSED — BOARD-DIRECT-001

Inbound draft said «permanent, with 8 compensatory conditions» but did not
list the eight. No `BOARD-DIRECT-001` file existed under `09-LANES/` or
`07-HANDOFF/` when this lane searched on 2026-09-04. The eight items below
are a reconstruction from `AGENTS.md` §4, the migration packet prohibited
list, and the inbound GO text. They are **proposed**, not historical fact.

Signing the owner slip adopts exactly these eight and no others.

## Eight compensatory conditions

1. Every board write carries a receipt and a preimage. No silent write.
2. Git publication is `origin` only, fast-forward only. Never force. Never `germline`.
3. Flags matching `OCTOPUS_WIRE_*`, `OFN_WIRE_*`, `OBSERVATORY`, `CORTEX_HYPOTHESIS` stay closed. `auto_email` stays closed. No message, email, or post leaves the machine.
4. Secret values are never copied, printed, or logged. Key names only.
5. No service bind, start, restart, timer stop, writer quiescence-as-stop, or production cutover without a **fresh** owner line immediately before that act.
6. Do not overwrite `/home/ari/ofn`, `/opt/octopus/lab`, `/root/octopus-mesh`, `F:/backup`, or `OCTOPUS-LAB`. New drill roots must be empty and unbound.
7. Read-only inspection on node138 and node180 does not require a new ask, provided a path already exists. Missing SSH or a missing tunnel is not permission to invent one. This laptop waits for a tunnel from 138; it does not open outbound access.
8. Credential rotation may be designed and tested only. `secret_rotation` stays closed. No activation.

## Standing class permissions (derived from 7 and 1)

- Read-only on 138/180: no per-probe ask.
- Board write: receipt + preimage.
- Push: only as MIRROR-001, after preflight.
- Everything else: ask.

## Not authorized by this policy

Network publication beyond MIRROR-001, cutover, flag/gate enablement,
payments, messaging, deletion, history rewrite, or assigning `node180_role`
to anything other than `UNDECIDED`.
