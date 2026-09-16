# Backup & restore — user-level guide

(Technical format: `docs/architecture/BACKUP_FORMAT.md`.)

## Backing up

Settings → **My data** → **BACK UP MY DATA**. The app makes ONE file
(`tradequote-backup-YYYYMMDD-HHMMSS.tqbackup.zip`) containing every
customer, quote, invoice, payment, template and setting, with built-in
integrity checksums. Android's save dialog then lets you choose where it
goes:

- your phone's storage or SD card — fully offline;
- **Google Drive**, only if the Drive app is installed and you tap it —
  internet is used just for that upload, by Drive, not by this app. No
  Google account is ever connected to the app itself.

The Settings page shows the date of your last backup. Back up after busy
weeks and keep at least one copy off the phone.

## Restoring (same phone or a new one)

1. Install the app (finish or skip through onboarding — it will be
   replaced anyway).
2. Settings → My data → **Restore from a backup file** → pick the file.
3. The app CHECKS the file first (format, checksums, database integrity,
   version). A bad or damaged file is rejected with a plain message and
   nothing changes.
4. You see when the backup was made and a clear warning that restoring
   replaces current data. A **safety copy of the current data is made
   automatically** before anything is touched.
5. Confirm → the data is swapped atomically. If anything fails midway,
   the previous data is put back and the app says so honestly.

## What is NOT in a backup

The optional AI key (secure storage is deliberately excluded — re-enter
it on a new phone) and the app itself (install the APK first).

## Rules the app follows

Never restores without your typed-out confirmation step · never uploads
anywhere by itself · never overwrites the live data until the staged copy
has passed every check.
