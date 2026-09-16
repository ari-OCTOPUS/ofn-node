---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [ops, blockers, migration, node-180]
author: "OCTOPUS ARCHITECT WORKSTATION — staged-migration inventory (propose-only)"
---

# Hard blockers — moving always-on duties to 192.168.0.180

Captured 2026-08-18 ~02:40 +10 on `DESKTOP-KA9RFN5`. **Propose-only.** No blocker was “cleared” by this pass.

Network repair and canonical migration are **separate**. Fixing Wi-Fi/SSH does **not** promote `.180`. Clearing GITWRITE (owner, later) does **not** promote `.180`. A Promotion Receipt is the only canonical switch.

## Binding constraints (not negotiable in this inventory)

- Until Promotion Receipt: `F:\backup` + `E:\germline` canonical; `.180` = continuity-candidate only.
- Stage 6–8 ≠ production/pilot proof.
- GITWRITE-FAILED stays until live hourly path is green (owner/other lane).
- Do not mix “network up” with “canonical moved”.

## Blockers

### B1 — No Promotion Receipt

`.180` is not canonical. Any always-on writer moved there without a receipt is a second source of truth.

**Evidence:** mission binding + HANDOFF pins still treat `F:\backup` as live tree.

**Unblocks:** owner Promotion Receipt ceremony — **not** this inventory.

### B2 — Canonical git and offbox germ line are this PC

Hourly/daily jobs write `F:\backup\.git` and `E:\germline\vault.git` / bundles. `E:` is a local volume on the laptop, not `.180`.

**Evidence:** tasks `germline-hourly` / `germline-daily`; scripts under `04 - Architect System\scripts\`; `E:\germline` listing; `git-serialize.ps1` lock on `_ops\backup\gitwrite.lock`.

**Unblocks:** new offbox + single-writer git design after Promotion Receipt. **Not** “rsync the repo to `.180` and keep pushing from both”.

### B3 — GITWRITE-FAILED and hourly `--tags` (separate incident)

Flag exists (`_ops/backup/GITWRITE-FAILED.flag`, mtime 2026-08-16 03:50:24). Hourly still logs `PUSH-FAIL` / bundle-fallback. `--all` can be green while `--tags` rejects `pre-deploy-2026-07-25`. Task LastResult 0 because throttled failure is logged as OK.

**Evidence:** flag file; `E:\germline\hourly.log`; `06-EVIDENCE/HOURLY-PUSH-EMPTY-ERR-2026-08-18.md`.

**Unblocks:** owner decision on that tag (skip / replace). **Does not** unblock `.180`. **Must not** be deleted to make a migration look clean.

### B4 — TCB signing is laptop-owner-bound

Private key is in the owner Windows profile. Manifest + sig live in `4d_system/config/`. Daemon runs with `OCTOPUS_TCB_MANIFEST_ENFORCE=1`. Unsigned TCB patches (EQUIP G2, JOB-RESEARCH) are already queued for a **laptop** ceremony.

**Evidence:** `Test-Path` on private pem; `generate_trust_boundary.py` openssl command; live daemon kernel.integrity_ok true.

**Unblocks:** owner ceremony on the canonical signer. Copying the private key to `.180` is forbidden in this mission.

### B5 — Secrets SoT cannot be agent-copied

Bearer, bot tokens, LLM keys, TLS key, Cloudflare tunnel json, Gmail app password all live on this host.

**Evidence:** secret-inventory names/paths companion.

**Unblocks:** owner-controlled provisioning. Dual presence of `TG_CENTER_BOT_TOKEN` = Telegram 409.

### B6 — Beat lease unarmed; FileLeaseStore forbids SMB

Always-on on `.180` while organism/4d still beat on the laptop = two writers. The fencing module exists but is **not** imported by organism/chrono. NATS KV backend needs a bus that **does not exist on the laptop** and must **not** be Sensorium `octopus.*`.

**Evidence:** `_ops/runtime/beat_lease.py` docstring; no nats process/port on laptop; charter: no `.182`↔`.180` interconnect.

**Unblocks:** redesign (armed lease + continuity bus + freeze file) **after** owner. Not a config flip.

### B7 — board-cp command authority is this listener + this sqlite

`:8801` TLS on `0.0.0.0`, flag on, queue `_ops/state/board_cp/commands.sqlite`. Boards pull **this** host (file evidence). A second listener on `.180` without a single queue and a board retarget is dual-dispatch.

**Evidence:** pid 26932 listen 8801; sqlite mtime; `board_cp/server.py` routes only pull/ack.

**Unblocks:** redesigned single command plane + board pin/fingerprint change (owner).

### B8 — Telegram center is a single poller

`center.py` WORKLOCK + watchdog restarts by pulse. Two hosts with one token is a known 409 failure mode.

**Evidence:** live pid 27844; `tg-center-watchdog.ps1` comments; token **names** in `.env`.

**Unblocks:** one consumer globally; move = cutover, not replicate.

### B9 — D13 vs current writers (architecture, not a network bug)

Owner doctrine: boards 24/7; laptop intermittent. **Today** the always-on writers (organism, 4d daemon, hourly git, board-cp, Telegram) still run **on the laptop**. That gap is exactly why a staged inventory exists — it is **not** solved by switching Wi-Fi.

**Evidence:** Inbox D13 doctrine vs this process snapshot.

**Unblocks:** redesign + Promotion Receipt. Not B3, not the other agent’s SSH lane.

### B10 — Desktop NBB observatory is outside the vault SoT

Two scheduled tasks run `run_observatory.py` from `C:\Users\Armin\Desktop\OCTOPUS-NBB-CP-WORKING\nbb-control-plane` while vault also contains `4d_system/src/nbb_cp`. FastAPI in-tree is **not** live.

**Evidence:** Get-ScheduledTask Actions + cwd; no FastAPI process.

**Unblocks:** pick one NBB-CP SoT; do not copy Desktop tree to `.180` as “the” control plane.

### B11 — germline-daily already failing; bundle stale

Daily LastResult **1**. `vault-latest.bundle` mtime 2026-08-07. Offbox restore-drill is not currently green.

**Evidence:** scheduled task info; `E:\germline` listing.

**Unblocks:** fix daily on **this** host. Unrelated to `.180` promotion.

## Top 5 (for parent summary)

1. **B1** No Promotion Receipt (`.180` not canonical).
2. **B2** Git/vault/`E:\germline` physically bound to this PC.
3. **B4+B5** TCB private key + secrets SoT must not be copied.
4. **B6+B7** Unarmed beat lease + board-cp single queue — lift-and-shift = split brain.
5. **B3** GITWRITE/hourly tags — **separate** incident; must not be bundled as a migration prerequisite or as a reason to move.

## What is **not** a hard blocker for a later RO replica

- Absence of NATS on the laptop (honest: bus is on `.182`, disjoint).
- Handshake sidecar not running (it is not the daemon).
- Ollama being local (CAN_MOVE as inference **proposal**).
- Pulse JSON being readable (CAN_REPLICATE).
