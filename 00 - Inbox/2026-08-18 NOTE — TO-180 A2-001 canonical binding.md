---
type: knowledge
status: inbox
created: 2026-08-18
updated: 2026-08-18
created_by: agent
tags: [octopus, a2-001, binding, node-180, sensorium]
sources:
  - "[[../06-EVIDENCE/canonical/inbox/TO-180-A2-001-binding.json]]"
  - "[[../06-EVIDENCE/TO-180-A2-001-BINDING-EMITTED-2026-08-18]]"
  - "[[../06-EVIDENCE/SENSORIUM-RECEIPT-NONCANONICAL-2026-08-18]]"
---

# TO-180 A2-001 canonical binding emitted from `.191`

State lock (hash of binding file verified on disk):

```yaml
a2_001_state:
  canonical_binding: DELIVERED_TO_180
  binding_file: "06-EVIDENCE/canonical/inbox/TO-180-A2-001-binding.json"
  binding_sha256: "95527b069a15af1cd45d35894d7e42861fc9b30fffa8b2c269a43392216f7d68"
  base_commit: "d10887cbb5c80ec2c3e347f070556ba8276d8a79"
  lab_execution: NOT_STARTED
  local_artifact: QUARANTINED_PASS_LOCAL_ONLY
  promotion_authority: NONE
  next_required_evidence: "ACK + fresh-worktree receipt from .180"
```

Machine copy: `06-EVIDENCE/canonical/decisions/a2-001-state-2026-08-18.json`

Lab تا ACK در `BLOCKED_BY_CANONICAL_BINDING` می‌ماند. این UNKNOWN_CANONICAL سالم است. `.191` local `QUARANTINED_PASS` اجرای Lab نیست. Promotion ممنوع. A2-002 / A2-003 شروع نشد.

`.182`: health محلی = `WAVE0_OBSERVATION_CANDIDATE`. receiptهای in-band canonical نیستند. `PASS_READONLY` فقط رعایت محدودیت مشاهده است.
