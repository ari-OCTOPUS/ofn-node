# Backup format v1

A backup is a single portable `.tqbackup.zip` file:

```
tradequote-backup-YYYYMMDD-HHMMSS.tqbackup.zip
├── manifest.json
├── database/tradequote.sqlite     (consistent copy via VACUUM INTO)
└── assets/…                       (logo now; photos/signatures in phase 2)
```

## manifest.json

```json
{
  "backupFormatVersion": 1,
  "appVersion": "0.1.0",
  "schemaVersion": 1,
  "createdAt": "2026-07-19T10:00:00Z",
  "files": [
    {"path": "database/tradequote.sqlite", "sha256": "…", "bytes": 123456}
  ]
}
```

## Creating a backup

1. `VACUUM INTO` a temp file — SQLite produces a consistent, checkpointed
   copy without closing the live DB.
2. Zip DB + assets + manifest (manifest lists SHA-256 of every file,
   computed with `package:crypto`).
3. Hand the bytes to the system **save dialog** (`FilePicker.saveFile`).
   The user may choose local storage, an SD card, or — if the Google Drive
   app is installed — Drive. No Google APIs, no credentials; Drive simply
   appears in Android's own picker and needs internet only at that moment.

## Restoring

1. User picks the archive (`FilePicker.pickFiles`).
2. Extract to a **staging** directory inside app support.
3. Validate: manifest present → format version supported → every SHA-256
   matches → sqlite file passes `PRAGMA integrity_check` →
   `PRAGMA user_version` ≤ current schema (older is fine, migrations run;
   newer app-than-backup is rejected with a clear message).
4. Show backup metadata (created date, app version) + a plain-language
   warning: "This will replace everything currently in the app."
5. **Safety backup** of current data is written automatically to app
   storage before anything is replaced.
6. Atomic swap: live DB closed → current file renamed `.pre-restore` →
   staged file moved in → reopen. Any failure rolls the `.pre-restore`
   file back and reports honestly.
7. UI reloads through the database holder provider; success screen states
   exactly what was restored.

## Failure modes covered

Corrupt zip, missing manifest, checksum mismatch, truncated sqlite, newer
schema than the app, path traversal (zip entries are sanitized — entries
containing `..` or absolute paths are rejected), out-of-space mid-restore
(staging keeps the live DB untouched until the final swap).
