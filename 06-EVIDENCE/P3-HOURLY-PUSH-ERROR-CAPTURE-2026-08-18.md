---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [ops, germline, hourly-push, p3]
author: "custodian-191"
---

# P3 — hourly push error capture

Closes the empty `push err:` hole without changing push policy.

## What changed

- Helper: `04 - Architect System/scripts/hourly-push-error-capture.ps1`
- Wired into `germline-hourly.ps1` for both `push --all` and `push --tags`
- Raw stderr: TEMP file, deleted after redaction
- Persisted: `E:\germline\hourly-push-errors.jsonl`
- `$pushErr` in `hourly.log` / `hourly-state.json` now uses the first redacted line of the **failing** push (so `--tags` reject is no longer dropped)

Unchanged: remotes, credential.helper, credentials, timers, GitHub auth, SMB, fallback throttle, retry count (still one `--all` then one `--tags`).

## Acceptance (this host, 2026-08-18)

```
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\backup\04 - Architect System\scripts\test-hourly-push-error-capture.ps1"
RESULT: PASS
nonzero class : REMOTE_NOT_FOUND  exit=128
success class : NONE  exit=0
secret-like ghp_ / password / https URL absent from persisted jsonl
```

Not in `_ops/tests/run_all.py` (WORKLOCK).
