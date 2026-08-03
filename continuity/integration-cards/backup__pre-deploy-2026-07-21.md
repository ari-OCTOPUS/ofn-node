# Integration Card — backup/pre-deploy-2026-07-21

id: branch:backup/pre-deploy-2026-07-21
path: git branch
type: branch
head: 28db463367f2a7dcb2e3ae4c5eab8128642404de
merge_base_with_master: a2183c3dfc20fea6fb8574078bd1737ebf08586d
ahead_of_master: 2
behind_master: 601
priority: ARCHIVE
lane: backup
risk: D0/D1 فقط index
decision: ARCHIVE_REFERENCE_ONLY
why: backup/state snapshot؛ ادغام عملیاتی ندارد
reversibility: high while unmerged; medium after staged; rollback via branch/head
external_effect: none during this card; must remain behind owner_gate/WAL if later ported

## Commit subjects
- 9b84c46 — backup: pre-deploy snapshot of live TRACKED deltas (17 state/log files + hermetic test_journal_bridge fix). Untracked runtime work intentionally left on disk (preserved by checkout). Restore point before deploy of canonical 0bd40d8.
- 28db463 — backup: residual cortex-state churn written by live cortex(8772) between backup commit and its shutdown

## Short stat
```text
18 files changed, 1561 insertions(+), 251 deletions(-)
```

## Risk buckets
### tcb-self (11)
- _ops/state/cortex-watchdog.json
- _ops/state/cortex/audit-matrix.json
- _ops/state/cortex/business-brain-latest.json
- _ops/state/cortex/cortex-state.json
- _ops/state/cortex/innervation-latest.json
- _ops/state/cortex/journal.jsonl
- _ops/state/cortex/outcomes.jsonl
- _ops/state/cortex/part-loops-latest.json
- _ops/state/cortex/self-model.json
- _ops/state/cortex/stress-latest.json
- _ops/state/cortex/upgrades-digest.json

### state (4)
- 07 - Knowledge/genome-system/ledger/ledger.jsonl
- _ops/state/events.jsonl
- _ops/state/saba-bridge.jsonl
- _ops/state/school-awareness.json

### docs (2)
- _memory/HEARTBEAT.md
- _ops/governor/governor-alerts.md

### tests (1)
- _ops/tests/test_journal_bridge.py

## Changed files
```text
M	07 - Knowledge/genome-system/ledger/ledger.jsonl
M	_memory/HEARTBEAT.md
M	_ops/governor/governor-alerts.md
M	_ops/state/cortex-watchdog.json
M	_ops/state/cortex/audit-matrix.json
M	_ops/state/cortex/business-brain-latest.json
M	_ops/state/cortex/cortex-state.json
M	_ops/state/cortex/innervation-latest.json
M	_ops/state/cortex/journal.jsonl
M	_ops/state/cortex/outcomes.jsonl
M	_ops/state/cortex/part-loops-latest.json
M	_ops/state/cortex/self-model.json
M	_ops/state/cortex/stress-latest.json
M	_ops/state/cortex/upgrades-digest.json
M	_ops/state/events.jsonl
M	_ops/state/saba-bridge.jsonl
M	_ops/state/school-awareness.json
M	_ops/tests/test_journal_bridge.py
```

## Proposed next action
- ARCHIVE_REFERENCE_ONLY
- No direct merge. If valuable: extract contract, run targeted tests, then cherry-pick/port minimal patch behind flag/owner gate.
