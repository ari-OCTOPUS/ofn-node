# Data dictionary (schema v1)

Column-level detail lives beside the definitions in
`lib/data/db/database.dart`; the ERD with every column is in `ERD.md`.
This dictionary records the semantics that are not obvious from types.

Conventions: TEXT UUID primary keys (`core/ids.dart`); INTEGER epoch-ms
UTC timestamps (D-008); money INTEGER cents; quantities INTEGER
thousandths; enums stored by `name` (never reorder — `domain/enums.dart`).

| Table | Row class | Semantics that matter |
|---|---|---|
| company_settings | CompanySettingsRow | Single row id=1, seeded at create. `gstMode` is the DEFAULT for new documents; documents carry their own copy. `abn` stored normalized 11 digits. |
| number_sequences | NumberSequenceRow | id 'quote'/'invoice'; `nextNumber` seeds at 1001; read+increment inside the document-creation transaction (D-004). |
| customers | CustomerRow | `name` is the one required field (senior quick-add). `siteAddress` = default job address, copied to new documents. `archivedAt` soft-hides; never hard-deleted once documents exist. |
| documents | DocumentRow | Quotes + invoices unified via `docType`. `docNumber` UNIQUE. `status` per DOCUMENT_LIFECYCLE — 'overdue' is DERIVED, never stored. `customerNameCache` keeps lists working if the customer is archived/renamed. Totals denormalized, recomputed only through `updateDraft`. `sourceQuoteId`/`convertedInvoiceId` link conversions. `sentAt` is set ONLY by the user's "I sent it". |
| line_items | LineItemRow | Ordered by `position`; cascade-deleted with their document; `lineTotalCents` stored = halfUp(qtyMilli×unitPriceCents/1000). |
| document_snapshots | SnapshotRow | One per issued document; `snapshotJson` = full DocumentRenderData (schema field v1). Existence == "frozen"; PDFs for issued docs render only from here. |
| payments | PaymentRow | Only against issued/partiallyPaid invoices; `deletedAt` soft-reversal keeps audit truth; sum(non-deleted) drives status roll-up in the same transaction. |
| share_events | ShareEventRow | channel × outcome (never a 'delivered' value — invariant 6). |
| audit_events | AuditEventRow | Append-only trail: created/updated/issued/markedSent/accepted/declined/convertedToInvoice/createdFromQuote/voided/paymentRecorded/paymentReversed/archived… `detailsJson` free-form. |
| message_templates | MessageTemplateRow | ids quote/invoice/reminder; `{placeholder}` tokens per FUGU/messages docs; seeded with defaults. |
| app_meta | AppMetaRow | key/value: backupFormatVersion, lastBackupAt, … |

Indexes & FK notes: FKs enforced (`PRAGMA foreign_keys=ON` at open);
line_items/document_snapshots/share_events cascade with documents;
payments deliberately do NOT cascade (an invoice with payments can only
be voided, not deleted). `sourceQuoteId` is informational (no self-FK
constraint) — enforced in repository logic instead.
