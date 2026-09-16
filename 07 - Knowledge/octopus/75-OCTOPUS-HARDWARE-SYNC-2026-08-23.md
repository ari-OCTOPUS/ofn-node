---
tags: [octopus, hardware-sync, season-note, laptop, orangepi, board2, 2026-08-23]
date: 2026-08-23
timezone: Australia/Sydney
status: CURRENT-TRUTH-SUMMARY
SoT: F:\backup
---

# 75 — OCTOPUS HARDWARE SYNC 2026-08-23

**Timezone:** Australia/Sydney (UTC+10)  
**Stamp:** 2026-08-23 (laptop SoT Obsidian sync)  
**Rule:** narrative alone is not evidence. Sourced from `06-EVIDENCE` packs listed below. Do **not** invent PASS.

Pointer map: [[CURRENT-HARDWARE]] · season rollup [[90-SEASON-ROLLUP-2026-08-22]] · business [[01-BUSINESS-MAP-CANONICAL]] · continuous [[76-OCTOPUS-CONTINUOUS-CHECKPOINT-2026-08-23]]

## CURRENT TRUTH (2026-08-23)

### Laptop (SoT `F:\backup`)

| Item | State | Evidence |
|---|---|---|
| Branch / HEAD | `rescue/octopus-live-tree-20260821` @ **d07c9ad** | `06-EVIDENCE\OCTOPUS-CONTINUOUS-DISCOVER-2026-08-23\DISCOVER.json` (`git.branch` / `git.head`) |
| Center / poller | **PID 35916 single**; `poller_id=center-canonical`; no duplicate poller | same DISCOVER `processes.telegram_center` + `poller_note` |
| LIVE-TELEGRAM | **ON** (`_ops\LIVE-TELEGRAM.flag` exists, enabled) | DISCOVER `flags_locks_leases.LIVE_TELEGRAM_flag` |
| Writer lock | **soft renew in flight** (`grok-ari-single-writer`, TTL 900s @ 2026-08-23T02:39:33+10) | `06-EVIDENCE\OCTOPUS-REMEMBER-CORRECT-PROVE-2026-08-23\LOCK-RENEW.json` + `RESULT.json` |
| A18 | **BLOCKED** for live Telegram re-verify; historical `MISSING_ACK_FOR_/remember` + invalid `/correct` **code-fixed** (local prove PARTIAL) | DISCOVER `a18_wave` + `A18-BLOCKER-NOTE.md` + REMEMBER-CORRECT `RESULT.json` (`status=PARTIAL`) |
| DISCOVER pack | **OCTOPUS-CONTINUOUS-DISCOVER-2026-08-23** (`status=OK`) | that folder |
| Continuous execution | **ON** (no FREEZE; center+lease alive; Board2 refresh notes owner continuous on laptop SoT) | DISCOVER `FREEZE_active=false` + Board2 `75-BOARD2-STATUS-REFRESH` |

### Board2 / Ziman (DietPi legs)

| Item | State | Evidence |
|---|---|---|
| Gallery | **11** Shopify products `ZM-GALLERY-0007..0017` | `BOARD2-ZIMAN-GALLERY-INGEST-2026-08-23\SKU-MAP.txt` |
| Photos on Shopify | **only** `IMG_4109` → **ZM-GALLERY-0016** PASS; Mom-set still missing on disk | `BOARD2-ZIMAN-GALLERY-PHOTOS-2026-08-23\` (IMG_4109-RESULT + BULK-FILTER) |
| Shipping | **PASS** domestic flat **AUD $20**; international **OFF** | `BOARD2-ZIMAN-MONEY-INFRA-2026-08-23\07-SHIPPING-20-ONLY.md` + `RESULT.json` |
| GST | **OK** (prices exclude tax; AU GST collecting; ABN Missing ID — vault later) | same money pack |
| Bank / PayPal / ABN | Deferred **Sunday noon** with **Maliheh** (wait ari GO) | money `RESULT.json` + Board2 status refresh |
| Studio | shot-**0001** tg **7**; shot-**0002** canonical tg **9**; tg **10** left as known duplicate; 0003..0022 HOLD | `BOARD2-STUDIO-BATCH-QUEUE-2026-08-23\` + `BOARD2-STUDIO-DUP-0002-NOTE-2026-08-23\` |

### Orange Pi (Sensorium `192.168.0.182`)

| Item | State | Evidence |
|---|---|---|
| WAVE0 soft estop | **PERMITTED_SOFTWARE_A0**; **ARMED=false**; software latch reprove PASS; physical Path H still absent/deferred | `OCTOPUS-WAVE0-SOFT-ESTOP-UNLOCK-2026-08-23\FROM-PI\RECEIPT-WAVE0-SOFT-UNLOCK.json` |
| MQTT | **local** loopback `127.0.0.1:1883` PASS (auth required; WAN closed) | `OCTOPUS-ORANGEPI-MQTT-1883-ENABLE-ABD-2026-08-22\FROM-PI\RECEIPT-MQTT-ENABLE.json` + WAVE0 `SUMMARY.json` |
| Feeds | **7/7** PASS (`OCT-FEED-*` list; timer active) | `OCTOPUS-ORANGEPI-ESP32-INET-DATA-START-2026-08-22\FROM-PI\RECEIPT-ESP32-INET-FEEDS-EXPAND.json` (`feeds_ok=7`) |
| Torch | **PASS** (2.9.1+cpu aarch64) | `OCTOPUS-ORANGEPI-TORCH-EXECUTE-2026-08-22\RECEIPT-TORCH-INSTALL.from-pi.json` |
| ckpt348 | **PASS** (owner-signed; verify PASS) | `OCTOPUS-CKPT348-OWNER-SIGN-2026-08-22\SIGN-RESULT.json` |

### Businesses (canonical)

| Business | People | State |
|---|---|---|
| Master Painting | owner + **Abbas** | lead lane — prior GO evidence stands |
| Ziman | **Maliheh** | gallery + money infra in flight (see Board2) |
| Studio / OF | **Saba** | 0001/0002 published; captions hold beyond |
| Mining | — | **deferred** |

Canonical map: [[01-BUSINESS-MAP-CANONICAL]]

## Explicit non-actions

- Do **not** invent A18 Full Loop / LIVE-B PASS (owner live TG canary still required)
- Do **not** treat soft WAVE0 as physical Path H / GPIO/PWM unlock
- Do **not** invent gallery photos/captions/prices; Mom-set still missing
- Do **not** auto bank/PayPal/ABN / refunds / withdrawals
- Mining stays deferred

## Evidence index (this sync)

- `F:\backup\06-EVIDENCE\OCTOPUS-CONTINUOUS-DISCOVER-2026-08-23\`
- `F:\backup\06-EVIDENCE\OCTOPUS-REMEMBER-CORRECT-PROVE-2026-08-23\`
- `F:\backup\06-EVIDENCE\OCTOPUS-A18-BLOCKER-2026-08-23\`
- `F:\backup\06-EVIDENCE\OCTOPUS-WAVE0-SOFT-ESTOP-UNLOCK-2026-08-23\`
- `F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-MQTT-1883-ENABLE-ABD-2026-08-22\`
- `F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-ESP32-INET-DATA-START-2026-08-22\`
- `F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-TORCH-EXECUTE-2026-08-22\`
- `F:\backup\06-EVIDENCE\OCTOPUS-CKPT348-OWNER-SIGN-2026-08-22\`
- `F:\backup\06-EVIDENCE\BOARD2-ZIMAN-GALLERY-INGEST-2026-08-23\`
- `F:\backup\06-EVIDENCE\BOARD2-ZIMAN-GALLERY-PHOTOS-2026-08-23\`
- `F:\backup\06-EVIDENCE\BOARD2-ZIMAN-MONEY-INFRA-2026-08-23\`
- `F:\backup\06-EVIDENCE\BOARD2-STUDIO-BATCH-QUEUE-2026-08-23\`
- `F:\backup\06-EVIDENCE\BOARD2-STUDIO-DUP-0002-NOTE-2026-08-23\`
- `F:\backup\06-EVIDENCE\BOARD2-STATUS-REFRESH-2026-08-23\`
- Sync receipt: `F:\backup\06-EVIDENCE\OCTOPUS-OBSIDIAN-SYNC-2026-08-23\`