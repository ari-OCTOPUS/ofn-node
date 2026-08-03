# Decision Record — Approval Disposition (2026-08-03)

**Decision ID:** DR-APPROVAL-DISPOSITION-20260803
**Date:** 2026-08-03
**Decided by:** owner (session)
**Baseline:** post-cleanup-baseline-2026-08-03

## Context

۳ approval زنده پس از expire-hygiene باقی مانده بودند. کارت تصمیم در
`APPROVAL-DECISION-CARD-2026-08-03.md` ساخته شد.

## Decisions

| approval | decision | reason |
|---|---|---|
| `sgc-mission-mis-1c23c01e91e00a8f30e9` (A) | **HOLD** | اولویتِ فعلی معماری است، نه درآمد |
| `sgc-mission-mis-c1a32c8b4dee05705752` (B) | **REJECT** | duplicate/superseded of A (same action/target/intent) |
| `M-20260803-204308-3e466908` (C) | **HOLD** | risk=high + dry_run=null — ناامن بدون dry-run |

## Applied

- B به status=rejected منتقل شد با reason و timestamp
- A و C در pending ماندند (HOLD)
- هیچ mission اجرا نشد
- هیچ claim/outbound/customer/money اتفاق نیفتاد

## Backup

- قبل: `continuity/backups/approvals.before-decision-20260803T112045Z.json`
- بعد: state فعلی در `_octopus/state/approvals.json`

## Result

```text
pending: 2 (A=HOLD, C=HOLD)
rejected: 104 (103 expired + 1 duplicate B)
approved: 28
```
