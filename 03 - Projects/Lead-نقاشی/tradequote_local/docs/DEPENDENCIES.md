# Dependencies

Researched on pub.dev **2026-07-19** (details + likes/publish dates in
`docs/research/SOURCES.md`). Constraints are caret ranges; exact pins land
in `pubspec.lock` after the first `flutter pub get` on the build machine —
commit that file.

| Package | Constraint | Why | Risk notes |
|---|---|---|---|
| flutter_riverpod | ^3.3.1 | DI + reactive state (v3 Notifier API) | v3 breaking vs v2 — code targets v3 only |
| go_router | ^17.2.3 | routing, flutter.dev-maintained | — |
| drift / drift_dev | ^2.32 | typed SQLite, migrations | requires build_runner step |
| sqlite3, sqlite3_flutter_libs | ^2.4 / ^0.5.24 | bundled SQLite + raw integrity checks in restore | — |
| pdf / printing | ^3.12 / ^5.14.3 | PDF build + preview/print | Helvetica base-14 (no Persian glyphs yet — D-009) |
| share_plus | ^13.1.0 | share sheet w/ FileProvider | NEW API `SharePlus.instance.share(ShareParams)` — old static API is deprecated |
| flutter_email_sender | ^9.0.0 | Gmail-compose intent with attachment | 9.0.0 released day of research; fall back to ^8.0.0 if resolution fails (same API) |
| file_picker | ^11.0.2 | SAF save/open for backups + PDFs | — |
| path_provider / path | ^2.1.6 / ^1.9 | app dirs | — |
| intl | ^0.20.2 | dates/currency | number format uses default locale deliberately (no locale-data init) |
| uuid / crypto / archive | ^4.5 / ^3.0.7 / **^3.6.1** | ids, SHA-256, zip | archive pinned to v3 API on purpose; v4 redesigned the API — migrating is a phase-2 chore |
| shared_preferences | ^2.5.5 | non-critical prefs only | never business data |
| flutter_secure_storage | ^10.2.0 | AI API key only | Android EncryptedSharedPreferences/AES |
| http | ^1.2 | AI client | — |

Dev: flutter_test, drift_dev, build_runner, flutter_lints (>=5 <7).

## Vendor lock-in

Everything is open-source (MIT/BSD/Apache), local, and replaceable; the
document snapshot format is app-owned JSON and the backup is plain
zip+sqlite — readable by any tooling. No SaaS, no proprietary SDKs.

## Known API-freshness risks (for the next agent's first compile)

Written blind (no compiler in the authoring workspace) against the
researched versions; double-check on first `flutter analyze`:

1. `DropdownButtonFormField(initialValue: …)` — if the installed Flutter
   still wants `value:`, rename in customer_edit_screen.dart and
   record_payment_sheet.dart (2 call sites).
2. `CardThemeData` / `DialogThemeData` in theme.dart require Flutter ≥3.29
   (fine on 3.44).
3. share_plus ShareParams field names (`text`, `subject`, `files`).
4. flutter_email_sender 9 `Email(...)` constructor unchanged vs 8.
5. drift `text().unique()()` and `references(..., onDelete: KeyAction.cascade)`
   (both present since drift 2.x).
