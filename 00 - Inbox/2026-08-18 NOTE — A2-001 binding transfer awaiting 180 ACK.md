---
type: knowledge
status: inbox
created: 2026-08-18
updated: 2026-08-18
created_by: agent
tags: [octopus, a2-001, binding, node-180]
sources:
  - "[[../06-EVIDENCE/A2-001-BINDING-TRANSFER-2026-08-18]]"
  - "[[../06-EVIDENCE/canonical/receipts/TO-180-A2-001-binding-transfer-2026-08-18.json]]"
---

# A2-001 binding copied to `.180` inbox — still NOT DELIVERED

`scp -p` to `/opt/octopus/a2-lab/inbox/TO-180-A2-001-binding.json` via existing `Host root` (`.180`). Source sha256 matched. `.191` also saw the same hash on the destination after copy.

**Not DELIVERED** until `.180` independently reports: file present + sha256 `95527b069a15af1cd45d35894d7e42861fc9b30fffa8b2c269a43392216f7d68`.

Lab not started. No git fetch/merge/push. No SSH key change.
