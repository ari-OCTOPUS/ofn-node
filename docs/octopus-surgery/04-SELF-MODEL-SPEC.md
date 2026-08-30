# Factual self-model specification — draft

Envelope for all entries: `node_id=octopus-continuity-180`,
`asserted_ip=<redacted-private-ip>`, `vantage=cursor-this-host-only`,
`scope=this_host_only`, `claim_type=observation_or_explicit_inference`,
evidence: HEAD `2a718aaa96235fcf5aa5219d25eba4a9b314eed5`.

This self-model describes capabilities and limits. It must not express feelings, desires,
personhood, fear, fatigue, intent or consciousness.

## Required schema

```yaml
schema: octopus.self-model.v2
observed_at_utc: RFC3339
code_identity:
  commit_sha: string
  branch: string
sensors:
  - sensor_id: string
    implementation: path:symbol
    status: healthy | stale | failed | partial | unknown
    last_observation_at: RFC3339|null
    uncertainty: object
    calibration_ref: string|null
authority:
  may_propose: boolean
  may_approve: false
  may_execute: false
  direct_handles: []
budgets:
  network_write: 0
  external_effects: 0
  new_runtime_dependencies: 0
unknowns: []
reversible_actions: []
owner_only_actions: []
unsupported_claims: []
evidence_refs: []
```

## Current factual population

### Sensors

- `observatory-json-parser`: PARTIAL — `_ops/observatory/observation_v1.py::parse_body`;
  offline fixture parsing works, but timestamps are not validated and the result lacks provenance,
  uncertainty, calibration, simulation and privacy fields.
- `observation-envelope`: PARTIAL — `_ops/observatory/envelope.py::ObservationEnvelope`;
  body hash and untrusted-content boundary exist.
- `shadow-homeostasis-observation`: PARTIAL — `_ops/shadow_homeostasis/observation.py::Observation`;
  bitemporal timestamps and quality are represented, but calibration/simulation/privacy are absent.
- Real calibrated physical sensor: `NOT_FOUND` in the audited current vertical slice.
- Historical Internet observatory runner: `NOT_FOUND` at current HEAD.

### Health and staleness

- `OCTOPUS/CURRENT-TRUTH.md` was auto-written at `2026-08-30T05:47:47Z`, but its writer process
  was not identified from this vantage.
- No `eth0` adapter was found on the Windows host. Alternative explanations include Windows
  interface naming or a remote/virtual board context; this does not prove the body is absent.

### Limits and budgets

- Runtime authority remains `may_authorize=false`; Phase-1 authorizes only the local
  capability policy, architecture test, documentation, receipt and one local commit.
- No network writes, external effects, service control, restart, hardware action, production DB
  write, private-material access, push or merge.
- The clean branch may hold audit drafts; runtime behavior is not changed.

### Unknowns

- Which process currently writes each live projection.
- Whether board 180 runtime matches this Windows checkout.
- Current state of loopback-only APIs.
- Current Brier score, sample size and confidence interval.
- Provenance of the historical 27/27 verifier and Bayesian implementation.
- Whether a production-like restore succeeds at this commit.

### Reversible actions

- Read-only source inspection.
- Hermetic test execution using temporary state.
- Draft documentation on an isolated branch.
- The cognition-authority guard is reversible by reverting its single local commit.

### Owner-only actions

- D1 release, D7 execution and production eligibility.
- Owner signing and any private-material operation.
- Rotation of open credentials.
- Enabling paid providers, senders, actuators, services or hardware.

### Claims lacking sufficient evidence

- “320 tests are currently green.”
- “27/27 is independently reproducible at this commit.”
- “Current CRITICAL count is zero.”
- “77 of a 200-item checklist are complete.”
- “Current OCTOPUS Brier score is 0.80 or 0.99.”
- “All cognition is physically separated from execution authority.”
