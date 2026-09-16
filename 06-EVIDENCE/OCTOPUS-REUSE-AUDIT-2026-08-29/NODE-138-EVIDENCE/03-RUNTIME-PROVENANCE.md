---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-138, runtime, provenance]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: en
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/runtime-provenance-20260828T230743Z/CHECKPOINT]]"
  - "[[03 - Projects/OFN-Board/deploy/systemd/ofn.service]]"
---

# 03 — Runtime provenance

```text
observed_at=2026-08-29T05:31:45Z
method=systemctl_show_plus_procfs_plus_ss
scope=this_host_only
truth_status=LIVE_VERIFIED
```

`/proc/<pid>/environ` was **not** read. `systemctl show -p Environment` was **not** used. EnvironmentFile **paths only**.

## ofn.service (body)

| Field | Value | Truth |
|---|---|---|
| unit | `ofn.service` | `LIVE_VERIFIED` |
| active/enabled | active / enabled | `LIVE_VERIFIED` |
| MainPID | **1351408** (same as 27–29 Aug audits) | `LIVE_VERIFIED` |
| start | Thu 2026-08-27 11:33:39 AEST; elapsed 2-03:58:29 at probe | `LIVE_VERIFIED` |
| NRestarts | 0 | `LIVE_VERIFIED` |
| ExecStart | `/usr/bin/python3 -m ofn.run` | `LIVE_VERIFIED` |
| exe | `/usr/bin/python3.13` | `LIVE_VERIFIED` |
| user/group | ari/ari | `LIVE_VERIFIED` |
| HOME implied | `/home/ari` | `LIVE_VERIFIED` |
| cwd | `/home/ari/ofn` | `LIVE_VERIFIED` |
| loaded code path | import from CWD; **no memory dump** | `LIVE_VERIFIED` path / `UNKNOWN` bytes-in-RAM |
| MemoryCurrent | 72294400 (~69 MiB); RSS 79500 KiB | `LIVE_VERIFIED` |
| Restart | always | `LIVE_VERIFIED` |
| EnvironmentFiles (names) | `node.env`; `secrets.env`; `shopify_oauth.env` under documented dirs | `LIVE_VERIFIED` names |
| listen | `127.0.0.1:8791-8794` | `LIVE_VERIFIED` |
| repo HEAD on disk | `a27eb05` | `LIVE_VERIFIED` |
| process vs HEAD | start **before** P1 commit 2026-08-29 09:27; P1 file mtimes 09:23 after start | `LIVE_VERIFIED` |

```text
RUNTIME_COMMIT=UNPROVEN_PRE_P1
SOURCE_CHANGED_AFTER_START=true
P1_RUNTIME_LOADED=NO
```

Disk SHA256 (not RAM):

| File | sha256 | mtime |
|---|---|---|
| `ofn/run.py` | `ac727863b72171cf50faf0fba00d50e4d85b2c4ffbf6e67333d5c258f06705f1` | 2026-08-29 09:23 |
| `ofn/node.py` | `d07963936cdea74b59e6d1c1ae27037845fb07b1af74acc44b5f2d6abb9cadaa` | 2026-08-29 09:23 |
| `cockpit_v2_read_model.py` | `b501c98ae3c76675eb0ff2e512ad90bf7f9e2ec04bdecb6a47ffac7e7cf06f45` | 2026-08-29 09:23 |
| `http_api.py` | `052864bed63976191022cfc921a43d5df8c66249f2b2ebe31dbf8cf55b284268` | 2026-08-27 11:02 (before PID start) |
| `ofn.service` | `b6310ba8c9698accd007d9683417ef265ea0356646d6687d935ffa3f3889d00b` | unit file |

Loopback `GET /api/v2/owner/version` Host `panel.master-painting.com` → **401** `{"error":"unauthorised"}`. No session. Not a queue consume.

## Other units (138)

| unit | active | enabled/state | MainPID | ExecStart (argv) | user | notes | Truth |
|---|---|---|---|---|---|---|---|
| ofn-boot | active (exited) | enabled | 0 | `python3 -m ofn.preflight` | ari | last enter 2026-08-17 | `LIVE_VERIFIED` |
| ofn-backup.timer | active waiting | enabled | — | oneshot `ofn.backup_job` | ari | last run 2026-08-29 03:19 exit 0 | `LIVE_VERIFIED` |
| ofn-alert | inactive | disabled | 0 | `ofn.adapters.alert` | ari | optional Telegram via flag name only | `LIVE_VERIFIED` |
| ofn-heartbeat | active | enabled | 676 | `/home/ari/.local/bin/ofn-heartbeat.sh` | ari | since 2026-08-17 | `LIVE_VERIFIED` |
| cloudflared | active | enabled | 669 | `cloudflared … tunnel run` | (unit default) | config path `/etc/cloudflared/config.yml` not opened | `LIVE_VERIFIED` |
| octopus-bridge | active | enabled | 589802 | `python3 -m octopus_bridge.run` | ari | `:8796`; env file name `octopus-bridge.env` | `LIVE_VERIFIED` |
| octopus-control-router | active | — | n/a glob | control plane | — | listed | `LIVE_VERIFIED` |
| octopus-cycle-settler | active | — | — | reconciliation loop | — | listed | `LIVE_VERIFIED` |
| octopus-router | active | — | — | queue loop | — | listed; **not consumed** | `LIVE_VERIFIED` |
| octopus-supervisor | active | — | — | worker health | — | listed | `LIVE_VERIFIED` |
| octopus-verify-dispatcher | active | — | — | verify dispatch | — | F-2 still open in MISSING-EDGES | `LIVE_VERIFIED` unit / `DOCUMENTED` gap |
| ofn-assistant-update.timer | active waiting | — | last job 2026-08-29 04:11 | `ofn.assistant_update` | ari | | `LIVE_VERIFIED` |
| ofn-marketing | inactive static | — | — | `ofn.marketing_run` | ari | | `LIVE_VERIFIED` |
| telegram / telegram-bridge / octopus-telegram-bridge / ofn-telegram / owner-center | **no fragment / inactive** | — | 0 | — | — | | `LIVE_VERIFIED` |
| cockpit as systemd | **no unit** | — | — | served by ofn.run | — | | `LIVE_VERIFIED` |

## Sockets

| bind | process | Truth |
|---|---|---|
| `127.0.0.1:8791-8794` | python3 PID 1351408 | `LIVE_VERIFIED` |
| `127.0.0.1:8796` | python3 PID 589802 bridge | `LIVE_VERIFIED` |
| `127.0.0.1:8895` | python3 PID 672 | `LIVE_VERIFIED` (role `UNKNOWN` this probe) |
| `127.0.0.1:20241` | (no process column) | `LIVE_VERIFIED` listen / owner `UNKNOWN` |
| `0.0.0.0:22` / `[::]:22` | sshd | `LIVE_VERIFIED` |
| `0.0.0.0:68/udp` | DHCP client | `LIVE_VERIFIED` |

Missing LAN port on 191 ≠ missing loopback API on 138 (`inference` already in L191; this session **observed** loopback 401).

## Canonical user vs telegram template

Resolved: **ari / /home/ari / /home/ari/ofn**. dietpi exists as uid 1000 with private home; no ofn service runs as dietpi; telegram-bridge unit absent. Template `User=dietpi` is **STALE** relative to live OFN.
