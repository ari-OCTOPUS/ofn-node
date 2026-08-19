---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [sensorium, deviation, automation, read-only]
author: "custodian-191"
---

# DEV-182-0001 — Cursor automation store unread

Automation id `automation-25cfa808-6251-4bb2-be54-98a8264c45a1` was **not** read from the Cursor Automations / harness store in this session. This review is **not** `PASS_READONLY`.

## Verdict

**INSUFFICIENT_EVIDENCE** for store fields. Automation was not cancelled, updated, or created here.

| field | from store |
|---|---|
| enabled | UNKNOWN |
| lifecycle | UNKNOWN |
| run count | UNKNOWN |
| created / updated | UNKNOWN |
| prompt / task scope | UNKNOWN |
| scheduled run occurred | UNKNOWN |
| output in-band only | UNKNOWN |

## Mutation scope

Not observed on `.182` systemd/cron or `.191` Task Scheduler for this id. If the id exists, it would be a Cursor cloud Automations object, not an OS timer on Sensorium. That object was not fetched.

## Owner options (not executed)

`KEEP_UNTIL_EXPIRY` or `CANCEL`

Machine receipt: `06-EVIDENCE/canonical/receipts/DEV-182-0001-review-2026-08-18.json`
