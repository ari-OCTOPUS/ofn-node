# Integration Card — claude/vigilant-grothendieck-8e8250

id: branch:claude/vigilant-grothendieck-8e8250
path: git branch
type: branch
head: 2894eda26604684fe2e33a484507eecb6c473324
merge_base_with_master: 6bbb45159a557ac237ca9e813415f71add8c47e3
ahead_of_master: 1
behind_master: 405
priority: P1-small
lane: test-hardening
risk: D3 test-only
decision: SMALL_TEST_HOTFIX_CANDIDATE
why: هرمتیک‌کردن تست؛ احتمالاً کم‌ریسک و مفید
reversibility: high while unmerged; medium after staged; rollback via branch/head
external_effect: none during this card; must remain behind owner_gate/WAL if later ported

## Commit subjects
- 2894eda — fix(test): هرمتیک‌کردنِ test_master_halt — RESTART-REQUESTED دیگر از دیسکِ زنده خوانده نمی‌شود

## Short stat
```text
1 file changed, 11 insertions(+)
```

## Risk buckets
### tests (1)
- _ops/tests/test_master_halt.py

## Changed files
```text
M	_ops/tests/test_master_halt.py
```

## Proposed next action
- SMALL_TEST_HOTFIX_CANDIDATE
- No direct merge. If valuable: extract contract, run targeted tests, then cherry-pick/port minimal patch behind flag/owner gate.
