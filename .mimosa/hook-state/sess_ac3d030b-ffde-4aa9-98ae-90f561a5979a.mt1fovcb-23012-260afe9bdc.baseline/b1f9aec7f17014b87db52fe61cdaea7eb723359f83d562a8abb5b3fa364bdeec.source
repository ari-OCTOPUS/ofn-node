---
title: "Octopus Event Taxonomy v1"
date: 2026-07-09
schema_version: "1.0.0"
status: LOCKED — do not rename without major version bump
convention: organ.domain.action (3-segment dot notation)
---

# Octopus Event Taxonomy v1

> Locked namespace. Every `event` field in log events MUST match one of these.
> New events require schema minor bump (1.x.0). Renames require major bump (2.0.0).

## Naming Convention

```
organ.domain.action
│     │      └── past tense verb (completed, failed, blocked, started, skipped)
│     └── domain within organ (tick, gate, tool, handoff, lifecycle, awareness)
└── organ name (heart, doctor, governor, legs, telegram, ledger, gates, money, learning, epistemics, selfmodel, watchdog, sensors, capability, box)
```

## Taxonomy

### Heart (Pacemaker + Cardiac)

| Event | When | Key Payload Fields |
|---|---|---|
| `heart.tick.started` | Tick loop iteration begins | `{tick_seq, epoch_mode}` |
| `heart.tick.completed` | Tick loop iteration ends | `{tick_seq, duration_ms, protective_skip}` |
| `heart.beat.pulsed` | Chrono pacemaker fires | `{beat_seq, phi, hlc}` |
| `heart.cardiac.adjusted` | Cardiac allometry changes period | `{period_s, mass, pace, baro_factor}` |
| `heart.cardiac.depleted` | BeatBudget runs out | `{remaining, daily_cap}` |

### Doctor

| Event | When | Key Payload Fields |
|---|---|---|
| `doctor.cycle.started` | Doctor run_cycle begins | `{beat_interval}` |
| `doctor.cycle.completed` | Doctor run_cycle ends | `{rfc_count, sandbox_passed}` |
| `doctor.rfc.drafted` | RFC created | `{rfc_id, bottleneck_type}` |
| `doctor.rfc.sandboxed` | RFC passed sandbox | `{rfc_id, tests_passed, critic_verdict}` |
| `doctor.rfc.submitted` | RFC sent for approval | `{rfc_id, channel}` |
| `doctor.rfc.rejected` | RFC rejected by human | `{rfc_id, reason}` |
| `doctor.box.tick` | Box-of-agents simulation tick | `{agent_count, jacobian_rho}` |

### Governor (Budget + Epoch)

| Event | When | Key Payload Fields |
|---|---|---|
| `governor.epoch.started` | Epoch allocation begins | `{pressure, allostatic_period}` |
| `governor.epoch.completed` | Epoch allocation ends | `{total_allocated, explore_reserve}` |
| `governor.epochs.allocated` | Per-organ allocation | `{organ, amount, floor, fitness_score}` |
| `governor.barbell.rebalanced` | Barbell redistribution | `{core_total, satellite_total}` |
| `governor.conflict.detected` | Budget conflict found | `{type, organs_involved}` |

### Legs

| Event | When | Key Payload Fields |
|---|---|---|
| `legs.lead.intake` | Lead registered | `{attribution_id, source}` |
| `legs.lead.quoted` | Quote drafted | `{attribution_id, scope, price_range}` |
| `legs.lead.claimed` | Quote sent to client | `{attribution_id}` |
| `legs.lead.confirmed` | Revenue confirmed | `{attribution_id, amount}` |
| `legs.budget.reserved` | Budget reserved via organ_gate | `{organ, amount}` |
| `legs.budget.settled` | Budget settled | `{organ, amount}` |

### Telegram (Human Interface)

| Event | When | Key Payload Fields |
|---|---|---|
| `telegram.message.sent` | Bot sends message | `{chat_id, message_type}` |
| `telegram.message.received` | Bot receives message | `{chat_id, message_type}` |
| `telegram.approval.received` | Human approves/rejects | `{rfc_id, verdict}` |
| `telegram.channel.stub` | Stub transport used (no creds) | `{reason}` |

### Ledger

| Event | When | Key Payload Fields |
|---|---|---|
| `ledger.entry.appended` | Entry written to ledger | `{type, agent}` |
| `ledger.guard.blocked` | Human-append-guard denies | `{reason}` |
| `ledger.heartbeat.written` | Heartbeat entry | `{beat_seq}` |

### Gates

| Event | When | Key Payload Fields |
|---|---|---|
| `gates.money.blocked` | Money gate denies | `{reason, organ, amount}` |
| `gates.money.approved` | Money gate approves | `{attribution_id, amount}` |
| `gates.capability.blocked` | Capability gate denies | `{reason}` |
| `gates.capability.passed` | Capability gate passes | `{test_count}` |
| `gates.organ.blocked` | Organ gate denies | `{organ, reason}` |
| `gates.live.locked` | Live gate date not reached | `{gate_name, unlock_date}` |

### Money / Risk

| Event | When | Key Payload Fields |
|---|---|---|
| `money.attribution.proposed` | Attribution proposed | `{cell_id, organ, amount}` |
| `money.fitness.computed` | Fitness snapshot | `{authoritative, claimed, confirmed}` |
| `money.reconcile.started` | Bank CSV reconciliation | `{file_count}` |
| `money.reconcile.completed` | Reconciliation done | `{matched, unmatched}` |
| `money.replication.evaluated` | Sigma replication check | `{sigma, zone}` |

### Learning / Neural

| Event | When | Key Payload Fields |
|---|---|---|
| `neural.stack.evaluated` | Neural driver evaluates | `{pain, reflex_active}` |
| `neural.consolidation.beat` | Consolidation cycle | `{paths_consolidated}` |
| `neural.sprint.started` | Sprint begins | `{goal, duration_beats}` |
| `neural.sprint.completed` | Sprint ends | `{outcome}` |
| `learning.hebbian.updated` | Hebbian weight change | `{source, target, delta}` |

### Sensors

| Event | When | Key Payload Fields |
|---|---|---|
| `sensors.observation.ingested` | Raw observation received | `{source, obs_type, label}` |
| `sensors.pii.detected` | PII pattern found | `{pattern, redacted}` |
| `sensors.afferent.alarm` | Afferent ratio too low | `{ratio, threshold}` |

### Epistemics

| Event | When | Key Payload Fields |
|---|---|---|
| `epistemics.metrics.computed` | Off-loop metrics done | `{identifiability, channel, levels}` |

### Self-Model

| Event | When | Key Payload Fields |
|---|---|---|
| `selfmodel.state.written` | ORGANISM-STATE.json updated | `{tick_seq, halted, frozen}` |

### Watchdog

| Event | When | Key Payload Fields |
|---|---|---|
| `watchdog.check.performed` | Port liveness check | `{port, alive}` |
| `watchdog.revive.proposed` | Revival proposed | `{reason}` |
| `watchdog.revive.executed` | Revival actually done | `{method}` |

### Capability Layer (Wiring)

| Event | When | Key Payload Fields |
|---|---|---|
| `capability.profile.applied` | Profile loaded | `{profile, flags_count}` |
| `capability.flag.changed` | Individual flag toggled | `{flag, old, new}` |
| `capability.restart.requested` | STOP + RESTART triggered | `{source}` |

### Debate

| Event | When | Key Payload Fields |
|---|---|---|
| `debate.round.started` | LLM debate round begins | `{round_num, role}` |
| `debate.round.completed` | LLM debate round ends | `{verdict, tokens_used}` |
| `debate.idea.killed` | Idea killed by architect | `{kill_condition}` |
| `debate.idea.survived` | Idea survived all rounds | `{survivor_id}` |

### System

| Event | When | Key Payload Fields |
|---|---|---|
| `system.incident.detected` | Anomaly detected | `{type, severity, affected_organs}` |
| `system.process.started` | Organism process starts | `{pid, port}` |
| `system.process.stopped` | Organism process stops | `{reason}` |

---

## Status Enum Reference

| Value | Meaning |
|---|---|
| `started` | Operation initiated |
| `success` | Completed successfully |
| `failed` | Errored out |
| `blocked` | Prevented by gate/policy |
| `retrying` | Will attempt again |
| `skipped` | Intentionally not executed |
| `unknown` | Cannot determine outcome |

## Approval State Enum Reference

| Value | Meaning |
|---|---|
| `required` | Needs human approval before proceeding |
| `approved` | Human approved |
| `denied` | Human rejected |
| `not_required` | Auto-approved (below threshold) |
| `pending` | Awaiting human response |
| `unknown` | Approval state cannot be determined |
