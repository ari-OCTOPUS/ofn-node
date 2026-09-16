# Document lifecycle

## Quote

```
draft ──issue/share──▶ sent ──▶ accepted ──convert──▶ (invoice created, quote preserved)
  │                    │  │
  │                    │  └──▶ declined
  │                    └────▶ expired (derived warning from expiryDate; user confirms)
  └──────────────▶ cancelled
```

- `draft`: fully editable. Auto-saved continuously and before any external
  app opens.
- Leaving `draft` (first share or manual "Mark as sent", or direct
  accept) **freezes a snapshot** (`DocumentRenderData` JSON). From then on
  content edits are blocked in UI and repository; to change the deal, the
  user duplicates the quote (new number, new draft).
- `accepted` records `acceptedAt`-equivalent via audit event; signature
  capture is a phase-2 feature and attaches here.
- Conversion (one big button): allowed from `accepted` (and from `sent` with
  an explicit extra confirmation). Creates the invoice in ONE transaction:
  new UUID + new invoice number, copies line items and totals from the
  quote's snapshot, links `sourceQuoteId`/`convertedInvoiceId`, writes audit
  event. If `convertedInvoiceId` is already set the button becomes "Open
  invoice" — double conversion is impossible without deliberately
  duplicating.

## Invoice

```
draft ──issue──▶ issued ──payment──▶ partiallyPaid ──▶ paid
  │                │  (derived: overdue, when dueDate past & balance > 0)
  └── cancelled    └───────────▶ void (recorded, number never reused)
```

- `draft`: editable; issuing freezes the snapshot (same rule as quotes).
- Payments only attach to non-draft, non-void invoices. Status roll-up runs
  in the payment transaction: balance 0 → `paid`; 0 < paid < total →
  `partiallyPaid`; overpayment is blocked in UI and repository (explicit
  error; policy D-007).
- `overdue` is **never stored** — derived at read time so it is always
  correct after date changes.
- Voiding requires typed confirmation, keeps the row + snapshot + audit
  trail, and never frees the number.

## Editing policy for issued documents (researched, D-005)

Ordinary editing of an issued invoice is blocked. The supported corrections:
1. **Void + reissue** (new number, audit-linked), or
2. **Duplicate as new draft** for a fresh deal.
This preserves the ATO expectation that records are protected from
alteration (RESEARCH_REPORT §4). Adjustment/credit notes are a documented
future feature, not in MVP.
