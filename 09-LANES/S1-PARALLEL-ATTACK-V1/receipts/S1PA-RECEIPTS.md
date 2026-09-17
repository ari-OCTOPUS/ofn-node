# S1-PARALLEL-ATTACK-V1 — Receipts

GOV_VERSION=V8 · LADDER=L2 · Mission date 2026-09-17 (t0 ≈ 08:04Z, close ≈ 08:40Z)
Receipt id convention: `S1PA-<UTC>-<sha256(INTENT)[:12]>` (owner Tier ruling).

## L-A — MIRROR-HARDENED-P1 ✅
- INTENT (pre-deploy): `S1PA-20260917T081400Z-fcb37aee6845`
- Negative suite: **23/23 PASS** (throwaway home, own test keypair; cases N1–N21+P1/P2).
- Deploy pre-images → post:
  - 182 receiver `/usr/local/bin/octopus-mirror-receive`: `3bcae465…` → `271973cc…` (py_compile OK; backup `.bak-s1pa-*`)
  - 138 sender `/home/ari/octopus-mirror/push.sh`: `9648858d…` → `f8779ca2…` (bash -n OK; backup `.bak-s1pa-*`)
- Live proof: push seq 1 → `RECEIVED+HASH-MATCH` v2, manifest `0628dafd…`, 7 files, both ledgers chained.
- Live duplicate push → `REJECTED duplicate_manifest_scope`, quarantined at
  `/var/lib/mirror-138/quarantine/20260917T082313Z-duplicate-manifest-scope-4a5166c3a1f0b`.
- Hygiene: unrestricted `dbg-mirror-test` key removed from mirror138 authorized_keys (backup `.bak-s1pa-*`; only forced-command key remains).
- Rollback: restore both `.bak-s1pa-*` files; optionally `systemctl disable --now octopus-mirror-push.timer`.

## L-B — S1-GAP-02B-PROFILED ✅ (profile slice; patches measured, NOT deployed)
- B1 telemetry live since 08:07Z (30s cadence, 4h bound): cgroup memory **pinned at ceiling** `memory.current=2,147,397,632` vs `max=2,147,483,648` (2048M), `swap.current≈710MiB`, cpu.pressure avg300=0.
- B5 patch table (same frozen 3000 real events, single run, real eMMC):
  | variant | wall | cpu | semantic preservation |
  |---|---|---|---|
  | A baseline fsync-per-event | 4.97s | 1.234s | reference |
  | B batch-commit(100) | 0.542s (**9.2×**) | 0.488s (**2.5×**) | journals byte-identical; replay hash equal |
  | C lazy-flush(32) | 0.582s | 0.451s | same |
- B3 inventory: events.jsonl 445MB (3.079M lines, 144.6 B/event), snapshots 1225 files / 51.9MB, rate 0.28 events/s.
- B6 retention dry-run: snapshots ARE wired (`octopus-prune-snapshots.timer` hourly, 24h window — corrects ROOT-CAUSE's "no pruning wired" for snapshots); **events.jsonl + derived have NO retention wired**; 30-day projection ≈ +105MB (UNVERIFIED estimate).
- Files: `telemetry-02B.jsonl`, `lb/lb-bench.json` on 182 under `/var/lib/octopus/state/s1pa-attack/`.

## L-C — S1-GAP-02C-FIRST-DIVERGENCE ✅ (forensic; fix NOT deployed)
- Journal integrity (R1/R4/R5 runners): 3,078,856 records, **0 missing / 0 duplicate seq / 0 duplicate content-hash / 0 corrupt / 0 file-order inversions / 0 CR / 0 torn lines**.
- Field-level diff (R2/R3): the G13 divergence is EXACTLY ONE FIELD — `health["OCT-SENSE-099"]`: from_empty=`healthy`, snapshot-lineage=`degraded`. Counters, identity, 512-hash window all equal.
- Timeline: all 13,823 journal health events for 099 are `healthy`, last at **seq 3,021,357**; every retained snapshot (1,216, back to 2026-09-16T080059Z @ **seq 3,054,411**) already says `degraded` → onset window **[3,021,357 … 3,054,411]** (33,054 events; bounded by retained anchors — older snapshots pruned, so <1000 narrowing impossible without older anchors).
- Mechanism (source): `octopus_sensorium/app.py:784` sets `self.health[sensor_id]="degraded"` in memory WITHOUT appending a health event to the journal. 099 = `policy_safety`, family meta, status SHADOW (registry.yaml:5950).
- Proposed fix (NOT deployed; sensorium restart currently blocked by 02B stance): journal every in-memory health transition (degraded/quarantine/unavailable) as a `health` event; then G13 converges by construction.
- Files: `lc_diff.py`, `lc_099.py` + outputs on 182.

## L-D — witnesses LAUNCHED (24h verdict due ~2026-09-18T08:28Z)
- W1 frozen-window watcher LIVE (PID 762748, 288×300s, read-only): baseline activations frozen at **07:18:41 / 07:18:32 UTC, NRestarts=0** (header's `historical_frozen_since_fix:false` is a prefix-matching artifact — see script note; sample data is authoritative).
- W2 exactly-once (sandbox toy path unit): **PASS** — 1 activation, 0 refires after consume (30s observation).
- W3 crash-boundary/consume unit tests on REAL `_consume_bundle()`: **4/4 PASS** (consume-once, idempotent, reversal byte-identical, same-fs rename atomic).
- W4 watch-path isolation: only 2 `.path` units exist, both watch `inbound/`, none watch `consumed/`; archive growth tracked in W1 samples.
- Pending (non-blocking, registered): production-signed fixture over the real inbound path needs an owner/laptop signature ceremony.

## L-E — SWAP-138-PREFLIGHTED-FB ✅ (read-only; NO reboot)
- Active: `/proc/swaps` → `/swapfile` 2,097,148K, used 512K, prio −2; `free`: Swap 2047/0/2047 MiB.
- fstab `/swapfile none swap sw 0 0` — `findmnt --verify`: **0 errors**, 3 benign warnings (perm-probe + swapfile-is-regular-file).
- Swapfile: 2.00GiB, mode `600 root:root` ✓. `vm.swappiness=10`.
- Versions: kernel `6.1.115-vendor-rk35xx`, systemd 257; zswap loaded (zstd/zbud). Root UUID `1597e95c-76e0-4d21-9265-cecea2aa24eb`. dmesg: swap added at uptime 197008s (= today 07:22Z, post-install).
- Memory pressure: none (3.1Gi available, swap ~0 used) → no conditional shrink warranted; runbook documented below.
- Recovery note (boot failure involving swap): rescue `init=/bin/sh` → `mount -o remount,rw /` → comment the `/swapfile` fstab line → continue boot; recreate swapfile later (`dd 2G`, `chmod 600`, `mkswap`, `swapon`).
- Drill (reboot test) still requires explicit owner GO (standing "never power-cycle 138" + no snapshot backend) — unchanged, centralized in L-H.

## L-F — ARCHIVE-HEALED-P1 ✅ (survey + hygiene; zero organism moves needed)
- 138 mirror staging: EMPTY (trap cleanup verified). Logs: 3 receipts retained (evidence).
- 182: mirror quarantine holds 1 evidence entry (duplicate push); s1pa-attack sandbox holds bench/witness artifacts (active).
- Snapshot duplicates: none — 1,225 unique files under wired 24h retention.
- Session scratch temps (Windows `$TEMP/s1pa-*`, node `/tmp` uploads) removed/self-cleaning; no vault paths stale.
- No `rm -rf`; no organism-consumed path touched; nothing moved ⇒ no manifest rows required (this file is the receipt).

## L-G — MIRROR-RECEIPT-SCHEMA-V1 ✅ — see `MIRROR-RECEIPT-SCHEMA-V1.md` (implemented + enforced + live-verified).

## L-H — Attack ledger
- `ATTACK-LEDGER.jsonl` pulses at t0 + close (cadence spec conflict 15/30min recorded at t0; wall-clock of this session ≈ 35min made per-15min pulses moot).
- Owner decisions centralized: (1) swap drill GO — pre-existing, unchanged; (2) OPTIONAL production-signed fixture ceremony for witness-2 hardening. No new blocking decisions.

## Compliance
REMOTE mutations: mirror receiver/sender upgrade (authorized L-A), authorized_keys test-key removal, watcher/sandbox processes under s1pa dirs — each with pre-image + rollback above. No secrets read or printed. No OCTOPUS_WIRE_*/OFN_WIRE_* flags touched. No service restarted/stopped (only S1PA-owned toy units, cleaned). No reboot on 138. Rollback paths listed per lane.
