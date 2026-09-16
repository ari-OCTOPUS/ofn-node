# Security

Threats + mitigations detail: `docs/THREAT_MODEL.md`. Privacy: `docs/PRIVACY.md`.

## Posture

- **No network for core features.** The only outbound calls are (a) the
  optional AI feature the user explicitly configures and taps, and (b)
  whatever the user's own share targets (Telegram/Gmail) do after handoff.
- **No telemetry, no crash reporting, no ads, no remote fonts/images.**
- **Storage**: SQLite + assets in the app-private support directory
  (Android app sandbox). Share PDFs go to an app-private cache and are
  cleaned after 7 days.
- **Secrets**: the AI API key lives only in flutter_secure_storage
  (EncryptedSharedPreferences/AES on Android) — never in the DB, prefs,
  logs or Git. No secrets are committed to this repo (.gitignore covers
  keystores/key.properties/.env).
- **Backups**: zip with per-file SHA-256 manifest. Restore validates
  format → checksums → `PRAGMA integrity_check` → schema compatibility,
  rejects `..`/absolute zip paths (path traversal), stages in a private
  dir, auto-creates a safety backup, then swaps atomically with rollback.
- **Logs/errors**: user-facing errors are plain-language AppExceptions;
  no customer data is interpolated into logs; release builds show a
  friendly ErrorWidget, not stack traces.
- **Tests** use fabricated data only (the ABR's own published example ABN).

## Database encryption — honest status

The database is NOT encrypted at rest in v0.1.0. It relies on the Android
app sandbox + device lock/encryption (Android full-disk/file-based
encryption on the S23 FE). We deliberately do not advertise encryption we
did not implement. Options researched for phase 2: SQLCipher via
`sqlcipher_flutter_libs` (drift-compatible; key management becomes the
hard part) — see FUTURE_EXTENSIONS.md. Recommendation to the owner today:
keep a screen lock on the phone; treat backup files like paper records.

## App lock

Not in v0.1.0 (reliability first for a senior user). If wanted later:
biometric gate via local_auth behind a Settings toggle; must never lock
the user out of their data (documented recovery = restore backup).

## Update discipline

Before each release: `flutter pub outdated`, review changelogs of
security-adjacent packages (secure_storage, share_plus, file_picker),
rerun the test suite and the manual checklist.
