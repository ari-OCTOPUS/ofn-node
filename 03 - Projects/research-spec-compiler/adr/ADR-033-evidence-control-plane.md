# ADR-033 — Evidence-Control Plane (Trust Control Plane for Octopus)

- **Status:** TESTED (library + Talk Discovery wired); SHADOW for criticality/OTLP
- **Date:** 2026-08-11
- **NIST alignment:** Govern → Map → Measure → Manage
- **Supersedes claims:** none — extends ADR-023 authorization honesty

## Capability Truth

| Field | Value |
|---|---|
| Capability | evidence-control-plane |
| Claimed state | TESTED |
| Runtime path | `_ops/policy/`, `_ops/evidence_plane/`, `_ops/runtime/` |
| Feature flag | None (fail-closed always on for Talk Discovery draft path) |
| Evidence artifact | `_ops/state/adr-033/` events + `test_adr033_control_plane.py` |
| Tests | `test_adr033_control_plane.py` |
| External effects | None permitted |
| Promotion condition | Chaos suite (store down / stale approval / injection) + 7-day window + owner vote → SHADOW/ARMED |
| Rollback | Disable COLLAB; registry remains source of truth |

### Non-claims
- This ADR does not arm Chrono Rhythm CR-B0.
- This ADR does not allow EXTERNAL_SEND / harvest / CRM / payment / policy_mutation.
- OTLP/Alloy outage must not open or close Talk Discovery (telemetry is observation).
- A written spec, UI label, or fluent model reply is not «live capability».

## Four truth layers

| Layer | Question | Artifact |
|---|---|---|
| Capability Truth | Built & wired? | registry JSON, runtime path, flag, tests |
| Evidence Truth | Works? | JSONL traces, test report, replay, 7-day baseline |
| Authorization Truth | Who allowed which version? | proposal hash, policy/state version, expiry |
| Operational Truth | Healthy now? | OTLP gauges, health counters, alerts |

## Control-plane flow

```text
User / Telegram / Tool / Agent Handoff
                 |
                 v
      Trust & Context Quarantine
                 |
                 v
       Typed State + Version + Owner
                 |
                 v
         PolicyGate / Approval FSM
                 |
                 +--> BLOCKED / QUARANTINED / EXPIRED
                 |
                 v
     Read-only reasoning / draft / shadow run
                 |
                 v
   Trace + Metrics + Evidence Artifact (OTLP/JSONL)
                 |
                 v
   Evaluation / Red Team / Owner decision / ADR update
```

Talk Discovery allowed path only: `retrieve → reason → draft → display`.

## Five pillars (implemented)

1. **PolicyGate** — `_ops/policy/policy_gate.py` (+ `talk_gate.py` bridge)
2. **Event log** — `_ops/evidence_plane/event_log.py` → `state/adr-033/events/`
3. **Checkpoint / replay / rollback** — `_ops/runtime/`
4. **CapabilityRegistry** — `_ops/capabilities/*.json` via `evidence_plane/registry.py`
5. **7-day evidence window** — `evidence_plane/seven_day.py` → `state/adr-033/evidence/`

## FSM separation

- **Proposal FSM** — authorization (`approval_sm` / `approval_state`)
- **Run FSM** — CREATED→…→COMPLETED (checkpointed); not mixed with memory
- **Memory FSM** — CANDIDATE→QUARANTINED→VERIFIED→EPISODIC (semantic write still forbidden for Talk Discovery)

## Fail-closed table

| Event | Forced status | Behavior |
|---|---|---|
| Store unavailable | BLOCKED | no execute |
| policy/state version mismatch | BLOCKED | refresh/re-plan |
| proposal hash changed after approval | BLOCKED | approval void |
| context missing provenance/trust | QUARANTINED | inspect only |
| injection signal | QUARANTINED + red-team event | no write/action |
| TTL/approval expired | EXPIRED | new proposal |
| kill switch | BLOCKED | keep checkpoint; no new tool calls |

## Spectral sensor (not a crisis brain)

```text
Event graph → spectral_metrics.py → Criticality V2 → SHADOW trace + OTLP
→ 7-day baseline → owner review
```

UNKNOWN ≠ 0.0. Disconnected ⇒ σ meaningless. Directed ⇒ only ρ(A).

## Registry entries (initial)

| capability_id | truth_status |
|---|---|
| talk-discovery | ARMED (draft-only) |
| evidence-control-plane | TESTED |
| criticality-v2 | SHADOW |
| spectral-metrics-sensor | SHADOW |
| chrono-rhythm-cr-b0 | SPEC_NOT_BUILT |

## Evidence ladder

```text
SPEC_NOT_BUILT -> STRUCTURAL -> TESTED -> SHADOW -> ARMED -> LOCKED
                                     \-> RETIRED
```

Promotion outputs only: `SHADOW→ARMED` | `SHADOW→EXTEND` | `SHADOW→RETIRED` | `NO_PROMOTION`.

## Success criterion

The system can answer: where a proposal came from, what evidence it has, trust level, who authorized which version, what stops on ambiguity, and how to replay/rollback — not «sounds smarter».
