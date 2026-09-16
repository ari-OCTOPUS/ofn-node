# Risk register — evidence-bounded draft

Default claim envelope: `node_id=octopus-continuity-180`,
`asserted_ip=192.168.0.180`, `vantage=cursor-this-host-only`,
`scope=this_host_only`, `claim_type=risk_from_observation`,
evidence: HEAD `2a718aaa96235fcf5aa5219d25eba4a9b314eed5` and `receipts/`.

| ID | Risk | Probability | Impact | Detector | Containment / rollback | Owner | Status |
|---|---|---|---|---|---|---|---|
| R-01 | Narrow planner/world-model could acquire sibling authority through a future import. | Medium | Critical | Capability-aware AST guard plus controlled alias/dynamic-import fixture. | Guard now blocks executor, shell, sender, owner-key and approval capabilities; revert the single surgery commit to roll back. | Architecture owner | MITIGATED |
| R-02 | Root test runner can write runtime-like state and intentionally make a live provider request. | High | High | `_ops/tests/run_all.py:1405-1646`; `harness.py:145-151`. | Do not run globally until a network/state tripwire is universal; use safe subsets. | Test owner | CONTAINED |
| R-03 | Historical observatory claims cannot be reproduced from current HEAD. | High | High | `git ls-files` finds no runner, Bayesian strategy or live verifier. | Do not quote current Brier/27/27/CRITICAL values; recover exact provenance read-only. | Evidence owner | OPEN |
| R-04 | `observation.v1` is partial and accepts an invalid timestamp. | High | High | Offline gap probe. | Keep it disconnected from live decisions; specify migration before runtime wiring. | Sensor owner | OPEN |
| R-05 | Claimed stdlib YAML fallback raises `TypeError`; behavior silently becomes deny-all without PyYAML. | High | Medium | Forced `_hand_yaml` probe. | Current failure is fail-closed; proposed S8 adds a regression test and minimal parser fix. | Observatory owner | OPEN / SAFE-FAIL |
| R-06 | Primary working tree contains 136 unknown pre-existing changes. | High | High | `git status --porcelain=v1`. | All work isolated from HEAD; never reset/stash/delete/overwrite/incorporate. | Existing writers | CONTAINED |
| R-07 | Documentation contains mutually inconsistent “closed”, “not integrated” and current-state claims. | High | Medium | Compare `15-BAYESIAN-STRATEGY.md`, `17-SYNC-DECISIONS.md` and HEAD inventory. | Status-tag by commit/time; never promote prose over code/receipts. | Documentation owner | OPEN |
| R-08 | D1/D7 and owner signing are incomplete. | High | Critical | Tracked D1-D8 governance artifact and current truth. | Keep fail-closed; no private-material operation from this session. | Owner only | BLOCKED |
| R-09 | Recovery confidence is based on historical receipts, not a current restore drill. | Medium | High | No reproduced restore command/receipt in this audit. | Run only on disposable non-production fixtures in a later owner-gated task. | Operations owner | OPEN |
| R-10 | Node identity is asserted but not independently proven from Windows `eth0`. | Medium | Medium | No adapter named `eth0`; hostname is redacted and not promoted. | Keep scope `this_host_only`; wait for valid mesh/tunnel evidence rather than infer absence. | Mesh owner | UNKNOWN |
| R-11 | Optional D6/dual-veto checks in `goal_action_bridge.run_for_cycle` use `except: pass`, so a gate exception continues toward execution. | Medium | High | Source trace around the A2+ checks. | Current A2+ planner/executor blocks contain the issue; change to explicit BLOCKED before any A2 promotion. | Action owner | CONTAINED |
| R-12 | Existing LLM-call inventory is red: five callers are unclassified and the lab full-loop gateway directly uses a provider client without the shared fence. | High | High | `test_llm_call_inventory.py` returned 5/6; log hash recorded in the surgery test log. | Do not weaken the inventory or call providers; handle as a separate evidence-backed surgery. | Provider owner | OPEN / PREEXISTING |

No risk entry authorizes execution. A failed gate remains a gate, not a task to bypass it.
