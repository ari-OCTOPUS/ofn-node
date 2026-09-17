# GAP-02 — Root-Cause Pack (node 182, witness)
**Lane:** S1-PROOF-OF-LIFE-20260917 · **Date:** 2026-09-17 · **GOV_VERSION=V8 · LADDER=L2**
**Receipt:** `S1POL-GAP02-182-20260917T072442Z-9d11b7dd9d3a` (INTENT/RESULT, Tier=Class-B pattern per owner Tier ruling)

## 1. Symptom (measured)
- Fleet heartbeat (`06-EVIDENCE/FLEET-HEARTBEAT-CANONICAL.md`): 182 `load1=3.5–3.6` sustained all day 2026-09-17 (all other nodes ≤0.1). 8 cores.
- Live probe 07:07Z: `octopus-sensorium.service` PID 6088 at **91.5% CPU lifetime** (2926 min CPU since Sep 15), RSS 1.9 GB; plus `apply_signed_inbound.py checkpoint` + `registry` each at **100% CPU**, new PIDs every ~60–90 s.
- PSI cpu: `some avg300=28.69%`. Temps 46–51 °C (not thermal). Swap 831M/2G used, mem 2.4/3.8 Gi.

## 2. Mechanism (the harvest's «حلقهٔ PathExists», confirmed from source)
1. `/etc/systemd/system/octopus-apply-checkpoint.path` watches `PathExists=/var/lib/octopus/inbound/SIGNED-CHECKPOINT-BUNDLE/checkpoint.json.sig`; `octopus-apply-registry.path` watches `.../SIGNED-REGISTRY-BUNDLE/registry.yaml.sig`.
2. Stale signed bundles sat in inbound since **Aug 17 11:33 (registry)** and **Aug 22 11:54 (checkpoint)** — classified long ago (registry=`already_live`, checkpoint=`DUPLICATE_STALE` class) but **never consumed**.
3. systemd `.path` units are level-triggered for `PathExists`: after each triggered service exit, the still-existing `.sig` re-fires the service. `NRestarts=0` yet `ExecMainStartTimestamp` advanced every ~minute → infinite respawn loop.
4. Each run costs real CPU: `export_checkpoint()` + `verify_chain()` over the 107 MB audit chain (`verify_chain` alone measured **3.8 s**), ×2 services continuously = the «≈۲ هسته» of GAP-02.

## 3. Fix (minimal, verify-logic untouched)
- `apply_signed_inbound.py` patched: new `_consume_bundle()` moves a processed bundle (only when its `.sig` exists) to `/var/lib/octopus/state/inbound-apply/consumed/<name>-<stamp>-<reason>/`. **Move-only, never delete**; reversal = move back.
- Verification/classification code paths unchanged. No secrets touched. Not hash-pinned anywhere (`grep -ri apply_signed /etc/octopus/config/` = 0 hits).
- Hashes: orig `642f048c56de…` → patched `4ea22df22a7b…` (identical on laptop copy and node). Node backup: `/opt/octopus/scripts/apply_signed_inbound.py.bak-gap02-20260917T0720Z`.
- Stale bundles consumed **by the patched service instances themselves** (real trigger path): registry @07:18:36Z, checkpoint @07:18:56Z. Manual `all` run afterwards returned correct steady-state (`incomplete_bundle` / `AWAITING_OWNER_SIGNATURE`, `consumed_bundles: []`).
- Path units restarted 07:22:18Z.

## 4. Result (verified 07:24:41Z, +6 min window)
- `ExecMainStartTimestamp` frozen at 07:18:32/41 — **zero respawns**; no apply processes.
- `consumed/` holds exactly the two archived bundles.
- Load: **3.50 → 2.02 (1-min)** and falling; remaining ≈1 core = GAP-02b.

## 5. Follow-ups registered (NOT fixed this session)
- **GAP-02b — sensorium design cost:** single thread, instant ~50% (lifetime avg 91.5%); 123 plugins × 5 s tick, hash-chained fsync per observation (~0.9 events/s measured). RSS **1.9 GB > unit `MemoryMax=1200M`** (running instance predates the limit → **any restart risks OOM loop**; `octopus-gap001-boot-probe` already oom-killed Sep 15, peak 2G). Unbounded growth: `derived.jsonl` 1.03 GB, `events.jsonl` 445 MB (seq 3,077,8xx), 1210 snapshot files, `RETENTION_SECONDS` defined but **no pruning wired**. Needs a dedicated lane (index pruning + restart-under-quota drill) before any sensorium restart.
- **GAP-02c — verifier G13 replay divergence:** `verify_sensorium.py` (first run since Aug 17) → `readiness=UNVERIFIED, gates_failed=[G13]`, detail `from_empty=sha256:56263b55… ≠ from_snapshot=sha256:8c39115a… (n=3,077,923)`. **Pre-existing, unrelated to the apply patch** (patch touches bundle consumption only). Needs journal forensics.
- Failed units on 182 (pre-existing, informational): `octopus-gap001-boot-probe.service` (oom-kill), `octopus-miniscientist-daily.service`.

## 6. Rollback
`cp -a /opt/octopus/scripts/apply_signed_inbound.py.bak-gap02-20260917T0720Z /opt/octopus/scripts/apply_signed_inbound.py && mv /var/lib/octopus/state/inbound-apply/consumed/SIGNED-*-BUNDLE-* /var/lib/octopus/inbound/ && systemctl restart octopus-apply-checkpoint.path octopus-apply-registry.path`
⚠ Rollback re-opens the infinite loop by design (the stale bundles are what fed it).

## 7. Files
- `apply_signed_inbound.py.orig` / `.patched` — byte-exact pre/post images (hashes above)
- `postfix-verification.txt` — live post-fix probe transcript

## VERDICT CORRECTIONS v2 — owner review accepted (2026-09-17, ~07:3xZ)

**This section supersedes the status vocabulary of the v1 report above; v1 text kept intact per append-only rule.**

### Canonical statuses (owner table, verbatim)
- S1-GAP-02A (apply loop on 182) = **CLOSED-PROVISIONAL** — was reported as "GAP-02 CLOSED"
- S1-GAP-02B (sensorium cost) = **OPEN-CRITICAL**
- S1-GAP-02C (G13 replay divergence) = **OPEN-INTEGRITY**
- swap 138 = **INSTALLED-NOT-DRILLED**
- money mirror 138→182 = was OPEN-WEEK1 → **BUILT + LIVE this session** (below)
- season S1 = ACTIVE

### ID canonicalization (done)
`GAP-02` collided with canonical `GAP-002` (outbox-180 TTL). Records appended to `F:/ofn-node/ops/GAP-LEDGER.jsonl` (commit 31a3aca7): one `alias_supersede` (GAP-02 → S1-GAP-02A/B/C, old id NOT deleted) + three `gap_row`s with the statuses above.

### Mission boundary correction (accepted)
This lane is an **independent mutation lane under owner authorization** (season charter + this review), NOT Tier1/ClassA/STRICT_READ_ONLY. The Harvest lane remains read-only; all receipts of this session (S1POL-*) belong to lane S1-PROOF-OF-LIFE only.

### MemoryMax claim — corrected by cgroup measurement (the review was right to challenge it)
- v1 claim "RSS 1.9G > MemoryMax=1200M" was wrong: the base unit file says 1200M but two owner-approved drop-ins escalate it — 60-chg-yellow (1536M, 2026-08-22) and 70-oom-headroom (**2048M**, 2026-08-27 "GO ari"). My earlier `systemctl cat | head` truncated the drop-ins.
- Live cgroup: `memory.current=2.0Gi`, `memory.peak=2.0Gi`, `memory.max=2.0Gi(2048M)`, `memory.swap.current=569M`, `memory.events: max=40,752,813, oom_kill=0`.
- Correct statement: the unit is **pinned at its 2048M ceiling** (40.7M max-events = chronic reclaim), not above it. No restart risk from cap mismatch per se; the real S1-GAP-02B problem is unbounded index growth + ~1 core design cost. Blind restart stance unchanged: no.

### Final-closure witnesses for S1-GAP-02A (registered, per review)
1. 24h frozen-window check (activation timestamps + zero procs) — scheduled (automation, t0=2026-09-17T07:18Z).
2. Artificial signed fixture test (exactly-one activation → classify → consumed → no reprocess).
3. Crash-boundary test (interrupt between classification and receipt; next run loses no bundle, re-applies no effect).
4. Archive-growth test (consumed/ not watched by any .path; retention defined).
Load drop alone is explicitly NOT sufficient (accepted).

### Money mirror 138→182 — BUILT + LIVE (review order #1, executed)
- Design exactly as ordered: push-based, append-only, restricted key (`command=` forced receiver, no-pty/no-fwd set), path allowlist, staging dir, signed sha256 manifest, fsync + atomic rename, unique timestamp dirs.
- Receipt policy: **RECEIVED + HASH-MATCH only; REPLAY-VALID NOT CLAIMED** (S1-GAP-02C open) — enforced in receiver text and every receipt.
- 138 signs (ed25519 `mirror-sign`), 182 verifies against `trusted/allowed_signers`; freshness checked from vault/laptop.
- Components: `/home/ari/octopus-mirror/` on 138 (keys, push.sh, known_hosts pinned to 182 hostkey SHA256:7Iur9…AN0), `/usr/local/bin/octopus-mirror-receive` + user `mirror138` (home `/var/lib/mirror-138`) on 182, `octopus-mirror-push.timer` daily 03:30Z UTC (next 2026-09-18).
- First receipts: manual push 20260917T075137Z and systemd-unit push 20260917T075156Z, both `RECEIVED+HASH-MATCH`, 7 files (budget-ledger sha 5d09c95c…, season-meter 14964b88…, provider configs).
- Rollback: `systemctl disable --now octopus-mirror-push.timer` + remove units (138); `userdel -r mirror138` + `rm /usr/local/bin/octopus-mirror-receive` (182); keys live only on 138.

### Traps found while building (for the memory file)
- dropbear rejects OpenSSH's `restrict` authorized_keys option → use explicit no-* set.
- dropbear performs the authorized_keys path check with the LOGIN USER's traversal rights → home under `/var/lib/octopus` (750 octopus:octopus) denied mirror138; fixed by neutral home `/var/lib/mirror-138` (no group grants given).
- `useradd -r` locks the account (`!`) — unlocking with `*` was applied (not proven to be the blocker, but hygiene).
- **OpenSSH 10.0 contract change: `ssh-keygen -Y verify` reads the signed message from STDIN; the old positional form fails with a misleading "incorrect signature"** (reproduced on 3 machines).
- ufw on 182 is INPUT DROP (only 22 open) — do not plan extra ports without owner.

### swap drill conflict surfaced (needs owner decision)
Review asks for a controlled-reboot drill of swap on 138. Standing order says **never power-cycle 138**, and DC-03E0 found **no snapshot backend** on 138 (ext4/eMMC; no btrfs/LVM). The drill therefore requires an explicit owner GO plus a quiesce+backup window. Listed as open owner decision; status stays INSTALLED-NOT-DRILLED until then.
