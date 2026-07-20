# Research Sources

All sources accessed **2026-07-19** from the cloud build workspace.

## Australian compliance (authoritative)

| # | Title | Publisher | URL |
|---|-------|-----------|-----|
| S1 | Tax invoices | Australian Taxation Office | https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/tax-invoices |
| S2 | Format of the ABN | Australian Business Register (ABN Lookup) | https://abr.business.gov.au/Help/AbnFormat |
| S3 | A New Tax System (GST) Act 1999 s 9-90 — Rounding of amounts of GST | AustLII (Cth legislation) | https://classic.austlii.edu.au/au/legis/cth/consol_act/antsasta1999402/s9.90.html |
| S4 | Overview of record-keeping rules for business | Australian Taxation Office | https://www.ato.gov.au/businesses-and-organisations/preparing-lodging-and-paying/record-keeping-for-business/overview-of-record-keeping-rules-for-business |
| S5 | Setting up your business invoices | Australian Taxation Office | https://www.ato.gov.au/businesses-and-organisations/preparing-lodging-and-paying/record-keeping-for-business/setting-up-and-managing-records/setting-up-your-business-invoices |

## Package health (pub.dev, checked 2026-07-19)

| Package | Version | Published | License | Notes |
|---------|---------|-----------|---------|-------|
| drift | 2.32.1 | ~2026-06 | MIT | 2.38k likes; Android/iOS/desktop/web |
| drift_flutter | 0.3.0 | 2026-02-28 | MIT | official drift helper for opening DBs |
| flutter_riverpod | 3.3.1 | 2026-03-09 | MIT | v3 API (Notifier-based) |
| go_router | 17.2.3 | 2026-05-01 | BSD-3 | flutter.dev verified |
| pdf | 3.12.0 | ~2026-06 | Apache-2.0 | 3k likes |
| printing | 5.14.3 | 2026-03-15 | Apache-2.0 | preview + share, same author as pdf |
| share_plus | 13.1.0 | 2026-04-21 | BSD-3 | new `SharePlus.instance.share(ShareParams)` API; old static methods deprecated |
| file_picker | 11.0.2 | ~2026-05 | MIT | `saveFile` supported on Android (SAF) |
| flutter_email_sender | 9.0.0 | 2026-07-19 | Apache-2.0 | intent-based compose w/ attachments; 9.0.0 released same day as research — pubspec notes ^8 fallback |
| flutter_secure_storage | 10.2.0 | ~2026-07 | BSD-3 | Android EncryptedSharedPreferences/AES-GCM |
| path_provider | 2.1.6 | 2026-06-15 | BSD-3 | flutter.dev verified |
| shared_preferences | 2.5.5 | 2026-03-25 | BSD-3 | flutter.dev verified |
| intl | 0.20.2 | 2025-01-24 | BSD-3 | dart.dev verified |
| uuid | 4.5.3 | ~2026-05 | MIT | RFC4122 |
| crypto | 3.0.7 | 2025-11-04 | BSD-3 | dart.dev verified |
| archive | 4.0.9 | 2026-02-17 | MIT | zip with file I/O redesign in v4 |

## Toolchain

| Item | Value | Source |
|------|-------|--------|
| Flutter stable | 3.44.0 (last three stable: 3.44.0, 3.41.0, 3.38.0) | https://docs.flutter.dev/release/release-notes |

## Open-source product references (architecture lessons only, no code copied)

Studied at design level from public documentation/repos in prior research context:
Invoice Ninja (immutable invoice snapshots, number sequences), Crater
(quote→invoice conversion model), Frappe Books (local-first accounting
boundaries). No source code or UI assets were copied into this project.
