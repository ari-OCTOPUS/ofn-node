---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [ops, migration, sequence, rollback, node-180]
author: "OCTOPUS ARCHITECT WORKSTATION — propose-only; nothing executed"
---

# Proposed migration sequence to 192.168.0.180 (NOT executed)

Status: **STOPPED awaiting owner confirmation.** No service moved. No task disabled. GITWRITE-FAILED not touched. `.180` not declared canonical.

Separate tracks (do not serialize as one unlock chain):

| Track | Owner | This inventory |
|---|---|---|
| A. Network / Wi-Fi / SSH / envelopes | other agent | **out of scope** |
| B. GITWRITE-FAILED / `--tags` reject | owner + git lane | **do not mix** |
| C. Canonical always-on move | owner Promotion Receipt then staged duties | **this document proposes C only** |

## YOU ARE HERE

```text
[x] S0  Inventory on DESKTOP-KA9RFN5 (this packet)
[ ] S0b Owner confirmation of inventory + first move
[ ] S1  Read-only replica of pulse/evidence on .180     PROPOSAL
[ ] S2  Still no writers on .180
[ ] …   Promotion Receipt (owner) — not designed here
[ ] Sn  Redesign then single-writer cutover
```

## Sequence (proposal)

### S0 — Inventory (done)

Deliverables in `06-EVIDENCE/*-2026-08-18.md` + Inbox launcher. Rollback: delete those notes if owner rejects (do not revert live services — none changed).

**ROLLBACK-POINT RP0:** current live pids/tasks as captured ~02:40 +10. Identity: 4d pid 24588, board-cp 26932, organism 7416, cortex 15368, live 19228, tg-center 27844, miniapp 22768.

### S1 — Read-only telemetry replica on `.180` (PROPOSED FIRST MOVE)

**What:** copy or pull **already-public-to-vault** pulse JSON / WAVE0 envelopes as **observe-only**. No NATS interconnect with `.182`. No git commit from `.180`. No board-cp bind. No Telegram poller. No TCB sign.

**Class used:** `CAN_REPLICATE_TO_180` (`pulse_telemetry`, optionally `handshake_sidecar` emit-on-demand).

**Why first:** lowest dual-write risk; does not require Promotion Receipt to *exist* as a candidate mirror; does **not** make `.180` canonical.

**ROLLBACK-POINT RP1:** delete the replica tree on `.180` only. Laptop writers unchanged. No flag files to restore.

**Do not include:** secrets, `.env`, TLS `key.pem`, signing private key, `commands.sqlite` as a second live queue.

### S2 — Explicit non-moves (until Promotion Receipt)

Keep on laptop (MUST_STAY or MUST_BE_REDESIGNED, not lifted):

- `germline-hourly` / `germline-daily` / `E:\germline`
- TCB generate/sign / `owner-verdicts.yaml` / flags.cmd SoT
- `4d_daemon`, `organism_loop`, `board_cp_tls`, `telegram_center`
- secrets files

**ROLLBACK-POINT RP2:** “did nothing” — if someone starts a writer on `.180` anyway: stop **that** writer; do not stop laptop; plant `BEAT-FREEZE.flag` on canonical host if a dual-beat is suspected (owner).

### S3 — Redesign gates (still proposal; after owner)

Required before any always-on **writer** on `.180`:

1. Promotion Receipt (canonical switch).
2. Armed beat lease with fencing token; FileLeaseStore stays local-disk; multi-host uses a **new** `continuity.*` bus — **not** joining Sensorium `octopus.*`.
3. Single command queue + single `:8801` (or successor) + board retarget/fingerprint.
4. Single Telegram poller cutover (token present on exactly one host).
5. Secret provisioning by owner (not agent copy).
6. TCB ceremony still defined (signer location explicit).

**ROLLBACK-POINT RP3:** unsigned TCB patches remain unapplied; previous `trust-boundary.json` + `.sig` pair; `daemon.stop` if a bad daemon start happens on laptop.

### S4 — Hypothetical cutover (not scheduled)

Owner freeze → vacate laptop beat → `.180` acquires lease → one health window → only then disable laptop watchdogs.

**ROLLBACK-POINT RP4:** `BEAT-FREEZE.flag` · re-enable laptop watchdogs · boards pinned back to laptop `:8801` · Telegram token only on laptop · git writers only on laptop.

This step is **not** authorized by this packet.

## ROLLBACK-POINTS (index)

| ID | When | Action | Must not |
|---|---|---|---|
| RP0 | now | live snapshot in matrix | stop/start anything “to prepare” |
| RP1 | after RO replica | delete `.180` mirror only | touch GITWRITE; retarget boards |
| RP2 | if illicit writer appears | stop the **new** writer | kill laptop organism “to force move” |
| RP3 | TCB/daemon | previous signed manifest; `daemon.stop` | copy private pem |
| RP4 | post-cutover (future) | freeze + laptop writers back | dual poller / dual hourly |
| RP-G | git | `E:\germline\hourly-latest.bundle` · `vault-latest.bundle` (stale daily) · git-serialize lock | delete GITWRITE-FAILED as rollback |
| RP-D | deploy snapshots | `_ops/deploy/rollback-from-snapshot.ps1` default **dry-run** | `-Apply` without owner |
| RP-P | processes | STOP-ORGANISM / STOP-TG-CENTER / STOP-CORTEX / STOP-LIVE / HALT-ALL / `daemon.stop` | watchdog fights a STOP |

## First move (single sentence)

**PROPOSAL:** replicate read-only pulse/evidence to `.180` (S1). Do not move daemons, git, TCB, secrets, board-cp, or Telegram.

## Explicit non-goals of this packet

- Did not migrate, failover, or declare `.180` canonical.
- Did not clear GITWRITE-FAILED.
- Did not edit TCB or flags.
- Did not SSH or switch Wi-Fi.
- Did not treat Stage 6–8 as proof.
