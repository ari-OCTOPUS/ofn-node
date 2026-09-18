# LANE REPORT — S1-PROOF-OF-LIFE-20260917 (week-1 survival slice)
GOV_VERSION=V8 · LADDER=L2 · Lane: S1-PROOF-OF-LIFE · Date: 2026-09-17 · Agent: ZCode (SENIOR-AGENT seat)

Season charter: `ACTIVE-SEASON-S1-PROOF-OF-LIFE-20260917.md` (installed verbatim from owner text this session).

## Receipts (Tier=Class ruling; INTENT/RESULT)
| id | act | scope |
|----|-----|-------|
| `S1POL-GAP02-182-20260917T072442Z-9d11b7dd9d3a` | patch apply_signed_inbound.py on 182 + archive stale bundles + restart .path units | node 182 (witness) |
| `S1POL-SWAP-138-20260917T072442Z-d391a8074fc9` | create+enable 2G /swapfile on 138, fstab + vm.swappiness=10 persisted | node 138 (heart) |

REMOTE_MUTATIONS: 2 boards touched (both additive/reversible, receipts + rollback below). Vault: 3 new files + 1 tail-append. DELETE/OVERWRITE/MOVE on vault: 0. Secret values printed: 0.

## What was done
1. **Season charter installed** — owner text verbatim → `ACTIVE-SEASON-S1-PROOF-OF-LIFE-20260917.md`; activation note tail-appended to `OCTOPUS/CURRENT-TRUTH.md` (canonical per size+mtime; UTF-8 verified; working-tree only — obsidian-sync lane commits).
2. **GAP-02 CLOSED (priority zero)** — the harvest's «حلقهٔ PathExists ≈۲ هسته» on witness 182:
   - Root cause: stale signed bundles (Aug 17 registry / Aug 22 checkpoint) never consumed after classification + level-triggered `PathExists` .path units → systemd respawned the two apply services forever (2×100% CPU; `verify_chain` 3.8 s over 107 MB audit × 2 services, continuously).
   - Fix: `_consume_bundle()` in `apply_signed_inbound.py` (move-only archive to `state/inbound-apply/consumed/`); verify logic untouched; not hash-pinned; sha `642f048c→4ea22df2`; node backup `.bak-gap02-20260917T0720Z`.
   - Verified: services frozen at 07:18:32/41Z, zero respawns in 6-min window, no apply procs, load **3.50→2.02↓** (rest = GAP-02b). Full pack: `06-EVIDENCE/S1-PROOF-OF-LIFE-20260917/gap02-182/ROOT-CAUSE.md`.
3. **Swap on 138 ENABLED** — `/swapfile` 2G (mkswap UUID 241dbe69-6cf9-4e5e-8e20-0e4e1aa6a49d), fstab line + `/etc/sysctl.d/99-octopus-swap.conf` (swappiness=10). Pre-state receipt: Swap 0B, disk 39G free.
4. **New findings registered:** GAP-02b (sensorium ~1 core design cost; RSS 1.9G > MemoryMax=1200M ⇒ restart-risk OOM loop; no retention pruning wired; derived.jsonl 1.03GB) and GAP-02c (verifier G13 `from_empty ≠ from_snapshot` replay divergence, pre-existing, first verify run since Aug 17). Both need their own lanes; deliberately NOT blind-surgeried today.

## Week-1 scoreboard (season §5)
| item | status | evidence |
|------|--------|----------|
| GAP-02 close | ✅ DONE 2026-09-17 | ROOT-CAUSE.md + postfix-verification.txt |
| swap 138 | ✅ DONE 2026-09-17 | receipt S1POL-SWAP-138 (output in session log; fstab readback) |
| overlay export to side branch | ✅ covered by E1A + PR#263 (same day, per harvest §10.1) | 06-EVIDENCE DC-03E1A receipts |
| money-state mirror 138→182 | ⬜ OPEN (next) | plan below |

## What remains (ordered)
1. **Mirror 138→182** (daily, hash-manifested): generate dedicated ed25519 on 138 (never leaves node) → restricted `command=` entry in 182 authorized_keys bound to a fixed receiver (writes to `/var/lib/octopus/mirror-138/` + sha256 manifest) → systemd timer on 138 (daily 03:xxZ) pushing `state/api-budget/` ledger + season-meter/revenue state (NOT raw PII beyond leads hash-manifest). Rollback: remove timer + authorized_keys line.
2. **GAP-02b lane**: index pruning (wire RETENTION_SECONDS), flush cadence, then restart-under-quota drill (fresh-start RSS measurement before touching the service).
3. **GAP-02c lane**: journal replay forensics (events.jsonl vs snapshots divergence at n=3,077,923).
4. Season weeks 2–3 per charter (guards PRs, RevenueRun contract, executor transport — owner vote precondition stands).

## What failed
- Nothing in this slice. Sensorium burn intentionally left unfixed (out of safe scope; restart risk documented) — recorded as GAP-02b, not silently dropped.

## Rollback
- GAP-02 fix: see ROOT-CAUSE.md §6 (restores the loop by design — do not run unless investigating).
- Swap 138: `sudo swapoff /swapfile && sudo rm /swapfile`; remove fstab swapfile line and `/etc/sysctl.d/99-octopus-swap.conf`.
- Vault: delete `ACTIVE-SEASON-S1-PROOF-OF-LIFE-20260917.md`, this lane dir, evidence dir; un-append CURRENT-TRUTH last line.

## Honesty notes
- All numbers above are from live probes this session (timestamps UTC in evidence files) or the cited files; none from memory.
- The apply-loop fix was validated by the patched units themselves in the real trigger path, not only by a manual run.
- 182 remains at ~1 core steady burn (GAP-02b) — GAP-02 is *closed for its named 2-core PathExists loop*, not for all CPU load on 182.

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
