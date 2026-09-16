# Architecture Map — Painting Operating System

```mermaid
flowchart TB
  Sources[Owned forms / GBP / Instagram / Email / Tenders / B2B directories] --> Intake[Intake + Evidence + Consent]
  Intake --> CRM[Painting CRM: Leads + Accounts + Tenders + Vendor Apps]
  CRM --> Math[Explainable Math: S(l), Q(s), B2B, Tender, U(a,c), Trust]
  Math --> Policy[Compliance + Policy Gates]
  Policy --> Owner[Owner Panel + Telegram Cockpit]
  Owner --> Outbox[Durable Outbox / OwnerRelease]
  Outbox --> Connectors[Official connectors: read-only first, dry-run before live]
  Connectors --> Ledger[Append-only Ledger]
  Ledger --> Learning[Outcome + Trust + Channel calibration]
```

## Boundaries
- Partner lead app can manage painting leads only.
- Owner panel can read safe cross-tenant summaries but not secrets.
- Model calls stay behind scrub/advisor/worker paths; normal UI polling is local reads only.
- Connectors are inventory/read-only until token health, dry-run and owner release exist.

## Audit notes (2026-08-08)
- Kill switch now spans the whole flow: engage halts at the Policy gate, before
  Outbox is even considered. `gates.py:54-57`.
- Board metrics (sysmetrics) and alert notifier are new side-paths that do NOT
  enter the main flow — they read `/sys` and `/proc` locally, never touch
  customer data, and the alert's Telegram layer is behind an explicit flag.
- ⚠️ Port 8090 backup server is outside this architecture but inside the same
  network namespace — see REPO-BASELINE for the security note.
