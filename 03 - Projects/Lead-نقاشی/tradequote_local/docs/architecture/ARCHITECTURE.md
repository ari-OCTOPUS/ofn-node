# Architecture — TradeQuote Local

Pragmatic clean architecture, feature-first, no over-engineering. Two modes
of the UI (Simple default; advanced screens tucked into Settings), one code
path underneath.

## Layers

```
UI (features/*)  →  providers (riverpod)  →  repositories  →  drift DB
                                   ↘  services (pdf, sharing, backup, ai)
                                   ↘  core (money, gst, abn, dates, ids)
```

- **core/** — pure Dart, no Flutter imports where possible. Money/GST/ABN
  logic lives here and is unit-tested with the Python-validated tables.
- **data/db/** — drift schema (`database.dart`) + `AppDatabase`.
- **data/repositories/** — the only layer that touches drift. Repositories
  expose domain models and enforce invariants (transactional numbering,
  snapshot-on-issue, payment/status roll-up, conversion).
- **services/** — PDF builder (renders ONLY from `DocumentRenderData`),
  share service (Telegram/share-sheet/email/save), message templates,
  backup service, optional AI client.
- **features/** — screens + feature-local providers. Screens never touch
  drift directly.
- **app/** — theme (senior-friendly M3), router, root widget.

## Folder map

```
lib/
  main.dart
  app/{app.dart, router.dart, theme.dart}
  core/{money.dart, gst.dart, abn.dart, dates.dart, ids.dart}
  domain/{enums.dart, models.dart, render_data.dart}
  data/db/database.dart
  data/repositories/{settings_repository.dart, customer_repository.dart,
                     document_repository.dart, payment_repository.dart}
  services/{pdf/pdf_builder.dart, sharing/share_service.dart,
            templates/message_templates.dart, backup/backup_service.dart,
            ai/ai_service.dart}
  features/{onboarding, home, customers, quote_flow, documents, share,
            payments, settings}
  shared/widgets.dart
  providers.dart
```

## Key invariants

1. **Money is integer cents**; quantities integer milli; GST total-invoice
   method, half-up (ADR-001).
2. **Issued documents are frozen**: on leaving `draft`, a full
   `DocumentRenderData` JSON snapshot is stored; PDFs for issued documents
   render only from the snapshot. Editing customers/settings later never
   changes an issued document.
3. **Numbers are unique** (DB unique constraint) and allocated inside the
   same transaction that creates the document; never reused after
   void/cancel; gaps acceptable (D-004).
4. **Conversion never mutates the quote**: a new invoice row is created,
   linked both ways, in one transaction; double conversion is blocked.
5. **Invoice status roll-up** (paid/partiallyPaid) is recomputed inside the
   same transaction as any payment change; `overdue` is always derived at
   read time, never stored.
6. **No fake delivery**: sharing writes a `ShareEvent`
   (`prepared`/`shareSheetOpened`/`manuallyConfirmedSent`/`failedToOpen`/
   `cancelledOrUnknown`); `sent` status is set only by the user's explicit
   confirmation.
7. **Drafts auto-save** before any external app opens.
8. **Backups are archives with manifests + SHA-256 checksums**, restored via
   staging + safety backup + atomic swap (BACKUP_FORMAT.md).
9. **AI is optional and off by default**; core features never require
   network; AI output is always reviewed by the user before being applied.

## Mode handling

Simple Mode = default navigation (Home, Customers, Documents, Settings) with
progressive disclosure ("More options" panels). Advanced features (per-line
GST toggles, detailed items, void workflow) are reachable but never block the
four-step quick flow. There is ONE navigation system; "Advanced Mode" only
reveals extra entries (D-006).

## Future extension points (design only)

`SettingsRepository`/`DocumentRepository` are interfaces over drift that a
future sync adapter can decorate; every entity carries `id` (UUID),
`createdAt`, `updatedAt`, and archived/void markers instead of hard deletes,
so CRDT-ish sync or an export-to-accounting bridge (Xero/MYOB) can be added
without schema redesign. See FUTURE_EXTENSIONS.md.
