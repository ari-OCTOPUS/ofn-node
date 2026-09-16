# Integration Card — fix/neural-loop-close-310-214

id: branch:fix/neural-loop-close-310-214
path: git branch
type: branch
head: 9a50c474686bd5f8e262a4cd06c9684c56a3d12e
merge_base_with_master: 21042e678e209436285c7ff69cdca5f22e222af7
ahead_of_master: 1
behind_master: 362
priority: P3
lane: neural-research
risk: D3؛ بدون اتصال live
decision: SANDBOX_SHADOW_ONLY
why: neural→decision حتی shadow-first حساس است
reversibility: high while unmerged; medium after staged; rollback via branch/head
external_effect: none during this card; must remain behind owner_gate/WAL if later ported

## Commit subjects
- 9a50c47 — fix(neural): close the intelligence loop — #214 BCM self-wipe guard + #310 neural→decision (shadow-first)

## Short stat
```text
5 files changed, 418 insertions(+), 14 deletions(-)
```

## Risk buckets
### tcb-self (3)
- RFC-NEURAL-LOOP-CLOSE-310-214.md
- _ops/neural/bcm.py
- _ops/neural/neural_driver.py

### tests (1)
- _ops/tests/test_neural_loop_close.py

### other (1)
- _ops/wiring.py

## Changed files
```text
A	RFC-NEURAL-LOOP-CLOSE-310-214.md
M	_ops/neural/bcm.py
M	_ops/neural/neural_driver.py
A	_ops/tests/test_neural_loop_close.py
M	_ops/wiring.py
```

## Proposed next action
- SANDBOX_SHADOW_ONLY
- No direct merge. If valuable: extract contract, run targeted tests, then cherry-pick/port minimal patch behind flag/owner gate.
