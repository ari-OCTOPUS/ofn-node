---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-182, runtime, provenance]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/BOARD-180-REPLY-REPAIR-2026-08-27/settle-138/obs182_extract]]"
  - "[[06-EVIDENCE/OCTOPUS-HEALTH-WATCH-2026-08-28/09-32-182]]"
  - "[[06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28]]"
  - "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/11-MOSQUITTO-INCIDENT]]"
---

# 02 — Runtime provenance

```text
WITNESS_182_RUNTIME=NOT_OBSERVED
this_session_ssh=0
PROBE_RERUN=NO
observed_at=2026-08-29T05:30:00Z
method=prior_artifacts_only
scope=this_host_only
claim_type=documented_remote
```

This session did not SSH to 192.168.0.182. `~\.ssh\config` has no 182 Host (only `Host root` → 192.168.0.180). `known_hosts` lists 182 (host key not copied). Prior Phase 0 process probe spawned a transient mosquitto via PowerShell `|mosquitto|`. Runtime below is **stale documented**, not live.

## Why SSH was not used

| item | value | source | method | observed_at | scope | truth_status |
|---|---|---|---|---|---|---|
| Host 182 in ssh config | ABSENT | `C:\Users\Armin\.ssh\config` | file_read | 2026-08-29T05:30:00Z | this_host_only | REPO_VERIFIED |
| known_hosts 182 | PRESENT | `C:\Users\Armin\.ssh\known_hosts` | file_read | 2026-08-29T05:30:00Z | this_host_only | REPO_VERIFIED |
| prior SSH success | YES (other sessions) | L191; health 09-32-ssh; Phase 0 | docs | 2026-08-27..28 | documented_remote | DOCUMENTED |
| this session connect | 0 | this pack | no ssh.exe | 2026-08-29 | this_host_only | REPO_VERIFIED |
| pgrep / mosquitto this session | not invoked | this pack | policy | 2026-08-29 | this_host_only | DOCUMENTED |

## Mesh worker (documented)

| item | value | source | method | observed_at | scope | truth_status |
|---|---|---|---|---|---|---|
| unit | `octopus-witness-worker.service` | obs182_extract.json `timer` | JSON extract | 2026-08-27T02:30:47Z | documented_remote | DOCUMENTED |
| description | `Octopus witness worker (node 182, lab-witness, may_authorize=false)` | same + health 09-32-182:28 | artifact | 2026-08-27 | documented_remote | DOCUMENTED |
| ExecStart | `python3 /root/octopus-mesh/bin/octopus_witness_worker.py --root /root/octopus-mesh --once` | obs182_extract.json | artifact | 2026-08-27T02:30:47Z | documented_remote | DOCUMENTED |
| type | oneshot; dead between ticks | L191 §3.3; health 09-32-182b | artifact | 2026-08-27..28 | documented_remote | DOCUMENTED |
| timer 02:30Z extract | `OnBootSec=45s` `OnUnitActiveSec=45s` | obs182_extract.json | artifact | 2026-08-27T02:30:47Z | documented_remote | DOCUMENTED |
| timer L191 / health | ~3 min (e.g. 23:53 → 23:56) | L191:112; health 09-32-182:15 | artifact | 2026-08-27..28 | documented_remote | DOCUMENTED |
| timer interval now | UNKNOWN | this pack | no re-read | 2026-08-29 | this_host_only | UNKNOWN |
| mesh root | `/root/octopus-mesh` | obs182_extract.json | artifact | 2026-08-27T02:30:47Z | documented_remote | DOCUMENTED |
| inbox count 02:30Z | 254 | obs182_extract.json `tree.inbox` | artifact | 2026-08-27T02:30:47Z | documented_remote | DOCUMENTED |
| inbox/outbox L191 | 3507 / 831 | L191:114 | prior SSH | 2026-08-28T11:48-11:59Z | documented_remote | DOCUMENTED |
| current counts | UNKNOWN | this pack | no re-read | 2026-08-29 | this_host_only | UNKNOWN |
| writing `witness_response_*.json` | exists; **not** proof of 138 mint | L191:114 | forensic | 2026-08-28 | documented_remote | DOCUMENTED |
| sample inbox type | `verification_task` from 138, `may_authorize=false` | obs182_extract.json hits | artifact | 2026-08-27T01:52:35Z | documented_remote | DOCUMENTED |

## Sensorium plane (documented, other contract)

| item | value | source | method | observed_at | scope | truth_status |
|---|---|---|---|---|---|---|
| `octopus-sensorium.service` | active running (health 09-32) | 09-32-182b | prior SSH | 2026-08-27T23:54Z | documented_remote | DOCUMENTED |
| later health | NRestarts=31; doctor_latest MISSING | SUMMARY-18-32 | prior SSH | 2026-08-28 18:32 AEST | documented_remote | DOCUMENTED |
| NATS | 127.0.0.1:8222 and 192.168.0.182:4222 | L191:113 | prior SSH | 2026-08-28 | documented_remote | DOCUMENTED |
| MQTT | 127.0.0.1:1883 baseline pid **382176** | health 09-32-182; Phase 0 incident | prior SSH | 2026-08-27..28 | documented_remote | DOCUMENTED |
| metrics | 0.0.0.0:9101 | L191; health | prior SSH | 2026-08-28 | documented_remote | DOCUMENTED |
| WAVE0 | stay locked | health SUMMARY-18-32 | prior SSH | 2026-08-28 | documented_remote | DOCUMENTED |

LAN listen ≠ loopback API proof. Missing LAN ports ≠ absent loopback APIs (`claim_type=inference` if generalized).

## Phase 0 mosquitto incident (do not re-probe)

| item | value | source | method | observed_at | scope | truth_status |
|---|---|---|---|---|---|---|
| trigger | `pgrep -af` pattern containing `|mosquitto|` via PowerShell | Phase 0; P2 11 | documented | 2026-08-28T23:34:07Z | documented_remote | DOCUMENTED |
| temp PIDs | 552046 on `[::1]:1883`; 552041 companion | P2 11 | documented | same | documented_remote | DOCUMENTED |
| baseline | 382176 on `127.0.0.1:1883` remained | P2 11 | documented | same | documented_remote | DOCUMENTED |
| this session | no re-probe; `RUNTIME_CHANGES=0` | this pack | policy | 2026-08-29 | this_host_only | DOCUMENTED |

## Code snapshots on this vault (not live 182)

| file | what it is | source | method | observed_at | truth_status |
|---|---|---|---|---|---|
| `runtime-provenance-20260828T230743Z/witness_mint.p2.py` | 138 STRUCTURAL mint; writes JSONL; sends nothing | 138 snapshot | file_read | 2026-08-28 | REPO_VERIFIED |
| `runtime-provenance-20260828T230743Z/owner_decision.p2.py` | 12-field card; no send | 138 snapshot | file_read | 2026-08-28 | REPO_VERIFIED |
| `oracle-182/isolated-once/octopus_witness_worker.py` | isolated copy; `may_authorize=false`; inbox types only | 2026-08-27 copy | file_read | 2026-08-27 | DOCUMENTED |
| live 182 worker bytes now | UNKNOWN | this pack | no hash | 2026-08-29 | UNKNOWN |

```text
WITNESS_182_RUNTIME=NOT_OBSERVED
RUNTIME_CHANGES=0
TEMP_PROCESSES_STARTED=0
```
