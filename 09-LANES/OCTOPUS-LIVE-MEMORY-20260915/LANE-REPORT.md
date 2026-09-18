# LANE-REPORT — OCTOPUS-LIVE-MEMORY-20260915

GOV_VERSION=V8 · LADDER=L2 · status=COMPLETE · 2026-09-15 ~08:10Z

## What was done (owner choice: گزینهٔ ۴ — حافظهٔ زنده)

Turned FORGOTTEN-100 into a permanent, self-maintaining memory brain on the organism:

1. **Engine** `deep_scan_tick.py` (522+ lines, stdlib-only) deployed at
   `/home/ari/ofn/state/deep-scan/` (sha256 13317075…, copies: lane scripts/ + 138):
   probe_runtime (queue, breakers via ops_agent import, fleet-jobs histogram, failed
   units, facts/tg-inbox counters, halt markers) · parse_mirror (checklists,
   frontmatter, OPEN-WORK OW items, status-words — capped at max_parse_files=400) ·
   prune (anchor re-verification → resolved/verified events) · grow (anchor-mandatory,
   dedupe-keyed, capped 15/tick, quarantined if anchorless) · reconcile (discrepancy
   classes incl. OPTIONAL_SOURCE_UNAVAILABLE + DOCS_CLAIM_RUNTIME_IDLE) · rank (U×R+C/5)
   · bounded delta report + CURRENT-TRUTH-ready block (never auto-appended) · DASHBOARD.
2. **Lifecycle** append-only `findings-events.jsonl` (286 events after acceptance):
   open→verified→queued→executed→resolved|abandoned; terminal sticky; request-refs
   promotion via `[F-xxx]` tags in canary requests (evidence graph edge).
3. **Seed**: FORGOTTEN-100 imported (100 open events).
4. **Vault mirror** (optional source): 71MB/1105 files seeded to
   `vault-mirror/` (09-LANES + owner-board + dashboards + decisions + handoff + plans +
   AGENTS.md; worktree/sources/py excluded). Absent mirror ⇒ SKIPPED_OPTIONAL_SOURCE_UNAVAILABLE.
5. **Timer**: `octopus-deep-scan.timer` Mon 04:00Z UTC, Persistent, RandomizedDelay 300;
   service User=ari CPUQuota=30% MemoryMax=200M Timeout=300. Enabled; first auto run
   2026-09-21T04:03Z.
6. **Acceptance (owner: "after 3 successful runs")**: 4 ticks back-to-back RC=0,
   zero collector errors, **zero duplicate finding ids**, 160 distinct findings,
   dashboard verified (F-001 rank 21 top; RY breaker OK ⇒ candidate correctly absent;
   B5 open ⇒ candidate present; tg-inbox=0 discrepancy auto-raised; facts 371→401 live).

## Defects found & fixed during acceptance

- bootstrap: rebuild_current read missing events file → guarded (run 0 crash)
- seed key mismatch (`index` vs `findings`) → fixed
- Windows-form paths (F:/backup/…) broke mirror lookups → normalize_vault_path
  (93 first-tick SOURCE_ABSENT "verified" events kept in log as documented history;
  states correct, why-text wrong — append-only discipline preserved)
- verified-event spam on unchanged findings → first-verification-only emission

## Known limits (honest)

- Mirror is a static seed; freshness decays (mirror_age_hours reported; data_stale
  flag at 14d). Laptop-side weekly sync is future work (one rsync/tar command).
- Mirror candidates default needs_review=true (rank defaults U2R3C3) — anti-noise
  tradeoff: growth is capped and flagged until a human/agent confirms scores.
- V-OW-* candidates double-enter the seeded OW items substantively (different ids);
  needs_review merge is manual for now.
- Runtime probes cover breakers/fleet-jobs/units; starvation (OW-8) and retire-miss
  (F-001) classes are seeded but not yet auto-probed (next iteration).

## Rollback

`sudo systemctl disable --now octopus-deep-scan.timer` + archive
`/home/ari/ofn/state/deep-scan/` (mv to /home/ari/archive_*). Engine + artifacts also
live in this lane (scripts/, artifacts/). No other runtime surface touched.

## Outcome vs owner acceptance

«بعد از سه اجرای موفق، پروژه دیگر با context loss یا تعویض ایجنت، کارهای حیاتی را
فراموش نمی‌کند» — the memory now lives on 138, independent of laptop and agent: any
future agent (or the owner) reads DASHBOARD.json + findings-current.json and inherits
the entire ranked debt register with anchors. ✔
