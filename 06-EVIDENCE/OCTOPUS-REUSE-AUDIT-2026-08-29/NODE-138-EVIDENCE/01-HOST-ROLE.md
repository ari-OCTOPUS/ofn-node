---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-138, identity, roles]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: en
sources:
  - "[[02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/02-ROLE-AUTHORITY]]"
  - "[[03 - Projects/OFN-Board/deploy/systemd/ofn.service]]"
---

# 01 — Host and role

```text
observed_at=2026-08-29T05:31:30Z
method=ssh_readonly_ari@192.168.0.138
scope=this_host_only
truth_status=LIVE_VERIFIED
```

## Observer (this session)

| Field | Value | Truth |
|---|---|---|
| hostname | `DESKTOP-KA9RFN5` | `LIVE_VERIFIED` |
| IPv4 | `192.168.0.191` (plus WSL `172.17.176.1`) | `LIVE_VERIFIED` |
| claimed_session_role | octopus-continuity-180 quality brain | `DOCUMENTED` (Cursor user rule) |
| live vault host | node 191 | `LIVE_VERIFIED` |
| identity vs claim | **CONTRADICTED** — session claims 180, eth0/Wi-Fi is 191 | `CONTRADICTED` |

This agent did not stop the 138 forensic (parent assigned 191-vantage). It does not speak as 180 or as 138.

source: `hostname` + `ipconfig` on vault · method: local observation · observed_at: 2026-08-29T05:33:00Z · scope: this_host_only

## Target 138 identity

| Field | Value | Source | Method | Truth |
|---|---|---|---|---|
| hostname | `DietPi` | remote `hostname` | SSH | `LIVE_VERIFIED` |
| machine-id sha256 | `5a5171be4aa73c66ff495c7a56cea69939a2ef4d6c4e552bf9e2860aa829c591` | `/etc/machine-id` (33 bytes hashed; raw id not copied) | `sha256sum` | `LIVE_VERIFIED` |
| IPs | lo `127.0.0.1/8`; eth0 `192.168.0.138/24` | `ip -4 -br addr` | SSH | `LIVE_VERIFIED` |
| current user | `ari` uid 1001 | `id` | SSH | `LIVE_VERIFIED` |
| HOME | `/home/ari` | `$HOME` | SSH | `LIVE_VERIFIED` |
| OS | Debian 13 (trixie) DietPi | `/etc/os-release` | SSH | `LIVE_VERIFIED` |
| kernel/arch | Linux 6.1.115-vendor-rk35xx aarch64 | `uname` | SSH | `LIVE_VERIFIED` |
| clock | AEST; NTP inactive; RTC present | `timedatectl` | SSH | `LIVE_VERIFIED` |
| memory | 3910 MiB total, ~3033 MiB available, swap 0 | `free -m` | SSH | `LIVE_VERIFIED` |
| disk | `/` 58G, 11G used, 20% | `df -h` | SSH | `LIVE_VERIFIED` |

## Users (ari vs dietpi)

| User | uid | home | ofn path | Truth |
|---|---|---|---|---|
| ari | 1001 | `/home/ari` | `/home/ari/ofn` mode 755 owner ari | `LIVE_VERIFIED` |
| dietpi | 1000 | `/home/dietpi` mode 700 | `/home/dietpi/ofn` **Permission denied / not visible** | `LIVE_VERIFIED` |
| root | 0 | `/root` | not probed | `NOT_RUN` |

`ofn.service` User/Group/`WorkingDirectory` = `ari` / `ari` / `/home/ari/ofn`. Telegram template user `dietpi` has **no loaded telegram-bridge unit**.

```text
CANONICAL_USER=ari
CANONICAL_HOME=/home/ari
CANONICAL_OFN_PATH=/home/ari/ofn
CON-USER-138=DOCUMENTED_RESOLVED_TO_ARI
```

source: `getent passwd` + `systemctl show ofn` + `ls -ld` · observed_at: 2026-08-29T05:31:30Z · scope: this_host_only

## Role sources found

| Path | On 138 disk | Signed | Claim | Truth |
|---|---|---|---|---|
| `ofn/adapters/cockpit_v2_read_model.py` `_NODE_ROLES` | YES @ HEAD `a27eb05` | NO | 138 commander-router-ledger-owner; 180 quality-brain; 182 lab-witness; `may_authorize` default false | `LIVE_VERIFIED` |
| `config/nodes.json` / `agent_roles.json` / `policy.json` under `/home/ari/ofn` | **NOT_FOUND** this probe | — | — | `NOT_FOUND` |
| `/etc/systemd/system/ofn.service` | YES | unit ≠ owner signature | OFN field node, User=ari | `LIVE_VERIFIED` |
| `02-DECISIONS/A2-001` (vault) | n/a | YES owner block | 138 = proposal origin; 180 = execution; 191 = canonical; 182 silent; EFFECT NONE; A2 sandbox only | `REPO_VERIFIED` |
| L191 EDGE table | vault | NO | 138 mint target; EDGE-6 180→138 send | `DOCUMENTED` |
| C-034 / Sensorium | vault | owner-verified other plane | 182 observation, not OFN witness | `DOCUMENTED` |
| Signed `{138,180,182}×{Producer,Witness,Executor,Receipt}` | — | — | — | `NOT_FOUND` |

## Role matrix (do not mint from this)

| Node | Role (unsigned live / A2) | May propose | May witness | May execute | May authorize | May issue receipt | Evidence |
|---|---|---|---|---|---|---|---|
| 138 | commander-reconciler-ledger-owner (V2) / proposal origin (A2) | disputed | NO as canonical (`witness_mint` STRUCTURAL only) | disputed (V2/charter vs A2) | false in V2 default | OFN ledger / `complete_manual` exist | `_NODE_ROLES`; A2-001; `node.py` |
| 180 | quality-brain (V2) / execution node A2-scoped | YES on EDGE-5 | NO | disputed | false | A2 observer only | P2 02; A2-001 |
| 182 | lab-witness (V2) / silent (A2) / observe (C-034) | NO | **DISPUTED** | NO | false | **DISPUTED** | P2 02 |
| 191 | vault / A2 canonical | NO | NO | NO | owner only | A2 evidence | A2-001 |

```text
138_commander=UNSIGNED_LIVE_YES
138_reconciler=UNSIGNED_LIVE_YES
138_only_ledger_owner=UNSIGNED_LIVE_CLAIM
138_witness=NO_CANONICAL
182_witness_or_receipt=DISPUTED
owner_authority=human_via_/api/v1/decide_and_A2_owner_block
registry_signed=NO
ROLE_STATUS=DISPUTED
RED_TIER_EXECUTION=BLOCKED
```
