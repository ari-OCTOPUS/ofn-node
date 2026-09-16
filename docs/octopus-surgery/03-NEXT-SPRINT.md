# Next sprint — atomic, evidence-bounded tasks

Default envelope: `node_id=octopus-continuity-180`,
`asserted_ip=192.168.0.180`, `vantage=cursor-this-host-only`,
`scope=this_host_only`, `claim_type=proposal`, evidence: HEAD
`2a718aaa96235fcf5aa5219d25eba4a9b314eed5`.

## S1 — selected first surgery

```yaml
id: S1
problem: "Planner/world-model isolation is real today but is not enforced against future imports of sibling shell, sender or provider modules."
evidence: "Read-only import/call audit found no dangerous handle in _ops/cognition, action_bridge/planner.py, epistemics/test_planner.py or shadow_homeostasis/world_model.py; dangerous sibling modules already exist."
files_allowed:
  - _ops/tests/architecture/cognition_authority_policy.yaml
  - _ops/tests/test_cognition_authority_denylist.py
  - _ops/tests/run_all.py
files_forbidden:
  - _ops/state/**
  - _ops/cognition/**
  - _ops/action_bridge/**
  - _ops/cortex/**
  - "**/*secret*"
  - "**/*key*"
change_budget: "3 files; 0 dependencies; AST-only architecture guard; no runtime behavior"
acceptance_test: "AST-walk the bounded planner/world-model set and fail on subprocess, coding_sandbox, Telegram sender, SMTP transport, provider client, payment or actuator imports/calls; include a synthetic violating fixture."
definition_of_done: "COMPLETE: 11/11 direct checks and 1/1 registered suite pass; the controlled fixture catches alias and dynamic-import violations."
rollback: "Revert the single local surgery commit."
stop_conditions: "Any runtime refactor, dependency addition, provider call, or scope beyond three surgery files."
owner_gate: "AUTHORIZED_PHASE_1"
outcome: "TEST_ONLY_GUARD; production_source_changes=0"
```

Priority inputs: information gain 5, risk reduction 5, reversibility 5, effort 1,
blast radius 1; relative score `125`. This is the highest safe bounded correction.

## S2

```yaml
id: S2
problem: "Two partial observation models disagree and observation.v1 lacks required provenance, uncertainty, calibration and simulation fields."
evidence: "_ops/observatory/observation_v1.py; _ops/shadow_homeostasis/observation.py; gap probe."
files_allowed: [docs/octopus-surgery/04-SELF-MODEL-SPEC.md, docs/observation-v1-spec.md]
files_forbidden: [_ops/observatory/**, _ops/shadow_homeostasis/**]
change_budget: "specification only"
acceptance_test: "Schema examples validate offline; simulated and physical examples cannot be confused."
definition_of_done: "One versioned contract and migration proposal, no runtime code."
rollback: "Remove the new draft documents."
stop_conditions: "Any runtime wiring or sensor/network action."
owner_gate: none
```

## S3

```yaml
id: S3
problem: "Cortex cognition directly owns provider transport and credential access."
evidence: "_ops/cortex/model_router.py::_ask_paid -> debate/client.py::MultiProviderClient.complete."
files_allowed: []
files_forbidden: ["all runtime files until design is split into <=5-file slices"]
change_budget: "design decomposition only"
acceptance_test: "Architecture test proves cognition imports a read-only port, never provider/client/env credential code."
definition_of_done: "A reviewed multi-slice migration plan with fail-closed parity."
rollback: "Per-slice revert."
stop_conditions: "More than five files, paid call, credential read, or behavior expansion."
owner_gate: required
```

## S4

```yaml
id: S4
problem: "Historical run_observatory.py, Bayesian predictor and 27/27 verifier are referenced but absent from HEAD."
evidence: "07 - Knowledge/OCTOPUS-TRUTH-2026-08-15/* versus git ls-files at HEAD."
files_allowed: ["read-only Git objects and non-sensitive evidence paths"]
files_forbidden: ["bare germline writes", "secret paths"]
change_budget: "discovery only"
acceptance_test: "Recover exact commit/path/hash or classify each artifact NOT_FOUND with searched refs."
definition_of_done: "Reproducible provenance chain, no reconstructed code from prose."
rollback: "Not applicable; read-only."
stop_conditions: "Requires network, secret access or editing the bare repository."
owner_gate: none
```

## S5

```yaml
id: S5
problem: "The root runner is non-hermetic: it writes runtime-like manifests/capability markers and intentionally includes a live routing test."
evidence: "_ops/tests/run_all.py:1405-1646 and harness.py:145-151."
files_allowed: ["test harness and architecture-test files in a later approved slice"]
files_forbidden: [_ops/state/**]
change_budget: "maximum 4 files"
acceptance_test: "Full suite runs with network blocked and temporary state; any escape fails closed."
definition_of_done: "One official hermetic command with full log hash."
rollback: "Revert harness slice."
stop_conditions: "Any live provider request or write outside temp."
owner_gate: required
```

## S6

```yaml
id: S6
problem: "Current independent observatory verification and Brier reproduction are absent."
evidence: "No verify_live_store.py, run_observatory.py or bayesian_strategy.py in HEAD."
files_allowed: ["fixture-only verifier package after S4 provenance"]
files_forbidden: ["runtime stores", "network adapters"]
change_budget: "one verifier vertical slice"
acceptance_test: "Mutation test catches copied baseline, hash tamper and future-data leakage."
definition_of_done: "Independent oracle, sample size, CI and receipt."
rollback: "Revert verifier slice."
stop_conditions: "Verifier imports implementation output or needs live writes."
owner_gate: required
```

## S7

```yaml
id: S7
problem: "No restore drill was reproduced at this commit."
evidence: "Only historical runbooks/receipts were found."
files_allowed: ["non-production fixture state and receipt paths"]
files_forbidden: ["production DB", "services", "hardware"]
change_budget: "one disposable fixture"
acceptance_test: "Backup, corrupt fixture, restore, verify independent hash, rollback."
definition_of_done: "Restore receipt with command and hash."
rollback: "Discard disposable fixture only."
stop_conditions: "Touches live state or needs service control."
owner_gate: required
```

## S8

```yaml
id: S8
problem: "_ops/observatory/allowlist_loader.py claims a stdlib-only YAML fallback, but _hand_yaml raises TypeError on the tracked allowlist."
evidence: "gap probe c9e9b14a...; the PyYAML-backed smoke path passes and does not exercise fallback."
files_allowed: [_ops/observatory/allowlist_loader.py, _ops/tests/test_observatory_allowlist_fallback.py, _ops/tests/run_all.py]
files_forbidden: [_ops/state/**, architecture/observatory-allowlist.yaml, "**/*secret*", "**/*key*"]
change_budget: "3 files; 0 dependencies; parser-only"
acceptance_test: "Force stdlib parsing; recover all seven approved rows and rejected rows; malformed input remains deny-all."
definition_of_done: "Failing test first, minimal fix, targeted baseline green, no network."
rollback: "Revert one local commit."
stop_conditions: "Schema reinterpretation, dependency addition, network call, or runtime wiring."
owner_gate: required
```
