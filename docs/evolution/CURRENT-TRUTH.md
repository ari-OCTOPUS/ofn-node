# CURRENT-TRUTH — BOARD 180

vantage: local-disk + loopback | node_id: 180 | asserted_ip: 192.168.0.180
machine_id_short: bb41a9407b4f | verified_by: `ip -o -4 addr show eth0`
generated_at (UTC): 2026-08-26T11:5xZ (anatomy read-only pass)
scope default: this_host_only. system_wide claims need a second node_id.

## زندهٔ تأییدشده (LIVE_VERIFIED, this_host_only)
| claim | value | source | method |
|---|---|---|---|
| identity | eth0=192.168.0.180, host=octopus-continuity-180, user=root | eth0 | `ip -o -4 addr show eth0` |
| OS/arch | Debian 13 trixie, aarch64, kernel 6.1.115-vendor-rk35xx | uname/os-release | read |
| RAM | 3.8Gi total, ~2.1Gi available, swap 4Gi (~2Mi used) | free -h | read |
| disk / | 58G total, 49G used, 6.2G free, **89% (>80% threshold)** | df -h | read |
| soc temp | 27.8C | thermal_zone | read |
| failed units | 0 | systemctl --failed | read |
| organism db | events=1394 (growing), outbox=1394, identity_ledger=529, 21 tables | organism.db (ro) | sqlite read |
| tests (organism) | 145 passed, 1 skipped | ofn/organism/tests | `python3 -m unittest` clean env |
| lab git | branch feat/phase3-completion @ 747c373, NO REMOTE, 84 untracked (additive) | git | read |
| ofn-l4 git | branch master @ 08f9155, no remote | git | read |
| runtime↔code | app.py mtime 2026-08-25T13:09Z < proc start 13:17Z → loaded == on-disk (not diverged) | proc/stat | read |

## سرویس‌های زنده (this_host_only)
| service | bind | note |
|---|---|---|
| octopus-gateway | 0.0.0.0:8780 | L0 read-only FastAPI (app.py: no command surface) |
| octopus-organism-lab | 127.0.0.1:8090 AND 192.168.0.180:8090 | dual-bind; LAN path guarded by OCTOPUS_REQUIRE_LAN_TOKEN |
| octopus-llama-lab | 127.0.0.1:8081 | local cortex |
| dropbear / sshd | 0.0.0.0:22 / 0.0.0.0:2222 | two SSH servers |
| octopus-heartbeat | (activating) | ICMP observe |
| octopus-mirror | dead/inactive | one-way pull, idle |

## DOCUMENTED / STALE / HYPOTHESIS (NOT live-verified on 180)
- test counts 634 / 1938 — DOCUMENTED (other tree/branch, not this run; this run = 145).
- gates dated 2026-08-10 — STALE/expired.
- OFN_WIRE_OUTBOUND=1 — DOCUMENTED, not enabled here (organism env OCTOPUS_LEARN_EXTERNAL=0).
- miner_isolation — HYPOTHESIS.
- approx SHAs 388594e / 32a81d0 — DOCUMENTED, not HEAD here (HEAD=747c373).
- historical branches main, ofn/board-snapshot-20260816, ofn/heartbeat, ofn/wire, ofn-v1.0-three-business-owner-center — NOT present on 180 (only archive/board-life-001-50f31db, experiment/board-life-001, feat/phase3-completion).
- Cycle 1 score=1.0 — DOCUMENTED (138 calculation; not independently recomputed by 180).

## body_not_on_this_host (نه body_missing)
- ofn/config.py (gate/secret_rotation config), ofn/node.py, packs/lead.yaml, adapters/outbox.py — absent on 180 lab tree. Only ofn-l4/ofnl4/config.py exists here. Revenue pipeline body lives on 138 per arbiter; 180 has the organism + continuity gateway, not the lead pipeline.
