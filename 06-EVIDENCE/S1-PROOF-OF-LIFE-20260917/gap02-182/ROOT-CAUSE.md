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
