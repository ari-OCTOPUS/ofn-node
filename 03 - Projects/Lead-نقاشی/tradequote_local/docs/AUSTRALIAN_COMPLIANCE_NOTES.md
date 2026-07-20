# Australian Compliance Notes

Sources with access dates: `docs/research/SOURCES.md` (S1–S5).
Classification: [LAW] statute · [ATO] ATO guidance · [DESIGN] app decision.

## What this app is — and is not

TradeQuote Local is a **record-keeping and document tool**. It prepares
quotes, invoices/tax invoices, payment records, and portable backups.
It does **not** prepare or lodge BAS, do payroll/STP/superannuation, give
tax advice, or replace a registered tax agent. That limitation is shown in
Settings → About and in the user guide.

## Tax invoices (S1, S5)

- [ATO] Provide a tax invoice within 28 days if asked, unless the sale is
  $82.50 (inc GST) or less.
- [ATO] Under $1,000, seven details are required (intent, seller identity,
  ABN, date, description with quantity and price, GST amount or "Total
  price includes GST", extent taxable). **$1,000 or more additionally
  requires the buyer's identity or ABN.**
- [DESIGN] The PDF always prints supplier identity + formatted ABN + date +
  description; the customer identity block always prints (safe for the
  ≥$1,000 rule); GST is shown either as a separate line or as
  "Total price includes GST of $X" exactly per mode.
- [DESIGN] Title logic: "TAX INVOICE" only when GST-registered; otherwise
  "INVOICE" with "No GST has been charged."; quotes are titled "QUOTE".
- [DESIGN] The UI nudges (helper text on the customer ABN field) but does
  not block issuing a ≥$1,000 invoice without a customer ABN, since buyer
  *identity* (name/address) satisfies the requirement.

## GST arithmetic (S3)

- [LAW] GST = 10%; the GST in a GST-inclusive price is 1/11. s 9-90:
  round GST to the nearest cent, 0.5 up; for multiple supplies, total-then-
  round is permitted.
- [DESIGN] Total-invoice method with pure integer arithmetic (D-003),
  validated by execution (tool/validate_financial_logic.py, 36/36) and
  mirrored in test/gst_test.dart.

## ABN (S2)

- [ATO/ABR] 11 digits, modulus-89 checksum (weights 10,1,3,5,7,9,11,13,15,
  17,19 after subtracting 1 from the first digit).
- [DESIGN] Validated locally on entry; stored normalized; displayed
  `NN NNN NNN NNN`. No network lookup required or performed.

## Records (S4)

- [ATO] Keep most records 5 years; digital records must be accessible,
  English, exportable, protected from alteration, reconstructable.
- [DESIGN] Issued documents freeze immutable snapshots; voiding is a
  recorded state, not deletion; numbers never reused; audit events kept;
  complete portable backups; CSV export planned phase 2 (traceability).

## Numbering

- [ATO] Invoices must be identifiable and dated; no gapless-sequence
  requirement found in S1/S5. [DESIGN] Sequential prefixed numbers,
  transactional allocation, unique constraint, gaps from deleted drafts
  are possible and acceptable (D-004, D-013).

## Not legal advice

Nothing here is legal or tax advice. Statutory requirements were read from
the cited primary sources on 2026-07-19 and can change — re-verify before
relying on them for anything beyond this app's scope.
