---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [ops, github, wire, recovery-design]
author: "custodian-191"
---

# GitHub / wire recovery — DESIGN ONLY

Precondition **P3 DIAGNOSTICS_VERIFIED** is not met. No option chosen. No credential changed. `GLOBAL_GITWRITE_FAILED` remains **OPEN**.

Observed on `.191`: `F:\backup` remotes are germline local-path only (`E:/germline/octopus.git`). Hourly writer target is `E:\germline\vault.git`. Known `--tags` reject of `pre-deploy-2026-07-25` is a **local-path REF_REJECTED**, not a GitHub auth class. Option R would not close that by itself.

## OPTION_R — restore/rotate GitHub credential

- Blast radius: Feet GitHub heartbeat and any remote still using that credential
- Rollback: previous secret version in the same secret manager; no history rewrite; no force-push
- Test: non-interactive redacted heartbeat probe after owner confirmation
- Owner confirmation: only after a scheduled P3 `github_wire` row is `AUTH_REQUIRED` or `AUTH_DENIED`

## OPTION_M — migrate Feet wire-read to germline

- Blast radius: command ingestion source; `WIRE_LAST`; duplicate consumption if both sources stay live
- Rollback: restore previous source pointer; keep GITWRITE flag OPEN
- Test: `WIRE_LAST` progression + germline source identity + no duplicate consume + no unexpected external action
- Owner confirmation: fresh record after P3 is `DIAGNOSTICS_VERIFIED`

Machine: `06-EVIDENCE/canonical/decisions/github-wire-recovery-design-2026-08-18.json`
