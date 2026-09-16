---
type: evidence
status: active
created: 2026-08-18
updated: 2026-08-18
created_by: agent
tags: [octopus, custodian, contradiction, a2-001, stale-ledger]
sources:
  - "[[custodian-191-health-ledger-2026-08-18]]"
  - "[[../A2-001-QUARANTINED-PASS-2026-08-18]]"
  - "[[../canonical/decisions/a2-001-development-canonical-owner-approved-2026-08-18.json]]"
---

# Stale custodian A2-001 vs later owner-approved implementation

Do not collapse. Two timestamps, both true for their window.

| when | claim | evidence |
|---|---|---|
| 03:03–03:12 +10 | A2-001 `UNKNOWN_CANONICAL`; `mirror_verify.py` ABSENT; recommended: do not implement | custodian receipt `06-EVIDENCE/canonical/receipts/custodian-191-20260818T030354p10.json` outcome `BASELINE_RED` |
| ~03:17 +10 | Owner approved `development_canonical` only | `06-EVIDENCE/canonical/decisions/a2-001-development-canonical-owner-approved-2026-08-18.json` |
| ~03:20 +10 | `QUARANTINED_PASS`; file exists `octopus-bridge/octopus_bridge/mirror_verify.py`; stubs unchanged; not merged | `06-EVIDENCE/A2-001-QUARANTINED-PASS-2026-08-18.md` |

Live this follow-up: `F:\backup\octopus-bridge\octopus_bridge\mirror_verify.py` **present**. Custodian receipt was **not** rewritten (append-only). GITWRITE / `01a00d3d` / TCB / official `octopus_key` parts of that ledger are still current.
