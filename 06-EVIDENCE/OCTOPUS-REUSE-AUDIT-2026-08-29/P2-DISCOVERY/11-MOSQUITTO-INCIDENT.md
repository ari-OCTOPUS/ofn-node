---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, incident, mosquitto]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
---

# 11 — Mosquitto incident (no re-probe)

```text
PROBE_RERUN=NO
claim_type=inference_plus_documented
observed_at=2026-08-28T23:34:07Z
RUN_ID=tg-web-debug-20260828T233407Z
```

| Item | Record | Truth |
|---|---|---|
| triggering command | First 182 process map: `pgrep -af` pattern containing `mosquitto` then `ss -lntup` | DOCUMENTED |
| why it spawned | Malformed pgrep via PowerShell: `|mosquitto|` treated as a pipeline and **exec’d the broker**. Alternative: explicit invoke not preserved. | HYPOTHESIS |
| temporary PID(s) | **552046** broker on `[::1]:1883`; **552041** companion | DOCUMENTED |
| baseline PID | **382176** on `127.0.0.1:1883` | DOCUMENTED |
| containment | `kill 552046 552041`; sleep 1; re-pgrep / ss | DOCUMENTED |
| proof temp PIDs ended | final listener map = baseline only | DOCUMENTED |
| proof baseline remained | 382176 still listening; no systemctl restart | DOCUMENTED |
| state/queue impact | UNKNOWN | UNKNOWN |
| network bind impact | transient extra `[::1]:1883` then gone | DOCUMENTED |
| regression guard | **none in tests**; narrative `RUNTIME_CHANGES=1_TRANSIENT_CONTAINED` | DOCUMENTED |

Do not re-run `pgrep` patterns with `|mosquitto|` through PowerShell. Do not invoke `mosquitto`.
