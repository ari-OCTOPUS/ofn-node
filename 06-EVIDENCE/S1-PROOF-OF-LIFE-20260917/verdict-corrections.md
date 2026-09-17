
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
