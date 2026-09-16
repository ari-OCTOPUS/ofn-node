---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-138, reuse]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: en
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/REUSE-MAP]]"
  - "[[03 - Projects/OFN-Board/ofn/node.py]]"
---

# 05 — Component reuse

```text
observed_at=2026-08-29T05:32:32Z
method=138_source_listing_plus_vault_ofn_board
scope=this_host_only
NEW_SUBSYSTEMS_REQUIRED=0
```

Do not build: new event store, command bus, broker, approval store, owner queue, `business_operator` package, Telegram subsystem, ledger, or Cockpit. `631913de` (vault event_store/command_bus) is **absent** from 138 and must stay absent.

| component | file:line (138 unless noted) | runtime caller | store | tests | live/repo/doc | missing edge | Truth |
|---|---|---|---|---|---|---|---|
| inbox | `inbox_processor.py`; `OFN_INBOX_DB` name | ofn.run | SQLite name only | `test_http_api` family | LIVE unit / DB `NOT_RUN` | — | `LIVE_VERIFIED` names |
| outbox | `outbox.py:118` `approve_manual:195` `complete_manual:239` | `Node.owner_decide` | SQLite outbox | `test_manual_dispatch`, painting outbox | LIVE_AND_USED | auto sender absent by design | `REPO_VERIFIED` vault + `LIVE_VERIFIED` file on 138 |
| outbox sender | `manual_dispatch.py`; `sender_dryrun.py`; `owner_outbox_packet` | human GET packet + POST complete | none auto | `test_manual_dispatch.py` | LIVE code / no poller send | T2 PARTIAL | `REPO_VERIFIED` |
| owner approval | `POST /api/v1/decide` `http_api.py` ~1284 vault / 138 same contract | `Node.owner_decide` | outbox status | `test_owner_api` | LIVE (401 on V2; v1 not hit) | V2 is GET-only | `REPO_VERIFIED` |
| owner decision card | `owner_decision.py` DECISION_FIELDS | **not** imported by `run.py` HTTP path | none | `test_owner_decision_fake.py` | BRANCH/spine **unwired** | E8 | `LIVE_VERIFIED` |
| release gate | `ConsentStore`; `publish_to_telegram` `node.py:3266` vault | node | `OFN_CONSENT_DB` name | `test_consent.py` | LIVE code | OF consent separate | `REPO_VERIFIED` |
| ledger | `ledger.py` | `owner_decide` VERDICT | ledger SQLite | kernel tests | LIVE_AND_USED | not OwnerDecision hashes | `REPO_VERIFIED` |
| facts | `facts.py` | node | facts | — | REPO | — | `LIVE_VERIFIED` file |
| tenant registry | packs YAML + `packloader.py` | run.py | packs | `test_packs.py` | LIVE | — | `LIVE_VERIFIED` |
| Telegram ingress | **zero pollers** | none | — | MiniApp HMAC tests | DEAD/BLOCKED | E5 | `LIVE_VERIFIED` |
| Telegram egress | `publish_to_telegram`; `alert.py`; `telegram_channel.py` | owner path / crash alert | outbox | `test_alert.py` | IMPLEMENTED; alert default off | tokens not read | `REPO_VERIFIED` |
| Mini App | HMAC `verify_init_data` in tests; 191 organism MiniApp is **other plane** | 191 gateway not 138 | — | `test_auth` | 138: code/tests; 191: live UI | do not merge | `DOCUMENTED` |
| Cockpit V2 | `cockpit_v2_read_model.py` 3058 lines; `GET /api/v2/owner/*` | ofn.run if loaded | mesh files + owner callback | `test_cockpit_v2_*` | disk YES; PID pre-P1 | scan budget; owner_items UI | `LIVE_VERIFIED` |
| Owner Center | no systemd unit | — | — | — | MISSING as service; **do not create** | use decide + panel | `LIVE_VERIFIED` |
| BrainPort / RemoteBrain | `remote_brain.py`; `router.py` | node | — | `test_brain_*` | REPO | — | `LIVE_VERIFIED` files |
| worker queue | octopus-router.service active | **not inspected/consumed** | mesh | — | LIVE unit | ≠ OFN outbox | `LIVE_VERIFIED` |
| receipt | ledger complete_manual; 182 wr_* other host | — | mixed | fake E2E | schema-local | EDGE-6 | `DOCUMENTED` |
| witness request | `witness_mint.py` | tests only; not owner_decide | JSONL test | `test_witness_mint.py` | REPO unwired | local mint FORBIDDEN | `LIVE_VERIFIED` |
| reconciler | octopus-cycle-settler.service | listed | — | — | LIVE unit | body unknown this probe | `LIVE_VERIFIED` unit |
| backup/restore | `ofn.backup_job` timer | systemd | OFN DBs | restore runbooks | LIVE timer | mesh `~/octopus-mesh` incomplete (E6) | `LIVE_VERIFIED` / `DOCUMENTED` |

Vault `03 - Projects/OFN-Board` has the same **legacy decide/outbox** family and **lacks** P1 `owner_queue_metadata`. Copying V2/spine into the vault tree would be a parallel rewrite (MISSING-EDGES E10).

```text
NEW_EVENT_STORE=FORBIDDEN
NEW_COMMAND_BUS=FORBIDDEN
NEW_TELEGRAM_SUBSYSTEM=FORBIDDEN
NEW_COCKPIT=FORBIDDEN
```
