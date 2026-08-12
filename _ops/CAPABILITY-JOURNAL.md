# CAPABILITY-JOURNAL — Talk Discovery

Rule: Novel ∧ Repeatable ∧ Useful ∧ Policy-Compliant. **No auto-arm.**

Seeded 2026-08-11 from held-out fixtures + AI-core dark pulse (worktree scan).
Owner votes stay `pending` until explicit verdict.

| candidate | level | evidence | owner_vote | next |
|---|---|---|---|---|
| DC001 local-first quality gate | TESTED | discovery-held-out + model_router LOCAL_FIRST | pending | shadow session then owner arm CORTEX_LOCAL_FIRST |
| DC002 circuit breaker per-provider | TESTED | test_ti_breaker_chaos | pending | keep as defense; no money arm |
| DC003 action_sha256 outbound bind | TESTED | test_outbound_https TOCTOU | pending | leave gated; do not mass-arm outbound |
| DC004 collaborator content-free memory | TESTED | test_ti_collab_security | pending | keep armed only with COLLAB_MEMORY vote |
| DC005 context_bundle schema enforce | TESTED | test_ti_context_bundle_contract | pending | document in living card |
| OCTOPUS_COLLAB_USE_MODEL | STRUCTURAL | collab_model_adapter wired; flag dark until owner arm | pending | arm after Gate A + daily cap 30 |
| OCTOPUS_WIRE_COLLAB_DIGEST | STRUCTURAL | collab_digest build-only; scheduler needs vote | pending | weekly digest build, no send |
| CORTEX_LOCAL_FIRST | STRUCTURAL | dark AI-core pulse | pending | experiment in shadow |
| CORTEX_ROUTE_SCORER | STRUCTURAL | dark AI-core pulse | pending | ignore or shadow |
| CORTEX_SELF_MONITOR | STRUCTURAL | dark AI-core pulse | pending | propose for weekly review |

```text
discovery-journal + propose-only
!= auto-arm != money-live != outbound-send
```

Machine append log (optional): `state/capability-journal.jsonl` via `capability_journal.append_entry`.
Generate pulse: `python -m owner_console.discovery_pulse` from `_ops`.
