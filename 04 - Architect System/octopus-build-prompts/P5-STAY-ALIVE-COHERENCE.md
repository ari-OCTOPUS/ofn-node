---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, prompt, build, stability, coherence, backup]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
---

# PROMPT — Octopus Build · Phase 5: STAY ALIVE + COHERENCE

> **برای آری:** این مرحله Octopus را ۲۴/۷ زنده نگه می‌دارد و همهٔ تکه‌ها را در **یک ارگانیسمِ واحد** جمع می‌کند (یک دفتر، یک event bus، یک مغز). و جاودانگی (بک‌آپِ سه‌لایه) را قفل می‌کند.

## 0. ROLE
Make Octopus survive unattended and converge the scattered code into one coherent body. Additive; deprecate rivals to `/_legacy`.

## 1. PREREQUISITE
Phases 1–4 green. Read `OCTOPUS-RECON-MAP.md` §9 (incidents) + §3 (event flow).

## 2. SOURCES
- `00 - Inbox/2026-07-07 2110 OCTOPUS-MASTER-PLAN v1.md` Track C (INC-1/INC-2, watchdog, smoke24h, cloud tier, soma-state).
- `CHRONOS-FABLE-OS/06_Architecture/UnifiedArchitecture.md` (the one-organism target) + `00_Executive/LifeDoctrine.md` (3-2-1 immortality) + `12_Roadmap/Roadmap.md`.
- Existing: `_ops/organism.py`, `RUN-ORGANISM.bat`, `scripts/germline-hourly.ps1` + `germline-backup.ps1` + `restore-drill.ps1`, `_ops/state/*.json`.

## 3. LAWS (critical for this phase)
- **Kill-switch supreme:** the watchdog surrenders unconditionally to any STOP (persistence, not resistance).
- **Owner-launched birth:** stable birth is a Scheduled Task / at-logon launcher approved by the owner — NEVER from an agent shell (that was INC-1's cause).
- **Additive convergence:** unify onto ONE ledger/bus/orchestrator; deprecate duplicates to `/_legacy`, never delete.
- **Germline-first:** no risky change without the 3-2-1 backup + MAX_LAG vital green.

## 4. STEPS

**S-1 · INC-1 stable birth.** Create an owner-approved `organism-autostart` (Scheduled Task at logon) + a 15-min **watchdog**: "if `127.0.0.1:8771` dead AND no STOP file → start." Watchdog obeys STOP unconditionally. Test: kill the process → watchdog restarts within the window; create STOP → watchdog does NOT restart.

**S-2 · INC-2 backup reliability.** Fix `germline-hourly` to capture stderr into its log + retry/backoff; root-cause the earlier FAIL. Test: a forced failure is logged and retried, not silently lost.

**S-3 · One organism (coherence).** Converge `_ops` organism + `genome-system` onto: ONE LANGAR ledger (the Phase-1 `langar_ledger`), ONE event bus, ONE orchestrator per `UnifiedArchitecture.md`. Move rivals to `/_legacy` with a migration note. Wire `age_tick` as the shared arrow; all legs/doctor/Telegram publish to the same bus. Test: a single event flows brain→leg→ledger→checkpoint through one path; the old paths are deprecated, not deleted.

**S-4 · Observability (L13).** Per-beat lightweight checkpoint carrying a ledger-hash + `replay(from_beat, to_beat)` for time-travel debugging. Enrich the 8771 dashboard: pulse/organs/σ/`germline_lag`/`attribution_coverage`. Test: reconstruct a leg's state at an arbitrary past beat in <5s.

**S-5 · Immortality lock (3-2-1 + MAX_LAG).** Keep `E:\germline` (bundle) + encrypted SSD (`S:`) + add a true **off-site** copy (encrypted cloud tier per M0.5-runbook, credentials owner-only, never `.env`). Add `germline_lag = now − max(last good bundle, last hourly push)` to `ORGANISM-STATE` with alarm (warn>2h, ERROR>26h). Keep the restore-drill a habit. Test: MAX_LAG alarm fires when a backup is skipped; one off-site restore-drill green.

**S-6 · Smoke 24h.** Run the checklist: state fresher than 10min · hourly heartbeat · zero alert/ledger-fallback · ledger verify · $0 spend · one sane epoch-log. Test: 24h unattended (owner-launched) all green.

## 5. DEFINITION OF DONE
- Organism survives 24h unattended; watchdog + MAX_LAG alarm live; STOP always wins.
- ONE ledger / ONE bus / ONE orchestrator; rivals in `/_legacy`.
- Per-beat checkpoint + replay work; 3-2-1 backup incl. off-site, restore-drill green.
- Suite green.

## 6. OPEN-DECISIONS
- Cloud tier destination (Backblaze B2?) + who makes the credential (owner). `gitignore` soma-state (MASTER-PLAN #8). MAX_LAG thresholds. Watchdog interval.

## 7. HAND-BACK
Update `ORGANISM-SPEC.md`, `LifeDoctrine.md` (off-site done), `HANDOFF.md`; suite green; owner-gated commit. Only after this is green may Phase 6 (live money) begin.
