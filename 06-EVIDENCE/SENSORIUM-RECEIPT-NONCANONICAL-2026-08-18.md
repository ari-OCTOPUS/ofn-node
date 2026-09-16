---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [sensorium, receipts, wave0, readonly]
author: "custodian-191"
---

# Sensorium `.182` — observation accepted; receipts not canonical

`.182` read-only behavior is accepted: local health only, missing allowlist/receipt path not hidden, `timedatectl` recorded as `UNKNOWN`, systemd contradiction reported without picking a winner. That is witness-with-uncertainty.

Split that must not collapse:

| item | status |
|---|---|
| local health data | `WAVE0_OBSERVATION_CANDIDATE` |
| in-band receipts | temporary evidence, **not** canonical receipts |
| `PASS_READONLY` | observation constraints were kept; **not** clock correctness, **not** full node health, **not** permission to expand scope |

Canonical receipts stay on `.191` evidence paths. Do not promote Sensorium in-band packets.
