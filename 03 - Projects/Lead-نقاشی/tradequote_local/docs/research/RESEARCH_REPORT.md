# Research Report — TradeQuote Local

Date: 2026-07-19. Sources: see `SOURCES.md` (S1–S5). Classification of every
conclusion: **[LAW]** statutory, **[ATO]** ATO guidance, **[PRACTICE]** common
business practice, **[DESIGN]** product design recommendation.

## 1. Tax invoice requirements (S1, S5)

**[ATO]** A tax invoice must be provided within 28 days if a customer asks,
unless the sale is **$82.50 (inc GST) or less**.

**[ATO]** For sales **under $1,000**, a tax invoice must clearly show seven
details:

1. that the document is intended to be a tax invoice;
2. the seller's identity;
3. the seller's ABN;
4. the date the invoice was issued;
5. a brief description of the items sold, including quantity (if applicable)
   and price;
6. the GST amount payable — shown separately, **or**, if GST is exactly 1/11
   of the total price, the statement **"Total price includes GST"**;
7. the extent to which each sale is a taxable sale.

**[ATO]** For sales of **$1,000 or more**, the invoice must additionally show
the **buyer's identity or ABN**.

→ App consequences: the invoice PDF always renders seller identity + ABN +
issue date + line descriptions; renders "Tax Invoice" title only when the
business is GST-registered; always shows the customer identity block (safe
for the ≥$1,000 rule); shows either a separate GST line or the
"Total price includes GST" statement depending on GST mode. When the owner is
NOT GST-registered the document is titled "Invoice" and no GST is shown.

## 2. GST calculation and rounding (S3, S1)

**[LAW]** GST is 10% of the value of a taxable supply; the GST component of a
GST-inclusive price is 1/11. Section 9-90: amounts of GST are **rounded to the
nearest cent, with 0.5 cents rounded upwards**. For multiple supplies on one
invoice, both the *total invoice* method (sum unrounded, round once) and the
*taxable supply* method (round per line, then total) are permitted.
**[ATO]** "You and your customers don't need to use the same rounding rules."

→ App decision **[DESIGN]**: the app uses the **total invoice method**: line
totals are computed in integer cents, the GST-applicable subset is summed,
and GST is computed once on that sum with half-up rounding. This is the
simplest permitted method and reconciles exactly on the printed document.
Implemented with pure integer arithmetic (`(2a+b) ~/ 2b`), validated by 36
executed Python cases mirroring the Dart implementation
(`tool/validate_financial_logic.py`, output in
`docs/testing/python_validation_output.txt`).

## 3. ABN validation (S2)

**[ATO/ABR]** The ABN is 11 digits with a modulus-89 checksum: subtract 1
from the first digit, multiply the 11 digits by weights
(10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19), sum, and the total must be divisible
by 89. Worked example on the ABR page: 51 824 753 556.

→ App: ABN validated locally with this algorithm (no network lookup
required); stored normalized (11 digits), displayed as `NN NNN NNN NNN`.
Online ABR lookup is a future interface only.

## 4. Record keeping (S4)

**[ATO]** Most business records must be kept for **5 years** (from when the
record was prepared/obtained or the transaction completed, whichever is
later; longer in some cases). Digital records must be accessible, in English
or easily convertible, exportable to a standard format (e.g. CSV/Excel), and
protected from alteration; the business must be able to reconstruct original
data if the system changes.

→ App consequences: issued documents are **immutable snapshots** (editing a
customer or company profile never rewrites an issued invoice); voiding is a
recorded state change, not deletion; complete portable backups are a
first-class feature; CSV export is planned (phase 2) to satisfy the
convertibility expectation.

## 5. Numbering policy research

**[ATO]** ATO invoice-setup guidance requires invoices to be identifiable and
dated; no requirement for a gapless sequence was found in S1/S5.
**[PRACTICE]** Sequential prefixed numbers (INV-1001…) are standard.
**[DESIGN]** Decision: transactional allocation at document creation; numbers
are unique (DB constraint) and never reused after void/cancel; gaps from
abandoned drafts are acceptable and documented. See `DECISIONS.md` D-004.

## 6. Android sharing research (applies to Samsung One UI)

**[PRACTICE]** `share_plus` 13 shares a PDF (`application/pdf`) plus text via
the system share sheet using an internal FileProvider — no storage
permissions needed. Direct package-targeting of Telegram is not exposed by
share_plus 13; the reliable, standards-based flow is: big "Send with
Telegram" button → system share sheet opens → user taps Telegram. The app
never claims delivery; after returning it asks the user what happened.
Gmail: `flutter_email_sender` opens the default mail app's compose screen via
intent with recipients/subject/body/attachment. Opening compose is NOT
proof a draft was saved or sent — reflected in UI wording ("Prepare in
Gmail") and in `docs/integrations/GMAIL_COMPOSE.md`. A true Gmail API draft
is an optional future online feature (documented, not implemented).

## 7. Environment constraint recorded

The cloud build workspace firewalls `pub.dev`, `storage.googleapis.com` and
`dl.google.com`, so `flutter pub get` / APK builds cannot run here. All
compile-dependent steps are therefore executed on the owner's machine per
`docs/BUILD_AND_RELEASE.md`; money-critical logic was cross-validated by
execution in Python (see §2). This limitation is honest and recorded in
`PROJECT_STATE.md`.

## 8. Non-claims

This app is a record-keeping and document tool. It does **not** do BAS,
payroll, STP, superannuation, accounting advice, or lodge anything with the
ATO. This limitation appears in `docs/AUSTRALIAN_COMPLIANCE_NOTES.md` and the
user guide.
