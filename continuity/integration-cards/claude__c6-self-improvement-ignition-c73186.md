# Integration Card — claude/c6-self-improvement-ignition-c73186

id: branch:claude/c6-self-improvement-ignition-c73186
path: git branch
type: branch
head: 1d6d13971c1c32ba66ba694b6293d8e1d4adba29
merge_base_with_master: 34535ec9faaf55324e0737cd5219c78c3cd0caa6
ahead_of_master: 3
behind_master: 449
priority: P3
lane: self-improvement-research
risk: D3 محدود؛ TCB/D6 sensitive
decision: SANDBOX_RESEARCH_ONLY
why: self-improvement/prediction gate به مغز و سیاست نزدیک است
reversibility: high while unmerged; medium after staged; rollback via branch/head
external_effect: none during this card; must remain behind owner_gate/WAL if later ported

## Commit subjects
- d91f0ae — feat(c6-cycle2): secondary indexes for memory get()/insert-dedupe — governed accepted (run2)
- 9a12577 — feat(c6-cycle2): final hardened index patch + 4-lens adversarial verify + honest disclosures
- 1d6d139 — feat(c6-cycle3): in-loop prediction pre-registration gate — governed accepted U=0.85

## Short stat
```text
28 files changed, 3342 insertions(+)
```

## Risk buckets
### other (14)
- _sandbox/evolution_v3/experiment2_v3.py
- _sandbox/evolution_v3/experiment_v3.py
- _sandbox/evolution_v3/governed_run_v3.py
- _sandbox/evolution_v3/governed_run_v3b.py
- _sandbox/evolution_v3/make_final_patch.py
- _sandbox/evolution_v3/memory_store_v3_final.py
- _sandbox/evolution_v3/memory_store_v3_indexed.py
- _sandbox/evolution_v3/profile_v3.py
- _sandbox/evolution_v3/proposed_v3.patch
- _sandbox/evolution_v3/proposed_v3_final.patch
- _sandbox/evolution_v4/experiment_c3.py
- _sandbox/evolution_v4/governed_run_c3.py
- _sandbox/evolution_v4/proposed_c3.patch
- _sandbox/evolution_v4/research_loop_v4.py

### state (12)
- _sandbox/evolution_v3/PREDICTION.json
- _sandbox/evolution_v3/PREDICTION2.json
- _sandbox/evolution_v3/governed_verdict_v3.json
- _sandbox/evolution_v3/governed_verdict_v3_run2.json
- _sandbox/evolution_v3/heldout_v3.json
- _sandbox/evolution_v3/result_exp2.json
- _sandbox/evolution_v3/result_v3.json
- _sandbox/evolution_v4/PREDICTION-C3.json
- _sandbox/evolution_v4/PREDICTION-C3b.json
- _sandbox/evolution_v4/governed_verdict_c3.json
- _sandbox/evolution_v4/heldout_c3.json
- _sandbox/evolution_v4/result_c3.json

### docs (2)
- _sandbox/evolution_v3/C6-CYCLE2-REPORT.md
- _sandbox/evolution_v4/C6-CYCLE3-REPORT.md

## Changed files
```text
A	_sandbox/evolution_v3/C6-CYCLE2-REPORT.md
A	_sandbox/evolution_v3/PREDICTION.json
A	_sandbox/evolution_v3/PREDICTION2.json
A	_sandbox/evolution_v3/experiment2_v3.py
A	_sandbox/evolution_v3/experiment_v3.py
A	_sandbox/evolution_v3/governed_run_v3.py
A	_sandbox/evolution_v3/governed_run_v3b.py
A	_sandbox/evolution_v3/governed_verdict_v3.json
A	_sandbox/evolution_v3/governed_verdict_v3_run2.json
A	_sandbox/evolution_v3/heldout_v3.json
A	_sandbox/evolution_v3/make_final_patch.py
A	_sandbox/evolution_v3/memory_store_v3_final.py
A	_sandbox/evolution_v3/memory_store_v3_indexed.py
A	_sandbox/evolution_v3/profile_v3.py
A	_sandbox/evolution_v3/proposed_v3.patch
A	_sandbox/evolution_v3/proposed_v3_final.patch
A	_sandbox/evolution_v3/result_exp2.json
A	_sandbox/evolution_v3/result_v3.json
A	_sandbox/evolution_v4/C6-CYCLE3-REPORT.md
A	_sandbox/evolution_v4/PREDICTION-C3.json
A	_sandbox/evolution_v4/PREDICTION-C3b.json
A	_sandbox/evolution_v4/experiment_c3.py
A	_sandbox/evolution_v4/governed_run_c3.py
A	_sandbox/evolution_v4/governed_verdict_c3.json
A	_sandbox/evolution_v4/heldout_c3.json
A	_sandbox/evolution_v4/proposed_c3.patch
A	_sandbox/evolution_v4/research_loop_v4.py
A	_sandbox/evolution_v4/result_c3.json
```

## Proposed next action
- SANDBOX_RESEARCH_ONLY
- No direct merge. If valuable: extract contract, run targeted tests, then cherry-pick/port minimal patch behind flag/owner gate.
