# Requirements traceability — MVP scope (agreed 2026-07-19)

Status legend: ✅ implemented (awaiting first on-machine compile/test run) ·
🧪 implemented + machine-validated in this workspace · 📋 designed/documented
only (deliberate phase 2+) · ❌ out of scope (honest limitation).

| # | Requirement (brief §) | Implementation | Tests / evidence | Status |
|---|---|---|---|---|
| R1 | Offline, no server/account/subscription (§2,4) | whole architecture; only optional AI + user-chosen share targets touch network | PRIVACY.md table; code has no other network call | ✅ |
| R2 | Flutter + Drift/SQLite + Riverpod (§4) | pubspec, lib/data/db, providers.dart | static check PASS | ✅ |
| R3 | Money as integer cents; no floats (§8.1) | core/money.dart, schema INTEGER cents, qty milli | 🧪 Python 36/36 + gst/money tests | 🧪 |
| R4 | GST inc/exc/none w/ lawful rounding (§7.4) | core/gst.dart (s 9-90 total method, D-003) | 🧪 Python + test/gst_test.dart | 🧪 |
| R5 | ABN local checksum validation (§7.1) | core/abn.dart; forms validate + normalize | 🧪 Python + test/abn_test.dart | 🧪 |
| R6 | Onboarding + company settings (§7.1) | onboarding/, company_form.dart, settings repo | widget/company_form_test | ✅ |
| R7 | Customers CRUD/search/archive (§7.2) | customers feature + repo | repository_test §archiving | ✅ |
| R8 | Quick Quote senior flow ≤4 steps (§addendum 4) | quote_flow/quick_flow_screen.dart (3 steps after customer) | manual checklist 4–9 | ✅ |
| R9 | Quote statuses + expiry + duplicate + revision-by-duplicate (§7.4) | document_repository, detail screen | repository_test | ✅ |
| R10 | Auto-save drafts; survive Back/kill; continue card (§addendum 9) | draft row from start (D-013), PopScope save, Home card | manual 11–12 | ✅ |
| R11 | Transactional numbering, unique, never reused (§8.3) | _allocateNumber in txn + UNIQUE docNumber | repository_test §numbering | ✅ |
| R12 | Issued docs frozen; edits never rewrite history (§8.2) | snapshots + renderDataFor + updateDraft guard | repository_test §snapshot | ✅ |
| R13 | Quote→invoice conversion, quote preserved, no double (§7.5) | convertQuoteToInvoice txn | repository_test §conversion | ✅ |
| R14 | Invoice lifecycle + derived overdue (§7.6) | DocStatus + isOverdue derivation | repository_test, manual 18 | ✅ |
| R15 | Issued-invoice edit policy: void/duplicate only (§7.6) | voidInvoice, deleteDraft guards | repository_test §void | ✅ |
| R16 | Payments: partial/multiple/balance/overpay-block/reverse (§7.7) | payment_repository, record_payment_sheet | repository_test §payments | ✅ |
| R17 | Professional PDFs per ATO fields, multi-page (§7.9) | services/pdf/pdf_builder.dart | render_data_test; visual = manual 7 | ✅ |
| R18 | PDF share via share sheet; Telegram-first UX (§addendum 6) | share_service + share_screen | manual 8; TELEGRAM_SHARING.md | ✅ |
| R19 | "Prepare in Gmail" compose w/ attachment + fallback (§addendum 7) | prepareEmail + email-ask sheet | manual 10; GMAIL_COMPOSE.md | ✅ |
| R20 | No fake delivery claims; manual sent confirm (§20) | ShareOutcome model + What-happened sheet | invariant 6; share_events | ✅ |
| R21 | Message templates w/ clean placeholder removal (§addendum 6.3) | message_templates service + settings screen | unit coverage inside repo tests TODO on machine | ✅ |
| R22 | Home: NEW QUOTE/INVOICE, to-do, month totals, recent (§7.10) | home_screen + providers | manual 16,18 | ✅ |
| R23 | Search customers/documents (§7.10) | watchAll queries + list screens | manual | ✅ |
| R24 | Versioned checksummed backup via SAF (§7.12) | backup_service.createBackupBytes/saveViaPicker | manual 19; BACKUP_FORMAT.md | ✅ |
| R25 | Staged atomic restore + safety copy + rollback (§7.12) | validateAndStage/restoreStaged + DbHandle.swapWith | manual 20–21 | ✅ |
| R26 | Optional AI, off-default, review-before-apply, secure key (§Fugu) | ai_service + ai_settings + share screen | manual 27–28; FUGU_API_SETUP.md | ✅ |
| R27 | Senior UI: 60dp+ targets, large text, plain AU English, colour+text status (§addendum 3) | theme.dart, shared/widgets.dart, all copy | manual 22–25 | ✅ |
| R28 | Text-size setting default Large; light/dark (§addendum 15) | display settings + textScaleProvider | manual 23–24 | ✅ |
| R29 | Docs set: research/architecture/compliance/security/guides (§15) | docs/ tree, state files | this repo | ✅ |
| R30 | Release APK + checksum + install guide (§16) | BUILD_AND_RELEASE.md exact commands | ❗cannot run here: pub.dev/dl.google.com firewalled (PROJECT_STATE) | 📋 |
| R31 | Before/after photos (§7.3) | FUTURE_EXTENSIONS (phase 2 next) | — | 📋 |
| R32 | Signature capture (§7.8) | FUTURE_EXTENSIONS; PDF has manual acceptance block meanwhile | — | 📋 |
| R33 | Reports + CSV/XLSX exports (§7.11) | FUTURE_EXTENSIONS; month totals on Home only | — | 📋 |
| R34 | Projects as first-class entities (§7.3) | documents carry site/workType; table designed | — | 📋 |
| R35 | Gmail API true drafts (§addendum 7.3) | GMAIL_COMPOSE.md Level-2 research | — | 📋 |
| R36 | Voice/OCR/photo-AI features (§Fugu 3.2 D–F) | FUGU_API_SETUP future section | — | 📋 |
| R37 | DB encryption at rest | SECURITY.md honest status + SQLCipher path | — | 📋 |
| R38 | BAS/payroll/e-invoicing/bank feeds (§17) | explicitly out of product scope | COMPLIANCE_NOTES | ❌ |

No core MVP requirement is represented by a mock or TODO; every 📋 item is
a deliberate, documented deferral agreed in the 2026-07-19 scope decision.
