---
type: knowledge
status: inbox
created: 2026-08-18
updated: 2026-08-18
created_by: agent
tags: [octopus, germline, hourly-push, p3]
sources:
  - "[[../06-EVIDENCE/P3-HOURLY-PUSH-ERROR-CAPTURE-2026-08-18]]"
  - "[[../04 - Architect System/scripts/germline-hourly.ps1]]"
---

# P3 — hourly push error capture

هر `git push` در `germline-hourly.ps1` حالا stderr را در TEMP می‌گیرد، URL/token را ردکت می‌کند، و یک ردیف jsonl با `exit_code` / `stderr_sha256` / `error_class` / `elapsed_ms` می‌نویسد.

مقصد پایدار: `E:\germline\hourly-push-errors.jsonl`  
رفتار push/fallback/remote/credential/timer عوض نشد. تست: `04 - Architect System/scripts/test-hourly-push-error-capture.ps1` (خارج از `run_all.py`).
