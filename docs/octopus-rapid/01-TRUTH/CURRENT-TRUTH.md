# CURRENT TRUTH — 138 · 2026-08-27T03:00:17+00:00Z
- clock: AEST/+1000 local, UTC synced, NTP active (timedatectl 2026-08-27T03:00:17Z) — directive's "138 unsynced" is STALE, recorded as contradiction C-1
- 180 clock: UTC, chronyd, synced (source: ssh timedatectl 02:54:30Z)
- 182 clock: timesyncd active; offset UNKNOWN (no chronyc/sntp on board) — C-2; ordering via sequence/idempotency only until offset known
- runtime: ofn.service @ /home/ari/ofn, worktree clean before this branch; branches live: owner-center + cockpit-v2 (HEAD 6070f51)
- VERIFIED_CASH = 0 AUD (source: audience.revenue_events=0, painting booked_amounts unset; verified 2026-08-27T03:00:17+00:00Z)
- mesh: policy sha eee2812d×3 boards; roles sha c0ebb5f0×3; incident 8fca48f3 (PC transport), 115b08f7 (expired-build, closed path)
- B2: packet 04af67d5 verdict was unresolved/claims-empty (root cause: auto-verify carried IDs only) → re-verify 1ce02788 dispatched with embedded claims, max_n=1

## board_138_source_truth (2026-08-30, owner-audited)
yaml:
  repository: ari322/ofn-node
  canonical_branch: backup/board138-20260830
  canonical_commit: c1969bce5384f3371b916470299c991627c3d63c
  remote_verified: true
  verified_method: git-ls-remote
  default_main_commit: 2533aa3
  main_merge_status: blocked_pending_audit
  tests:
    collected: 2076
    passed: 2065
    failed: 0
    errors: 1
    skipped: 10
  excluded_runtime_evidence_files: 31
  secret_scan: clean
