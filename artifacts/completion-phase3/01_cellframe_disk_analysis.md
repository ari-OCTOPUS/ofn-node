# Phase 3 P1 — Cellframe disk analysis (read-only)

PATH_REQUESTED: /opt/cellframe
PATH_FOUND: /opt/cellframe-node
PATH_MISSING: /opt/cellframe does not exist
MUTATIONS: none (no delete, compress, move, chmod, chown, service start/stop)

## What it is

Debian package `cellframe-node` 5.7-36 arm64. Ordinary directory on the root ext4 filesystem (`/dev/mmcblk0p1`), not a separate mount, not a git repository.

It is a Cellframe/DAP full node install:

- `bin/` native node binaries
- `etc/` config
- `python/` bundled CPython 3.10
- `share/` assets (diagtool unit symlink target missing)
- `var/` runtime state: chain cells, global MDBX, logs

Node process is **not running**. Pidfile `var/run/cellframe-node.pid` contains 617; `/proc/617` is dead. No open file descriptors from any process into `/opt/cellframe-node`. Ports 8079 / 8080 / 12345 not listening.

systemd:

- `cellframe-node.service` unit file **missing** (`not-found`); drop-in dir `/etc/systemd/system/cellframe-node.service.d/limits.conf` is an orphan
- `cellframe-diagtool.service` enabled but **bad/not-found** (symlink to missing `share/cellframe-diagtool.service`)
- no Docker container named cellframe

Last writes to the large state files: **2026-08-16** (about 9 days before this scan). Chain data is stale relative to a running node, but still local ledger state.

## Volume (du / find)

Total `/opt/cellframe-node`: 42737517412 B ≈ 39.8 GiB

| subtree | size | class |
| --- | --- | --- |
| var/lib/network/scorpion/main/0.dchaincell | 18977042230 B (~17.7 GiB) | CRITICAL_STATE_DO_NOT_DELETE |
| var/lib/network/kelvpn/main/0.dchaincell | 16305613992 B (~15.2 GiB) | CRITICAL_STATE_DO_NOT_DELETE |
| var/lib/network/scorpion/zerochain/0.dchaincell | 3466955848 B (~3.2 GiB) | CRITICAL_STATE_DO_NOT_DELETE |
| var/lib/network/scorpion/zerochain/0.dchaincell.unsorted | 3466922382 B (~3.2 GiB) | BACKUP_REQUIRED_BEFORE_DELETE |
| var/lib/network/kelvpn/zerochain/0.dchaincell | 121943466 B (~116 MiB) | CRITICAL_STATE_DO_NOT_DELETE |
| var/lib/global_db/gdb-mdbx/mdbx.dat | 184549376 B (~176 MiB) | CRITICAL_STATE_DO_NOT_DELETE |
| var/log/cellframe-node.log | 128349603 B (~122 MiB) | STALE_LOG_CANDIDATE |
| python/ (stdlib + libpython) | ~70 MiB | SOURCE_DO_NOT_DELETE |
| bin/ cellframe-node{,-cli,-tool,-config} | ~17 MiB | SOURCE_DO_NOT_DELETE |
| etc/ | ~452 KiB | SOURCE_DO_NOT_DELETE |
| share/ | ~420 KiB | SOURCE_DO_NOT_DELETE |
| var/lib/wallet/ | empty dir | CRITICAL_STATE_DO_NOT_DELETE (wallet path) |
| var/lib/ca/node-addr.dcert | 4097 B | CRITICAL_STATE_DO_NOT_DELETE |
| var/run/ | pidfile only | ACTIVE_RUNTIME_DO_NOT_TOUCH (stale pid) |

`var/lib/network` contains 5 files, 4 `*.dchaincell` + 1 `*.unsorted`. Not a source tree. This is chain cell data.

Symlinks: only python `libpython3.10.so` → `libpython3.10.so.1.0` inside the install. No bind-mounts.

## Source vs state vs rebuildable

- **Source / install:** `bin/`, `etc/`, `python/`, `share/`. Reinstallable via the `cellframe-node` package, but not OCTOPUS-owned. Do not delete to "save the board" without owner.
- **Non-reconstructible local state:** `var/lib/network/**/*.dchaincell`, `var/lib/global_db/**`, `var/lib/ca/node-addr.dcert`, wallets path (empty but designated). Re-downloading a chain is possible in theory from the network if the node is later started; that is **not** a local reconstruction and can take tens of GiB and days. Treat as CRITICAL.
- **Maybe leftover:** `0.dchaincell.unsorted` (~3.2 GiB) looks like an incomplete/sort buffer. Still BACKUP_REQUIRED; deleting it while a node is off may or may not be safe. Unknown without Cellframe docs/owner.
- **Rebuildable-ish:** `var/log/cellframe-node.log` (~122 MiB), last write 2026-08-16, no process holding it. STALE_LOG_CANDIDATE. Truncating still needs Owner Gate.
- **Not a compiler build tree.** No `REBUILDABLE_BUILD_CANDIDATE` except bundled pip wheels inside python/ensurepip (tiny vs 40G).

## What deleting each class would break

- Delete `var/lib/network`: local KelVPN + Scorpion chain history gone; node would have to resync from network if ever started.
- Delete `global_db`: node global DB / MDBX state gone.
- Delete `bin`/`python`/`etc`: package install broken; `dpkg` would report missing files; node cannot start.
- Delete log: observability only; node can start without it.
- Delete `.unsorted`: unknown; could be redundant or an incomplete cell.

## Safe reclaim estimate (analysis only, not executed)

| option | reclaim | risk |
| --- | --- | --- |
| truncate/rotate `var/log/cellframe-node.log` | ~122 MiB | low if node stays stopped |
| delete `.unsorted` after backup | ~3.2 GiB | medium/unknown |
| uninstall node + delete var | ~40 GiB | high: irreversible local chain |
| do nothing | 0 | none |

Honest **safe** reclaim without owner: **0 bytes**. Lowest-risk Owner Gate option is log rotation (~122 MiB), which does **not** move the disk off 89%.

Cellframe is independent of OCTOPUS. No octopus unit opens these files.

See `01_cellframe_inventory.csv` and `gates/GATE-CELLFRAME-DISK-CLEANUP.json`.
