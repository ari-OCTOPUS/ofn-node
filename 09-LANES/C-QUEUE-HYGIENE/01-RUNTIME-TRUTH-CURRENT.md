---
type: runtime-truth
scope: this_host_only
node_id: session-claimed octopus-continuity-180
asserted_ip: unverified-eth0
measured_ipv4_wifi: 192.168.0.191
vantage: this_host_only
claim_type: file+runtime
measured_at: 2026-09-03T09:13:57Z
producer: C-QUEUE-HYGIENE execute pass
supersedes_receipt: receipts/runtime-truth-20260903T0900Z.json
---

# Runtime truth — this host only

Do not promote to system_wide. Session rule claimed board 180; this OS is Windows and Wi-Fi is 192.168.0.191 (`DESKTOP-KA9RFN5`). 180-body claims stop here. Disk absence of 180 is `body_not_on_this_host`.

| field | value | source |
|---|---|---|
| ROOT | `F:/backup` | `git rev-parse --show-toplevel` exit 0 this session |
| SHA | `8d8be71f1afb697ed1c80c40435c1e404be73368` | `git rev-parse HEAD` this session |
| BRANCH | `rescue/octopus-live-tree-20260821` | `git branch --show-current` this session |
| dirty_lines | 426 | `git status --porcelain` saved to `receipts/git-porcelain-20260903T0912Z.txt` |
| dirty_lines_prior | 423 | `receipts/git-porcelain-20260903T0900Z.txt` — both kept, `resolution: null` |
| hostname | `DESKTOP-KA9RFN5` | `$env:COMPUTERNAME` |
| wifi_ipv4 | `192.168.0.191` | `Get-NetIPAddress` InterfaceAlias Wi-Fi |
| process_count | 362 | `receipts/processes-20260903T0900Z.csv` |
| listen_count | 38 | `receipts/listen-20260903T0900Z.csv` |
| scheduled_task_count | 205 | `receipts/scheduled-tasks-20260903T0900Z.csv` |
| doctor_report_status | UNKNOWN | no `state/doctor/report.json`; see doctor table |
| queue_candidate | C | default-if-silent: Windows vault, 138/180 body not on this host |
| github_writes | none | this session |
| external_effects | none | this session |

## Listeners that matter (loopback)

Missing LAN ports are not evidence that a board API is absent.

| port | pid | command (secret names redacted) | source |
|---|---|---|---|
| 127.0.0.1:8771 | 22936 | `python -X utf8 organism.py` | Get-NetTCPConnection + Win32_Process |
| 127.0.0.1:8772 | 22584 | `python -X utf8 cortex/cortex.py` | same |
| 127.0.0.1:8773 | 11992 | `python -X utf8 live/server.py` | same |
| 127.0.0.1:8774 | 19176 | `python -X utf8 F:\backup\_ops\telegram_center\miniapp_gateway.py` | same |
| 127.0.0.1:8776 | 6912 | `python -X utf8 telegram_center\center.py` | 0912Z listen; was pid 25636 at 0900Z |
| 127.0.0.1:8777 | 22936 | same organism.py | same |
| 127.0.0.1:8791 | 2324 | `tools/buynsw-harvester/ingest_server.py --port 8791 --allow-no-auth` | same |
| 8792,8793,8794,8796 | — | not in Listen csv this session | `listen-20260903T0900Z.csv` |

Inference, not fact: 8791–8794/8796 as 138-leg tunnel is **unproven** on this host. 8791 here is a local harvester, not a proven 138 forward.

## Dirty classification (no revert)

Source: `receipts/dirty-classification-20260903T0905Z.csv`

| class | n | rule |
|---|---|---|
| GENERATED | 238 | `_ops/state`, `_memory`, CURRENT-TRUTH auto, neural/governor/pulse/cortex/doctor, hook-ledger, genome ledger |
| UNKNOWN | 182 | everything else, including `docs/`, `06-EVIDENCE/`, prior lane files |
| AGENT_CHANGE | 3 | this session paths matching HANDOFF pin / open prompt / this lane (count from porcelain snapshot; later writes are additional) |
| USER_CHANGE | 0 | none identified |

## Doctor freshness

Canonical `state/doctor/report.json`: **absent**. Status for S0: **UNKNOWN**.

| path | exists | mtime local | age_hours at 2026-09-03T19:02:18+10 | sha256 | producer | consumers |
|---|---|---|---|---|---|---|
| `state/doctor/report.json` | no | — | — | — | — | — |
| `_ops/state/doctor/self-knowledge-latest.json` | yes | 2026-09-03T18:43:26+10 | 0.315 | `16abc8a597947478afde06c937bb1b76978c0232866a7721c3f0cebccb71850e` | organism self-knowledge cache (file) | unverified |
| `_ops/state/doctor/box-latest.json` | yes | 2026-09-03T17:37:18+10 | 1.417 | `e08c39bfb11a710d537a39a7afac04a68c8ccdd2ffe51027c35cb9c8b502bdf1` | box/RFC tick (file) | unverified |
| `_ops/state/doctor/digest-nudge.json` | yes | 2026-09-03T15:32:01+10 | 3.505 | `1f71a9fd030c2f502a1b0e6f5fc5dafa1b1bb66af858d54d39cbf7cc840b0011` | digest nudge (file) | unverified |
| `_ops/state/doctor/poller-uniqueness-latest.json` | yes | 2026-09-03T18:43:26+10 | 0.315 | `9de07426513d4ae4caa5e7280a6953fd64314076d669758980962a2f0c54ebee` | `doctor_uniqueness_beat` (file) | center pid 25636 matches live center.py |
| `_ops/state/doctor/rfcs.json` | yes | 2026-09-03T17:37:10+10 | 1.419 | `680a60e492dae0bec0c8cce77e911bf444d5c35a5cd5b2ec18f02dec21e75b0f` | RFC store (file) | unverified |
| `OCTOPUS-DOCTOR/90-_meta/state/doctor-vitals.json` | yes | 2026-09-03T07:03:07+10 | 11.986 | `b6eedb1b0d89f7fa5f3c4bf6b01ca5db7d255d6ca32f9e0c4791848bccc2ac9c` | doctor-vitals.v1 | unverified |
| `06-EVIDENCE/OCTOPUS-DOCTOR-REFRESH-2026-08-23/doctor-report.json` | yes | 2026-08-23T13:25:29+10 | 269.614 | `7ea16c7ba5afc253c1614859250ad51f4e5171eac29bb1adc0328bef30b1db8d` | octopus.doctor-report.v1 | stale; `status: FAIL`; other host |

Contradiction kept open: `07-HANDOFF/contradictions.csv` row `L0-GIT-HEAD` still has `0f0e7f5` vs `bf88423`. This file adds a third measured HEAD `8d8be71f…`. `resolution: null`.

## Tests

See `receipts/test-matrix-20260903T0910Z.json`. `tests/test_repair_api.py` absent on this vault.
