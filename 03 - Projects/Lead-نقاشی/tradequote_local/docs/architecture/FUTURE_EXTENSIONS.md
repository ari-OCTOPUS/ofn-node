# Future extensions — what fits where

The MVP schema/architecture was shaped to leave doors open without
building speculative machinery (immutable-constraints §17 of the brief).

## Fits behind current interfaces (no schema change)

- **Photos & signatures (phase 2 priority)**: new tables
  (project_photos, signatures) + image_picker/signature packages; PDFs
  already render from RenderData — add optional signature block v2.
- **Reports & CSV/PDF exports**: read-only over existing tables; CSV
  escaping util + tests (listed in traceability as planned).
- **Reminder scheduling UI**: share flow already supports kind=reminder.
- **Direct Telegram intent** (android_intent_plus + `<queries>`), keeping
  the share-sheet fallback (TELEGRAM_SHARING.md).
- **App lock** (local_auth) behind Settings.
- **More AI features**: the one-file protocol adapter (FUGU_API_SETUP.md)
  and review-before-apply pattern generalise.

## Needs migrations (designed for, not built)

- Projects/jobs as first-class entities (documents already carry
  siteAddress/workType; a projects table + FK slots in cleanly).
- Adjustment/credit notes: new docType + link columns; numbering table
  already generic by sequence id.
- Deposits on quotes; multiple invoices per quote (deliberate workflow).
- Per-year number patterns (sequences table gains pattern column).
- SQLCipher at-rest encryption (sqlcipher_flutter_libs swap in
  AppDatabase.open + key management — the hard part is UX for key
  recovery; see SECURITY.md).

## Needs professional review before building

- BAS figures/GST reports presented as lodgeable numbers (accountant).
- Payroll/STP/superannuation (out of product scope — refer out).
- APP/privacy posture if the tool is ever multi-tenant.

## Needs a backend (all deliberately absent today)

- Multi-device sync + conflict resolution (every entity already has
  UUID/createdAt/updatedAt/soft-delete markers so a sync adapter can
  decorate repositories; snapshots make document history mergeable).
- Xero/MYOB/QuickBooks bridges (export adapters over repositories),
  Stripe/Square payments, automated email/SMS, Peppol eInvoicing
  (the RenderData model keeps the fields Peppol needs).

## Can remain entirely local forever

Everything the MVP does today, plus reports/exports, photos, signatures,
OCR/voice via on-device models, desktop builds (Windows/macOS —
BUILD_AND_RELEASE §7).
