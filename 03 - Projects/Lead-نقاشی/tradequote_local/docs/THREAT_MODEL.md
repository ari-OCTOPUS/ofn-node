# Threat model (practical, v0.1.0)

Assets: customer PII (names, phones, addresses), financial records,
issued tax documents, the backup archive, the optional AI key.

| # | Threat | Vector | Mitigation | Residual risk |
|---|---|---|---|---|
| T1 | Lost/stolen phone | physical | Android sandbox + device lock/encryption; no cloud copy to leak | DB not app-layer encrypted (SECURITY.md) — phase-2 SQLCipher |
| T2 | Malicious/corrupt backup file | restore path | format+checksum validation, integrity_check, schema gate, zip path-traversal rejection, staging + safety backup + atomic swap w/ rollback | zip-bomb style resource exhaustion — bounded by picker + device limits, accepted |
| T3 | Data loss (crash, storage failure, bad update) | reliability | WAL sqlite, transactions, auto-saved drafts, VACUUM'd backups, pre-restore safety copies, no destructive migrations | user forgetting to back up — mitigated by last-backup date nudge |
| T4 | Tampering with issued records | insider/error | issued docs frozen (snapshot), edits blocked, void-not-delete, numbers never reused, audit events | determined user with root/file access — out of scope for a personal tool |
| T5 | Share-target data exposure | Telegram/Gmail | explicit user action per share; app-private cache with 7-day cleanup; no silent sharing | what the receiving app does is outside app control (documented) |
| T6 | AI key theft / key misuse | secure storage | key only in flutter_secure_storage; never logged/exported/backed up; disconnect wipes it | compromised device — same as T1 |
| T7 | AI prompt/content leakage | optional feature | off by default; only message text sent; review-before-apply; provider policy flagged to owner | provider-side retention — user's provider choice |
| T8 | Fake "delivered" assumptions | UX honesty | ShareOutcome model has no delivered state; manual confirmation only | user mis-remembering — history shows share events |
| T9 | Supply-chain (malicious package update) | pub.dev | caret ranges + committed lockfile after first resolve; review `pub outdated` before releases; no obscure packages | as for any Flutter app |
| T10 | Backup left in shared location | user behaviour | guide tells owner to treat backups like paper records | user discretion |

Out of scope for this personal-use MVP: multi-user auth, server threats
(no server), Play-Store distribution hardening, rooted-device defenses.
