# ADR-001 — Technology stack

Date: 2026-07-19 · Status: **Accepted**

## Context

Local-first, offline-first business app for an Australian painting company.
Android (Samsung S23 FE) first; Windows/macOS later. Senior, non-technical
primary user. No mandatory backend, no Firebase/Supabase, no telemetry.
Money-critical correctness (GST, tax invoices). Built initially in a cloud
workspace where the Flutter toolchain cannot execute (see RESEARCH_REPORT §7).

## Decision

| Concern | Choice | Why (evidence in docs/research/SOURCES.md) |
|---|---|---|
| Framework | Flutter 3.44 stable / Dart | Constraint; single codebase for Android now, desktop later |
| Database | SQLite via **drift 2.32** + drift_flutter | Typed schema, migrations, transactions, reactive queries; MIT; very active |
| State | **flutter_riverpod 3.3** | Compile-safe DI + reactive providers; Notifier API; avoids inherited-widget plumbing |
| Routing | **go_router 17** | flutter.dev-maintained, declarative, deep-link ready for desktop later |
| PDF | **pdf 3.12** + **printing 5.14** | Mature pair; widget-style layout, MultiPage repeating headers, in-app preview |
| Sharing | **share_plus 13** (`SharePlus.instance.share`) | System share sheet with FileProvider, no storage permissions |
| Email compose | **flutter_email_sender 9** with share-sheet fallback | Prefills recipient/subject/body/PDF via intent |
| Backup archive | **archive 4** + **crypto** (SHA-256) | Zip with manifest + checksums; no platform channel needed |
| Secure storage | **flutter_secure_storage 10** | AI API key only; never in the DB |
| Codegen | drift_dev + build_runner only | freezed/json_serializable REJECTED (D-002) — benefit does not justify extra generated surface, especially with no compile loop in the build workspace |

## Money representation

All persisted money = **integer cents (AUD)**. Quantities = **integer
thousandths** (`quantityMilli`). GST = total-invoice method with half-up
rounding per GST Act s 9-90, implemented in pure integer arithmetic and
cross-validated by execution (36/36 cases) in
`tool/validate_financial_logic.py`.

## Rejected alternatives

- **sqflite raw SQL**: no typed schema/migration story; drift is strictly better here.
- **Isar/Hive/ObjectBox**: not SQLite (constraint), weaker export/backup interoperability.
- **bloc**: more ceremony for a solo-maintained app; riverpod covers DI + reactivity.
- **Native Android (Kotlin)**: kills the Windows/macOS future requirement.
- **printing-only PDFs via HTML**: unreliable layout control for tax documents.
- **Firebase/Supabase/any cloud DB**: violates immutable constraints.

## Consequences

- `dart run build_runner build` is a required build step (drift codegen).
- Because the cloud workspace cannot compile, first build on the owner's
  machine is expected to surface minor compile fixes; the repo is structured
  so that money logic (already validated) is isolated from UI code.
- Platform folders are generated on the build machine with `flutter create .`
  (exact steps in docs/BUILD_AND_RELEASE.md) so Gradle files always match the
  installed Flutter version instead of being hand-written blind.
