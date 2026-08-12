---
type: ops-journal
status: active
created: 2026-08-11
updated: 2026-08-11
tags: [octopus, discovery, capability, propose-only]
aliases: [دفترچه قابلیت, Capability Journal]
---

# CAPABILITY-JOURNAL — Talk Discovery

Rule: Novel ∧ Repeatable ∧ Useful ∧ Policy-Compliant. **No auto-arm.**

پروتکل: [[_ops/DISCOVERY-PROTOCOL|DISCOVERY-PROTOCOL]] ·  
قرارداد: [[06 - Architecture Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT|Interaction Contract]] ·  
جلسه: [[00 - Inbox/2026-08-11 SESSION — Talk Discovery Implemented|SESSION]]

Seeded 2026-08-11 from held-out fixtures + AI-core dark pulse (worktree scan).
Owner votes stay `pending` until explicit verdict.

| candidate | level | evidence | owner_vote | next |
|---|---|---|---|---|
| DC001 local-first quality gate | TESTED | discovery-held-out + model_router LOCAL_FIRST | pending | shadow session then owner arm CORTEX_LOCAL_FIRST |
| DC002 circuit breaker per-provider | TESTED | test_ti_breaker_chaos | pending | keep as defense; no money arm |
| DC003 action_sha256 outbound bind | TESTED | test_outbound_https TOCTOU | pending | leave gated; do not mass-arm outbound |
| DC004 collaborator content-free memory | TESTED | test_ti_collab_security | pending | keep armed only with COLLAB_MEMORY vote |
| DC005 context_bundle schema enforce | TESTED | test_ti_context_bundle_contract | pending | document in living card |
| OCTOPUS_COLLAB_USE_MODEL | ARMED | live boot snapshot all limbs; cap=20 | owner | keep; watch daily cost |
| OCTOPUS_WIRE_COLLAB_DIGEST | ARMED | digest build armed; scheduler send still gated | pending | weekly digest review |
| CORTEX_LOCAL_FIRST | STRUCTURAL | dark AI-core pulse | pending | experiment in shadow |
| CORTEX_ROUTE_SCORER | STRUCTURAL | dark AI-core pulse | pending | ignore or shadow |
| CORTEX_SELF_MONITOR | STRUCTURAL | dark AI-core pulse | pending | propose for weekly review |

```text
discovery-journal + propose-only
!= auto-arm != money-live != outbound-send
```

Machine append log (optional): `state/capability-journal.jsonl` via `capability_journal.append_entry` (worktree).
Generate pulse: `python -m owner_console.discovery_pulse` from worktree `_ops`.
