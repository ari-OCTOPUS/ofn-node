---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [a2-001, binding, transfer, node-180]
author: "custodian-191"
---

# A2-001 binding copy to `.180` inbox — NOT DELIVERED

Source hash on `.191` matched. Bytes were copied with `scp -p` to the existing SSH host `root` → `192.168.0.180`. Content was not reformatted.

This host observed destination sha256 after copy. That is **not** an independent `.180` report. **Delivery claim remains NOT_DELIVERED.**

| field | value |
|---|---|
| source | `06-EVIDENCE/canonical/inbox/TO-180-A2-001-binding.json` |
| source_sha256 | `95527b069a15af1cd45d35894d7e42861fc9b30fffa8b2c269a43392216f7d68` |
| destination | `/opt/octopus/a2-lab/inbox/TO-180-A2-001-binding.json` |
| transfer_method | `scp -p` via existing OpenSSH `Host root` (no key change) |
| dest bytes / hash (observed from `.191`) | 363 / same sha256 |
| independent `.180` ACK | none |
| lab_execution | NOT_STARTED |

Machine receipt: `06-EVIDENCE/canonical/receipts/TO-180-A2-001-binding-transfer-2026-08-18.json`

Inbox dir was missing under existing `/opt/octopus/a2-lab`; only `mkdir -p .../inbox` was added. No fetch, merge, push, or Lab job.
