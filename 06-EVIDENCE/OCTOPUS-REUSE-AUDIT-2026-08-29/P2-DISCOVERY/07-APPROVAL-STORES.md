---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, approvals, aggregates]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
---

# 07 — Approval stores (4 / 29 / 0 / 40)

```text
AGGREGATES_ARE_ONE_QUEUE=false
observed_at=2026-08-28T23:40:00Z
method=phase0_191_probe_plus_file_reads
scope=this_host_only
truth_status=DOCUMENTED
```

These four numbers were reported together in Phase 0 (`OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29.md:65-66`). They are **not** one queue.

| N | Store | Path | Owner service | Schema | Scope | Tenant/node | Meaning | Freshness | Count semantics | Dedupe | Authoritative? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | MiniApp outcomes pending | `F:\backup\_ops\state\outcomes\outcomes.db` | MiniApp `get_approvals_state` / OpsActionEngine | SQLite `outcomes`; pending = latest delivered + verdict IS NULL; sandbox channel filtered | 191 `/api/approvals` | organism 191 | 4 production ziman-gallery delivered-not-decided | last write cited 2026-08-28 08:53 | latest delivered row per item | sandbox hidden | YES for MiniApp cards. Not OFN. Not EDGE-6 |
| 29 | Telegram Center jobs | `F:\backup\_octopus\state\approvals.json` | `approval_store.py`; Center `ap:*` | `{pending[], approved[], rejected[], done[]}` | Telegram Center page | 191 Center | 29 pending jobs | cited 2026-08-28 14:26 | list length | store-local | YES for Center jobs. Not MiniApp. Not OFN |
| 0 | Unified HITL (deprecated) | `F:\backup\_ops\state\unified-approval-queue.json` | `approval_queue_unified.py` unused; `owner_api.py` counts `preview_sent` | JSON list | legacy Owner Cockpit `/approvals` | 191 | 0 preview_sent | cited 2026-08-08 05:38 | status==preview_sent | n/a | STALE / non-authoritative |
| 40 | Lifecycle stalled RFCs | `F:\backup\_ops\state\pulse\pending-cards.json` | pulse / `lifecycle_fold.stalled_cards`; `/api/lifecycle` | RFC cards; stalled ⊂ 119 | MiniApp lifecycle tab | 191 | 40 stalled of 119 | cited 2026-08-24 14:10 | stall predicate | n/a | YES for RFC stall. Not approvals |

## Not those four

| Artifact | Number | Meaning |
|---|---|---|
| `outbox-status-counts.txt` | `manual_completed\|25` | 138 OFN SQLite, all `studio:<hex>`, 23 Aug. Zero pending |
| `v2-queue-http.txt` | `401` | GET `/api/v2/owner/queue` without session. Not a count |
| CHECKPOINT | 25 completed, 0 pending | same 138 outbox |
| Phase 0 “138 business pending/held” | 0 | fifth store |
| 180 mesh inbox/outbox approvals | 0 | cannot explain UI 4 |

Do not add these numbers. Label source + `observed_at`.

## Lifecycle mapping (join keys, no merge)

| Object | Canonical store | Join key |
|---|---|---|
| approval request | depends on plane (outcomes / approvals.json / OFN outbox / mesh pending) | plane-local id |
| owner decision | OFN: `POST /api/v1/decide` + ledger VERDICT; MiniApp: outcomes verdict; Center: approvals.json | `tenant:idem` vs job id vs outcome id |
| execution authorization | OFN `approve_manual` ≠ send; 180 `may_authorize=false` | UNKNOWN across planes |
| effect | 138 executor / Telegram send — HOLD_EXTERNAL for spine | UNKNOWN |
| ACK | mesh transport / inbox store | envelope / message_id |
| receipt | 182 witness file; owner-receipt.json; `complete_manual` packet_sha | often **not** the same run_id |
| witness | 182 `STRUCTURAL_PASS` | source hash, not proposal enqueue |

No new aggregate. No store merge.
