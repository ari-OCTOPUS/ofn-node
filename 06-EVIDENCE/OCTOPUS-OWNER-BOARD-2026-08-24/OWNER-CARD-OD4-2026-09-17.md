---
type: recorded-note
status: active
tags: [octopus, owner-card, od-4, halt-oracle, coverage, approved-targets]
updated: 2026-09-17
authority: owner
subject: OD-4 Option B — corrected targets, non-negotiable order, hard boundaries
---

# OWNER CARD — OD-4 + BQ-1/BQ-2 (2026-09-17)

**Recorded verbatim. Owner card. Date: 2026-09-17.**
Registered by: OD4 lane. This entry **records**; it opens no gate and authorizes no change
in itself.

---

## Decision

**OD-4 = Option B, with corrected targets after trace evidence.**

## Approved targets (verbatim)

> 1. Effect A — Telegram send:
>    site = ofn/node.py publish_to_telegram / ReleaseContext construction
>    plan = feed kill_switch_active from self.killed or canonical halt oracle result
>    oracle = existing opslib.master_halted(), not a second HALT path
>
> 2. Effect B — model spend:
>    site 1 = ofn/adapters/router.py model admission point
>    site 2 = ofn/assistant_update.py:32 direct call
>    accepted answer to BQ-2 = put halt check at the direct call site

## Rejected target (verbatim)

> - Do NOT wire callbudget.py for OD-4.
> - Trace says it does not gate the two real model-spend consumers.
> - Touching it would create a DECLARED ≠ WIRED fix.

## Non-negotiable order (verbatim)

> 1. Build doctor first.
> 2. Run doctor once offline.
> 3. Produce machine-readable pre/post receipts for coverage.
> 4. Only then apply the narrow wiring.

## Hard boundaries (verbatim)

> - No changes to release_switch.py, consent, ledger, budget thresholds, flags,
>   systemd, timers, HALT files, or any live node.
> - No implementation in this lane.
> - No live ablation.
> - No scope expansion into generalized guard architecture.
> - If any consumer path is still UNVERIFIED, stop and report instead of guessing.

## Acceptable coverage labels (verbatim)

> - WIRED
> - TESTED_ONLY
> - DOC_ONLY
> - UNVERIFIED

## Success definition (verbatim)

> - The packet must prove coverage, not just path correctness.
> - Any implementation must map only to the two approved effects:
>   Telegram send + model spend.
> - Nothing else counts as OD-4 scope.

---

## Status recorded against this card

| Item | State |
|---|---|
| BQ-1 (corrected target for effect B) | **CLOSED — approved as traced** |
| BQ-2 (assistant_update direct site vs router) | **CLOSED — direct call site** |
| `callbudget.py` as a wiring target | **REJECTED by owner**, matching the trace |
| Effect A site | **APPROVED** — `node.py:3607`, oracle = `opslib.master_halted()` |
| Effect B sites | **APPROVED** — `router.py` admission + `assistant_update.py:32` |
| Implementation of the wiring | **NOT AUTHORIZED yet** — gated on owner order steps 1–3 |
| Doctor build | **AUTHORIZED (read-only)** per OD-1 clause 3 + this card step 1 |
| Doctor run on live hardware | **NOT AUTHORIZED** — step 2 is "run once offline" |
| This lane's mode | **spec + prep + coverage proof only; no implementation** |

Related: `09-LANES/OD4-HALT-COVERAGE-WIRING-PREP-20260917/CHANGE-PREP-PACKET.md`,
`…/CONSUMER-MAP.json`, `…/LANE-REPORT.md`,
`09-LANES/LIVE-PATH-GATE-AUDIT-20260917/HALT-ORACLE-DOCTOR-SPEC.md`,
`06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/OWNER-RULING-OD1-2026-09-17.md`.
