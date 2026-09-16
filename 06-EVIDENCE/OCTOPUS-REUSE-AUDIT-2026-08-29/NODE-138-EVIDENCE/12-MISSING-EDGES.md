---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-138, missing-edges]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: en
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/MISSING-EDGES]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/08-EDGE6-CAUSAL-TRACE]]"
---

# 12 — Missing edges

```text
observed_at=2026-08-29T05:32:32Z
scope=this_host_only
NEW_SUBSYSTEMS_REQUIRED=0
```

Edges only. No new module.

| ID | Edge | Status now | Proof still needed | Do not build | Truth |
|---|---|---|---|---|---|
| E1 | restart provenance vs HEAD | **OPEN** — PID 1351408 ≠ `a27eb05` | start time + HEAD + file sha after **owner** restart | new provenance system | `LIVE_VERIFIED` gap |
| E2 | V2 queue vs legacy decide | CONFIRMED mismatch (mesh `message_id` vs `tenant:idem`) | P1 projection unloaded in PID | `/api/control/v2` | `DOCUMENTED` + `LIVE_VERIFIED` P1 disk |
| E3 | verify-dispatcher claims | unit **active** on 138; file not re-read | disk diff `/home/ari/octopus-mesh/bin/octopus_verify_dispatcher.py` | new verify service | `LIVE_VERIFIED` unit / `NOT_RUN` source |
| E4 / EDGE-6 | 180 proposal → 138 | first missing **proposal_enqueue** | isolated 180 PATH_A vs B | 3-line PATH_B again | `DOCUMENTED` |
| E5 | Telegram decision renderer | CONTRACT_GAP; 0 pollers | env names exist; values unknown | sixth bot | `LIVE_VERIFIED` |
| E6 | backup mesh | timer backups OFN DBs; mesh completeness unproven this session | additive path with GO | fourth backup system | `DOCUMENTED` |
| E7 | test count canon | 118 files; prior 2028 vs 2076 | one runner receipt | extra tests for vanity | `LIVE_VERIFIED` / `DOCUMENTED` |
| E8 | OwnerDecision ↛ http_api | still unwired on 138 HEAD | bind before enqueue | local mint | `LIVE_VERIFIED` |
| E9 | fake_executor ↛ outbox | files present; not sole egress | keep fake in tests | promote fake to prod | `LIVE_VERIFIED` files |
| E10 | vault ↛ 138 V2/spine | vault OFN-Board lacks P1; `c803dee` not in 138 | merge inside ofn-node only | copy into vault OFN-Board | `LIVE_VERIFIED` |
| E11 | dual “Cockpit V2” name | 191 `_ops` vs 138 OFN | qualify in docs | merge codebases | `DOCUMENTED` |
| E12 | `owner_items` UI | `queue.js` ignores field | after P1 load | new cockpit | `LIVE_VERIFIED` |
| E13 | scan budget 2048 vs receipts | Phase 0: >3871 claims starve mesh | partition budget; serialize vs P1 file | raise 2048 unbounded | `DOCUMENTED` / `STALE` as live count |
| E14 | signed role registry | missing | owner rank A2 vs V2 vs C-034 | mint P2 from unsigned JSON | `NOT_FOUND` |
| E15 | NTP sync | timesyncd dead; clock unsynced | owner GO to enable NTP | assume synced HMAC | `LIVE_VERIFIED` |

```text
FIRST_MISSING_SAME_RUN_EDGE6=proposal_enqueue
P1_FIRST_MISSING=runtime_load_then_queue.js
P2_FIRST_MISSING=canonical_producers_plus_signed_roles
```
