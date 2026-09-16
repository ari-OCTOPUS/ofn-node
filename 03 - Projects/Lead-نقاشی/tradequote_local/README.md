# TradeQuote Local

Local-first quotes, invoices and payments for an Australian painting
business. **Offline. No accounts. No cloud. No subscriptions.**

Built senior-first for a Samsung Galaxy S23 FE: the whole common workflow is
*Home → NEW QUOTE → choose customer → describe → price → PDF → Send with
Telegram / Prepare in Gmail*, with big buttons, plain Australian English and
auto-saved drafts.

## What it does (v0.1.0 MVP)

- First-run business setup: name, ABN (validated locally with the official
  ABR checksum), GST registration, bank details, prefixes, terms
- Customers: one-field quick add, search, archive, per-customer history
- Quick Quote / Quick Invoice: one-price or item-by-item, GST engine
  (inclusive / exclusive / not-registered) with law-compliant rounding
- Professional PDFs: quote / tax invoice / invoice per ATO requirements,
  multi-page, printable, no internet needed
- Sharing: Telegram via the system share sheet, "Prepare in Gmail" compose
  with the PDF attached, save-PDF, honest "What happened?" confirmation —
  the app never claims delivery
- Quote → invoice conversion in one transaction; the quote is preserved
- Payments: partial/multiple, balance tracking, overdue detection,
  overpayment blocked, reversible with audit history
- Issued documents are frozen snapshots — later edits to customers or
  settings can never rewrite an issued invoice
- Complete backup (single portable file with checksums) and staged, atomic
  restore with an automatic safety copy
- Optional AI assistance (OFF by default): message improvement through the
  owner's own AI API, key in secure storage, review-before-apply

## What it deliberately does not do

No BAS, payroll, STP, bank feeds, e-invoicing or accounting advice. It is a
record-keeping and document tool. See `docs/AUSTRALIAN_COMPLIANCE_NOTES.md`.

## Repository map

```
lib/            app code (see docs/architecture/ARCHITECTURE.md)
test/           unit + database + widget tests
tool/           Python cross-validation of the financial algorithms
docs/           research, architecture, compliance, guides, testing
PROJECT_STATE.md            live build status (start here to resume work)
REQUIREMENTS_TRACEABILITY.md  requirement → code → test matrix
DECISIONS.md                decision log (D-001 …)
```

## Building the APK

This repository was authored in a cloud workspace where the Flutter
toolchain cannot run (documented in PROJECT_STATE.md). **Follow
`docs/BUILD_AND_RELEASE.md`** on a normal PC with Flutter installed —
it takes about six commands from unzip to installable APK.

## Honesty notes

- The money/GST/ABN algorithms were validated by real execution
  (`tool/validate_financial_logic.py`, 36/36 cases pass; output committed).
- The Dart code has not yet been compiled — expect the first
  `flutter analyze` to surface minor fixes; the build guide explains what
  to do.
- Share buttons open apps; they do not and cannot prove delivery. The UI
  and data model reflect that truthfully.
