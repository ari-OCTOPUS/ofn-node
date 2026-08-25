# Phase 3 P6 — Live skin replacement package (DO NOT EXECUTE)

LIVE_SKIN_REPLACED: false
GATE: GATE-LIVE-SKIN-REPLACEMENT execute=false

## Package identity

- lab git: branch `feat/phase3-completion` (see 03_git_reproducibility.md after commit)
- OFN-L4 git: `/opt/octopus/ofn-l4` independent, not deployed
- dependency: CPython 3.13 stdlib + existing llama-server on 127.0.0.1:8081
- no pip install, no cbor2, no pymdp, no vllm

## Config diff vs live PID 12748

Live cmdline heartbeat 180; meta interval already 240. New source does not change systemd ExecStart except owner may add:

`Environment=OCTOPUS_ALLOW_LIVE_SCHEMA=1`

Required for first start after this skin because `db.connect()` blocks `/opt/octopus/lab/lab-data/organism.db` otherwise.

Do **not** set `OCTOPUS_GET_PURE=1` or `OCTOPUS_REQUIRE_LAN_TOKEN=1` on first restart (soak GETs 8090; token would 401).

## Preflight (must all be true)

- df available > 5 GiB and use% < 92
- soak abort is null
- llama pid 527 or successor healthy
- identity verifier valid on RO db
- backup receipt integrity ok
- `OCTOPUS_ALLOW_LIVE_SCHEMA=1` explicitly approved

## Commands (not run)

Backup:

```
python3 -c 'import sqlite3,os,time; src=sqlite3.connect("file:/opt/octopus/lab/lab-data/organism.db?mode=ro", uri=True); src.execute("PRAGMA query_only=ON"); dst=sqlite3.connect("/opt/octopus/lab/lab-data/backups/pre-skin.db"); src.backup(dst, pages=32, sleep=0.25)'
```

Migration is implicit in connect() after env is set. Rehearse first on a copy, never by pointing tests at live db.

Stop:

```
systemctl stop octopus-organism-lab.service
```

Do not stop llama, soak, afferent, gateway unless soak cannot tolerate organism down. Soak will see organism HTTP fail; abort rule is service_down_streak>=5. Keep downtime short.

Start:

```
systemctl start octopus-organism-lab.service
```

Expected downtime: 3–20s (TimeoutStopSec=20).

Health verification (after start, still owner):

- `systemctl is-active octopus-organism-lab`
- new MainPID != 12748
- `python3 bin/verify-identity-chain.py --db /opt/octopus/lab/lab-data/organism.db`
- RO check: `memory_read_receipts` table exists
- soak abort still null
- do not GET 8090 from a test harness that cannot tolerate snapshot side effects unless soak already does

Memory-gate verification: tempfile tests already passed; live proof is receipts appearing after first tick, `future_use_count=0`.

Soak continuation: leave `octopus-soak-lab` running across the restart.

Rollback:

```
systemctl stop octopus-organism-lab.service
git -C /opt/octopus/lab checkout 50f31db -- ofn/organism
# or checkout archive/board-life-001-50f31db tree for organism package only — prefer tagged copy
systemctl start octopus-organism-lab.service
```

Abort conditions: disk halt, identity invalid, llama down, connect() exception, soak abort set, unexpected WAN traffic.

OFN-L4 is not part of this replacement.
