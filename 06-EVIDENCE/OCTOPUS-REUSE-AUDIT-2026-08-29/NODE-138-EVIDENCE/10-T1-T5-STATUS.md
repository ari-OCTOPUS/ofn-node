---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-138, t1-t5]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: en
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/NODE-138-EVIDENCE/09-TELEGRAM-CONSENT]]"
  - "[[03 - Projects/OFN-Board/docs/runbooks/NTP]]"
---

# 10 — T1 to T5

```text
observed_at=2026-08-29T05:32:32Z
method=ssh_readonly_no_firewall_change
scope=this_host_only
NO_T1_T5_EXECUTION=1
```

Statuses used: LIVE_COMPLETE | REPO_COMPLETE | IMPLEMENTED_NOT_WIRED | PARTIAL | DOCUMENTED_ONLY | BLOCKED | NOT_NEEDED_DUPLICATE | UNKNOWN

## T1 Telegram

```text
T1_STATUS=PARTIAL
```

Five token **names**, consent + `publish_to_telegram` + alert + MiniApp tests exist. Zero pollers. Bridge unit absent. CONTRACT_GAP. No bot API this session.

source: 09 + WHAT-IS-DEAD + `systemctl` · truth: `LIVE_VERIFIED` units / `REPO_VERIFIED` code

## T2 outbox sender

```text
T2_STATUS=PARTIAL
```

Outbox + `approve_manual` + `complete_manual` + `ManualPacket` are live code and the sole egress design. Automatic provider sender is **intentionally absent** (O2: approval ≠ claim ≠ send). `sender_dryrun.py` is dry-run only. Not a missing architecture — missing **human complete** / wiring, not a new sender service.

source: `outbox.py` vault+138 · truth: `REPO_VERIFIED` / `LIVE_VERIFIED` file

## T3 legacy organs

```text
T3_STATUS=PARTIAL
```

| Expected path | On 138 | Truth |
|---|---|---|
| ziman-node standalone | **ABSENT** `/home/ari/ziman-node` | `LIVE_VERIFIED` |
| Project-F | **ABSENT** | `LIVE_VERIFIED` |
| Lead / Studio / Ziman | `packs/{lead,studio,ziman}.yaml` + `lead_store.py` `studio_store.py` `products.py` | `LIVE_VERIFIED` |
| hypno | `packs/hypno.yaml` (out of portfolio charter) | `LIVE_VERIFIED` |
| business cycle | `weekly_cycle.py` | `LIVE_VERIFIED` file |
| organ adapters | under `ofn/adapters/` | `LIVE_VERIFIED` |
| feet138 | `/home/ari/feet138` exists (purpose not opened) | `LIVE_VERIFIED` path / `UNKNOWN` role |
| zip source | not searched beyond homes | `NOT_RUN` |

Organs are **YAML packs + adapters inside ofn-node**, not separate ziman-node/Project-F trees.

## T4 firewall / miner isolation

```text
T4_STATUS=PARTIAL
```

| Check | Result | Truth |
|---|---|---|
| ufw | binary not found | `LIVE_VERIFIED` |
| nft | binary not found | `LIVE_VERIFIED` |
| iptables | binary not found; `/proc/net/ip_tables_names` permission denied | `LIVE_VERIFIED` / `UNKNOWN` kernel tables |
| dietpi-firewall | not found | `LIVE_VERIFIED` |
| OFN bind | `127.0.0.1:8791-8794` only | `LIVE_VERIFIED` |
| SSH | `0.0.0.0:22` | `LIVE_VERIFIED` |
| miner units | `*mine*` `*xmrig*` `*hash*` → 0 loaded | `LIVE_VERIFIED` |

Isolation observed as **loopback bind**, not as a readable nft/UFW policy. No firewall change.

## T5 clock / NTP

```text
T5_STATUS=PARTIAL
```

**Do not assume timesyncd is the running provider.**

| Field | Value | Truth |
|---|---|---|
| unit file | `systemd-timesyncd.service` present; **enabled**; **inactive (dead)** since 2026-08-29 01:25:03 AEST | `LIVE_VERIFIED` |
| last run | exited 0 after 1.498s; status Idle | `LIVE_VERIFIED` |
| `timedatectl` | NTP service inactive; System clock synchronized: **no**; NTP=no; NTPSynchronized=no; CanNTP=yes | `LIVE_VERIFIED` |
| timezone | Australia/Sydney (AEST) | `LIVE_VERIFIED` |
| RTC | `timedatectl` shows RTC time ≈ UTC; `RTC in local TZ: no` | `LIVE_VERIFIED` |
| chrony / ntp.conf / timesyncd.conf | **not found** at usual paths | `LIVE_VERIFIED` |
| vault `NTP.md` | “board has no RTC battery” | `DOCUMENTED` — **CONTRADICTED or incomplete** vs live RTC line (battery vs RTC device are different claims) |

Provider **present**: systemd-timesyncd. Provider **active**: no. Clock source now: local clock + RTC readout, unsynchronized.

## Execution

T1–T5 were **not** implemented or repaired. Status only.
