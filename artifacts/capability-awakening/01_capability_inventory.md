# Capability implementation inventory

Discovery was performed against commit `65258776598c6eb43bb49dacb5208c42a65084b4` before implementation. No capability-specific environment flags existed. Activation is controlled by the validated file registry, not by invented environment variables. The live schema remains `phase3-skin-1`.

## 1. MEMORY_RETRIEVAL

- Existing source: `ofn/organism/memory/gate.py`, `ofn/organism/memory/episodic.py`.
- Entrypoint: `require_memory_gate()` / `mandatory_memory_read()`.
- Readers: bitemporal reads from `episodes` and `events`; `recall()` joins episode provenance.
- Writers: successful reads write `memory_read_receipts`; accepted decisions write `decision_evidence`.
- Tables: `episodes`, `events`, `memory_read_receipts`, `decision_evidence`.
- Real feature flag: none. This is fail-closed runtime behavior.
- Tests: `test_memory_gate.py`; controlled-growth tests verify a receipt and evidence before every experiment.
- Side effects: one or more small receipt/evidence inserts per decision; no external effect.
- Rollback: registry returns to `TESTED`; the mandatory memory gate remains enabled and evidence is preserved.
- Budget: one mandatory query bundle per controlled experiment, limit 20 per events/episodes query.

## 2. MEMORY_CONSOLIDATION

- Discovery result: single-event episode creation existed in `memory/episodic.py`; multi-event provenance-preserving consolidation did not.
- Implemented source: `ofn/organism/growth/controlled.py`.
- Entrypoint: `run_controlled_growth(..., experiment="EPISODIC_CONSOLIDATION")`.
- Readers: up to 20 recent heartbeat events, prior `memory_consolidation` events, and mandatory memory evidence.
- Writers: one `memory_consolidation` result event and episode, followed by one complete `controlled_growth` receipt event and episode, all through the official event kernel.
- Tables: existing `events`, `outbox`, `episodes`, `memory_read_receipts`, `decision_evidence`.
- Real feature flag: none; registry must be `CANARY` under the exact one-use execution ID.
- Tests: `test_consolidation_preserves_raw_events_and_records_all_provenance`.
- Side effects: adds provenance-bearing events/episodes only; raw source rows are hash-checked before and after and never updated.
- Rollback: return registry to `TESTED`; preserve consolidation and failure evidence.
- Budget: at most three source events in one canary experiment; no model or network call.

## 3. LOCAL_CURIOSITY

- Existing source: `ofn/organism/cognition/curiosity.py`.
- Added controlled entrypoint: the `SELF_MODEL_GAP` experiment in `growth/controlled.py`.
- Readers: validated registry evidence plus mandatory local memory evidence.
- Writers: a non-executable `CapabilityProposal` result event/episode and controlled receipt.
- Tables: existing `events`, `outbox`, `episodes`, `memory_read_receipts`, `decision_evidence`.
- Real feature flag: none. `OCTOPUS_LEARN_EXTERNAL` does not gate local gap detection and remains `0`.
- Tests: existing named-decision-path test plus `test_self_model_gap_persists_non_executable_proposal_with_memory`.
- Side effects: records one local proposal; it cannot dispatch an action.
- Rollback: return registry to `TESTED`; retain the proposal with `executable=false`.
- Budget: one deterministic registry scan over ten entries; zero model calls.

## 4. LOCAL_LEARNING

- Discovery result: `cognition/learn.py` implemented external model learning only when `OCTOPUS_LEARN_EXTERNAL=1`; that path remains disabled and is not reused.
- Implemented source: classification/provenance persistence in `growth/controlled.py`.
- Entrypoint: completion of any allowed experiment, especially `LOCAL_HYPOTHESIS`.
- Readers: local telemetry and mandatory memory evidence.
- Writers: result and receipt events/episodes carrying `SUPPORT`, `REJECT`, or `INSUFFICIENT_EVIDENCE`.
- Tables: existing `events`, `outbox`, `episodes`, `memory_read_receipts`, `decision_evidence`; no `learned_topics` write.
- Real feature flag: none for local learning. `OCTOPUS_LEARN_EXTERNAL=0` is a required invariant.
- Tests: controlled self-gap, consolidation, and hypothesis tests.
- Side effects: only provenance-bearing local evidence; no unsupported fact is promoted.
- Rollback: return registry to `TESTED`; preserve post-deploy cognitive evidence.
- Budget: one classification per experiment, maximum three for this execution.

## 5. SELF_MODEL_UPDATE

- Existing source: `ofn/organism/identity/self_model.py`, called from `runtime/life_cycle.py`.
- Entrypoint: `build_self_model()` and `persist_self_model()` after a committed `self_model` source event.
- Readers: measured snapshot, prior `self_models`, mandatory `introspect` memory read.
- Writers: `self_model` event/episode and versioned `self_models` row.
- Tables: `events`, `outbox`, `episodes`, `self_models`, `memory_read_receipts`, `decision_evidence`.
- Real feature flag: none.
- Tests: named decision path, life-cycle tests, and controlled proposal test.
- Side effects: the ordinary heartbeat may append a version; controlled experiments do not force an unsupported self-model fact.
- Rollback: registry to `TESTED`; never delete post-deploy self-model versions.
- Budget: unchanged ordinary heartbeat behavior; no extra self-model write is required by the experiment endpoint.

## 6. INNER_SPEECH

- Existing source: `ofn/organism/cognition/inner.py`, called from `runtime/life_cycle.py`.
- Entrypoint: `inner_turn()`.
- Readers: local snapshot, learned-topic metadata, and mandatory `inner_speech` memory evidence.
- Writers: `inner_speech` row plus an `inner` event/episode during ordinary heartbeats.
- Tables: `inner_speech`, `events`, `outbox`, `episodes`, `memory_read_receipts`, `decision_evidence`, and read-only `learned_topics`.
- Real feature flag: none.
- Tests: life-cycle tests and named decision path test.
- Side effects: one grounded local turn per ordinary cycle; no send or actuator.
- Rollback: registry to `TESTED`; preserve turns already written.
- Budget: existing one turn per heartbeat; heartbeat interval is unchanged.

## 7. LOCAL_HYPOTHESIS_ENGINE

- Discovery result: futures hypotheses existed, but no bounded falsifiable local telemetry experiment/classifier existed.
- Implemented source: `_local_hypothesis_plan()` and the controlled dispatcher in `growth/controlled.py`.
- Entrypoint: `run_controlled_growth(..., experiment="LOCAL_HYPOTHESIS")`.
- Readers: `/proc/meminfo`, local cortex responses on numeric loopback `127.0.0.1:8081`, and mandatory memory evidence.
- Writers: one `local_hypothesis` result event/episode plus a controlled receipt.
- Tables: existing `events`, `outbox`, `episodes`, `memory_read_receipts`, `decision_evidence`.
- Real feature flag: none; exact registry/gate checks are required.
- Tests: `test_local_hypothesis_is_bounded_local_and_noncausal`.
- Side effects: five tiny local inference requests; model text is discarded, only latency/status and memory telemetry are retained.
- Rollback: registry to `TESTED`; quarantine while preserving result evidence.
- Budget: exactly five local calls, at most four output tokens each, eight-second timeout each, zero WAN calls, no induced load.

## 8. SANDBOX_EXPERIMENTS

- Discovery result: no live controlled sandbox dispatcher existed.
- Implemented source: `growth/controlled.py` and authenticated POST routing in `runtime/app.py`.
- Entrypoint: `POST /api/v1/controlled-growth`.
- Readers: one validated registry, one real heartbeat event, safety state, identity, SQLite checks, and memory evidence.
- Writers: only official runtime result/receipt events and episodes.
- Tables: existing `events`, `outbox`, `episodes`, `memory_read_receipts`, `decision_evidence`.
- Real feature flag: none; exact gate, execution ID, registry state, and token authentication are mandatory.
- Tests: one-per-heartbeat, maximum-three, registry-transition, provenance, and LAN/GET-purity suites.
- Side effects: only the three enumerated local experiments; unknown or repeated requests return a non-executable error.
- Rollback: registry to `TESTED` disables the endpoint without a service restart.
- Budget: one experiment per real heartbeat, maximum three in the one-use execution.

## 9. ENGINEERING_THETA

- Discovery result: a pure disconnected Δθ function existed only in `/opt/octopus/ofn-l4/ofnl4/theta.py`; it had no tests or writer.
- Implemented source: pure `engineering_delta_theta()` in `growth/controlled.py`, with explicit non-subjective/non-conscious/non-executable labels.
- Entrypoint: calculation attached to each complete controlled-growth receipt.
- Readers: bounded experiment classification and safe homeostatic status.
- Writers: no `theta` table; the metric is stored inside the existing controlled receipt event/episode.
- Tables: existing `events`, `outbox`, `episodes` only through the enclosing receipt.
- Real feature flag: none.
- Tests: `test_engineering_theta_is_pure_non_executable_metric`.
- Side effects: pure arithmetic only.
- Rollback: registry to `TESTED`; historical metrics remain evidence.
- Budget: four clamped scalar inputs and constant-time arithmetic.

## 10. ACTIVE_INFERENCE_SHADOW

- Existing source: `ofn/organism/cognition/active_inference.py`.
- Entrypoint: pure `expected_free_energy()` / `plan_shadow()`.
- Readers: caller-provided matrices of at most four states.
- Writers: none; it is not imported by the heartbeat or any action dispatcher.
- Tables: none.
- Real feature flag: none.
- Tests: `test_active_inference_shadow_not_executable`.
- Side effects: pure local ranking with `EXECUTABLE=False`.
- Rollback: remain `SHADOW`; no activation transition is permitted.
- Budget: at most four states, no dependency install, no model, no network.

## Schema and forbidden-surface finding

The implementation uses only the existing `phase3-skin-1` tables and event payload JSON. No migration, new table, identity format, port, token, firewall, LAN configuration, heartbeat interval, or external-learning setting is required.

All forbidden capabilities remain represented by exact false/locked invariants in `02_capability_registry.json`. No shell execution, service control, file deletion, write outside `/opt/octopus`, external message, sensor recording, actuation, purchase, financial action, identity rewrite, safety-gate modification, autonomy escalation, or executable action is present in the controlled runtime path.
