# Risk register — evidence-bounded draft

Default claim envelope: `node_id=octopus-continuity-180`,
`asserted_ip=192.168.0.180`, `vantage=cursor-this-host-only`,
`scope=this_host_only`, `claim_type=risk_from_observation`,
evidence: HEAD `2a718aaa96235fcf5aa5219d25eba4a9b314eed5` and `receipts/`.

| ID | Risk | Probability | Impact | Detector | Containment / rollback | Owner | Status |
|---|---|---|---|---|---|---|---|
| R-01 | Narrow planner/world-model could acquire sibling authority through a future import. | Medium | Critical | Capability-aware AST guard plus controlled alias/dynamic-import fixture. | Guard now blocks executor, shell, sender, owner-key and approval capabilities; revert the single surgery commit to roll back. | Architecture owner | MITIGATED |
| R-02 | Root test runner could write runtime-like state and intentionally make a live provider request. | Low | High | Hermetic contract 7/7; live test expected-block; scoring 14/14 after nested-env isolation. | Default temp state/artifacts, loopback-only network and two-signal live admission. | Test owner | RESOLVED |
| R-03 | Historical observatory claims cannot be reproduced from current HEAD. | High | High | Exhaustive ref/path/object/runtime-name search with hashed narrative artifacts. | Status fixed to NOT_FOUND_IN_CURRENT_LINEAGE; no current Brier superiority claim. | Evidence owner | ACCEPTED_GAP |
| R-04 | USGS/HN `observation_v1.parse_body` remains a partial event parser, not the record contract. | Medium | Medium | Foundation tests 15/15 on `observation_record.py`. | Keep parser disconnected from live decisions; use the new record for future sensors. | Sensor owner | PARTIAL |
| R-05 | Claimed stdlib YAML fallback raises `TypeError`; behavior silently becomes deny-all without PyYAML. | High | Medium | Forced `_hand_yaml` probe. | Current failure is fail-closed; proposed S8 adds a regression test and minimal parser fix. | Observatory owner | OPEN / SAFE-FAIL |
| R-06 | Primary working tree contains 136 unknown pre-existing changes. | High | High | `git status --porcelain=v1`. | All work isolated from HEAD; never reset/stash/delete/overwrite/incorporate. | Existing writers | CONTAINED |
| R-07 | Documentation contains mutually inconsistent “closed”, “not integrated” and current-state claims. | High | Medium | Compare `15-BAYESIAN-STRATEGY.md`, `17-SYNC-DECISIONS.md` and HEAD inventory. | Status-tag by commit/time; never promote prose over code/receipts. | Documentation owner | OPEN |
| R-08 | D1/D7 and owner signing are incomplete. | High | Critical | Tracked D1-D8 governance artifact and current truth. | Keep fail-closed; no private-material operation from this session. | Owner only | BLOCKED |
| R-09 | Recovery confidence is based on historical receipts, not a current restore drill. | Medium | High | No reproduced restore command/receipt in this audit. | Run only on disposable non-production fixtures in a later owner-gated task. | Operations owner | OPEN |
| R-10 | Node identity is asserted but not independently proven from Windows `eth0`. | Medium | Medium | No adapter named `eth0`; hostname is redacted and not promoted. | Keep scope `this_host_only`; wait for valid mesh/tunnel evidence rather than infer absence. | Mesh owner | UNKNOWN |
| R-11 | Optional D6/dual-veto checks in `goal_action_bridge.run_for_cycle` use `except: pass`, so a gate exception continues toward execution. | Medium | High | Source trace around the A2+ checks. | Current A2+ planner/executor blocks contain the issue; change to explicit BLOCKED before any A2 promotion. | Action owner | CONTAINED |
| R-12 | LLM caller inventory was stale and the lab gateway callable lacked an explicit admission gate. | Low | High | Inventory now 8/8; gateway tests 11/11; production importers zero. | Default-deny lab gate plus AST reachability test. Revert Surgery 2 to roll back. | Provider owner | RESOLVED |
| R-13 | Local vault history and `ari-OCTOPUS/ofn-node` GitHub main are unrelated. | High | Critical | `git merge-base github/main HEAD` returned none; divergence 155/1835. | No push/PR; never force or graft histories. Publish only through an explicitly designed migration. | Repository owner | BLOCKED |
| R-14 | The complete hermetic default has not been executed. | Low | Medium | OWNER-09 receipt 2026-08-30T09:29:42Z. | 770/827 passed; 57 classified at run; scoring later repaired; no live suite. | Test owner | EXECUTED |
| R-15 | Hermetic child env does not stop tracked `_ops/state` and `06-EVIDENCE` writes. | High | High | git status after OWNER-09; 12 restored paths. | Restore after measurement; later close hardcoded writers. | Test owner | OPEN |

No risk entry authorizes execution. A failed gate remains a gate, not a task to bypass it.
