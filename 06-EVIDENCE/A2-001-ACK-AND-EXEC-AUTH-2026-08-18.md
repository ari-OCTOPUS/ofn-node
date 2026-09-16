---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [a2-001, binding, ack, lab-180]
author: "custodian-191"
---

# A2-001 — binding ACK verified, execution authorized, Lab halted

Independent `.180` ACK matched the original binding. Execution authorization was copied byte-identically and consumed. Lab did **not** implement A2-001.

## Binding (now DELIVERED)

| field | value |
|---|---|
| source | `06-EVIDENCE/canonical/inbox/TO-180-A2-001-binding.json` |
| sha256 | `95527b069a15af1cd45d35894d7e42861fc9b30fffa8b2c269a43392216f7d68` |
| ACK | `06-EVIDENCE/canonical/inbox/from-180/run-20260817T175442Z-a2-001-binding-ack.json` |
| ACK sha256 | `a2f0fce71b9327b57703b3695a06895745547c9541f4ccd8374bee8f4e859ae8` |
| ACK outcome | `BINDING_ACKED` · `hash_match: true` · field verify `ALL_OK` |
| event_time | `2026-08-17T17:54:58Z` |

Older transfer receipt still says `NOT_DELIVERED` on purpose (that moment had no independent ACK).

## Execution authorization

| field | value |
|---|---|
| source | `06-EVIDENCE/canonical/inbox/TO-180-A2-001-execution-authorization.json` |
| file sha256 | `9fb65045556362c02482035aed9ed957c318669d064a955b36d42bf1230fb771` |
| packet_hash | `a7dc5dfde2c96f655a91a50deb8c581160980784edd8a3d548eb926bea101b11` |
| dest | `/opt/octopus/a2-lab/inbox/TO-180-A2-001-execution-authorization.json` |
| method | `scp -p` via existing `Host root` (no key change, bytes not regenerated) |

`.191` did not start `runner.py`.

## Lab execute envelope (observed)

Copy: `06-EVIDENCE/canonical/inbox/from-180/run-20260817T180808Z-a2-001-execute.json`  
sha256: `c9e1d18336aed489b910a57cb6920ff9feb8de9169679140af06884814ea5191`

Outcome: **`BASE_COMMIT_UNAVAILABLE`**. `implemented/merged/pushed/deployed/canonical` all false. Fetch and SSH from `.180` denied. Pre-existing sandbox worktree was not reused.

Promotion remains **NONE**. Success on Lab, if it later happens, is still only `QUARANTINED_PASS`.

Machine receipts: `06-EVIDENCE/canonical/receipts/TO-180-A2-001-binding-ack-verified-2026-08-18.json` · `...execution-authorization-transfer-2026-08-18.json` · `...lab-execute-observed-2026-08-18.json`
