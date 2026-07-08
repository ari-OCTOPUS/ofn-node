# Event Catalog & Module APIs (L0 bus + module contracts)

_Evidence: A (DOC-02 event record AKO-002) + [EST] for the module API surface. Every inter-module message is an immutable event on L0 (INV-05/10). No module direct-calls another (AP-08)._

## Event record (immutable) — AKO-002 `[SOLID]`

```
{ event_id, type, source, payload, requires_approval, autonomy_level, rollback_ref, ts }
```
`requires_approval` + `autonomy_level` make each event self-describing for the Guards.

## Event types (open set; extend additively)

| type | emitted by | consumed by | irreversible? |
|---|---|---|---|
| `beat` | Pacemaker | Orchestrator, all legs | no |
| `task.created` | Orchestrator | target leg | no |
| `subleg.spawned` / `subleg.killed` | Leg | Orchestrator, cost meter | no |
| `proposal.created` | Leg / Doctor | Epistemic Kernel → Critic → Guards | no (until settled) |
| `guard.decision` | Guard layer | Orchestrator, audit | no |
| `settled` | Ledger (on human-append) | effect dispatcher | **yes** (releases gated effect) |
| `money.recorded` | Money Agent | project registry | **yes** |
| `mode.changed` | Personal-State/Mode | all guards | no |
| `project.stalled` | Money Agent | Orchestrator | no |
| `module.failed` | any | Doctor (restart) | no |

## Core module APIs `[EST]` (proposal-only; never write source-of-truth)

- **Ledger (L0):** `append(event, is_human=0) -> entry_seq`; `replay(from_seq,to_seq)`; `head_hash()`. Only `is_human=1` advances `age_tick`.
- **Guard layer (L8):** `evaluate(event, active_mode) -> allow|deny|cooldown`. Default-deny.
- **Orchestrator (L3):** `dispatch(task)`; `spawn_subleg(parent, mission, budget)` (capped ~2–3 total, cost-billed to parent); `broadcast(beat, hlc, present)`.
- **Epistemic Kernel (L1):** `tag(claim) -> [E/S/P/M/I/R/C/G]`; `eliminability_test(node)`; `gap_report(output)`.
- **Memory (L4):** `vault.put(item)` (additive; `superseded_by`), `vault.get(id)`, `cache.extract(every_K_beats)`, `cache.evict()`; cache is non-authoritative.
- **Doctor (L7):** `mine(fabric, metrics) -> bottleneck`; `rfc(fix)`; merges require human-append (INV-02).

## Rules for every API

Propose, don't execute (INV-03) · emit an event per action (INV-10) · tag every claim (INV-08) · additive-only (INV-12) · irreversible effect ⇒ human-append (INV-01).

## Open

Exact API signatures / worker spawn-kill hooks / scheduler contract are **[UNVERIFIED]** — verbatim worker-runtime spec lives in a primary not fully in context (partly recoverable from DOC-B §9 pseudocode).
