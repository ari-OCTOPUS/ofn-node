# 05 RISKS — A01 Repository Cartographer (2026-08-16)

Severity scale: CRITICAL / HIGH / MEDIUM / LOW. Each risk lists mitigations already present (observed) and what is missing.

## R-01 · Organism running FROZEN for hours (CRITICAL)
- **What**: Budget FREEZE.flag since 2026-08-16T20:09:05 (Errno 22 on budget-state.json settle); organism ticks on with `frozen: true`.
- **Impact**: All grants frozen; governor allocations shadow-only; any dependent subsystem that *expects* settle to succeed may degrade silently. Fail-closed behavior is correct, but the incident is unattended.
- **Mitigations present**: I3 fail-closed by design; loop survives; alert path exists (governor-alerts.md).
- **Missing**: root-cause fix for the Windows file-handle fault; owner acknowledgement; a post-freeze recovery procedure. **No project file should be "repaired" by a council agent — only a wired lane with owner word may touch it.**
- **Next**: A02/A03 diagnose read-only (locks, concurrent writers); owner decides clear/recovery.

## R-02 · Triple-fork NBB-CP with no canonical home (HIGH)
- **What**: `nbb_cp` exists at `03 - Projects/NBB-Control-Plane/src/nbb_cp`, `4d_system/src/nbb_cp`, and Desktop `OCTOPUS-NBB-CP-WORKING/nbb-control-plane/src/nbb_cp` — each with unique adapters; all three differ in api/app files. Desktop repo is the only one under active development (commit today 16:02) and its remote is a **git bundle file**.
- **Impact**: "The NBB brain" is ambiguous; a fix applied to one fork silently diverges; governance claims about NBB-CP cannot be verified against a single codebase; a lost bundle file would orphan the Desktop repo's history.
- **Missing**: owner decision on canonical home; read-only mirrors for the others; bundle-file backup strategy.

## R-03 · Repo-in-repo at genome-system (HIGH)
- **What**: `07 - Knowledge/genome-system/` has its own `.git` directory while its files are also tracked by the root repo (both dirty: root 219, nested 220 entries).
- **Impact**: Double-tracking → divergent states; commits to root repo and nested repo interleave unpredictably; `git status` noise; risk of accidental deletion from one side or the other; nested `.git` itself may be committed someday (gitignore risk).
- **Missing**: decision: promote to submodule, remove nested .git (keep root tracking), or untrack from root.

## R-04 · Claim-driven architecture drift (MEDIUM)
- **What**: Brief claims (L0–L8, Sensorium, viability loop, bitemporal ledger, A2/A4) do not match the system that actually runs. Docs are honestly labeled, but any new engineer/agent reading the brief first will look for things that don't exist.
- **Impact**: Wasted verification effort; false "missing feature" reports; confidence erosion between owner and council.
- **Mitigation present**: `ARCHITECTURE-LAYERS` ERRATA explicitly says "don't trust this doc, check disk first".
- **Missing**: a single current SoT document (this wave's outputs can seed it) and vocabulary alignment with the owner.

## R-05 · Stale lore inside live code (MEDIUM)
- **What**: `organism.py` docstring references `app.py:8768` brain lock — no app.py exists; `4d_system/start.bat` points to a non-existent Desktop path; KRE README install path wrong.
- **Impact**: A future operator follows the lore and expects a component on 8768 (which is actually free — a real port squatting risk if a process ever binds it believing it's the brain lock).
- **Missing**: one-line doc/launcher corrections by a wired lane.

## R-06 · "Memory affects reasoning" unproven (MEDIUM)
- **What**: Memory layer is write-heavy; read-back paths were only recently restored; consolidation lacks dedup/retract; live recall_reach small (median 21 events).
- **Impact**: Self-improvement claims ("memory drives cognition") may overstate; the loop may be spending budget on writes nobody reads.
- **Next**: A02 trace one live recall path end-to-end; A03 verify the consolidation contract.

## R-07 · Test debt with recorded failures (MEDIUM)
- **What**: Root pytest cache records 5 lastfailed tests; `_ops` cache records 1 (test_context_assembler fail-soft). Cache dates Aug 5–6 — stale, but unresolved at that time.
- **Impact**: Unknown current suite health; "18/18 re-verified" (HEAD commit message) refers to the octopus_v3 suite only.
- **Missing**: a fresh, sanctioned full-suite run + failure triage (see 07_TEST_PLAN).

## R-08 · Governance primitives behind unset flags (MEDIUM)
- **What**: Dual-veto wiring (`OCTOPUS_WIRE_DUAL_VETO`) unset; 4d observe lane (`OCTOPUS_OBSERVE_4D`) unset; octopus_v3 P0 WIRED=False; ACTIVATION-GOVERNOR-LLM.flag.off.
- **Impact**: Claimed "governance" is dormant by design; if owner believes it is active, coverage is illusory. Conversely, arming without owner word would violate the design's own fail-closed intent.
- **Missing**: owner decision per flag; a flag-status inventory (this list is a start).

## R-09 · Naming collisions across trees (LOW→MEDIUM)
- **What**: 6 `contracts.py`, 5 `server.py`, 5 `schemas.py`, 5 `registry.py`, 4 `policy.py` in `_ops`+`4d_system`; two `test_dual_brain*.py` (documented, intentional); `OCTOPUS/` folder is the static-viz layer, not the organism.
- **Impact**: Wrong-import risk; grep-ambiguity in future audits; the "OCTOPUS" name pointing at the least-organism directory misleads newcomers.
- **Next**: name collisions register kept in DUPLICATE_CANDIDATES.csv; optional renaming later.

## R-10 · Frozen Desktop checkouts and orphaned worktrees (LOW)
- **What**: ~12 Desktop checkouts pinned at a3000f0 (2026-07-14); 2 orphaned archived worktrees; 5 active worktrees.
- **Impact**: Disk clutter; someone may edit the wrong checkout believing it's live; confusing evidence sources.
- **Next**: mark read-only or archive; keep one canonical checkout.

## R-11 · Secrecy hygiene (LOW — positive)
- **What**: `.env` (2039 B) exists with `OCTOPUS_WIRE_VAULT_RAG=1` visible; this agent did NOT open secret values. Telegram tokens live in env/config by design (TgClient-only egress).
- **Impact**: minimal observed; council-wide rule: never print env content. Board queue + owner-allowlist in telegram center are the main trust surfaces for A04.
