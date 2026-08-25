# Phase 3 LIVE BASELINE (official)

SCAN_UTC: 2026-08-25T11:08:32Z
LIVE_PROCESS_PID: 12748
LIVE_PROCESS_STARTED_AT: 2026-08-25T08:52:03Z
LIVE_HEALTH: STABLE
LIVE_AUTONOMY: PROPOSE_ONLY
LIVE_HEARTBEAT_INTERVAL_META: 240
LIVE_HEARTBEAT_INTERVAL_CMDLINE: 180
SOURCE_RUNTIME_MATCH: false
MANDATORY_MEMORY_READ_LIVE: false
OFN_L4_RUNNING: false
GPU_PRESENT: false
VLLM_PRESENT: false
NEW_SKIN_DEPLOYED: false

This file is the Phase 3 live baseline. It is measured evidence, not a tour.

## Disk / memory / thermal

Command: `df -B1 /` and `/proc/meminfo`, `thermal_zone0`.

- filesystem: `/dev/mmcblk0p1` ext4 on `/`
- total_bytes: 61326831616
- used_bytes: 51776450560
- available_bytes: 7021752320 (~6.54 GiB)
- use_percent: 89
- MemTotal_kB: 4004732
- MemAvailable_kB: 2220608
- soc_temp_mC: 29615
- loadavg: 0.27 0.21 0.15
- `/opt/octopus` bytes: 832568346 (~794 MiB du -sb; ~819 MiB du -xh)
- `/opt/cellframe-node` bytes: 42737517412 (~40 GiB)
- `/opt/cellframe` path: DOES_NOT_EXIST (real tree is `/opt/cellframe-node`)

Halt rule: available < 5 GiB OR use >= 92%. Halt not triggered.

## Live process (no env dump)

PID 12748 alive. cwd `/opt/octopus/lab`. exe `/usr/bin/python3.13`. rss 65264 kB.

cmdline:

`python3 -m ofn.organism.runtime.app --db /opt/octopus/lab/lab-data/organism.db --host 127.0.0.1 --port 8090 --heartbeat-interval 180 --pid-file /opt/octopus/lab/receipts/organism.pid`

systemd `octopus-organism-lab.service`: ActiveState=active SubState=running MainPID=12748 NRestarts=0 ExecMainStartTimestamp=Tue 2026-08-25 08:52:03 UTC

Source files `db.py` mtime 10:52Z and `wan.py` mtime 08:59Z are newer than process start. Live SQLite has no `wan_fetches` and no `memory_read_receipts`.

## Other units (NRestarts=0)

| unit | pid | started UTC | listen |
| --- | --- | --- | --- |
| octopus-llama-lab | 527 | 05:30:08 | 127.0.0.1:8081 |
| octopus-organism-lab | 12748 | 08:52:03 | 127.0.0.1:8090 and 192.168.0.180:8090 |
| octopus-soak-lab | 4235 | 06:49:18 | none |
| octopus-afferent-lab | 4218 | 06:49:16 | none |
| octopus-gateway | 641 | 05:30:09 | 0.0.0.0:8780 |

No listener on :8091 (OFN-L4 not running). Cellframe listen ports 8079/8080/12345: not listening.

## Listening ports (ss -lntp) organism-relevant

- 192.168.0.180:8090 python3 pid 12748
- 127.0.0.1:8090 python3 pid 12748
- 127.0.0.1:8081 llama-server.f280b26 pid 527
- 0.0.0.0:8780 uvicorn pid 641
- 0.0.0.0:22 dropbear; 0.0.0.0:2222 sshd
- 127.0.0.1 node/cursor and containerd (not organism)

## Source hashes on disk at baseline

| path | sha256 | mtime UTC | bytes |
| --- | --- | --- | --- |
| ofn/organism/__init__.py | 1bd50fb91c5e534cbf558fd3d30e9bda9d994fbc8d201fbf27c9c4fabed2bfae | 2026-08-25T08:48:31Z | 53 |
| ofn/organism/persistence/db.py | e4f9d1da428d6a3fd4f3c664ce09282a3dce83826f91e9c6f2605d2193c45509 | 2026-08-25T10:52:25Z | 6869 |
| ofn/organism/cognition/wan.py | ae6fcc383bd450510d9090d3e7d8fc9630a986933cfab995f6fe96d2619e9acb | 2026-08-25T08:59:23Z | 13364 |
| ofn/organism/cognition/backend.py | d3a2867f2b8f7fef434c81275496c4470073c19c44469ee30fcede8d60e54ec0 | 2026-08-25T10:53:18Z | 18051 |
| ofn/organism/runtime/app.py | 48ea7a614bdd00725565424e7f06d28ed8f9a1b7bb30bf5c54d7826238f67db3 | 2026-08-25T10:53:51Z | 26290 |
| ofn/organism/runtime/life_cycle.py | 72988a7a08a08a99712e542a89f1f134edadfa39df7ae3ef053d4bbba2177462 | 2026-08-25T10:54:01Z | 14111 |
| ofn/organism/memory/gate.py | aa935cc85f8a6af98b92cfafe3c11664da943c9dee0c076ed1433242f1f8b5b7 | 2026-08-25T10:51:56Z | 7721 |
| ofn/organism/school/curriculum.py | 3f01ba304461cfb7f6e30b8135232399b70840098bda8420d1eb535782cb1273 | 2026-08-25T10:53:31Z | 6332 |
| ofn/organism/cognition/active_inference.py | 8e305ee8018a8cabac80030b96a6c52f29c12bd564bb8116ec3c4177cd2b7fed | 2026-08-25T10:52:14Z | 3461 |
| ofn/organism/science/wbe_allometry.py | 536b1c897a8cd633ed44419267298950ef4bce0ee6fa7e37967fbf804081df83 | 2026-08-25T10:52:11Z | 1717 |
| bin/start-organism.sh | 64bcfc0f84d2485e94e67d794631414a03a8252f4b859a739001f6db17caf272 | 2026-08-25T08:48:35Z | 1264 |

Git at scan: branch `feat/phase3-completion` HEAD `539d2960f67482653d2c77c98f402c6d96765cb1`

## SQLite live (read-only URI, query_only=ON)

- organism.db 1056768 B mode 0644 mtime 10:44:52Z
- organism.db-wal 4120032 B mode 0644 mtime 11:07:55Z
- organism.db-shm 32768 B
- journal_mode=wal integrity_check=ok quick_check=ok
- tables=18 (no wan_fetches, no memory_read_receipts)

Counts at 11:08Z (WAL included via live RO connection):

| table | count |
| --- | --- |
| events | 371 |
| episodes | 371 |
| outbox | 371 |
| identity_ledger | 210 |
| identity_heartbeat | 173 |
| inner_speech | 52 |
| utterances | 29 |
| self_models | 63 |
| school_courses | 10 |
| futures | 9 |
| learned_topics | 4 |
| ask_cache | 6 |
| world_hosts | 3 |
| growth_habits | 5 |
| lessons | 9 |
| exams | 10 |
| meta | 19 |

Note: operator snapshot earlier in chat used events=367 / identity=209. The live organism continued ticking; baseline uses the later measured counts.

## Identity head

Independent verifier `bin/verify-identity-chain.py`:

- valid: true
- entries: 210
- first_hash: `21cd26ba968b5ea358bfd2393ed740592e35428c22a167fe091598552ca82f7e`
- last_hash: `606c577d7762f3af5aabbd7fb2ad4495f58b38678d5a6fe24db2eb195235e2b7`
- genesis event_type: chain_genesis
- head event_type: identity_heartbeat
- verification_scope: INTERNAL_HASH_CHAIN_CONSISTENCY
- external_anchor: null

Public status `identity_chain_valid=true` matches verifier.

## Soak

`/opt/octopus/lab/evidence/SOAK-RESULTS.json`:

- running: true
- abort: null
- samples: 260
- age_seconds: 15577
- last health HTTP 200, organism HTTP 200 (existing soak; this mission did not GET 8090)
- last llama_pid: 527
- last mem_avail_kB: 2192684
- last temp_mC: 28692

## LIFE.json / public at baseline

- given_name: بچه-برد
- developmental_stage: MATURE
- health_state: STABLE
- autonomy_state: PROPOSE_ONLY
- school_passed: true
- external_api: LEARN_ONLY_DEEPSEEK
- first_stage_label: OWNER_ALIVE_C
- llama_health / local_cortex: AVAILABLE
- microphone: ES8323_CAPTURE
- season_city: Sydney OWNER_STATED

## Dependencies absent

nvidia-smi absent. vllm absent. cbor2 absent. pymdp absent.

## What this baseline forbids

Do not treat this scan as authorization to restart PID 12748, migrate live SQLite, delete Cellframe, or bind OFN-L4.
