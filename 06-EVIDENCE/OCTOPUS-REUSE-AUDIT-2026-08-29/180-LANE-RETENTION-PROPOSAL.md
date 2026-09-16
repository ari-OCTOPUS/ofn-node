---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, board-180, retention, proposal-only]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/180-QUALIFICATIONS]]"
---

# 180 lane — retention / disk (proposal only)

```text
MUTATIONS=0
DELETE_AUTHORIZED=NO
WORKER_CHANGE=NO
observed_at=2026-08-29T05:26:00Z
scope=this_host_only
truth_status=DOCUMENTED
```

Source of counts: owner-pasted 180 pack 2026-08-29 (not re-hashed here). Inbox 3377 (ping 3185, wake 170, task 12); outbox 27; dead-letter 2; state ~60MB / 6807+6123 files; disk ~93%.

## Problem

Mesh receive ACK stores inbox files. `find_duplicate` is a linear scan of all files (180 pack). No retention index. Growth is operational, not a license to delete.

## Proposed reuse (do not build a new queue)

Use existing reply-outbox + `processed_ids.json` + dead-letter. Add an **index sidecar** (path → type → mtime → sha) generated offline, then a **dry-run archive** that copies ping-class files older than TTL to an archive dir **without unlinking** until restore proof exists.

| Class | Suggested TTL (proposal) | Action after GO |
|---|---|---|
| ping | 7d | archive candidate |
| wake/snapshot ACK'd | 30d | archive candidate |
| task / proposal / reply pending | never auto | owner only |
| dead-letter | 90d keep + label | no delete |
| cognition predictions | 14d if `reply_acked` | archive candidate |

## Archive candidates (names only — not moved)

From 180 census, first class to review: inbox `ping` majority (3185/3377). Exact filenames must be listed on 180 live disk in a later read-only `find` — **not run from this vault**.

## Restore proof (required before any unlink)

1. Copy N=1 ping file to archive.
2. SHA256 match.
3. Replay receive dedupe still treats it as duplicate (hermetic fixture, fake transport).
4. Only then owner may authorize unlink of that class.

## Replay test design (hermetic)

Fixture: two inbox JSON with same checksum/idempotency. Assert second is SUPERSEDED or duplicate, no `fn(wire)`, no mosquitto. File: propose `octopus_mesh_receive_dedupe` next to existing WAVE0 reply-outbox tests — **not written this turn**.

## Forbidden in this lane

Delete queue/state; change worker; change 8081 bind; change UFW; install resource-monitor; enable Telegram; new broker/event store.
