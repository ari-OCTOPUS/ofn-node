# Integration Card — phase-d

id: branch:phase-d
path: git branch
type: branch
head: 6d4355d188937c60c8040103fc320aadaae0b9c7
merge_base_with_master: 05d2b5a1363299497f20af86e6a46c8b1c647f7a
ahead_of_master: 8
behind_master: 512
priority: P1
lane: lead-outbound-safety
risk: D2→D4 staged، بدون outbound واقعی
decision: PORT_SAFETY_COMPONENTS_BEHIND_FLAGS
why: به lead/outbound نزدیک است؛ consent/release separation مهم اما اثر بیرونی حساس
reversibility: high while unmerged; medium after staged; rollback via branch/head
external_effect: none during this card; must remain behind owner_gate/WAL if later ported

## Commit subjects
- 4e9d37a — feat(lead): D1 — wire verdict button to lead_effect_gate (flag-off, NOT_ARMED)
- 75785f3 — feat(lead): D2a — consent_store + consent_gate core safety (flag-off, fail-closed)
- e5f3f3c — feat(lead): D3 — funnel_store + fold + metrics (append-only, replay-safe, flag-free)
- 93a03a7 — feat(lead): D4 — speed_to_lead first-response draft (flag-off, fallback-safe, no send)
- 9fee97f — feat(lead): D5 — M3 producer migration (harvest/email → submit_candidate, flag-off)
- 779aa7e — feat(lead): D6 — release/send separation (real staleness, NOT_ARMED still)
- 49468c1 — feat(lead): D7 — telegram-owner notification transport (NOT customer, R2 preserved)
- 6d4355d — docs(lead): PHASE-D-COMPLETION-2026-07-21 + HANDOFF note (94/94, STOP intact)

## Short stat
```text
20 files changed, 3056 insertions(+), 7 deletions(-)
```

## Risk buckets
### outbound (8)
- "03 - Projects/Lead-\331\206\331\202\330\247\330\264\333\214/Trust-Engine-v1.1/PHASE-D-COMPLETION-2026-07-21.md"
- _ops/legs/consent_gate.py
- _ops/legs/consent_store.py
- _ops/legs/email_inbound.py
- _ops/legs/lead_effect_gate.py
- _ops/legs/outbound_worker.py
- _ops/legs/speed_to_lead.py
- _ops/outcomes/funnel_store.py

### tests (8)
- _ops/tests/test_consent_gate.py
- _ops/tests/test_funnel_store.py
- _ops/tests/test_lead_effect_gate.py
- _ops/tests/test_lead_verdict_wiring.py
- _ops/tests/test_outbound_owner_transport.py
- _ops/tests/test_producer_migration.py
- _ops/tests/test_release_send_separation.py
- _ops/tests/test_speed_to_lead.py

### other (3)
- _ops/legs/harvest_austender.py
- _ops/live_loop.py
- _ops/wiring.py

### docs (1)
- 01 - Dashboard/HANDOFF.md

## Changed files
```text
M	01 - Dashboard/HANDOFF.md
A	"03 - Projects/Lead-\331\206\331\202\330\247\330\264\333\214/Trust-Engine-v1.1/PHASE-D-COMPLETION-2026-07-21.md"
A	_ops/legs/consent_gate.py
A	_ops/legs/consent_store.py
M	_ops/legs/email_inbound.py
M	_ops/legs/harvest_austender.py
M	_ops/legs/lead_effect_gate.py
M	_ops/legs/outbound_worker.py
A	_ops/legs/speed_to_lead.py
M	_ops/live_loop.py
A	_ops/outcomes/funnel_store.py
A	_ops/tests/test_consent_gate.py
A	_ops/tests/test_funnel_store.py
M	_ops/tests/test_lead_effect_gate.py
A	_ops/tests/test_lead_verdict_wiring.py
A	_ops/tests/test_outbound_owner_transport.py
A	_ops/tests/test_producer_migration.py
A	_ops/tests/test_release_send_separation.py
A	_ops/tests/test_speed_to_lead.py
M	_ops/wiring.py
```

## Proposed next action
- PORT_SAFETY_COMPONENTS_BEHIND_FLAGS
- No direct merge. If valuable: extract contract, run targeted tests, then cherry-pick/port minimal patch behind flag/owner gate.
