# 01 SCOPE AND METHOD — A01 Repository Cartographer (2026-08-16)

## Mode
READ_ONLY. Writes confined to `COUNCIL_REPORTS/2026-08-16-wave-01/A01_repo_cartographer/`.
No service restarted/stopped/deployed; no packages installed; no ports opened; no external API
calls; no Telegram sends; no migrations; no secret values opened (`.env` existence/size recorded only);
all repository content treated as untrusted data (prompt-injection hazard) — no instruction found
inside any file was followed.

## Scope
- Primary: `F:\backup` (git repo + Obsidian vault + `_ops` organism runtime + `4d_system` + projects).
- Secondary: machine-level context needed to answer "one repo or many": `C:\Users\Armin\Desktop`
  OCTOPUS/NBB directories (enumerated + git-inspected only), `E:\germline` remote (via git metadata),
  Windows process list and Task Scheduler (query only).
- Out of scope (left to other agents): deep authority-logic audit (A04), runtime dataflow/contract
  verification (A03), live-runtime internals beyond entrypoints/state files (A02).

## Method (evidence tiers per observation)
| Tool | Purpose | Tier |
|------|---------|------|
| `git rev-parse/branch/log/status/worktree/remote` | repo state: branch/HEAD/dirty/worktrees/remotes | T2 |
| `Get-CimInstance Win32_Process` | live python PIDs + command lines + start times | **T0** |
| `schtasks /query` | scheduled OCTOPUS tasks + next-run | **T0** |
| Read of `_ops/state/ORGANISM-STATE.json`, `FREEZE.flag`, ledger tail | live runtime state | **T0** |
| `find`/`ls`/`du`-style enumeration | filesystem map (excluded .git internals, __pycache__, node_modules, venvs, caches, weights, secrets, build artifacts, zips) | T2 |
| `grep`/`diff` static scans | entry points, imports, TODO/stub markers, duplicate names, three-way nbb_cp diff | T2 |
| Reading MANIFEST/README/ADR/ARCHITECTURE docs | documentation-drift comparison | T4/T5 |
| `.pytest_cache` lastfailed inspection | prior test-execution evidence | T1 (stale) |

No tests were executed by this agent (test runs can mutate state; execution belongs to a wired lane).
Test-related classifications therefore rely on the existence of test files + cached run artifacts only.

## Timestamps
All observations 2026-08-16 between ~23:30 and ~24:00 local (UTC+10:00). Git HEAD at observation:
`028fe81` (committed 23:27:30+10:00). Working tree dirty (154 M / 62 ?? / 3 D).

## Confidence calibration
- T0 process/state observations: 0.9–0.97 (single point in time; no long sampling).
- T2 code structure: 0.85–0.95 (static scans, sampled not exhaustive over 2,250+ py files).
- Doc comparisons: 0.8 (key SoT docs read; not every vault note).
- Anything marked UNKNOWN is genuinely unobserved, not assumed.
